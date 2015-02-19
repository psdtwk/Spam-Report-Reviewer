import praw
import requests
import re
import time
import os

agentstring="/r/spam submission deleter version 2.0 by /u/captainmeta4"
r = praw.Reddit(user_agent=agentstring)
headers = {'User-Agent': agentstring}

bot_user = "Spam_Report_Reviewer"
bot_pass = os.environ.get('password')

class bot(object):

    def login_bot(self):
        print ("logging in as bot...")
        r.login(bot_user, bot_pass)
        print ("...success")

    def check_messages(self):
        print ("checking messages...")
        try:
            r.get_unread(limit=1)
        except:
            print ("...failed.")
            self.login_bot()
            print ("checking messages")

        users_to_check = []

        #Prevent crashing on 503 Service Unavailable
        try:
            for message in r.get_unread(limit=None):

                message.mark_as_read()

                if message.author.name!="captainmeta4" and "spam" in message.subject.lower():
                    users_to_check.append(message.author.name)
                    print ("message from /u/"+message.author.name)
                elif message.author.name=="captainmeta4" and "spam" in message.subject.lower():
                    users_to_check.append(re.search("[\w-]+",message.body).group(0))
                    print ("order from /u/captainmeta4 - check /u/"+message.body)
        except:
            pass

        return users_to_check

    def run_reports(self, users_to_check):

        for searchuser in users_to_check:

            print ("running report on "+searchuser)

            #Load the spam reports
            spamreports = r.search("author:"+searchuser, subreddit="spam", sort = "new", limit=None)

            print ("List of spam reports loaded.")

            #Initialize stuff
            alreadychecked = []
            nonbannedusers = []
            count=0
            dupcount=0
            sbcount=0
            invalidcount=0

            #Check through spam reports
            for thing in spamreports:
                #needs to be a try so that we can ignore invalid submissions
                try:
                    reporteduser=str(re.search("(?:u(?:ser)?/)([\w-]+)(?:/)?", thing.url).group(1))
                      
                    #If it's not a duplicate...
                    if reporteduser not in alreadychecked:
                        #...then check profile
                        u = requests.get("http://reddit.com/user/"+reporteduser+"/?limit=1", headers=headers)

                        #Deal with any ratelimiting
                        while u.status_code==429:
                            print ("Too many requests. Waiting 10 seconds")
                            time.sleep(10)
                            u = requests.get("http://reddit.com/user/"+reporteduser+"/?limit=1")

                        #If shadowbanned...
                        if u.status_code==404:
                            print ("shadowbanned: /u/"+reporteduser)
                            sbcount+=1
                        else:
                            print ("not shadowbanned: /u/"+reporteduser)
                            nonbannedusers.append(reporteduser)
                                    
                        alreadychecked.append(reporteduser)

                    #If duplicate...   
                    elif reporteduser in alreadychecked:
                        print ("duplicate entry: /u/"+reporteduser)
                        dupcount+=1

                except:
                    print ("invalid submission: "+thing.url)
                    invalidcount+=1

                count+=1

            #If there are nonbanned users...
            if len(nonbannedusers)!=0:

                #Alphabetize the list
                nonbannedusers.sort()

                print ("assembling message")

                #Put the message together
                message = ("^(This message was automatically generated by /u/captainmeta4's /r/spam review script. )[^(Github)](https://github.com/captainmeta4/Spam-Report-Reviewer)\n\n"
                           "/u/"+searchuser+" has "+str(count)+" /r/spam reports, of which "+str(dupcount)+ " are duplicates and "+str(invalidcount)+" are invalid submissions that do not link to a userpage.\n\n"
                           "Of the "+str(count-dupcount-invalidcount)+" unique users reported, "+str(sbcount)+" have been shadowbanned, leaving the following "+str(len(nonbannedusers))+" non-banned users.\n\n")

                #If not on your own profile (so no auto admin message), add instructions to send to admins
                message += ("To send this list to the admins, click \"source\""
                    " and copy/paste the list into a [new message to /r/reddit.com](http://www.reddit.com/message/compose?to=%2Fr%2Freddit.com)\n\n")

                for user in nonbannedusers:
                    message = message+"* /u/"+user+"\n"

                #Send message to user
                try:
                    r.send_message(searchuser,"Spam reports",message)
                    print ("message successfully sent to /u/"+searchuser+".")
                except:
                    r.send_message("captainmeta4","Spam reports","I could not send a message to /u/"+searchuser)
                                        
            #else (if there are no nonbanned users)
            else:
                print ("/u/"+searchuser+" has no non-banned /r/spam reports.")
                r.send_message(searchuser,"Spam reports","You have no non-banned /r/spam reports.")

    def run_cycle(self):

        print ("running cycle")

        users_to_check = self.check_messages()

        if len(users_to_check)>0:

            self.run_reports(users_to_check)
        else:
            print ("no new messages")

spambot=bot()
spambot.login_bot()

while 1:
    bot.run_cycle(spambot)
    print ("Sleeping for 30 seconds")
    time.sleep(30)

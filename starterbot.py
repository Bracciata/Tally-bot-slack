import os
import time
import re
from slackclient import SlackClient
import json
import requests
import urllib
import subprocess
import tempfile
# instantiate Slack client
slack_client = SlackClient('')
user_client= SlackClient('')

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
ADD_COMMAND = "add "
CREATE_COMMAND = "create "
SET_COMMAND = "set "
DELETE_COMMAND="delete "
HELP_COMMAND="help"

MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def findList(listname, channel):
    count = None
    deleted=False
    messageHistory = user_client.api_call("channels.history", channel=channel)
    for message in messageHistory['messages']:
        try:
            if count==None:
                if deleted==False:
                    if message['subtype']=='bot_message':
                        if message['text'].startswith(listname+" total: "):
                            count =str(message['text'])[len(listname+" total: "):]
                        if message['text'].startswith(listname+" deleted"):
                            deleted=True
        except:
            print("user message")
    return count
def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(
        HELP_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(ADD_COMMAND):
        worked=False
        try:
            amountAndListName = str(command)
            amountAndListName = amountAndListName[len(ADD_COMMAND):]
            amountAndListName = amountAndListName.strip()
            amount=None
            listName=amountAndListName
            for i in range(0, len(amountAndListName)):
                if amount==None:
                    if amountAndListName[i] == ' ':
                        try:
                            amount = amountAndListName[:i]
                            amount=amount.strip()
                            amount =int(amount)
                            listName = amountAndListName[i:]
                            listName=listName.strip()
                        except:
                            amount=None
            listName=listName.strip()
            if findList(listName,channel)==None:
                response = None
            else:
                count = findList(listName,channel)
                if amount==None:
                    amount=1
                response = "Sure added " + str(amount)+" to " + listName
                worked=True
                responseFinal =listName+" total: "+str(int(count)+int(amount))
        except:
            response = None
         # Sends the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
        if worked:
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=responseFinal
            )
    elif command.startswith(CREATE_COMMAND):
        listName = command[len(CREATE_COMMAND):]

        response = "Sure created "+listName
        responseFinal =listName+" total: "+str(0)
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=responseFinal
        )
    elif command.startswith(SET_COMMAND):
        worked=False
        try:
            amountAndListName = str(command)
            amountAndListName = amountAndListName[len(ADD_COMMAND):]
            amountAndListName = amountAndListName.strip()
            amount=None
            for i in range(0, len(amountAndListName)):
                if amount==None:
                    if amountAndListName[i] == ' ':
                        amount = amountAndListName[:i]
                        listName = amountAndListName[i:]
                        amount=amount.strip()
                        listName=listName.strip()
            if findList(listName,channel)==None:
                response = None
            else:
                response = "Sure set total of "+listName+" to " + str(amount)
                worked=True
                responseFinal =listName+" total: "+str(amount)
        except:
            response = None
         # Sends the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
        if worked:
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=responseFinal
            )
    elif command.startswith(DELETE_COMMAND):
        listName = command[len(DELETE_COMMAND):]
        response = listName+" deleted"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
    elif command.startswith(HELP_COMMAND):
        response = "Try the following commands:\n   @tally add (amount (optional)) (listname)\n   @tally set (amount) (listname)\n   @tally create (listname)\n   @tally delete (listname)"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
    else:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text= default_response
        )
def networkCheck():
    print ("test 1")
    loop_value = 1
    while loop_value == 1:
        print ("test 2")
        try: 
            urllib.request.urlopen("http://www.google.com")
            loop_value = 0
        except urllib.error.URLError as e:
            print(e.reason)
        time.sleep(5)
def checkRunning():
    runningPrograms=""
    with tempfile.TemporaryFile() as tempf:
        proc = subprocess.Popen('ps -aef | grep python', stdout=tempf,shell=True)
        proc.wait()    	    
        tempf.seek(0)
        runningPrograms = str(tempf.read())
    print(runningPrograms)
    return runningPrograms.count('python/slack/tallyBot/Tally-bot-slack/starterbot.py')
if __name__ == "__main__":
    if  checkRunning()==1:
        networkCheck()
        if slack_client.rtm_connect(with_team_state=False):
            print("Starter Bot connected and running!")
            # Read bot's user ID by calling Web API method `auth.test`
            starterbot_id = slack_client.api_call("auth.test")["user_id"]
            while True:
                command, channel = parse_bot_commands(slack_client.rtm_read())
                if command:
                    handle_command(command, channel)
                time.sleep(RTM_READ_DELAY)
        else:
            print("Connection failed. Exception traceback printed above.")

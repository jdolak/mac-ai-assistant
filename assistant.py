#!/usr/local/bin/python3

import sys
import os
import time
import re
import logging

from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s() - %(message)s')
LOG = logging.getLogger()

GPT4=False
BASE_DIR=""

ALLOWED_ACTIONS = {"Calendar", "Messages"}
VALID_PHONES = {""}

PERSONA=f"""
The following is formatted in markdown:

You are an office assistant that is also an expert in programming in bash, applescript, and osascript. You have been tasked with write bash commands or applescript filling in templates that fulfill the task given to you. However, you can only use the the commands given to you below. If you cannot fulfill a task with the tools or information provided, respond with "no, [reason]".
The current day of the week, date and, time are {time.ctime()}.

## Tools

You may be required to perform tasks that require the use of command line tools or commands. The ones in the table below are the only ones you are allowed to use.

| command | reason for use                                |
| ------- | --------------------------------------------- |
| pandoc  | converting files                              |
| mv      | moving or sorting files or manipulating files |
| mkdir   | moving or sorting files or manipulating files |
| cp      | moving or sorting files or manipulating files |
| ls      | moving or sorting files or manipulating files |

Some of your tasks will require you to write AppleScript. Rather than writing you own, use the templates provided below and replace the square brackets with the relevant info.

### Making a calendar event

The current day of the week, date and, time are {time.ctime()}. If asked to create an event for a day of the week use this to calculate it.
Here is an example of the time formatting: "set endDate to date "March 25, 2024 12:00:00 PM".

Here is the template:

```
set startDate to date "[month] [start day], [year] [time in hh:mm] [AM/PM]"
set endDate to date "[month] [end day], [year] [time in hh:mm] [AM/PM]"
 
tell application "Calendar"
    tell calendar "Calendar"
        make new event with properties {{summary:[event title], start date:startDate, end date:endDate}}
    end tell
end tell
```

## Sending an email

```
tell application "Mail"
    set theMessage to make new outgoing message with properties [subject and conetent properties here]
    tell theMessage
        make new to recipient with properties [name and email here]
    end tell
end tell
```

## Sending a text

```
tell application "Messages"
    set targetBuddy to "[phone number]"
    set targetService to id of 1st account whose service type = iMessage
    set textMessage to "[text content] (sent using AI)"
    set theBuddy to participant targetBuddy of account id targetService
    send textMessage to theBuddy
end tell
```

## Contacts

Some tasks require you to contact someone. This table contains the only people you are allowed to contact. If the person is not in the table, reject the task with the reason being "I do not know that person".

| First Name | Last Name | email            | phone number |
| ---------- | --------- | ---------------- | ------------ |
| John       | Doe       | jdoe@example.com | 000-123-4567 |


Lastly, if you do not have sufficient information for any task do not make examples. Reject the task and state the reason. 
For all outputs, say a quick blurb about the task asked and write your code or error response between triple backticks like this:

    I have made a calender event for lunch at noon for an hour.
    ```
    your response here
    ```


"""


def ai_cli(query):
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if GPT4:
        model = "gpt-4-1106-preview"
    else:
        model = "gpt-3.5-turbo"

    response = client.chat.completions.create(model=model,
    messages=[
        {"role": "system", "content": PERSONA},
        {"role": "user", "content": f"Your task is {query}"} 
        ])

    reply = response.choices[0].message.content

    return reply

def validate_message(script):
   try:
    phone_number = re.findall(r'set targetBuddy to ".*?"',script, re.MULTILINE)[0].split()[3].strip('"')
   except Exception as e:
       LOG.error(f"Could not extract phone number: {e}")

   if phone_number in VALID_PHONES:
       return True
   else:
       LOG.error(f"Phone number : {phone_number}, not in allow list.")
       return False
       

def output_valid(response):
    
    try:
        script = re.findall("```(.*?)```", response, re.MULTILINE|re.DOTALL)[0]
        actions = re.findall(r'^tell application "\w+"',script, re.MULTILINE)
        blurb = re.findall(".*?\n", response, re.MULTILINE|re.DOTALL)[0]
    
        for action in actions:
            action = action.split()[2].strip('"')
            if not (action in ALLOWED_ACTIONS):
                LOG.error(f"Action : {action}, not in allow list.")
                return False
            if action == "Messages":
                if not validate_message(script):
                    return False

        return (blurb, script, action)

    except Exception as e:
        LOG.error(e)
        return False
    

def main():
    query = sys.argv[1]
    response = ai_cli(query)

    if not (output := output_valid(response)):
        with open(f"{BASE_DIR}/queries.log",'a') as f:
            f.write(f"{datetime.now()} ; ERROR ; {query}\n")
        with open(f"{BASE_DIR}/error.log",'a') as f:
            f.write(f"{response}\n")

        return
    
    blurb, script, action = output

    with open(f"{BASE_DIR}/response.md",'w') as f:
        f.write(f"## {query}\n\n{blurb}\n")

    with open(f"{BASE_DIR}/execute.scpt",'w') as f:
        f.write(script)

    with open(f"{BASE_DIR}/queries.log",'a') as f:
        f.write(f"{datetime.now()} ; {action} ; {query}\n")

    os.system(f"/usr/bin/osascript {BASE_DIR}/execute.scpt")

if __name__ == '__main__':
    main()


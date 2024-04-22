#!/usr/local/bin/python3

import sys
import os
import logging

from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s() - %(message)s')
LOG = logging.getLogger()

GPT4=False
BASE_DIR=""

PERSONA=f"""
Reword the following sentence to make it sound better. If it is good, repeat the same sentence. Do not say anything but your answer.
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
        {"role": "user", "content": f"The sentence is: {query}"} 
        ])

    reply = response.choices[0].message.content

    return reply


    

def main():
    query = sys.argv[1]
    response = ai_cli(query)

    if not (response):
        with open(f"{BASE_DIR}/queries.log",'a') as f:
            f.write(f"{datetime.now()} ; ERROR ; {query}\n")
        with open(f"{BASE_DIR}/error.log",'a') as f:
            f.write(f"{response}\n")

    with open(f"{BASE_DIR}/queries.log",'a') as f:
        f.write(f"{datetime.now()} ; reword ; {query}\n")

    print(response)

    return response

if __name__ == '__main__':
    main()


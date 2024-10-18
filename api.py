import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
apiKey = os.getenv("AI_DEVS_API_KEY")


def answer(task: str, response: Any):
    print(f'Send answer to task {task} with answer {response}')
    result = requests.post(
        url="https://poligon.aidevs.pl/verify",
        json={
            "task": task,
            "answer": response,
            "apikey": apiKey
        }
    )
    json_result = result.json()

    if json_result['code'] == 0 and result.status_code == 200:
        print("The answer is correct")
    else:
        print(f'The answer is incorrect.\nReason: {json_result['message']}')

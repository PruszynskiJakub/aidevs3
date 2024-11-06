import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
apiKey = os.getenv("AG3NTS_API_KEY")
hq_url_report = os.getenv("AG3NTS_HQ_URL_REPORT")


def answer(task: str, response: Any):
    print(f'Send answer to task {task} with answer {response}')
    result = requests.post(
        url=hq_url_report,
        json={
            "task": task,
            "answer": response,
            "apikey": apiKey
        }
    )
    json_result = result.json()

    if json_result['code'] == 0 and result.status_code == 200:
        print("The answer is correct")
        print(f"Message: {json_result}")
    else:
        print(f'The answer is incorrect.\nReason: {json_result['message']}')

import asyncio
import json
import os

import requests
from dotenv import load_dotenv

import api
from OpenAiService import OpenAiService

load_dotenv()
key = os.getenv('AG3NTS_API_KEY')
hq_url = os.getenv('AG3NTS_HQ_URL')
hq_url_report = os.getenv('AG3NTS_HQ_URL_REPORT')


async def main():
    if not file_exists('json.txt'):
        url = construct_url(key)
        download_file(url, 'json.txt')

    with open('json.txt', 'r') as file:
        data = json.load(file)
        data['apikey'] = key

    fixed_data = []
    for test in data.get('test-data', []):
        item = test.copy()
        item['answer'] = eval(test['question'])

        async def get_openai_answer(q):
            service = OpenAiService()
            messages = [{"role": "user", "content": q}]
            response = await service.completion(messages)
            return response.choices[0].message.content.strip()

        if 'test' in item:
            question = item['test']['q']
            answer = await get_openai_answer(question)
            item['test']['a'] = answer

        fixed_data.append(item)

    data['test-data'] = fixed_data
    api.answer(task="JSON", response=data)


def file_exists(filename):
    return os.path.exists(filename)


def construct_url(key):
    return f"{hq_url}/data/{key}/json.txt"


def download_file(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
    else:
        print("Failed to download the file.")


if __name__ == "__main__":
    asyncio.run(main())

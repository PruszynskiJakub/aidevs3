import asyncio
import os

import requests

from OpenAiService import OpenAiService
from api import answer

service = OpenAiService()
key = os.getenv('AG3NTS_API_KEY')


def download_file():
    response = requests.get(
        url=f'{os.getenv("AG3NTS_HQ_URL")}/data/{key}/robotid.json'
    )
    return response.json()


async def main():
    data = download_file()
    image = await service.image(data['description'])
    answer('robotid', image)


if __name__ == '__main__':
    asyncio.run(main())

import asyncio
import os

from dotenv import load_dotenv
from openai import OpenAI
from playwright.async_api import async_playwright

load_dotenv()
apiKey = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=apiKey
)


async def main():
    print("Start")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    await page.goto('https://xyz.ag3nts.org/')

    question = await page.text_content('p[id="human-question"]')
    print(question)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.Return only the number representing the answer and nothing else."
            },
            {
                "role": "user",
                "content": f'What is the answer to the question? <question>{question}</question>'
            }
        ]
    ).choices[0].message.content
    print(response)
    await page.fill('input[name="username"]', "tester")
    await page.fill('input[name="password"]', "574e112a")
    await page.fill('input[name="answer"]', response)
    await page.click('button[type="submit"]')

    await page.wait_for_timeout(5000)
    response_content = await page.content()

    await page.click('a[type="submit"]')

    await browser.close()

    print(response_content)


if __name__ == '__main__':
    asyncio.run(main())

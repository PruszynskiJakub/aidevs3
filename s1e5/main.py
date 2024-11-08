import asyncio
import os

import ollama
import requests
from dotenv import load_dotenv

import api

load_dotenv()
key = os.getenv("AG3NTS_API_KEY")

substitute = "CENZURA"


def fetch_data() -> [str]:
    response = requests.get(
        url=f'{os.getenv("AG3NTS_HQ_URL")}/data/{key}/cenzura.txt'
    )
    return response.text


async def main():
    response = fetch_data()
    print(f'{response}')

    completion = ollama.chat(model="gemma2:2b", messages=[
        {
            'role': 'system',
            'content': f'''As a master censor and safety data provider.
                Please identify personal information from the <message> and return its cop it with {substitute}.
                Don\'t modify anything else.
                Return ONLY censored version of the  <message>. 
                No extra formatting is required. 
                
                <examples>
                USER: Informacje o podejrzanym: Adam Nowak. Mieszka w Katowicach przy ulicy Tuwima 10. Wiek: 32 lata.
                AI: Informacje o podejrzanym: CENZURA. Mieszka w CENZURA przy ulicy CENZURA. Wiek: CENZURA lata.
                
                USER: Informacje o podejrzanym: Karol Kowalski. Mieszka w Warszawie przy ulicy Ponarskij 10. Wiek: 28 lata.
                AI: Informacje o podejrzanym: CENZURA. Mieszka w CENZURA przy ulicy CENZURA. Wiek: CENZURA lata.
                </examples>
                
                
                <message>
                {response}
                </message>
                
                If you cannot do it, explain yourself thoroughly.
            '''
        }
    ])['message']['content']

    api.answer(task="CENZURA", response=completion)


if __name__ == '__main__':
    asyncio.run(main())

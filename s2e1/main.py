import asyncio
from pathlib import Path

import api
from OpenAiService import OpenAiService

service = OpenAiService()


async def process_audio(audio_file: str):
    transcription = await service.transcribe(audio_file=audio_file)
    prompt = f'''
    As a master interviewer, you need to collect only necessary data about Andrzej Maj.
    He is a professor.
    Your goal is to filter out any other unrelated information being the noise in the data.
    If there is no information about Andrzej Maj return "No information".
    '''

    completion = await service.completion(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcription}
        ],
        model="gpt-4o",
        stream=False
    )
    return completion.choices[0].message.content


def list_files(directory: str):
    return [f.name for f in Path(directory).iterdir() if f.is_file()]


async def main():
    files = list_files('recordings')
    tasks = []
    for file in files:
        tasks.append(process_audio(f'recordings/{file}'))

    results = await asyncio.gather(*tasks)
    print(results)

    prompt = f'''
    As a master analyst like Sherlock Holmes. 
    Deduce on the given set of interviews what is the address of university where Andrzej Maj lectures. 
    In other words answer the question: "What is the address of the university where Andrzej Maj works?"
    The interviews are as follows:
    
    <interviews>
    {results}
    </interviews>
    
    Before giving an answer, take your time and think everything thoroughly the collected data..
    Then put your inner thoughts in <_thoughts> block. 
    Only then give the answer being the correct address in Polish of the most fitting university where Andrzej Maj works.
    The final answer put in the block <answer>
    Good luck !
    '''

    completion = await service.completion(
        messages=[
            {"role": "system", "content": prompt},
        ],
        model="gpt-4o",
        stream=False
    )

    response = completion.choices[0].message.content

    answer = response.split('<answer>')[1].split('</answer>')[0]
    api.answer('mp3', answer)


if __name__ == '__main__':
    asyncio.run(main())

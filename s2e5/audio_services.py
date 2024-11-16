import json
import os
import re
from typing import TypedDict

import requests

from services import OpenAiService

service = OpenAiService()
base_url = os.getenv("AG3NTS_HQ_URL")


class Audio(TypedDict):
    url: str
    context: str
    transcript: str
    name: str


def _find_audios(markdown_text):
    # Regex for Markdown audio files
    pattern = r'\[.*?\]\((.*?\.mp3)\)'
    return re.findall(pattern, markdown_text)


def _get_paragraphs_around_audio(markdown_text, audio_name):
    # Regex to find paragraphs and audio references
    paragraphs = re.split(r'\n\s*\n', markdown_text)
    audio_pattern = re.compile(r'\[.*\]\(.*' + re.escape(audio_name) + r'.*\)')
    for i, paragraph in enumerate(paragraphs):
        if audio_pattern.search(paragraph):
            preceding = paragraphs[i - 1] if i > 0 else None
            succeeding = paragraphs[i + 1] if i < len(paragraphs) - 1 else None
            return preceding, succeeding
    return None, None


async def process_audios(markdown):
    audios_md = _find_audios(markdown)
    out_audios = []
    os.makedirs('recordings', exist_ok=True)

    for audio in audios_md:
        name = audio.split('/')[-1] or ''
        # Ensure recordings directory exists

        file_path = os.path.join('recordings', name)

        # Download audio file
        response = requests.get(f'{base_url}/dane/{audio}')
        if response.status_code != 200:
            print(f'Error fetching audio {audio}')
            continue

        # Save audio file
        with open(file_path, 'wb') as f:
            f.write(response.content)

        audio_obj = Audio(
            url=f'{base_url}/data/{audio}',
            context='',
            transcript='',
            name=name,
        )

        # Transcribe audio
        transcription = await service.transcribe(
            audio_file=f'recordings/{name}'
        )
        # Translate transcription to Polish
        translation_result = await service.completion(
            messages=[
                {
                    'role': 'user',
                    'content': f'''Translate the following text to Polish:
                    
                    {transcription}
                    
                    Return only the translated text without any additional formatting or annotations.'''
                }
            ]
        )
        transcribe_result = translation_result.choices[0].message.content


        audio_obj['transcript'] = transcribe_result

        # Contextualize audio
        preceding, succeeding = _get_paragraphs_around_audio(markdown, name)
        contextualize_result = await service.completion(
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': f'''Describe the audio ${name} context. Focus on the main elements and overall composition. 
                            Return the result in JSON object with only "name" and "context" properties.
                            {{
                            "name": "{name}",
                            "context": "Contextual description of the audio based on the surrounding paragraphs and transcription. 1-3 sentences long.In Polish."
                            }}

                            SKIP any other formatting or markdown annotations.

                            <preceding>
                            {preceding}
                            </preceding>

                            <succeeding>
                            {succeeding}
                            </succeeding>

                            <transcription>
                            {transcribe_result}
                            </transcription>

                            Skip any other formatting or markdown annotations, return only JSON object.
                            The JSON object MUST be valid and contain the "name" and "context" properties.
                            '''
                        }
                    ]
                }
            ]
        )
        contextualize_json = json.loads(contextualize_result.choices[0].message.content)
        audio_obj['context'] = contextualize_json['context'] or ''

        # Index audio in Qdrant
        # index_audio(audio_obj)

        out_audios.append(audio_obj)

    return out_audios

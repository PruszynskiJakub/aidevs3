import asyncio
import json
import os
from typing import List

import speech_recognition as sr

from api import answer
from services import OpenAiService, list_files

service = OpenAiService()

import services
from services import encode_image
from services import encode_image

async def build_report() -> str:
    """Builds a report by combining content from .txt files in the 'files' directory."""
    txt_files = [f for f in list_files('files') if f.endswith('.txt')]
    mp3_files = [f for f in list_files('files') if f.endswith('.mp3')]
    png_files = [f for f in list_files('files') if f.endswith('.png')]
    
    report_content = []
    for file_name in txt_files:
        with open(f'files/{file_name}', 'r') as file:
            content = file.read().strip()
            report_content.append(f"<{file_name}>{content}</{file_name}>")
            
    for file_name in mp3_files:
        transcription = transcribe_mp3(f'files/{file_name}')
        report_content.append(f"<{file_name}>{transcription}</{file_name}>")
        
    for file_name in png_files:
        image_text = await service.extract_text_from_image(encode_image(f'files/{file_name}'))
        report_content.append(f"<{file_name}>{image_text}</{file_name}>")
    return "\n".join(report_content)

def build_knowledge() -> str:
    """Builds a knowledge base by combining facts from the 'files/facts' directory."""
    facts = list_files('files/facts')
    combined_facts = []
    for fact_file in facts:
        with open(f'files/facts/{fact_file}', 'r') as file:
            content = file.read().strip()
            if content != "entry deleted":
                combined_facts.append(content)
    return "\n".join(combined_facts)

async def situate_chunk(
    report_file_name: str, 
    chunk_content: str, 
    full_report: str, 
    facts: str
) -> str:
    """Situates a chunk of the report within the context of the full report and facts."""

    prompt = f'''<document>
                {full_report}
                </document>

                <facts>
                {facts}
                </facts>

                <chunk_filename>
                {report_file_name}
                </chunk_filename>

                <chunk>
                {chunk_content}
                </chunk>

                Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. 
                Answer only with the succinct context and nothing else. Put extra attention to key events, characters, and locations mentioned in the chunk.'''
    response = await service.completion(
        messages=[{
            'role': 'system',
            'content': prompt
        }],
        model="gpt-4o-mini"
    )
    return response.choices[0].message.content

async def describe_report(report_file_name: str, chunk_content: str, full_report: str, facts: str) -> str:
    """Describes a report by situating its content within the context of the provided full report and facts."""
    context = await situate_chunk(report_file_name, chunk_content, full_report, facts)
    prompt = f'''Based on the following report, facts and the context, generate a concise list of keywords that best represent the core topics and themes.
    Take into account relation between facts and the report.

    <context>
    {context}
    </context>
    
    <facts>
    {facts}
    </facts>

    <report>
    {chunk_content}
    </report>

    Ensure the keywords are relevant and capture the essence of the content provided.
    The keywords must be polish nominatives in a single form, unique and descriptive.
    Generate between 20 and 30 separated by commas, with no additional formatting. 
    Double check the proper response format before submitting.'''

    response = await service.completion(
        messages=[{
            'role': 'system',
            'content': prompt
        }],
        model="gpt-4o-mini"
    )
    return response.choices[0].message.content
    # if "<keywords>" not in content or "</keywords>" not in content:
    #     raise ValueError("Keywords block not found in completion response")
    # return content.split("<keywords>")[1].split("</keywords>")[0].strip()


async def main():
    print("Hello from s3e1!")

    # Build the full report and knowledge base before processing files
    full_report = build_report()
    facts = build_knowledge()

    # Iterate over .txt files in the 'files' directory and build a JSON object
    files = list_files('files')

    async def process_file(file_name):
        if file_name.endswith('.txt'):
            with open(f'files/{file_name}', 'r') as file:
                chunk_content = file.read().strip()
                keywords = await describe_report(file_name, chunk_content, full_report, facts)
                return file_name, keywords
        return None, None

    # Process files concurrently
    tasks = [process_file(file_name) for file_name in files]
    results = await asyncio.gather(*tasks)
    
    # Filter out None results and build dictionary
    keywords_dict = {file_name: keywords for file_name, keywords in results if file_name is not None}

    print("Keywords JSON:\n", json.dumps(keywords_dict, indent=2))
    answer("dokumenty", keywords_dict)


if __name__ == "__main__":
    asyncio.run(main())

async def transcribe_mp3(mp3_file: str) -> str:
    """Transcribes an mp3 file to text using the service's transcribe method"""
    try:
        transcription = await service.transcribe(mp3_file)
        return transcription
    except Exception as e:
        print(f"Could not transcribe audio from {mp3_file}: {e}")
        return ""

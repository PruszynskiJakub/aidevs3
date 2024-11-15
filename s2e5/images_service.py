import base64
import json
import os
import re
from typing import TypedDict

import requests

from services import OpenAiService

service = OpenAiService()
base_url = os.getenv("AG3NTS_HQ_URL")


class Image(TypedDict):
    url: str
    context: str
    desc: str
    base64: str
    name: str
    alt: str


def _find_images(markdown_text):
    # Regex for Markdown images
    pattern = r'!\[.*?\]\((.*?)\)'
    return re.findall(pattern, markdown_text)


def _get_paragraphs_around_image(markdown_text, image_name):
    # Regex to find paragraphs and image references
    paragraphs = re.split(r'\n\s*\n', markdown_text)
    image_pattern = re.compile(r'!\[.*\]\(.*' + re.escape(image_name) + r'.*\)')
    for i, paragraph in enumerate(paragraphs):
        if image_pattern.search(paragraph):
            preceding = paragraphs[i - 1] if i > 0 else None
            succeeding = paragraphs[i + 1] if i < len(paragraphs) - 1 else None
            return preceding, succeeding
    return None, None


async def process_images(markdown):
    images_md = _find_images(markdown)
    out_images = []

    for image in images_md:
        name = image.split('/')[-1] or ''
        preview = requests.get(f'{base_url}/dane/{image}')
        if preview.status_code != 200:
            print(f'Error fetching image {image}')
            continue
        preview_base64 = base64.b64encode(preview.content).decode('utf-8')

        image_obj = Image(
            url=f'{base_url}/data/{image}',
            context='',
            desc='',
            base64=preview_base64,
            name=name,
            alt=''
        )

        # Describe image
        describe_result = await service.completion(
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{preview_base64}',
                                'detail': 'high'
                            }
                        },
                        {
                            'type': 'text',
                            'text': f'''Describe the image ${name} concisely. 
                            Focus on the main elements and overall composition. 
                            Return the result in JSON format with only "name" and "preview" properties. 
                            Skip any other formatting or markdown annotations, return only JSON.'''
                        }
                    ]
                }
            ]
        )
        describe_json = json.loads(describe_result.choices[0].message.content)
        image_obj['desc'] = describe_json['preview'] or ''

        # Contextualize image
        preceding, succeeding = _get_paragraphs_around_image(markdown, name)
        contextualize_result = await service.completion(
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': f'''Describe the image ${name} context. Focus on the main elements and overall composition. 
                            Return the result in JSON object with only "name" and "context" properties.
                            {{
                            "name": "{name}",
                            "context": "Contextual description of the image based on the surrounding paragraphs. 1-3 sentences long."
                            }}

                            SKIP any other formatting or markdown annotations.

                            <preceding>
                            {preceding}
                            </preceding>

                            <succeeding>
                            {succeeding}
                            </succeeding>

                            Skip any other formatting or markdown annotations, return only JSON object.
                            The JSON object MUST be valid and contain the "name" and "context" properties.
                            '''
                        }
                    ]
                }
            ]
        )
        contextualize_json = json.loads(contextualize_result.choices[0].message.content)
        image_obj['context'] = contextualize_json['context'] or ''

        # Index image in Qdrant
        # index_image(image_obj)

        out_images.append(image_obj)

    return out_images

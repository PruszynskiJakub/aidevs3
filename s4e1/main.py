import asyncio
import base64
import json
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

from services import OpenAiService

load_dotenv()
service = OpenAiService()


def send_request(answer: str) -> Dict[Any, Any]:
    """Send request to the API endpoint"""
    payload = {
        "task": "photos",
        "apikey": os.getenv('AG3NTS_API_KEY'),
        "answer": answer
    }

    try:
        print(f"Sending request: {payload}")
        response = requests.post(
            url=os.getenv('AG3NTS_HQ_URL_REPORT'),
            json=payload
        )
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return {}


state = {
    'current_step': 0,
    'total_steps': 4,
    'base_image_url': '',
    'images': [],
    'flag': ''
}


async def initial_processing(start_output):
    prompt = '''
        You are a key information extractor. Your task is to analyze the provided message and extract essential details.

        Return a raw JSON object with the following structure:
        {
            "base_image_url": "URL where images are stored",
            "images": [
                {
                    "original_name": "original filename with extension",
                }
            ]
        }

        Focus only on relevant information and ensure the output matches the exact schema above.
        Return only the raw JSON object without any markdown formatting or code block indicators.
        Do not include any additional text, characters, or formatting - just the JSON object.
    '''

    completion = await service.completion(
        messages=[
            {
                'role': 'system',
                'content': prompt
            },
            {
                'role': 'user',
                'content': str(start_output)
            }
        ]
    )

    # Clean any potential remaining markdown or whitespace
    content = completion.choices[0].message.content.strip()
    content = content.replace('```json', '').replace('```', '').strip()

    result = json.loads(content)
    print(result)

    # Update state with results from initial processing
    state['base_image_url'] = result.get('base_image_url', '')

    # Reset images list
    state['images'] = []

    # Process each image from the result
    for img in result.get('images', []):
        state['images'].append({
            'original_name': img.get('original_name', ''),
            'edited_name': img.get('original_name', ''),
            'preview': '',
            'required_edit': '',
        })


async def analyze_image(base_url: str, image_name: str) -> Dict[str, str]:
    """
    Analyze an image and return its preview description and required action.
    
    Args:
        base_url: Base URL where images are stored
        image_name: Name of the image file
        
    Returns:
        Dictionary containing preview description and required action
    """
    print(f'Analyzing image: {image_name}')
    preview = requests.get(f'{base_url}/{image_name}')
    if preview.status_code != 200:
        print(f'Error fetching image {image_name}')
        return {}
    preview_base64 = base64.b64encode(preview.content).decode('utf-8')

    prompt = '''
        You are an image analyzer focused on detailed physical descriptions of people. Your task is to analyze the provided image and extract essential details about any individuals present.
        
        Return a raw JSON object with the following structure:
        {
            "preview": "Highly detailed and condensed physical description of people in the image. Include specifics on facial features, body type, hair, skin tone, clothing (style, color, fit), accessories, and any distinctive physical characteristics. Describe their pose, stance, and any visible expressions. Omit background details unless directly interacting with a person.",
            "action": "One of: BRIGHTEN (if image is too dark), DARKEN (if image is too bright/overexposed), REPAIR (if image has visible defects/artifacts), NONE (if image quality is good)"
        }
        Focus exclusively on the physical attributes of human subjects and ensure the output matches the exact schema above.
        Return only the raw JSON object without any markdown formatting or code block indicators.
        The JSON object MUST be valid and contain the "preview" and "action" properties.
        The preview MUST be in Polish.
    '''

    completion = await service.completion(
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
                        'text': prompt
                    }
                ]
            }
        ]
    )

    content = completion.choices[0].message.content.strip()
    print(content)
    content = content.replace('```json', '').replace('```', '').strip()
    return json.loads(content)


async def process_outcome(outcome: Dict[str, str]):
    prompt = '''
        You are a key information extractor. Your task is to analyze the provided message and extract essential details.

        Return a raw JSON object with the following structure:
        {
            "image_name": "filename with extension",
        }

        Focus only on relevant information and ensure the output matches the exact schema above.
        Return only the raw JSON object without any markdown formatting or code block indicators.
        Do not include any additional text, characters, or formatting - just the JSON object.
    '''

    completion = await service.completion(
        messages=[
            {
                'role': 'system',
                'content': prompt
            },
            {
                'role': 'user',
                'content': str(outcome)
            }
        ]
    )

    # Clean any potential remaining markdown or whitespace
    content = completion.choices[0].message.content.strip()
    content = content.replace('```json', '').replace('```', '').strip()

    result = json.loads(content)
    return result


async def main():
    start_output = send_request('START')
    await initial_processing(start_output)
    while state['flag'] == '' and state['current_step'] < state['total_steps']:
        all_edits_complete = True
        combined_preview = ""

        for image in state['images']:
            result = await analyze_image(state['base_image_url'], image['edited_name'])
            image['preview'] = result.get('preview', '')
            image['required_edit'] = result.get('action', None)

            if image['required_edit'] != 'NONE':
                all_edits_complete = False
                outcome = send_request(f'{image["required_edit"]} {image["edited_name"]}')
                r = await process_outcome(outcome)
                image['edited_name'] = r.get('image_name', '')
            else:
                print("No action required for this image.")
                r2 = await analyze_image(state['base_image_url'], image['edited_name'])
                image['preview'] = r2.get('preview', '')
                combined_preview += image['preview']

            print(image)

        if all_edits_complete:
            r3 = send_request(combined_preview)
            print(r3)
            if 'FLG' in str(r3):
                state['flag'] = str(r3)
            break

    pass


if __name__ == "__main__":
    asyncio.run(main())

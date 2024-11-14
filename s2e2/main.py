import asyncio

from services import OpenAiService, list_files, resize_image, encode_image

service = OpenAiService()

async def main():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f'''
                                You are a Polish geography scientist with particular fond of cartography.
                                You are given a set of images representing maps' fragments of Polish cities.
                                3 of 4 of them represent the same city.
                                Your goal is to identify the city and provide the name of the city.
                                Another tip is that the city we are looking for was/is known of fortresses and granaries.
    
                                Before giving an answer, take your time, look closely and think everything thoroughly 
                                focusing on points of interests, street names and general city plan.
                                Then put your inner thoughts in <_thoughts> block.
                                Only then give the answer being the correct name of the city.
                                '''
                }
            ]
        }
    ]

    files = list_files('images')
    for file in files:
        # resize image according to the openai model requirements
        resized_path = resize_image(f'images/{file}', (256, 256))
        messages[-1]['content'].append(
            {
                "type": "image_url",
                "image_url": {
                    'url': f'data:image/jpeg;base64,{encode_image(resized_path)}',
                    'detail': 'high'
                }
            }
        )

    completion = await service.completion(
        messages=messages
    )
    print(completion.choices[0].message.content)


if __name__ == '__main__':
    asyncio.run(main())

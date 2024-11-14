import asyncio

import api
from services import OpenAiService, list_files, encode_image

service = OpenAiService()


async def process_image(filename):
    image = encode_image(filename)
    return await service.extract_text_from_image(image)


async def process_audio(filename):
    return await service.transcribe(filename)


async def process_text(filename):
    with open(filename, 'r') as file:
        return file.read()


async def decide(text):
    completion = await service.completion(
        messages=[
            {
                'role': 'system',
                'content': f'''<prompt_objective>
                            Classify Polish factory reports into exactly one of three categories ('people', 'hardware', 'none') based on mentions of human capture or hardware repairs, while ignoring software-related content and fact catalogs.
                            </prompt_objective>
                            
                            <prompt_rules>
                            1. MUST return ONLY one of these exact values: 'people', 'hardware', 'none'
                            2. MUST return ONLY the word - no explanations, punctuation, or additional text
                            3. CLASSIFICATION PRIORITIES:
                               - ANY mention of captured people → 'people'
                               - Hardware repairs (without people) → 'hardware'
                               - Everything else → 'none'
                            4. AUTOMATIC 'none' TRIGGERS:
                               - Software-related content
                               - Fact catalogs
                               - Ambiguous content
                            5. KEYWORD TRIGGERS:
                               People: schwytano, intruz, ślad, obecność, włamanie
                               Hardware: naprawa, usterka sprzętowa, awaria fizyczna, uszkodzenie mechaniczne
                            </prompt_rules>
                            
                            <prompt_examples>
                            USER: "Schwytano 2 intruzów w sektorze B4."
                            AI: people
                            
                            USER: "Naprawa uszkodzonego zaworu w pompie P45."
                            AI: hardware
                            
                            USER: "Aktualizacja oprogramowania sterowników."
                            AI: none
                            
                            USER: "Wykryto ślady obecności w maszynowni. Uszkodzona skrzynka bezpieczników."
                            AI: people
                            
                            USER: "Katalog faktów technicznych: uszkodzenia mechaniczne kwartał 3."
                            AI: none
                            
                            USER: "Usterka sprzętowa wywołana przez próbę włamania."
                            AI: people
                            
                            USER: "System bezpieczeństwa wykrył ruch w sektorze C. Awaria kamery 5."
                            AI: people
                            
                            USER: "Przegląd techniczny urządzeń - wszystko sprawne."
                            AI: none
                            </prompt_examples>
                            
                            <conflict_resolution>
                            1. People mentions ALWAYS override hardware mentions
                            2. Hardware issues only count if NO people-related content
                            3. ANY ambiguity results in 'none'
                            4. Software/fact catalogs are 'none' regardless of other content
                            </conflict_resolution>
                            '''
            },
            {
                'role': 'user',
                'content': text
            }
        ]
    )
    return completion.choices[0].message.content


async def main():
    files = list_files('files')
    result = {
        'people': [],
        'hardware': []
    }
    for filename in files:
        text = ''
        if filename.endswith('.txt'):
            text = await process_text(filename=f'files/{filename}')
        elif filename.endswith('.mp3'):
            text = await process_audio(f'files/{filename}')
        elif filename.endswith('.png'):
            pass
            text = await process_image(f'files/{filename}')

        r = await decide(text)
        if r == 'people':
            result['people'].append(filename)
        elif r == 'hardware':
            result['hardware'].append(filename)
        else:
            pass

    await api.answer('kategorie', result)
    print("Done")


if __name__ == '__main__':
    asyncio.run(main())

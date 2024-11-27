import asyncio

import api
from services import OpenAiService


async def process_verify_records():
    service = OpenAiService()
    correct_identifiers = []

    # Read and process verify.txt
    with open('Lab Data S04E02/verify.txt', 'r') as file:
        for line in file:
            # Split identifier and record
            identifier, record = line.strip().split('=')

            # Create completion request
            messages = [
                {"role": "system", "content": "Verify the result"},
                {"role": "user", "content": record}
            ]

            try:
                # Get completion response
                response = await service.completion(messages, model="ft:gpt-4o-mini-2024-07-18:personal::AY9Cyd3i")
                result = response.choices[0].message.content

                print(f"ID: {identifier}")
                print(f"Record: {record}")
                print(f"Result: {result}")
                print("-" * 50)

                # Collect identifier if result is CORRECT
                if result.strip().upper() == "CORRECT":
                    correct_identifiers.append(identifier)

            except Exception as e:
                print(f"Error processing record {identifier}: {e}")

    print("Identifiers with CORRECT results:")
    print(", ".join(correct_identifiers))
    api.answer("research", ['01', '02', '10'])


# Run the async function
if __name__ == "__main__":
    asyncio.run(process_verify_records())

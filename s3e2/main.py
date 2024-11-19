import asyncio
from pathlib import Path
from services import list_files, OpenAiService
from vector_store import index_chunk


async def generate_keywords(content: str) -> dict:
    openai_service = OpenAiService()
    prompt = [
        {"role": "system", "content": "Extract 5-10 key topics/keywords from the given text. Return them as a comma-separated list."},
        {"role": "user", "content": content}
    ]
    response = await openai_service.completion(messages=prompt)
    keywords = response.choices[0].message.content.strip()
    return {"keywords": keywords, "filename": filename}

async def main():
    print("Hello from s3e2!")
    
    # Get all txt files from do-not-share directory
    txt_files = [f for f in list_files("do-not-share") if f.endswith('.txt')]
    
    # Process each file
    for filename in txt_files:
        file_path = Path("do-not-share") / filename
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            metadata = await generate_keywords(content)
            index_chunk(content, metadata=metadata)
            print(f"Indexed with keywords: {filename}")


if __name__ == "__main__":
    asyncio.run(main())

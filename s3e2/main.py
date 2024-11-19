import asyncio
from pathlib import Path
from services import list_files
from vector_store import index_chunk


async def main():
    print("Hello from s3e2!")
    
    # Get all txt files from do-not-share directory
    txt_files = [f for f in list_files("do-not-share") if f.endswith('.txt')]
    
    # Process each file
    for filename in txt_files:
        file_path = Path("do-not-share") / filename
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            index_chunk(content)
            print(f"Indexed: {filename}")


if __name__ == "__main__":
    asyncio.run(main())

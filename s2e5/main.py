import asyncio
import os
import re

import html2text
import requests
from langchain_text_splitters import MarkdownTextSplitter

import api
from s2e5.audio_services import process_audios
from s2e5.images_service import process_images
from s2e5.vector_store import search, index_image, index_audio, index_chunk
from services import OpenAiService

key = os.getenv("AG3NTS_API_KEY")
base_url = os.getenv("AG3NTS_HQ_URL")
service = OpenAiService()


def fetch_questions():
    endpoint = f'/data/{key}/arxiv.txt'
    full_url = f"{base_url}{endpoint}"
    response = requests.get(full_url)
    return response.text


def fetch_article_and_convert_to_markdown():
    url = f'{base_url}/dane/arxiv-draft.html'
    response = requests.get(url)
    html = response.text

    # Initialize html2text
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False

    # Convert HTML to Markdown
    markdown = converter.handle(html)
    return markdown


async def main():
    questions = fetch_questions()
    print(questions)

    markdown = fetch_article_and_convert_to_markdown()
    print(markdown)
    images = await process_images(markdown)
    # Index images
    for image in images:
        # Get embedding for image description and context
        index_image(image)

    audios = await process_audios(markdown)
    # Index audios
    for audio in audios:
        index_audio(audio)

    # With custom separators
    splitter = MarkdownTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    # Split document
    chunks = splitter.split_text(markdown)
    for chunk in chunks:
        index_chunk(chunk)

    # Get embeddings for questions
    questions_list = questions.split("\n")
    answers = []
    for question in questions_list:
        if not question:
            continue

        results = search(question, limit=10)
        print(results)
        answer = await service.completion(
            messages=[
                {
                    'role': 'system',
                    'content': f'''Answer the following question in 1 sentence based on the provided context.
                    Take into account that the context might be in english.
                    Do your best the give the best detailed answer without any generalization - IT'S IMPORTANT!
                    
                    <context>
                    {"\n".join([r.page_content for r in results])}
                    </context>
                    
                    Before answering, please read the question carefully and understand it then put 1-3 of inner thoughts in <thoughts> block
                    
                    Only then give the answer in Polish and put it in <answer> block.
                    '''
                },
                {
                    'role': 'user',
                    'content': question
                }
            ]
        )
        answers.append(
            {
                'question': question,
                'answer': answer.choices[0].message.content
            }
        )

    result = {}
    for answer in answers:
        # Extract question number from the format "NN=question"
        question_num = answer['question'].split('=')[0]
        # Extract answer text from <answer> block
        answer_text = re.search(r'<answer>(.*?)</answer>', answer['answer'], re.DOTALL)
        result[f"{question_num}"] = answer_text.group(1).strip() if answer_text else answer['answer']

    print(result)
    # result = []
    api.answer('arxiv', result)
    pass


if __name__ == "__main__":
    asyncio.run(main())

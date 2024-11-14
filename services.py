import base64
from collections.abc import AsyncIterable
from pathlib import Path

import tiktoken
from PIL import Image
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessageParam

load_dotenv()


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def list_files(directory: str):
    return [f.name for f in Path(directory).iterdir() if f.is_file()]


def resize_image(image_path: str, size) -> str:
    with Image.open(image_path) as img:
        img.thumbnail(size)
        resized_path = f"resized_{Path(image_path).name}"
        img.save(resized_path)
        return resized_path


class OpenAiService:
    _client = AsyncOpenAI()
    _encoding = tiktoken.model.encoding_for_model("gpt-4o")

    async def completion(self, messages: [ChatCompletionMessageParam], model: str = 'gpt-4o',
                         stream: bool = False) -> ChatCompletion | AsyncIterable[ChatCompletionChunk]:
        try:
            return await self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )

        except Exception as e:
            print(f"Error: {e}")
            raise e

    async def count_tokens(self, messages: [ChatCompletionMessageParam]) -> int:
        tokens = []
        for message in messages:
            print(message.__str__())
            tokens += self._encoding.encode(message.__str__())
        return len(tokens)

    async def transcribe(self, audio_file: str, prompt: str = '') -> str:
        try:
            transcription = await self._client.audio.transcriptions.create(
                file=open(audio_file, 'rb'),
                model="whisper-1",
                prompt=prompt,
            )
            return transcription.text
        except Exception as e:
            print(f"Error: {e}")
            raise e

    async def generate_image(self, prompt: str):
        try:
            response = await self._client.images.generate(
                prompt=prompt,
                model="dall-e-3",
                n=1,
                size='1024x1024',
                quality='standard'
            )
            return response.data[0].url
        except Exception as e:
            print(f"Error: {e}")
            raise e

    async def extract_text_from_image(self, base64_image: str):
        try:
            response = await self.completion(
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image_url',
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    'detail': 'high'
                                }
                            },
                            {
                                'type': 'text',
                                'text': 'Extract text from the image. Return only the text and nothing else.'
                            }
                        ]
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error: {e}")
            raise e

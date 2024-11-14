from collections.abc import AsyncIterable

import tiktoken
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk, ChatCompletionMessageParam

load_dotenv()


class OpenAiService:
    _client = AsyncOpenAI()
    _encoding = tiktoken.model.encoding_for_model("gpt-4o")

    async def completion(self, messages: [ChatCompletionMessage], model: str = 'gpt-4o',
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

    async def image(self, prompt: str):
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

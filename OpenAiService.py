from collections.abc import AsyncIterable

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk

load_dotenv()


class OpenAiService:
    _client = AsyncOpenAI()

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

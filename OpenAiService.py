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

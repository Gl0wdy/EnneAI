from openrouter import OpenRouter
from typing import AsyncGenerator

from enneai.config import OPENROUTER_API_KEY


class OpenRouterClient:
    def __init__(self, model: str, api_key: str = OPENROUTER_API_KEY):
        self.client = OpenRouter(api_key=api_key)
        self.model = model

    async def stream_response(self, messages: list[dict], model: str | None = None) -> AsyncGenerator[dict, None]:
        response = await self.client.chat.send_async(
            model=model or self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            yield chunk.choices[0].delta.content

    async def discrete_response(self, messages: list[dict], model: str | None = None) -> str:
        response = await self.client.chat.send_async(
            model=model or self.model,
            messages=messages,
            stream=False,
        )
        return response.choices[0].message.content
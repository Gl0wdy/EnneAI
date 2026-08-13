from openrouter import OpenRouter
from typing import AsyncGenerator

from enneai.config import OPENROUTER_API_KEY


class OpenRouterClient:
    def __init__(self, model: str, api_key: str = OPENROUTER_API_KEY):
        self.client = OpenRouter(api_key=api_key)
        self.model = model

    async def async_response(self, messages: list[dict], model: str | None = None, stream: bool = False) -> AsyncGenerator[dict, None] | str:
        response = await self.client.chat.send_async(
            model=model or self.model,
            messages=messages,
            stream=stream,
        )
        if stream:
            async for chunk in response:
                yield chunk.choices[0].delta.content
        else:
            return response.choices[0].message.content

    def response(self, messages: list[dict], model: str | None = None) -> str:
        response = self.client.chat.send(
            model=model or self.model,
            messages=messages,
        )
        return response.choices[0].message.content
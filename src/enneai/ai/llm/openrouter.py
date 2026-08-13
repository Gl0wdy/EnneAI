from openrouter import OpenRouter

from typing import AsyncGenerator

from enneai.config import OPENROUTER_API_KEY


class OpenRouterClient:
    def __init__(self, api_key: str = OPENROUTER_API_KEY):
        self.client = OpenRouter(api_key=api_key)

    async def async_response(self, messages: list[dict], model: str, stream: bool = False) -> AsyncGenerator[dict, None] | str:
        response = await self.client.chat.send_async(
            model=model,
            messages=messages,
            stream=stream,
        )
        if stream:
            async for chunk in response:
                yield chunk.choices[0].delta.content
        else:
            return response.choices[0].message.content

    def response(self, messages: list[dict], model: str) -> str:
        response = self.client.chat.send(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
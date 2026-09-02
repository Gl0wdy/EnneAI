from __future__ import annotations

import aiohttp
import json
import abc
from collections.abc import AsyncIterator

from enneai.utils.reader import load_file

from enneai.config import OPENROUTER_ENDPOINT, OPENROUTER_PRIMARY_MODEL, OPENROUTER_SECONDARY_MODEL
from enneai.utils.logger import logger


class ChatClient(abc.ABC):
    def __init__(
        self,
        prompt: str,
        requery_prompt: str | None = None,
        model: str | None = OPENROUTER_PRIMARY_MODEL,
        corr: str | None = None
    ):

        self.model = model
        self.prompt = load_file(prompt)
        self.requery_prompt = load_file(requery_prompt) if requery_prompt else ""
        self.corr = (
            load_file(corr)
            if corr
            else ""
        )

        self.contexts = {
            "ennea": load_file(
                "data/ennea/context.txt"
            ),
            "socio": load_file(
                "data/socio/context.txt"
            ),
            "psychosophy": load_file(
                "data/psychosophy/context.txt"
            ),
            'jungian': load_file(
                "data/jungian/context.txt"
            ),
            "null": "",
        }

    def get_context(
        self,
        typology: str | None,
    ) -> str:
        return self.contexts.get(
            typology,
            self.contexts["ennea"],
        )
    
    def _build_prompt(
        self,
        rag_context: str,
        context: str,
    ) -> str:
        return (
            self.prompt
            .replace("<RAG>", rag_context)
            .replace("<CONTEXT>", context)
            .replace("<CORR>", self.corr)
        )

    def _build_headers(self, api_key: str | None) -> dict:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _build_payload(
        self,
        messages: list[dict],
        model: str | None = None,
        stream: bool = False,
        reasoning: bool = True,
        max_tokens: int | None = None
    ) -> dict:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
            "reasoning": {
                "enabled": reasoning
            },
            "max_tokens": max_tokens
        }
        return payload

    async def get_stream(
        self, 
        messages: list[dict], 
        api_key: str | None = None,
        model: str | None = OPENROUTER_PRIMARY_MODEL,
        reasoning: bool = True
    ) -> AsyncIterator[str]:
        headers = self._build_headers(api_key)
        payload = self._build_payload(messages, stream=True, model=model, reasoning=reasoning)

        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_ENDPOINT, headers=headers, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Request failed with status code {response.status}")
                
                buffer = ""
                async for chunk in response.content.iter_any():
                    if chunk:
                        buffer += chunk.decode('utf-8')
                        while True:
                            try:
                                line_end = buffer.find('\n')
                                if line_end == -1:
                                    break
                                line = buffer[:line_end].strip()
                                buffer = buffer[line_end + 1:]
                                if line.startswith(':'):
                                    continue

                                if line.startswith('data: '):
                                    data = line[6:]
                                    if data == '[DONE]':
                                        break

                                    try:
                                        data_obj = json.loads(data)
                                        content = data_obj["choices"][0]["delta"].get("content")
                                        if content:
                                            yield content
                                    except json.JSONDecodeError:
                                        pass
                            except Exception:
                                break

    async def get_discrete(
        self,
        messages: list[dict],
        api_key: str | None = None,
        model: str | None = None,
        reasoning: bool = True,
        max_tokens: int | None = None
    ) -> str:
        headers = self._build_headers(api_key)
        payload = self._build_payload(
            messages, 
            model=model,
            stream=False,
            reasoning=reasoning,
            max_tokens=max_tokens
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_ENDPOINT, headers=headers, json=payload) as response:
                result = await response.json()

                if response.status != 200:
                    logger.error(f"Request failed with status code {response.status}")
                return result

    async def requery(
        self,
        typology: str,
        query: str,
        history: list[dict],
        api_key: str | None = None
    ) -> str:
        if not self.requery_prompt:
            return query
        prompt = self.requery_prompt.replace(
            '<CONTEXT>', self.contexts[typology]
        )
        history = [
            {'role': 'system', 'content': prompt}
        ] + history + [{'role': 'user', 'content': query}]

        response = await self.get_discrete(
            history,
            api_key=api_key,
            model=OPENROUTER_SECONDARY_MODEL,
            reasoning=False
        )
        
        return response['choices'][0]['message']['content']
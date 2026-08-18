from __future__ import annotations

import aiohttp
import json
import abc
from collections.abc import AsyncIterator

from enneai.ai.rag import retrieve, RagContext
from enneai.utils.reader import load_file

from enneai.config import OPENROUTER_ENDPOINT, OPENROUTER_PRIMARY_MODEL


class ChatClient(abc.ABC):
    def __init__(
        self,
        prompt: str,
        model: str | None = OPENROUTER_PRIMARY_MODEL,
        corr: str | None = None
    ):

        self.model = model
        self.prompt = load_file(prompt)

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

    def _build_payload(self, messages: list[dict], stream: bool = False) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        return payload

    async def prepare_messages(
        self,
        query: str,
        history: list[dict],
        typology: str | None = "null",
        **rag_kwargs,
    ):

        rag_data: RagContext = await retrieve(
            query,
            rerank_top_n=15,
            **rag_kwargs,
        )

        prompt = self._build_prompt(
            rag_context=str(rag_data),
            context=self.get_context(typology),
        )

        return rag_data, [
            {
                "role": "system",
                "content": prompt
            }
        ] + history + [
            {
                "role": "user",
                "content": query
            }
        ]

    async def get_stream(self, messages: list[dict], api_key: str | None = None) -> AsyncIterator[str]:
        headers = self._build_headers(api_key)
        payload = self._build_payload(messages, stream=True)

        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_ENDPOINT, headers=headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Request failed with status code {response.status}")
                
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

    async def get_discrete(self, messages: list[dict], api_key: str | None = None) -> str:
        headers = self._build_headers(api_key)
        payload = self._build_payload(messages, stream=False)

        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_ENDPOINT, headers=headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Request failed with status code {response.status}")

                result = await response.json()
                return result

    async def response(
        self,
        query: str,
        history: list[dict],
        typology: str | None = "null",
        stream: bool = False,
        api_key: str | None = None, # - наранхо откуда ключи? - вертолет дает
        **kwargs,
    ):
        rag_data, messages = await self.prepare_messages(
            query=query,
            history=history,
            typology=typology,
            **kwargs,
        )

        if stream:
            return rag_data, self.get_stream(
                messages=messages,
                api_key=api_key
            )

        return rag_data, await self.get_discrete(
            messages=messages,
            api_key=api_key
        )
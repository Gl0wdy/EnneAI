from __future__ import annotations

import abc
from collections.abc import AsyncIterator

from enneai.ai.llm import OpenRouterClient
from enneai.ai.rag import retrieve, RagContext
from enneai.utils.reader import load_file


class ChatClient(abc.ABC):
    def __init__(
        self,
        prompt: str,
        model: str,
        corr: str | None = None,
        api_key: str | None = None,
    ):
        self.client = OpenRouterClient(
            model=model,
            api_key=api_key,
        )

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

    def build_prompt(
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

    def get_context(
        self,
        typology: str | None,
    ) -> str:
        return self.contexts.get(
            typology,
            self.contexts["ennea"],
        )

    async def prepare_messages(
        self,
        query: str,
        typology: str | None = "null",
        **rag_kwargs,
    ) -> list[dict[str, str]]:

        rag_data: RagContext = await retrieve(
            query,
            **rag_kwargs,
        )

        prompt = self.build_prompt(
            rag_context=str(rag_data),
            context=self.get_context(typology),
        )

        return [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": query,
            },
        ]

    async def response(
        self,
        query: str,
        model: str | None = None,
        typology: str | None = "null",
        stream: bool = False,
        **kwargs,
    ):
        messages = await self.prepare_messages(
            query=query,
            typology=typology,
            **kwargs,
        )

        if stream:
            return self.client.stream_response(
                messages=messages,
                model=model,
            )

        return await self.client.discrete_response(
            messages=messages,
            model=model,
        )
    
    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> AsyncIterator[str]:

        async for chunk in self.client.stream_response(
            messages=messages,
            model=model,
        ):
            yield chunk
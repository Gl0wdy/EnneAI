from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
from ddgs import DDGS
from trafilatura import extract

from enneai.ai.modules.chat import ChatClient
from enneai.config import OPENROUTER_PRIMARY_MODEL


@dataclass(slots=True)
class WebContext:
    text: str


class Jung(ChatClient):
    def __init__(
        self,
        model: str | None = OPENROUTER_PRIMARY_MODEL,
    ):
        super().__init__(
            prompt="src/enneai/ai/modules/jung/prompt.txt",
            requery_prompt="src/enneai/ai/modules/jung/requery_prompt.txt",
            corr="data/corr/correlations.txt",
            model=model
        )

    async def get_web(
        self,
        query: str,
        limit: int = 5,
        timeout: float = 10.0,
        max_chars: int = 12000,
    ) -> str:
        results = await asyncio.to_thread(
            lambda: list(DDGS().text(query, max_results=limit))
        )
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        headers = {"User-Agent": "EnneAI/0.1"} # ))))))) cloudflare will EXTERMINATE me

        async with aiohttp.ClientSession(
            timeout=client_timeout,
            headers=headers,
        ) as session:
            pages = await asyncio.gather(
                *(self._fetch_page(session, result) for result in results),
                return_exceptions=True,
            )

        context_parts: list[str] = []
        used_chars = 0
        for page in pages:
            if not isinstance(page, str) or not page.strip():
                continue

            block = page.strip()
            remaining_chars = max_chars - used_chars
            if remaining_chars <= 0:
                break
            if len(block) > remaining_chars:
                block = block[:remaining_chars].rsplit(" ", 1)[0]
            context_parts.append(block)
            used_chars += len(block)

        return "\n\n".join(context_parts)

    @staticmethod
    async def _fetch_page(
        session: aiohttp.ClientSession,
        result: dict[str, Any],
    ) -> str | None:
        url = result.get("href") or result.get("url")
        if not url:
            return None

        try:
            async with session.get(url, allow_redirects=True) as response:
                if response.status >= 400:
                    return None
                html = await response.text(errors="replace")
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

        return extract(html) or ""

    async def prepare_messages(
        self,
        query: str,
        history: list[dict],
        web_query: str | None = None,
        typology: str | None = "null",
        **web_kwargs,
    ) -> tuple[WebContext, list[dict]]:
        web_text = await self.get_web(web_query or query, **web_kwargs)
        prompt = (
            self.prompt
            .replace("<SUBJECT>", web_text)
            .replace("<CONTEXT>", self.get_context(typology))
            .replace("<CORR>", self.corr)
        )

        return WebContext(text=web_text), [
            {
                "role": "system",
                "content": prompt,
            }
        ] + history + [
            {
                "role": "user",
                "content": query,
            }
        ]

    async def response(
        self,
        query: str,
        history: list[dict],
        rag_query: str | None = None,
        typology: str | None = "null",
        stream: bool = False,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs,
    ):
        web_data, messages = await self.prepare_messages(
            query=query,
            web_query=rag_query,
            history=history,
            typology=typology,
            **kwargs,
        )

        if stream:
            return web_data, self.get_stream(
                messages=messages,
                api_key=api_key,
                model=model,
            )

        return web_data, await self.get_discrete(
            messages=messages,
            api_key=api_key,
            model=model,
        )
from __future__ import annotations

from dataclasses import dataclass

from enneai.ai.modules.chat import ChatClient
from enneai.scraper import scraper
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
            prompt="data/prompts/jung.txt",
            requery_prompt="data/prompts/jung_requery.txt",
            corr="data/prompts/correlations.txt",
            model=model
        )

    async def prepare_messages(
        self,
        query: str,
        web_text: str,
        history: list[dict],
        typology: str | None = "null",
    ) -> tuple[WebContext, list[dict]]:
        prompt = (
                self.prompt
                .replace("<SUBJECT>", web_text or "None")
                .replace("<CONTEXT>", self.get_context(typology))
                .replace("<CORR>", self.corr)
            )

        return WebContext(text=(web_text or "None")), [
            {
                "role": "system",
                "content": prompt,
            }
        ] + [
            {
                "role": "user",
                "content": query,
            }
        ]

    async def response(
        self,
        query: str,
        web_text: str,
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
            web_text=web_text,
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
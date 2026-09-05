from enneai.ai.modules.chat import ChatClient
from enneai.ai.rag import retrieve, RagContext
from enneai.config import OPENROUTER_PRIMARY_MODEL

import json


class Naranjo(ChatClient):
    def __init__(
        self,
        model: str | None = OPENROUTER_PRIMARY_MODEL
    ):
        super().__init__(
            prompt="data/prompts/naranjo.txt",
            requery_prompt="data/prompts/naranjo_requery.txt",
            model=model
        )

    def _chunks_for_prompt(self, chunks: list[dict]) -> str:
        lean = [
            {
                "book": c["book_title"],
                "author": c["book_author"],
                "category": c["category"],
                "section": " > ".join(c["headings"]) if c["headings"] else None,
                "text": c["text"],
            }
            for c in chunks
        ]
        return json.dumps(lean, ensure_ascii=False, indent=2)

    async def prepare_messages(
        self,
        query: str,
        history: list[dict],
        rag_query: str | None = None,
        typology: str | None = "null",
        **rag_kwargs,
    ) -> tuple[RagContext, list[dict]]:
        if rag_query != 'None':
            rag_data: RagContext = await retrieve(
                rag_query or query,
                category=typology,
                rerank_top_n=25,
                **rag_kwargs,
            )
        else:
            rag_data = RagContext(text="", sources=[], chunks=[])

        prompt = self._build_prompt(
            rag_context=self._chunks_for_prompt(rag_data.chunks),
            context=self.get_context(typology),
        )
        return rag_data, [
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
        rag_query: str,
        typology: str | None = "null",
        stream: bool = False,
        api_key: str | None = None, # - наранхо откуда ключи? - вертолет дает
        model: str | None = None,
        reasoning_effort: str = "medium",
        **kwargs,
    ):
        rag_data, messages = await self.prepare_messages(
            query=query,
            rag_query=rag_query,
            history=history,
            typology=typology,
            **kwargs,
        )

        if stream:
            return rag_data, await self.get_stream(
                messages=messages,
                api_key=api_key,
                model=model,
                reasoning_effort=reasoning_effort
            )

        return rag_data, await self.get_discrete(
            messages=messages,
            api_key=api_key,
            model=model,
            reasoning_effort=reasoning_effort
        )

from enneai.ai.modules.chat import ChatClient
from enneai.ai.rag import retrieve, RagContext
from enneai.config import OPENROUTER_PRIMARY_MODEL


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

    async def prepare_messages(
        self,
        query: str,
        history: list[dict],
        rag_query: str | None = None,
        typology: str | None = "null",
        **rag_kwargs,
    ) -> tuple[RagContext, list[dict]]:
        rag_data: RagContext = await retrieve(
            rag_query or query,
            metadata={'category': typology},
            rerank_top_n=25,
            **rag_kwargs,
        )

        prompt = self._build_prompt(
            rag_context=str(rag_data),
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
            return rag_data, self.get_stream(
                messages=messages,
                api_key=api_key,
                model=model
            )

        return rag_data, await self.get_discrete(
            messages=messages,
            api_key=api_key,
            model=model
        )

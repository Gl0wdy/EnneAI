import aiohttp
import json
import abc
from string import Template
from collections.abc import AsyncIterator

from enneai.utils.reader import load_file

from enneai.config import (
    OPENROUTER_ENDPOINT,
    OPENROUTER_PRIMARY_MODEL,
    OPENROUTER_SECONDARY_MODEL,
    OPENROUTER_TIMEOUT,
)
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
        self.prompt = Template(load_file(prompt))
        self.requery_prompt = Template(load_file(requery_prompt)) if requery_prompt else Template("")
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
        return self.prompt.substitute(
            RAG=rag_context,
            CONTEXT=context,
            CORR=self.corr
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
        reasoning_effort: str = "medium",
        max_tokens: int | None = None
    ) -> dict:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
            "reasoning": {
                "enabled": reasoning,
                'effort': reasoning_effort
            },
            "max_tokens": max_tokens
        }
        return payload

    async def get_stream(
        self,
        messages: list[dict],
        api_key: str | None = None,
        model: str | None = OPENROUTER_PRIMARY_MODEL,
        reasoning: bool = True,
        reasoning_effort: str = "medium",
        max_tokens: int | None = None
    ) -> AsyncIterator[str]:
        headers = self._build_headers(api_key)
        payload = self._build_payload(
            messages, model=model, stream=True, reasoning=reasoning,
            reasoning_effort=reasoning_effort, max_tokens=max_tokens
        )

        session = aiohttp.ClientSession()
        response = await session.post(OPENROUTER_ENDPOINT, headers=headers, json=payload)

        if response.status != 200:
            body = await response.text()
            await response.release()
            await session.close()
            logger.error(f"Request failed with status code {response.status}")
            raise RuntimeError(f"OpenRouter request failed ({response.status}): {body}")

        return self._iter_stream(response, session)

    async def _iter_stream(self, response, session) -> AsyncIterator[str]:
        try:
            buffer = ""
            async for chunk in response.content.iter_any():
                if chunk:
                    buffer += chunk.decode('utf-8')
                    while True:
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
        finally:
            response.release()
            await session.close()

    async def get_discrete(
        self,
        messages: list[dict],
        api_key: str | None = None,
        model: str | None = OPENROUTER_PRIMARY_MODEL,
        reasoning: bool = True,
        reasoning_effort: str = "medium",
        max_tokens: int | None = None
    ) -> str:
        headers = self._build_headers(api_key)
        payload = self._build_payload(messages, model=model, stream=False, reasoning=reasoning, reasoning_effort=reasoning_effort, max_tokens=max_tokens)

        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_ENDPOINT, headers=headers, json=payload) as response:
                result = await response.json()
                if response.status != 200:
                    logger.error(f"Request failed with status code {response.status}")
                    raise RuntimeError(f"OpenRouter request failed ({response.status}): {result}")
                return result

    async def requery(
        self,
        typology: str,
        query: str,
        history: list[dict],
        api_key: str | None = None
    ) -> str:
        if not self.requery_prompt.template:
            return query

        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in history
        ) or "(empty)"

        prompt = self.requery_prompt.substitute(
            CONTEXT=self.contexts[typology],
            HISTORY=history_text
        )

        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': query}
        ]

        response = await self.get_discrete(
            messages,
            api_key=api_key,
            model=OPENROUTER_SECONDARY_MODEL,
            reasoning=False,
            max_tokens=120
        )
        if "error" in response:
            logger.error("LLM error response: %s", response)
            raise Exception(response["error"])
        return response['choices'][0]['message']['content']
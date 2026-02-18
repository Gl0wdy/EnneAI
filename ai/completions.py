from g4f import AsyncClient
from g4f.providers.any_provider import PollinationsAI

from ai.vector_db import VectorDb
from ai.data import Data, GROUP_PROMPT

from utils.logger import logger
from utils.key_rotation import ApiKey
from config import API_KEYS


class Chat:
    def __init__(self):
        self._client = AsyncClient(
            provider=PollinationsAI
        )
        self.key = ApiKey(API_KEYS)
        self.vector_db = VectorDb()

    async def create(self,
                     request: str,
                     collection: str,
                     chat_history: list = [],
                     is_group: bool = False,
                     tags: str = ""):
        if self.key.main is None:
            await self.key.update_status()
        print(self.key.main)
        data_chunks = await self.vector_db.search(f"{tags}\n{request}", collection) or []
        data = Data(collection)
        messages = data.static + [
            {'role': 'system', 'content': f'БАЗА ЗНАНИЙ N.{n}:\n{chunk}'}
            for n, chunk in enumerate(data_chunks, 1) 
        ]  + data.prompt + (GROUP_PROMPT if is_group else []) + chat_history
        try:
            response = await self._client.chat.completions.create(
                messages=messages,
                model='openai',
                max_tokens=1000,
                api_key=self.key.main
            )
        except Exception as err:
            error_msg = str(err).lower()
        
            if "402" in error_msg or "balance" in error_msg:
                logger.info('Changing api key!')
                await self.key.update_status()
            else:
                logger.error('Error in ai/completions.py', exc_info=err)
                return "Сервера Pollinations не отвечают. Попробуйте отправить запрос позже ещё раз."

        response_content = response.choices[0].message.content
        return response_content
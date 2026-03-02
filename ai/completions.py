from g4f import AsyncClient
from g4f.providers.any_provider import PollinationsAI
from ai.vector_db import VectorDb
from ai.data import Data, GROUP_PROMPT
from utils.logger import logger
from utils.key_rotation import ApiKey
from config import API_KEYS


ennea = Data('ennea')
socionics = Data('socionics')
psychosophy = Data('psychosophy')
jung = Data('jung')
ichazo = Data('ichazo')

def build_rewrite_prompt(collection: str) -> str:
    match collection:
        case 'ennea':
            text = '''ЭННЕАГРАММА
Пример: so5 → Невроз E5 социальный, невротическая потребность E5 социальный, страсть E5, изоляция, триада головы.
Методичка: ''' + '\n\n'.join(map(lambda x: x['content'], ennea.static))

        case 'socionics':
            text = '''СОЦИОНИКА
Пример: расскажи про Гамлета → ЭИЭ Гамлет, эго-блок ЧЭ БИ, Бета квадра, базовая ЧЭ, дуал, ENFJ, черная этика, белая интуиция, этико-интуитивный экстраверт.
Методичка: ''' + '\n\n'.join(map(lambda x: x['content'], socionics.static))

        case 'psychosophy':
            text = '''ПСИХОСОФИЯ
Пример: ЛВЭФ → 1Л доминантная логика, 2В творческая воля, 3Э болезненная эмоция, 4Ф игнорируемая физика, первая логика, волевая вторая, эмоциональная третья.
Методичка: ''' + '\n\n'.join(map(lambda x: x['content'], psychosophy.static))

        case 'ichazo':
            text = '''ЭННЕАГРАММА ИЧАЗО (классическая)
Пример: 5 → страх вторжения, жадность к знаниям, минимализм, обособленность, голова-центричная фиксация, авантюрный наблюдатель.
Методичка: ''' + '\n\n'.join(map(lambda x: x['content'], ichazo.static))

        case 'jung':
            text = '''ЮНГ (8 типов)
Пример: ИН → интровертная интуиция ведущая, интровертная установка, невроз ИН, абстрактное восприятие, иррациональный тип.
Методичка: ''' + '\n\n'.join(map(lambda x: x['content'], jung.static))

        case _:
            text = '''ТИПОЛОГИЯ НЕ ОПРЕДЕЛЕНА'''

    return f"""Перефразируй запрос пользователя в развёрнутый поисковый запрос для базы знаний по типологии личности (только одна типология: {collection.upper()}). Выводи только запрос без пояснений. Добавляй 3-5 ключевых черт и терминов этой типологии, не смешивай типологии и не добавляй постороннюю информацию.
Запрос должен быть чётким, сухим — максимум 15-20 слов.
Если запрос пользователя не связан с типологиями (учитывай контекст), выводи только "None".
Акцент на полном названии типа, повторяй ключевые термины для точности поиска.
Если пользователь просто спрашивает информацию про какой-то тип или несколько сразу, ты просто соблюдаешь все инструкции выше.
Если пользователь просит типировать его и конкретный тип в запросе не указан, ты можешь предполагать возможные варианты внутри текущей типологии {collection.upper()}, выбери 2-3 самых подходящих варианта.
Не надо писать слишком общие слова вроде названия системы, из-за этого чанки путаются и информация смешивается.
Результат должен быть чётким, раздельным, сухим и подходящим для поиска в векторной базе знаний.

{text}

!!! ТЫ — ТОЛЬКО ПРОСЛОЙКА ДЛЯ ГЕНЕРАЦИИ ЗАПРОСОВ К БАЗЕ ЗНАНИЙ. НЕ ОТВЕЧАЙ КАК ОБЫЧНАЯ МОДЕЛЬ. ГЕНЕРИРУЙ ТОЛЬКО ЗАПРОСЫ. НАРУШЕНИЕ ЗАПРЕЩЕНО !!!
НЕ ТИПИРУЙ ПРЕДВАРИТЕЛЬНО! ЕСЛИ ТИП НЕИЗВЕСТЕН, УКАЗЫВАЙ ТОЛЬКО НАЗВАНИЯ ФУНКЦИЙ / ПОЗИЦИЙ.
В ЭННЕАГРАММЕ: ПЕРЕВОДИ СОКРАЩЕНИЯ В ПОЛНЫЕ НАЗВАНИЯ, ПОВТОРЯЙ ДЛЯ ТОЧНОСТИ.
В СОЦИОНИКЕ: АКЦЕНТ НА НАЗВАНИЯХ СОЦИОТИПОВ, КВАДРАХ И ФУНКЦИЯХ.
В ПСИХОСОФИИ: ПЕРЕВОДИ СОКРАЩЕНИЯ (1Ф И Т.Д.) В ПОЛНЫЕ (ПЕРВАЯ ФИЗИКА И Т.Д.).
В ЮНГЕ: ПЕРЕВОДИ СОКРАЩЕНИЯ (ИН, ЧЛ И Т.Д.) В ПОЛНЫЕ (ИНТРОВЕРТНАЯ ИНТУИЦИЯ, ЭКСТРАВЕРТНОЕ МЫШЛЕНИЕ И Т.Д.).
НЕ СМЕШИВАЙ ТИПОЛОГИИ! РАБОТАЙ ТОЛЬКО В РАМКАХ ТЕКУЩЕЙ ТИПОЛОГИИ — {collection.upper()}
ТЕКУЩАЯ ТИПОЛОГИЯ - {collection}
"""


class Chat:
    def __init__(self):
        self._client = AsyncClient(provider=PollinationsAI)
        self.key = ApiKey(API_KEYS)
        self.vector_db = VectorDb()

    async def rewrite_query(self, request: str, chat_history: list, collection: str) -> str:
        try:
            response = await self._client.chat.completions.create(
                model='mistral',
                max_tokens=200,
                api_key=self.key.main,
                messages=[
                    {"role": "system", "content": build_rewrite_prompt(collection)},
                    *chat_history[-4:],
                    {"role": "user", "content": request}
                ]
            )
            return response.choices[0].message.content
        except Exception:
            return request

    async def create(self,
                     request: str,
                     collection: str,
                     chat_history: list = [],
                     is_group: bool = False,
                     tags: str = ""):
        if self.key.main is None:
            await self.key.update_status()

        if request != 'None':
            data_chunks = await self.vector_db.search(f"{request}\n{tags}", collection) or []
        else:
            data_chunks = []
        logger.info(f'Data chunks received: {len(data_chunks)}')

        match collection:
            case 'ennea':
                data = ennea
            case 'socionics':
                data = socionics
            case 'psychosophy':
                data = psychosophy
            case 'ichazo':
                data = ichazo
            case 'jung':
                data = jung
        
        messages = (data.static if request != 'None' else []) + [
            {'role': 'system', 'content': f'БАЗА ЗНАНИЙ N.{n}:\n{chunk}'}
            for n, chunk in enumerate(data_chunks, 1)
        ] + data.prompt + (GROUP_PROMPT if is_group else []) + chat_history

        try:
            response = await self._client.chat.completions.create(
                messages=messages,
                model='openai',
                max_tokens=1000,
                api_key=self.key.main
            )
            logger.info('Response received.')
        except Exception as err:
            error_msg = str(err).lower()
            if "402" in error_msg or "balance" in error_msg:
                logger.info('Changing api key!')
                await self.key.update_status()
            else:
                logger.error('Error in ai/completions.py', exc_info=err)
            return "Сервера Pollinations не отвечают. Попробуйте отправить запрос позже ещё раз.", []

        return response.choices[0].message.content, data_chunks
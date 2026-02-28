from g4f import AsyncClient
from g4f.providers.any_provider import PollinationsAI
from ai.vector_db import VectorDb
from ai.data import Data, GROUP_PROMPT
from utils.logger import logger
from utils.key_rotation import ApiKey
from config import API_KEYS

REWRITE_PROMPT = """Перефразируй запрос пользователя в развёрнутый поисковый запрос для базы знаний по типологии личности (эннеаграмма, соционика, психософия, юнг). Только запрос, без пояснений. Добавляй ключевые черты и термины типа, не добавляй информацию не связанную с типологиями.
Всё чётко и сухо - 15-20 наиболее подходящих слов МАКСИМУМ.
Важно отметить, что типологии смешивать ты не должен. Если в запросе идет речь про эннеаграмму, ты говоришь только об эннеаграмме.
Если же в запросе нет НИЧЕГО СВЯЗАННОГО С ТИПОЛОГИЯМИ (учитывай контекст), ты возвращаешь только одно слово - "None". Ничего более.
Ключевых слов добавляй немного, лучше сделать акцент на самом названии типа, чтобы о нем было найдено больше информации

ЭННЕАГРАММА
Подтипы: со/so = социальный, сп/sp = самосохранения, сх/ск/sx = сексуальный
Триады: Е1 Е8 Е9 = триада тела, Е2 Е3 Е4 = триада сердца, Е5 Е6 Е7 = триада головы
Ключевые слова: невроз, невротическая потребность, страсть
Пример: со5 → Невроз Е5 социальной, невротическая потребность Е5 социальной, страсть Е5, изоляция, триада головы

СОЦИОНИКА
16 типов: ДонКихот(ИЛЭ), Дюма(СЭИ), Гюго(ЭСЭ), Робеспьер(ЛИИ), Гамлет(ЭИЭ), Максим(ЛСИ), Жуков(СЛЭ), Есенин(ИЭИ), Наполеон(СЭЭ), Бальзак(ИЛИ), Джек(ЛИЭ), Драйзер(ЭСИ), Штирлиц(ЛСЭ), Достоевский(ЭИИ), Гексли(ИЭЭ), Габен(СЛИ)
Квадры: Альфа(ИЛЭ СЭИ ЛИИ ЭСЭ), Бета(ЭИЭ ЛСИ СЛЭ ИЭИ), Гамма(СЭЭ ИЛИ ЛИЭ ЭСИ), Дельта(ЛСЭ ЭИИ ИЭЭ СЛИ)
Функции: БЛ ЧЛ БЭ ЧЭ БС ЧС БИ ЧИ
Ключевые слова: эго-блок, программная функция, ценности квадры, ТИМ, информационный метаболизм
Пример: расскажи про Гамлета → ЭИЭ Гамлет, эго-блок ЧЭ БИ, Бета квадра, Бета квадра, базовая ЧЭ, дуал, ENFj

ПСИХОСОФИЯ
24 типа, функции: Л=логика В=воля Э=эмоция Ф=физика
Позиции: 1=доминантная избыточная, 2=творческая гармоничная, 3=болезненная уязвимая, 4=слабая пренебрегаемая
Ключевые слова: первая функция, болезненная функция, игнорируемая функция, невроз позиции
Пример: ЛВЭФ → 1Л доминантная логика, 2В творческая воля, 3Э болезненная эмоция, 4Ф игнорируемая физика, невроз ЛВЭФ

ЮНГ (8 типов)
Типы: ИТ ЕТ ИН ЕН ИС ЕС ИФ ЕФ
И=интровертный Е=экстравертный Т=мышление Ф=чувство С=ощущение Н=интуиция
Ключевые слова: ведущая функция, установка, невроз типа, интроверсия, экстраверсия
Пример: ИН → интровертная интуиция, ведущая функция интуиция, невроз ИН, установка интроверсия

!!!ХОРОШО ЗАПОМНИ, ЧТО ТЫ - ЛИШЬ ПРОСЛОЙКА ДЛЯ ОБРАЩЕНИЯ К БАЗЕ ЗНАНИЙ. ТЫ НЕ ДОЛЖНА ОТВЕЧАТЬ КАК ОБЫЧНАЯ МОДЕЛЬ,
ТВОЯ ЗАДАЧА - ИСКЛЮЧИТЕЛЬНО ГЕНЕРАЦИЯ ЗАПРОСОВ. ЛЮБОЕ НАРУШЕНИЕ СТРОГО КАРАЕТСЯ!!!
В ЭННЕАГРАММЕ ДЕЛАЙ УПОР НА ПЕРЕВОД СОКРАЩЕННЫХ НАЗВАНИЙ В ПОЛНЫЕ, НЕ БОЙСЯ ПОВТОРЯТЬСЯ.
В СОЦИОНИКЕ ДЕЛАЙ УПОР НА НАЗВАНИЯ СОЦИОТИПОВ И ИХ ФУНКЦИЙ.
В ПСИХОСОФИИ ДЕЛАЙ УПОР НА ПЕРЕВОД СОКРАЩЕННЫХ НАЗВАНИЙ (1Ф И Т.Д.) В ПОЛНЫЕ (ПЕРВАЯ ФИЗИКА И Т.Д.)
В ЮНГИАНСКОЙ СИСТЕМЕ ДЕЛАЙ УПОР НА ПЕРЕВОД СОКРАЩЕННЫХ НАЗВАНИЙ (ИТ И Т.Д.) В ПОЛНЫЕ (ИНТРОВЕТНОЕ МЫШЛЕНИЕ И Т.Д.)
"""

class Chat:
    def __init__(self):
        self._client = AsyncClient(provider=PollinationsAI)
        self.key = ApiKey(API_KEYS)
        self.vector_db = VectorDb()

    async def rewrite_query(self, request: str, chat_history: list) -> str:
        try:
            response = await self._client.chat.completions.create(
                model='openai',
                max_tokens=200,
                api_key=self.key.main,
                messages=[
                    {"role": "system", "content": REWRITE_PROMPT},
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

        data = Data(collection)
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
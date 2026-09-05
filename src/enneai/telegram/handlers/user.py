from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputRichMessage, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import (
    Text,
    Bold,
    Italic
)

from enneai.db import User
from enneai.db.repositories import UserMessageRepository, UserRepository
from enneai.ai.modules.naranjo.response import Naranjo
from enneai.ai.modules.jung.response import Jung
from enneai.ai.llm.keys_rotation import KeyRotator

import enneai.telegram.fsm as fsm
import enneai.telegram.keyboards.user as user_kb
from enneai.telegram.utils.custom_emoji import CustomEmojis
from ..stream import TelegramStream

from enneai.config import OPENROUTER_API_KEY, ENCRYPTION_KEY, TELEGRAM_ADMIN_ID
from enneai.utils.openrouter import check_openrouter_key
from enneai.utils.encryption import Encryptor
from enneai.utils.lang import is_not_english
from enneai.scraper import scraper
from enneai.utils.logger import logger

from datetime import datetime as dt
from zoneinfo import ZoneInfo

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set in the environment variables.")

naranjo = Naranjo()
jung = Jung()
router = Router(name='user')
message_rep = UserMessageRepository()
user_rep = UserRepository()
encryptor = Encryptor(ENCRYPTION_KEY)


@router.message(CommandStart())
async def start_handler(message: Message):    
    text = (
        "Привет! Я - типологический AI-бот **Клаудио Наранхо**"
        " [с полностью открытым исходным кодом](https://github.com/Gl0wdy/EnneAI).\n"
        "Проект выступает как экспериментально-развлекательный, но также выполняет и свою *образовательную роль.*\n"
        "# Как это работает?\n"
        "Проект основан на технологии [RAG](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)"
        ", что позволяет обогащать LLM знаниями *без прямого обучения модели*. "
        "Мы используем книги от самого Наранхо, Юнга и прочих авторов в качестве источников информации.\n"
        "# Что я умею?\n"
        "Бот основан на своих предшественниках, которые некогда существовали раздельно - **бот Наранхо и бот Юнг.**\n"
        "Модуль *Наранхо* общается с пользователям в формате диалога, помогает быстро искать информацию из книг"
        " и интерпретировать её с помощью LLM, например, типируя его по ответам на вопросы.\n"
        "Модуль *Юнга* существует только и только для того, чтобы типировать различного рода fictionю." 
        " (персонажи из сериалов, книг, музыку и прочий контент). Эти два модуля **не взаимозаменяемы** и в их основе лежит абсолютно разный подход.\n\n"
        "Просто напиши мне свой вопрос!"
    )

    await message.answer_rich(
        InputRichMessage(markdown=text),
        reply_markup=user_kb.main_menu_keyboard
    )


# ========== ХЭНДЛЕР ОЧЕРЕДИ (!!!) ================
@router.message(Command('cancel'))
async def command_cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Запрос отменен.')

@router.message(fsm.ProfileStates.in_progress)
async def in_progress_handler(message: Message):
    content = Text(CustomEmojis.pepe_thinking, " Ваш запрос обрабатывается. Пожалуйста, подождите...")
    await message.answer(
        **content.as_kwargs())


# =========== ХЭНДЛЕРЫ КОМАНД ================
@router.message(Command('clear'))
async def command_clear_handler(message: Message, state: FSMContext):
    content = Text(
        CustomEmojis.clear,
        ' Это полностью сотрёт боту память о вашей последней переписке. Вы уверены?'
    )
    
    await message.answer(
        **content.as_kwargs(),
        reply_markup=user_kb.build_reply_keyboard('Стереть', 'Отмена')
    )
    await state.set_state(fsm.CommandStates.waiting_for_clear)

@router.message(fsm.CommandStates.waiting_for_clear)
async def clear_confirmation_handler(message: Message, state: FSMContext):
    match message.text:
        case 'Стереть':
            await message_rep.clear_history(message.from_user.id)
            await message.answer(
                'Теперь вы начинаете с чистого листа...',
                reply_markup=user_kb.main_menu_keyboard
            )
            await state.clear()
        case 'Отмена':
            await message.answer(
                'Очистка истории отменена. Продолжайте.',
                reply_markup=user_kb.main_menu_keyboard
            )
            await state.clear()
        case _:
            await message.answer('Просто нажми на кнопку. Не нужно ничего писать.')

@router.message(
    or_f(
        Command('profile'),
        F.text == 'Профиль'
    )
)
async def show_profile_handler(message: Message, user: User):
    content = Text(
        CustomEmojis.account,
        " Это вы, ",
        Bold(user.username),
        ":\n",
        Italic('> ' + user.typologies),
        "\n",
        "> осталось ",
        Italic(f"{user.request_remain}/{user.request_limit}"),
        " запросов на сегодня."
    )

    await message.answer(**content.as_kwargs())

def build_settings_message(user: User):
    text = Text(
        CustomEmojis.settings,
        Bold(' Настройки:\n'),
        f'$ Режим > {user.settings.mode}\n',
        f'- Уровень рассуждения > {user.settings.reasoning}\n',
        f'- База знаний > {user.settings.system}\n',
        f'$ Re-query > {["❌ OFF", "✅ ON"][user.settings.requery]}'
    )
    return text.as_kwargs()

@router.message(
    or_f(
        Command('settings'),
        F.text == 'Настройки'
    )
)
async def show_settings_handler(message: Message, user: User):
    text = build_settings_message(user)
    await message.answer(
        **text, 
        reply_markup=user_kb.build_settings_keyboard(user)
    )

@router.callback_query(F.data.startswith('settings'))
async def switch_settings_handler(callback: CallbackQuery, user: User):
    _, field, value = callback.data.split(':')
    match field:
        case 'mode':
            user.settings.mode = value
        case 'reasoning':
            user.settings.reasoning = value
        case 'system':
            user.settings.system = value
        case 'requery':
            user.settings.requery = value == 'on'

    await user.save()
    text = build_settings_message(user)
    await callback.message.edit_text(
        **text,
        reply_markup=user_kb.build_settings_keyboard(user)
    )

    await callback.answer(f'Вы успешно сменили {field}!')

@router.message(Command('key'))
async def wait_for_key_handler(message: Message, user: User, state: FSMContext):
    if user.encrypted_key:
        text = 'Вы уже зарегистрировали свой ключ. Если хотите поменять его, просто пришлите новый.'
    else:
        text = 'Зарегистрируйте свой ключ [здесь](https://openrouter.ai/workspaces/default/keys) и пришлите его ниже ("бурмалда" для отмены).'

    await state.set_state(fsm.CommandStates.waiting_for_key)
    await message.answer(text, reply_markup=user_kb.register_key_keyboard)

@router.message(fsm.CommandStates.waiting_for_key)
async def fetch_key_handler(
    message: Message,
    user: User,
    state: FSMContext,
    keychain: KeyRotator
):
    key = message.text
    if key.lower() == 'бурмалда':
        await message.answer('Отменено...', reply_markup=user_kb.main_menu_keyboard)
        return
    msg = await message.answer('Проверяем ваш ключ...')

    is_valid = await check_openrouter_key(key)
    if is_valid:
        keychain.add_key(key)
        await msg.edit_text(
            '*Ключ успешно зарегистрирован!*\nВаши лимиты были расширены.',
            reply_markup=user_kb.main_menu_keyboard
        )
        user.request_remain = 40
        user.request_limit = 40
        user.encrypted_key = encryptor.encrypt(key)
        await user.save()
    else:
        await msg.edit_text(    # ...
            '*Ключ невалиден*. Попробуйте команду /key снова и проверьте целостность своего ключа.',
            reply_markup=user_kb.main_menu_keyboard
        )

    await state.clear()
    


# =========== ХЭНДЛЕРЫ ПЕРСОНАЛИЗАЦИИ ================

@router.message(
    or_f(
        Command('persona'),
        fsm.ProfileStates.waiting_for_confirmation
    )
)
async def custom_username_handler(message: Message, state: FSMContext, user: User):
    if message.text not in ('Да', '/persona'):
        await state.clear()
        # ВОТ ЭТА ХУЙНЯ УНИЧТОЖИЛА ПРОД 
        user.new = False
        user.username = message.from_user.full_name
        await user.save()

        await message.answer('Хорошо. Повторите свой запрос.', reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(
        '1. Как к вам обращаться? Введите никнейм (или "бурмалда" для отмены).',
        reply_markup=user_kb.build_username_keyboard(message.from_user.full_name)
    )
    await state.set_state(fsm.ProfileStates.waiting_for_username)

@router.message(fsm.ProfileStates.waiting_for_username)
async def custom_username_handler(message: Message, user: User, state: FSMContext):
    if message.text != 'бурмалда':
        user.username = message.text
        await user.save()
    else:
        user.username = message.from_user.full_name
        await user.save()

    await message.answer(
        f'2. Славно, *{user.username}*.\nНапиши свои типологии. Если не знаешь точно, можешь написать предположительные (или "бурмалда" для отмены).',
        reply_markup=user_kb.build_reply_keyboard('Скип')
    )
    await state.set_state(fsm.ProfileStates.waiting_for_typologies)

@router.message(fsm.ProfileStates.waiting_for_typologies)
async def custom_typologies_handler(message: Message, user: User, state: FSMContext):
    if message.text != 'бурмалда':
        user.typologies = message.text
    else:
        user.typologies = 'Не указаны'
    user.new = False
    await user.save()

    await message.answer(
        'Ваши предыдущие ответы повлияют на работу бота.\nПосмотреть ваши текущие данные можно с помощью /profile. Хорошего пользования!\n_Заполнить заново - /persona_'
    )
    await state.clear()


# =========== ХЭНДЛЕРЫ ЗАПРОСОВ ================

async def get_chat_history(user_id: int):
    chat = await message_rep.get_all(user_id=user_id)
    chat_history = []
    for msg in chat:
        chat_history.extend(
            (
                {'role': 'user', 'content': msg.user_query},
                {'role': 'assistant', 'content': msg.response}
            )
        )

    return chat_history

@router.message(F.text)
async def request_handler(
    message: Message, 
    user: User, 
    state: FSMContext,
    keychain: KeyRotator
):
    if message.chat.type != 'private':
        return # на первое время пока вообще офф

    if user.new:
        await message.answer(
            'Желаете ли вы персонализировать бота под себя? Это займет пару секунд.',
            reply_markup=user_kb.build_reply_keyboard('Да', 'Нет')
        )
        await state.set_state(fsm.ProfileStates.waiting_for_confirmation)
        return

    today = dt.now(ZoneInfo("Europe/Moscow")).date()
    if user.burmaldate != today:
        user.request_remain = user.request_limit
        user.burmaldate = today
        await user.save()

    preferred_key = None
    if user.encrypted_key:
        try:
            preferred_key = encryptor.decrypt(user.encrypted_key)
        except Exception:
            logger.warning("Не удалось расшифровать пользовательский ключ %s", user.tg_id)

    if user.request_remain == 0 and user.tg_id != TELEGRAM_ADMIN_ID:
        text = f'*Ваш лимит запросов на сегодня был исчерпан* ({user.request_limit}). Лимиты сбрасываются в 03:00 по МСК.'
        if not user.encrypted_key:
            text += '\nЧтобы расширить лимиты, создайте свой [ключ OpenRouter](https://openrouter.ai/settings/keys) с помощью команды /key'
            await message.answer(text, reply_markup=user_kb.register_key_keyboard)
        else:
            await message.answer(text)
        return

    chat_history = await get_chat_history(user.tg_id)
    await state.set_state(fsm.ProfileStates.in_progress)
    api_calls = 0

    try:
        match user.settings.mode:
            case 'naranjo':
                if user.settings.requery:
                    content = Text(CustomEmojis.rika_thinking, " Наранхо переделывает ваш запрос...")
                    msg = await message.answer(
                        **content.as_kwargs()
                    )
                    rag_query = await keychain.rotate(
                        naranjo.requery,
                        preferred_key=preferred_key,
                        typology=user.settings.system,
                        query=message.text,
                        history=chat_history
                    )
                    api_calls += 1
                    if rag_query == 'None':
                        await msg.edit_text('Дополнительный поиск не требуется. Формирую ответ...')
                    else:
                        await msg.edit_text(f'Уточняю информацию по запросу _"{rag_query}"_. Формирую ответ...')
                else:
                    rag_query = message.text
                
                rag_data, chunks = await keychain.rotate(
                    naranjo.response,
                    preferred_key=preferred_key,
                    rag_query=rag_query,
                    query=message.text,
                    history=chat_history,
                    typology=user.settings.system,
                    stream=True,
                    reasoning_effort=user.settings.reasoning
                )
                api_calls += 1

            case 'jung':
                if is_not_english(message.text):
                    content = Text(CustomEmojis.warning, " Полезный совет: пиши имя нужного тебе персонажа на латинице (будет лучше индексация -> лучше и ответ)\n:3")
                    await message.answer(**content.as_kwargs())

                content = Text(CustomEmojis.rika_thinking, " Юнг углубляется в ваш piece of media...")
                msg = await message.answer(**content.as_kwargs())
                web_text = await scraper(message.text)
                await msg.edit_text('*Найдена информация по вашему запросу*. Один момент...')

                if user.settings.requery:
                    rag_query = await keychain.rotate(
                        jung.requery,
                        preferred_key=preferred_key,
                        typology=user.settings.system,
                        query=web_text,
                        history=chat_history
                    )
                    api_calls += 1
                    await msg.edit_text(f'Уточняю информацию по запросу _"{rag_query}"_. Формирую ответ...')
                else:
                    content = Text(CustomEmojis.warning, ' Предупреждение: работа Юнга может значительно ухудшиться с выключенным requery.\nСменить это можно в /settings')
                    await message.answer(**content.as_kwargs())
                    rag_query = message.text
                
                rag_data, chunks = await keychain.rotate(
                    jung.response,
                    preferred_key=preferred_key,
                    web_text=web_text,
                    query=message.text,
                    history=chat_history,
                    typology=user.settings.system,
                    stream=True,
                    reasoning_effort=user.settings.reasoning
                )
                api_calls += 1
            case _:
                await message.answer('Выберите режим работы бота с помощью /settings.')
                return
        
        telegram_stream = TelegramStream(
            message.bot, message.chat.id
        )
        response = await telegram_stream.stream(chunks)

        await message_rep.create(
            user_id=user.tg_id,
            user_query=message.text,
            response=response,
            rag_context=rag_data.text,
            system=user.settings.system
        )

        user.request_remain -= api_calls

    except Exception as exc:
        try:
            await message.answer(
                f'Произошла ошибка при обработке запроса: {exc}.\n'
                f'Осталось запросов на сегодня: {user.request_remain}.',
                parse_mode=None
            )
            logger.exception("Error processing request for user %s: %s", user.tg_id, exc)
        except Exception:
            await message.answer(
                f'Произошла ошибка при генерации ответа на запрос: {exc}.\n'
                f'Осталось запросов на сегодня: {user.request_remain}.',
                parse_mode=None
            )
            logger.exception("Error generating response for user %s: %s", user.tg_id, exc)
    finally:
        await state.clear()
        user.burmaldate = dt.now(ZoneInfo("Europe/Moscow")).date()
        await user.save()
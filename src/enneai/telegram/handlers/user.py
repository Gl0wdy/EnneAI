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

import enneai.telegram.fsm as fsm
import enneai.telegram.keyboards.user as user_kb
from enneai.telegram.utils.custom_emoji import CustomEmojis
from ..stream import TelegramStream

from enneai.config import OPENROUTER_API_KEY, TELEGRAM_ADMIN_ID
from enneai.ai.llm.keys_rotation import KeyRotator
from datetime import datetime as dt

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set in the environment variables.")

keychain = KeyRotator(map(str, OPENROUTER_API_KEY.split(',')))
naranjo = Naranjo()
jung = Jung()
router = Router(name='user')
message_rep = UserMessageRepository()
user_rep = UserRepository()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):    
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
        InputRichMessage(markdown=text)
    )

# =========== ХЭНДЛЕРЫ КОМАНД ================
@router.message(Command('mode'))
async def command_mode_handler(message: Message, state: FSMContext):
    content = Text(
        CustomEmojis.info,
        ' Какого бота вы хотите использовать сейчас?'
    )
    
    await message.answer(
        **content.as_kwargs(),
        reply_markup=user_kb.build_reply_keyboard('Наранхо', 'Юнг')
    )
    await state.set_state(fsm.CommandStates.waiting_for_mode)

@router.message(fsm.CommandStates.waiting_for_mode)
async def mode_selection_handler(message: Message, user: User, state: FSMContext):
    match message.text:
        case 'Наранхо':
            await user_rep.change_field(user.id, 'settings.mode', 'naranjo')
            await message.answer(
                'Вы выбрали модуль Наранхо. Продолжайте.',
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
        case 'Юнг':
            await user_rep.change_field(user.id, "settings.mode", "jung")
            await message.answer(
                'Вы выбрали модуль Юнга. Продолжайте.',
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
        case _:
            await message.answer('Просто нажми на кнопку. Не нужно ничего писать.')

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
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
        case 'Отмена':
            await message.answer(
                'Очистка истории отменена. Продолжайте.',
                reply_markup=ReplyKeyboardRemove()
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

# =========== ХЭНДЛЕРЫ ПЕРСОНАЛИЗАЦИИ ================

@router.message(fsm.ProfileStates.waiting_for_confirmation)
async def custom_username_handler(message: Message, state: FSMContext):
    if message.text != 'Да':
        await state.clear()
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
        'Ваши предыдущие ответы повлияют на работу бота.\nПосмотреть ваши текущие данные можно с помощью /profile. Хорошего пользования!'
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
async def request_handler(message: Message, user: User, state: FSMContext):
    if user.new:
        await message.answer(
            'Желаете ли вы персонализировать бота под себя? Это займет пару секунд.',
            reply_markup=user_kb.build_reply_keyboard('Да', 'Нет')
        )
        await state.set_state(fsm.ProfileStates.waiting_for_confirmation)
        return

    # if user.request_remain == 0 and user.id != TELEGRAM_ADMIN_ID:
    #     text = f'*Ваш лимит запросов на сегодня был исчерпан* ({user.request_limit}). Лимиты сбрасываются в 03:00 по МСК.'
    #     if not user.encrypted_key:
    #         text += '\nЧтобы расширить лимиты, создайте свой [ключ OpenRouter](https://openrouter.ai/settings/keys)'
    #         await message.answer(text, reply_markup=user_kb.register_key_keyboard)
    #     else:
    #         await message.answer(text)
    #     return

    chat_history = await get_chat_history(user.id)

    match user.settings.mode:
        case 'naranjo':
            if user.settings.requery:
                content = Text(CustomEmojis.rika_thinking, " Переделываю ваш запрос...")
                msg = await message.answer(
                    **content.as_kwargs()
                )
                user.request_remain -= 1
                rag_query = await keychain.rotate(
                    naranjo.requery,
                    query=message.text,
                    history=chat_history
                )
                await msg.delete()
            else:
                rag_query = message.text
            
            rag_data, chunks = await keychain.rotate(
                naranjo.response,
                rag_query=rag_query,
                query=message.text,
                history=chat_history,
                typology=user.settings.system,
                stream=True
            )
        case 'jung':
            if user.settings.requery:
                content = Text(CustomEmojis.rika_thinking, " Переделываю ваш запрос...")
                msg = await message.answer(
                    **content.as_kwargs()
                )
                user.request_remain -= 1
                rag_query = await keychain.rotate(
                    jung.requery,
                    query=message.text,
                    history=chat_history
                )
                await msg.delete()
            else:
                rag_query = message.text
            
            rag_data, chunks = await keychain.rotate(
                jung.response,
                rag_query=rag_query,
                query=message.text,
                history=chat_history,
                typology=user.settings.system,
                stream=True
            )
        case _:
            await message.answer('Выберите режим работы бота с помощью /mode.')
            return
    telegram_stream = TelegramStream(
        message.bot, message.chat.id
    )
    response = await telegram_stream.stream(chunks)

    user.request_remain -= 1
    await user.save()

    await message_rep.create(
        created_at=dt.now(),
        user_id=user.id,
        user_query=message.text,
        response=response,
        rag_context=rag_data.text,
        system=user.settings.system
    )
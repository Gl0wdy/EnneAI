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
from enneai.db.repositories import UserMessageRepository
from enneai.ai.modules.naranjo.response import Naranjo
from enneai.ai.modules.jung.response import Jung

import enneai.telegram.fsm as fsm
import enneai.telegram.keyboards.user as user_kb
from enneai.telegram.utils.custom_emoji import CustomEmojis
from ..stream import TelegramStream

from enneai.config import OPENROUTER_API_KEY, TELEGRAM_ADMIN_ID
from enneai.ai.llm.keys_rotation import KeyRotator
from datetime import datetime as dt


naranjo = Naranjo(model='nvidia/nemotron-3-super-120b-a12b:free', api_key=OPENROUTER_API_KEY)
router = Router(name='user')
message_rep = UserMessageRepository()

# naranjo = Naranjo(model='poolside/laguna-s-2.1:free', api_key=OPENROUTER_API_KEY)
# jung = Jung(model='nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free', api_key=OPENROUTER_API_KEY)


# Ты собираешься эту бурмалду переписывать так что я пока что один ключ из env буду юзать

# async def processor(msg: Message, user: User, api_key: str): # начинка для хэндлера чтобы крутить ключи на вертолете
#     '''вот тут всю логику пиши иначе кирдык'''
#      # каждый раз реинициализация клиента по приказу вертолета
#     naranjo = Naranjo(model='nvidia/nemotron-3-super-120b-a12b:free', api_key=OPENROUTER_API_KEY)
#     

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
        InputRichMessage(markdown=text)
    )


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
    await message.answer(
        '1. Как к вам обращаться? Введите никнейм.',
        reply_markup=user_kb.build_username_keyboard(message.from_user.full_name)
    )
    await state.set_state(fsm.ProfileStates.waiting_for_username)

@router.message(fsm.ProfileStates.waiting_for_username)
async def custom_username_handler(message: Message, user: User, state: FSMContext):
    if message.text != 'Скип':
        user.username = message.text
        await user.save()

    await message.answer(
        f'2. Славно, *{user.username}*.\nНапиши свои типологии. Если не знаешь точно, можешь написать предположительные.',
        reply_markup=user_kb.build_reply_keyboard('Скип')
    )
    await state.set_state(fsm.ProfileStates.waiting_for_typologies)

@router.message(fsm.ProfileStates.waiting_for_typologies)
async def custom_typologies_handler(message: Message, user: User, state: FSMContext):
    if message != 'Скип':
        user.typologies = message.text
    user.new = False
    await user.save()

    await message.answer(
        'Админу было лень писать валидатор, так что если вы ввели какой-то бред... Ну, дело ваше.\nПосмотреть ваши текущие данные можно с помощью /profile. Хорошего пользования!'
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
            reply_markup=user_kb.confirmation_keyboard
        )
        await state.set_state(fsm.ProfileStates.waiting_for_confirmation)
        return

    if user.request_remain == 0 and user.id != TELEGRAM_ADMIN_ID:
        text = f'*Ваш лимит запросов на сегодня был исчерпан* ({user.request_limit}). Лимиты сбрасываются в 03:00 по МСК.'
        if not user.encrypted_key:
            text += '\nЧтобы расширить лимиты, создайте свой [ключ OpenRouter](https://openrouter.ai/settings/keys)'
            await message.answer(text, reply_markup=user_kb.register_key_keyboard)
        else:
            await message.answer(text)
        return

    chat_history = await get_chat_history(user.id)
    rag_data, chunks = await naranjo.response(
        query=message.text, history=chat_history,
        typology=user.settings.system, stream=True
    )

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
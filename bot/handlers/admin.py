from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

import bot.keyboards as kb
import bot.database as db
from config import ADMIN_ID
from bot.fsm import SendingState, PremiumState
from .base import chat

from datetime import timedelta


admin_router = Router(name='router')


@admin_router.message(Command(commands=['admin']))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer('Админ-панель открыта.', reply_markup=kb.admin_markup)


@admin_router.message(lambda x: x.text == 'Баланс')
async def check_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = ""
    total = 0
    for key, value in chat.key.status.items():
        total += value
        text += f'{key}: {value}\n'
    text += f'\n\nTotal: {total}'
    await message.answer(text, parse_mode='HTML')

@admin_router.message(lambda x: x.text == 'Рассылка')
async def sending(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(SendingState.enter_content)
    await message.answer('Отправьте контент для рассылки:')


@admin_router.message(lambda x: x.text == 'Коллекции')
async def give_premium(message: Message):
    collections_response = chat.vector_db.get_collections()
    collections_list = collections_response.collections  # ← почти всегда так в qdrant-client

    if not collections_list:
        await message.answer("Коллекций пока нет.")
        return

    lines = []
    for coll in collections_list:
        name = coll.name
        points = coll.points if hasattr(coll, 'points') else "?"
        status = coll.status if hasattr(coll, 'status') else "?"
        vec_size = coll.config.params.vectors.size if coll.config and coll.config.params and coll.config.params.vectors else "?"

        lines.append(f"📁 {name}\n   • точек: {points:,}\n   • статус: {status}\n   • размер вектора: {vec_size}")

    text = "Список коллекций:\n\n" + "\n\n".join(lines)
    await message.answer(text)


@admin_router.message(PremiumState.giving)
async def give_premium2(message: Message, state: FSMContext):
    uid, period = message.text.split()
    period = timedelta(days=int(period))
    await db.set_status(int(uid), True, period)
    await message.bot.send_message(chat_id=uid, text=f'*🔓 Вы получили премиум на {period.days} дней!*', message_effect_id="5046509860389126442")
    await message.answer('Успешно.')
    await state.clear()


@admin_router.message(SendingState.enter_content)
async def enter_sending(message: Message, state: FSMContext):
    await state.clear()
    users = await db.get_all_users()
    c = 0
    async for i in users:
        try:
            await message.copy_to(i['user_id'])
            c += 1
        except:
            pass
    await message.answer(f'Успешно разослано всем пользователем ({c})')


@admin_router.message(lambda x: x.text == 'Логи')
async def sending(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        file = FSInputFile('app.log', 'app.log')
        await message.answer_document(file)
    except:
        await message.answer('Логовый файл пуст.')


@admin_router.message(lambda x: x.text == 'Юзеры')
async def sending(message: Message):
    users_cursor = await db.get_all_users()
    premium = 0
    default = 0
    async for i in users_cursor:
        if i.get('premium') == True:
            premium += 1
        default += 1
    await message.answer(f'Количество живых юзеров: {default}\nКоличество премиум юзеров: {premium}')
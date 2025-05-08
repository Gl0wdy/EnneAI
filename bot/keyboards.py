from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def create_buttons(data: list):
    kb = ReplyKeyboardBuilder()
    for i in data:
        kb.button(text=i)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def set_collection_buttons(user_id: int, selected: str):
    kb = InlineKeyboardBuilder()
    for i in ('dynamic', 'socionics', 'ennea', 'psychosophy'):
        kb.button(text=f'✅ {i}' if i == selected else i, callback_data=f'set__{i}_{user_id}')
    return kb.adjust(2).as_markup()

main_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='👤 Профиль'), KeyboardButton(text='⚙️ Настройки')]
    ],
    resize_keyboard=True
)

admin_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Рассылка'), KeyboardButton(text='Логи')],
        [KeyboardButton(text='Юзеры'), KeyboardButton(text='Выдать премиум')],
        [KeyboardButton(text='Доход')]
    ],
    resize_keyboard=True
)

confirm_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='✅Да'), KeyboardButton(text='❌Нет')]
    ],
    resize_keyboard=True
)

premium_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='👑 Премиум', url='https://t.me/m/KCKTEdqAM2Iy')]
    ]
)
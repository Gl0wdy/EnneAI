from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def create_buttons(data: list):
    kb = ReplyKeyboardBuilder()
    for i in data:
        kb.button(text=i)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def settings_buttons(user_id: int, selected: str, group: bool = False):
    kb = InlineKeyboardBuilder()
    data = ['ennea', 'socionics', 'psychosophy', 'jung', 'ichazo']
    index = data.index(selected)
    left, right = data[(index - 1) % len(data)],  data[(index + 1) % len(data)]
    kb.button(text='◀️', callback_data=f'collection__{left}_{user_id}')
    kb.button(text='📂', callback_data=f'colinfo__{selected}')
    kb.button(text='▶️', callback_data=f'collection__{right}_{user_id}')
    kb.button(text='🧠 Долгая память', callback_data=f'long_memory')
    return kb.adjust(3).as_markup()

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
        [KeyboardButton(text='Баланс')]
    ],
    resize_keyboard=True
)

confirm_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='✅Да'), KeyboardButton(text='❌Нет')]
    ],
    resize_keyboard=True
)

rate_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='1 ⭐️', callback_data='star_1'), InlineKeyboardButton(text='2 ⭐️', callback_data='star_2'), InlineKeyboardButton(text='3 ⭐️', callback_data='star_3')],
        [InlineKeyboardButton(text='4 🌟', callback_data='star_4'), InlineKeyboardButton(text='1 🤩', callback_data='star_5')]
    ]
)
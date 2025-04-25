from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def create_buttons(data: list):
    kb = ReplyKeyboardBuilder()
    for i in data:
        kb.button(text=i)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

main_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Что такое эннеаграмма?'), KeyboardButton(text='Что ты умеешь?')],
        [KeyboardButton(text='Типируй меня поэтапно')]
    ],
    resize_keyboard=True
)

admin_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Рассылка'), KeyboardButton(text='Логи')]
    ],
    resize_keyboard=True
)

confirm_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='✅Да'), KeyboardButton(text='❌Нет')]
    ],
    resize_keyboard=True
)
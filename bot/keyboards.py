from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


admin_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Рассылка')]
    ],
    resize_keyboard=True
)

confirm_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Да'), KeyboardButton(text='Нет')]
    ],
    resize_keyboard=True
)
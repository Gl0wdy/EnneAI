from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def build_username_keyboard(username: str):
    builder = ReplyKeyboardBuilder()
    builder.button(text=username)

    return builder.as_markup(resize_keyboard=True)

def build_reply_keyboard(*args: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for btn in args:
        builder.button(text=btn)

    return builder.as_markup(resize_keyboard=True)

register_key_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='OpenRouter', url='https://openrouter.ai/settings/keys', icon_custom_emoji_id='5244496750244293014')],
        [InlineKeyboardButton(text='Зачем это нужно', url='https://teletype.in/@boneheaded/B9nP-6DV_im', icon_custom_emoji_id='5352989913358826882')]
    ]
)
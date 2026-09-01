from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from enneai.db import User


main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Профиль', icon_custom_emoji_id='5258011929993026890')],
        [KeyboardButton(text='Настройки', icon_custom_emoji_id='5258096772776991776')]
    ],
    resize_keyboard=True
)

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

def build_settings_keyboard(user: User):
    builder = InlineKeyboardBuilder()

    next_mode = ['naranjo', 'jung'][user.settings.mode == 'naranjo']
    reasoning = ['low', 'medium', 'high']
    next_reasoning = reasoning[
        (reasoning.index(user.settings.reasoning) + 1) % len(reasoning)
    ]
    systems = ['ennea', 'socio', 'psychosophy', 'jungian']  # без auto (пока что)
    next_system = systems[
        (systems.index(user.settings.system) + 1) % len(systems)
    ]
    next_requery = ["on", "off"][user.settings.requery]

    builder.button(
        text=f'Режим > {next_mode}',
        callback_data=f'settings:mode:{next_mode}',
        icon_custom_emoji_id="5258093637450866522"
    )
    builder.button(
        text=f'Рассуждение > {next_reasoning}',
        callback_data=f'settings:reasoning:{next_reasoning}',
        icon_custom_emoji_id="5172398207988139299"
    )
    builder.button(
        text=f'БЗ > {next_system}', 
        callback_data=f'settings:system:{next_system}',
        icon_custom_emoji_id="5258334872878980409"
    )
    builder.button(
        text=f'Re-query > {next_requery}', 
        callback_data=f'settings:requery:{next_requery}',
        icon_custom_emoji_id="5370546867786523009"
    )
    builder.adjust(1)

    return builder.as_markup()
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
import asyncio

from bot.config import BOT_TOKEN, DEBUG_TOKEN
from bot.handlers.base import base_router
from bot.handlers.admin import admin_router


async def main():
    bot = Bot(
        token=DEBUG_TOKEN,
        default=DefaultBotProperties(
            parse_mode='Markdown',
            link_preview_is_disabled=True
        )
    )
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(base_router)

    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
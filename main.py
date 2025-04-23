from aiogram import Bot, Dispatcher
import asyncio

from bot.config import BOT_TOKEN, DEBUG_TOKEN
from bot.handlers.base import base_router
from bot.handlers.admin import admin_router


async def main():
    bot = Bot(token=DEBUG_TOKEN)
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(base_router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
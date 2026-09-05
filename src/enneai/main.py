import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from enneai.telegram import admin_router, router, UserMiddleware
from enneai.config import (
    TELEGRAM_DEBUG_TOKEN,
    TELEGRAM_ADMIN_ID,
    MONGO_URI,
    OPENROUTER_API_KEY
)
from enneai.db import MongoDB
from enneai.ai.rag.query import warmup
from enneai.ai.llm.keys_rotation import KeyRotator

from enneai.utils.logger import logger


bot = Bot(
    token=TELEGRAM_DEBUG_TOKEN,
    default=DefaultBotProperties(
        parse_mode="Markdown",
        link_preview_is_disabled=True,
    ),
)
dp = Dispatcher(storage=MemoryStorage())

mongo = MongoDB(
    uri=MONGO_URI,
    database="enneai",
)

@dp.startup()
async def startup():
    await warmup()

    await bot.delete_webhook(
        drop_pending_updates=True,
    )

    await bot.send_message(
        TELEGRAM_ADMIN_ID,
        "✅ Бот запущен",
    )


@dp.shutdown()
async def shutdown():
    await bot.send_message(
        TELEGRAM_ADMIN_ID,
        "❌ Бот остановлен",
    )

    await mongo.close()


async def main():
    dp.include_router(admin_router)
    dp.include_router(router)

    dp.message.middleware(
        UserMiddleware()
    )
    dp.callback_query.middleware(
        UserMiddleware()
    ) 
    await mongo.init()
    system_keys = [key.strip() for key in OPENROUTER_API_KEY.split(',') if key.strip()]
    keychain = KeyRotator(system_keys)

    logger.info("Starting bot with %d API keys", len(keychain.keys))
    await dp.start_polling(
        bot,
        skip_updates=True,
        keychain=keychain
    )


if __name__ == "__main__":
    asyncio.run(main())
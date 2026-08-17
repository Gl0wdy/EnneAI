import asyncio
import time

from aiogram import Bot
from aiogram.types import InputRichMessage
from aiogram.exceptions import TelegramRetryAfter


class TelegramStream:
    def __init__(
        self,
        bot: Bot,
        chat_id: int,
    ):
        self.bot = bot
        self.chat_id = chat_id
        self.draft_id = int(time.time() * 1000)


    async def update_draft(self, text: str):
        try:
            await self.bot.send_rich_message_draft(
                chat_id=self.chat_id,
                draft_id=self.draft_id,
                rich_message=InputRichMessage(
                    markdown=text,
                ),
            )

        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)


    async def stream(self, chunks):
        text = ""

        last_update = 0
        last_length = 0

        update_interval = 0.8
        min_chars = 50


        async for chunk in chunks:
            text += chunk

            now = time.monotonic()

            if (
                now - last_update < update_interval
                and len(text) - last_length < min_chars
            ):
                continue


            await self.update_draft(text)

            last_update = now
            last_length = len(text)

        await self.bot.send_rich_message(
            chat_id=self.chat_id,
            rich_message=InputRichMessage(
                markdown=text,
            ),
        )

        return text
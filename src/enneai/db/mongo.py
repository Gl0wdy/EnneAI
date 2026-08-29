from pymongo import AsyncMongoClient
from beanie import init_beanie

from enneai.db.models import AdminStatsSnapshot, User, UserMessage


class MongoDB:
    def __init__(
        self,
        uri: str,
        database: str,
    ):
        self.client = AsyncMongoClient(uri)
        self.db = self.client[database]


    async def init(self):   # интересный нейминг
        await init_beanie(  # и что тебе не нравится.
            database=self.db,
            document_models=[
                User,
                UserMessage,
                AdminStatsSnapshot,
            ],
        )


    async def close(self):
        await self.client.close()
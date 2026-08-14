from pymongo import AsyncMongoClient


class MongoDB:
    def __init__(self, uri: str, database: str):
        self.client = AsyncMongoClient(uri)
        self.db = self.client[database]

    async def close(self):
        await self.client.close()
import random
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase


class ApiKeyManager:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["api_keys"]

    def _next_hour(self) -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    async def add_key(self, api_key: str):
        existing = await self.col.find_one({"_id": api_key})
        if not existing:
            await self.col.insert_one({
                "_id": api_key,
                "balance": 0.0,
                "cooldown_until": None
            })

    async def remove_key(self, api_key: str):
        await self.col.delete_one({"_id": api_key})

    async def get_key(self) -> str | None:
        now = datetime.now(timezone.utc)
        docs = await self.col.find({
            "$or": [
                {"cooldown_until": None},
                {"cooldown_until": {"$lte": now}}
            ]
        }).to_list(None)

        if not docs:
            return None

        doc = random.choice(docs)

        if doc.get("cooldown_until"):
            await self.col.update_one(
                {"_id": doc["_id"]},
                {"$set": {"cooldown_until": None}}
            )

        return doc["_id"]

    async def put_on_cooldown(self, api_key: str):
        await self.col.update_one(
            {"_id": api_key},
            {"$set": {"cooldown_until": self._next_hour()}}
        )

    async def _check_key(self, session: aiohttp.ClientSession, doc: dict):
        async with session.get(
            "https://gen.pollinations.ai/account/balance",
            headers={"Authorization": f"Bearer {doc['_id']}"}
        ) as response:
            data = await response.json()
            balance = float(data.get("balance", 0))
            await self.col.update_one(
                {"_id": doc["_id"]},
                {"$set": {"balance": balance}}
            )

    async def update_balances(self):
        docs = await self.col.find().to_list(None)
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*(self._check_key(session, doc) for doc in docs))

    async def balances(self) -> list[dict]:
        docs = await self.col.find().to_list(None)
        now = datetime.now(timezone.utc)
        return [
            {
                "key": doc["_id"],
                "balance": doc["balance"],
                "available": not doc["cooldown_until"] or doc["cooldown_until"].replace(tzinfo=timezone.utc) <= now,
                "cooldown_until": doc["cooldown_until"]
            }
            for doc in docs
        ]
    
    async def reset_cooldowns(self):
        result = await self.col.update_many({}, {"$set": {"cooldown_until": None}})
        return result.modified_count
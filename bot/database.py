from motor.motor_asyncio import AsyncIOMotorClient

from bot.config import MAX_GROUP_HISTORY_LENGTH
from typing import List, Dict


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.chat_db
collection = db.chat_history
group_collection = db.group_chat_history


async def get_all_users():
    cursor = collection.find()
    return cursor

async def save_group_message(group_id: int, username: str, role: str, content: str):
    message = {"role": role, "content": f'@{username}:\n{content}'}

    await group_collection.update_one(
        {"group_id": group_id},
        {"$push": {"history": message}},
        upsert=True
    )
    doc = await group_collection.find_one(
        {"group_id": group_id},
        {"history": 1}
    )
    
    if doc and "history" in doc and len(doc["history"]) > MAX_GROUP_HISTORY_LENGTH:
        await group_collection.update_one(
            {"group_id": group_id},
            {"$pop": {"history": -1}}
        )


async def get_group_history(group_id: int):
    doc = await group_collection.find_one({'group_id': group_id})
    if doc and "history" in doc:
        return doc["history"]
    return []


async def save_message(user_id: str, role: str, content: str):
    message = {"role": role, "content": content}

    await collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"history": message},
            "$setOnInsert": {"busy": False}
        },
        upsert=True
    )


async def get_history(user_id: str) -> List[Dict[str, str]]:
    doc = await collection.find_one({"user_id": user_id})
    if doc and "history" in doc:
        return doc["history"]
    return []


async def clear_history(user_id: str):
    await collection.update_one(
        {"user_id": user_id},
        {
            "$set": {"history": [], "busy": False}
        },
        upsert=True
    )


async def set_busy_state(user_id: str, is_busy: bool):
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"busy": is_busy}},
        upsert=True
    )


async def get_busy_state(user_id: str) -> bool:
    doc = await collection.find_one({"user_id": user_id}, {"busy": 1})
    return doc.get("busy", False) if doc else False

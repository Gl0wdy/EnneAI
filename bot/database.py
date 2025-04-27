from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict
from datetime import datetime, timezone


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.chat_db
collection = db.chat_history
group_collection = db.group_chat_history


async def get_all_users():
    cursor = collection.find()
    return cursor

async def save_group_message(group_id: int, username: str, role: str, content: str):
    message = {"role": role, "content": f'сообщение от @{username}:\n{content}'}
    await group_collection.update_one(
        {"group_id": group_id},
        {
            "$push": {"history": message}
        },
        upsert=True
    )
    await group_collection.update_one(
        {
            "group_id": group_id,
            "floodwait": {"$exists": False}
        },
        {
            "$set": {"floodwait": 10}
        }
    )
    await group_collection.update_one(
        {
            "group_id": group_id,
            "last_request": {"$exists": False}
        },
        {
            "$set": {"last_request": None}
        }
    )

    doc = await group_collection.find_one(
        {"group_id": group_id},
        {"history": 1}
    )
    if doc and "history" in doc:
        chat_history_length = len(doc["history"])
        while chat_history_length > 100:
            await group_collection.update_one(
                {"group_id": group_id},
                {"$pop": {"history": -1}}
            )
            chat_history_length -= 1


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
    doc = await group_collection.find_one(
        {"user_id": user_id},
        {"history": 1}
    )
    if doc and "history" in doc:
        chat_history_length = len(doc["history"])
        while chat_history_length > 80:
            await group_collection.update_one(
                {"user_id": user_id},
                {"$pop": {"history": -1}}
            )
            chat_history_length -= 1


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


async def set_floodwait(chat_id: int, value: int):
    await collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"floodwait": value}},
        upsert=True
    )

async def get_floodwait(chat_id: int):
    doc = await collection.find_one({"chat_id": chat_id}, {"floodwait": 1})
    return doc.get("floodwait", False) if doc else False


async def set_last_request(chat_id: int):
    now = datetime.now()
    await collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"last_request": now}},
        upsert=True
    )

async def get_last_request(chat_id: int):
    doc = await collection.find_one({"chat_id": chat_id}, {"last_request": 1})
    return doc.get("last_request", False) if doc else False
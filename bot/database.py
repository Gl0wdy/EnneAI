from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Literal, Optional
from datetime import datetime
from config import MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client.chat_db
collection = db.chat_history
group_collection = db.group_chat_history

HISTORY_LIMIT = 100


async def _trim_history(col, query: dict, limit: int = HISTORY_LIMIT):
    doc = await col.find_one(query, {"history": 1})
    if not doc or "history" not in doc:
        return
    excess = len(doc["history"]) - limit
    for _ in range(excess):
        await col.update_one(query, {"$pop": {"history": -1}})


async def get_all_users():
    return collection.find()


async def get_user(user_id: int) -> Optional[dict]:
    return await collection.find_one({"user_id": user_id})


async def delete(user_id: int):
    if user_id == 0:
        return
    await collection.delete_many({"user_id": user_id})


async def save_message(user_id: int, role: str, content: str, chunks: list = []):
    message = {"role": role, "content": content}
    if chunks:
        message["chunks"] = chunks

    await collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"history": message},
            "$setOnInsert": {
                "busy": False,
                "collection": "ennea",
                "premium": False,
                "tags": "",
                "long_memory": "",
            }
        },
        upsert=True
    )
    await _trim_history(collection, {"user_id": user_id})


async def get_history(user_id: int) -> List[Dict[str, str]]:
    doc = await collection.find_one({"user_id": user_id})
    if doc and "history" in doc:
        return doc["history"]
    return []


async def get_last_chunks(user_id: int) -> list:
    doc = await collection.find_one({"user_id": user_id}, {"history": 1})
    if not doc or "history" not in doc:
        return []
    for message in reversed(doc["history"]):
        if message.get("role") == "assistant" and "chunks" in message:
            return message["chunks"]
    return []


async def clear_history(user_id: int):
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"history": [], "busy": False, "tags": ""}},
        upsert=True
    )


async def get_group(group_id: int) -> Optional[dict]:
    return await group_collection.find_one({"group_id": group_id})


async def save_group_message(group_id: int, username: str, role: str, content: str):
    message = {"role": role, "content": f"сообщение от @{username}:\n{content}"}

    await group_collection.update_one(
        {"group_id": group_id},
        {
            "$push": {"history": message},
            "$setOnInsert": {
                "floodwait": 10,
                "last_request": None,
                "collection": "ennea",
            }
        },
        upsert=True
    )
    await _trim_history(group_collection, {"group_id": group_id})


async def get_group_history(group_id: int) -> List[Dict[str, str]]:
    doc = await group_collection.find_one({"group_id": group_id})
    if doc and "history" in doc:
        return doc["history"]
    return []


async def clear_group_history(group_id: int):
    await group_collection.update_one(
        {"group_id": group_id},
        {"$set": {"history": [], "last_request": None}},
        upsert=True
    )


async def set_busy_state(user_id: int, is_busy: bool):
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"busy": is_busy}},
        upsert=True
    )


async def get_busy_state(user_id: int) -> bool:
    doc = await collection.find_one({"user_id": user_id}, {"busy": 1})
    return doc.get("busy", False) if doc else False


async def set_floodwait(chat_id: int, value: int):
    await collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"floodwait": value}},
        upsert=True
    )


async def get_floodwait(chat_id: int) -> int:
    doc = await collection.find_one({"chat_id": chat_id}, {"floodwait": 1})
    return doc.get("floodwait", 0) if doc else 0


async def set_last_request(chat_id: int):
    await collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"last_request": datetime.now()}},
        upsert=True
    )


async def get_last_request(chat_id: int) -> Optional[datetime]:
    doc = await collection.find_one({"chat_id": chat_id}, {"last_request": 1})
    return doc.get("last_request") if doc else None


async def set_collection(user_id: int, new_collection: Literal["ennea", "socionics", "psychosophy", "jung", "ichazo"], group: bool = False):
    if group:
        await group_collection.update_one(
            {"group_id": user_id},
            {"$set": {"collection": new_collection}},
            upsert=True
        )
    else:
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"collection": new_collection}},
            upsert=True
        )


async def get_collection(user_id: int, group: bool = False) -> str:
    if group:
        doc = await group_collection.find_one({"group_id": user_id}, {"collection": 1})
        return doc.get("collection", "ennea") if doc else "ennea"
    doc = await collection.find_one({"user_id": user_id}, {"collection": 1})
    return doc.get("collection", "ennea") if doc else "ennea"


async def set_status(user_id: int, premium: bool = True, period=None):
    if period:
        end_date = datetime.now() + period
        user = await get_user(user_id)
        if user and (user_end_date := user.get("end_date")):
            if user_end_date > datetime.now():
                end_date += user_end_date - datetime.now()
    else:
        end_date = None

    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"premium": premium, "end_date": end_date}},
        upsert=True
    )


async def get_status(user_id: int) -> bool:
    doc = await collection.find_one({"user_id": user_id}, {"premium": 1, "end_date": 1})
    if not doc:
        return False
    end_date = doc.get("end_date")
    if end_date and datetime.now() > end_date:
        await set_status(user_id, False)
        return False
    return doc.get("premium", False)


async def set_tags(user_id: int, tags: str):
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"tags": tags}},
        upsert=True
    )


async def get_tags(user_id: int) -> str:
    doc = await collection.find_one({"user_id": user_id}, {"tags": 1})
    return doc.get("tags", "") if doc else ""


async def set_long_memory(user_id: int, data: str, group: bool = False):
    if group:
        await group_collection.update_one(
            {"group_id": user_id},
            {"$set": {"long_memory": data}},
            upsert=True
        )
    else:
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"long_memory": data}},
            upsert=True
        )


async def get_long_memory(user_id: int, group: bool = False) -> str:
    if group:
        doc = await group_collection.find_one({"group_id": user_id}, {"long_memory": 1})
    else:
        doc = await collection.find_one({"user_id": user_id}, {"long_memory": 1})
    return doc.get("long_memory", "") if doc else ""


async def set_last_review(user_id: int):
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_review": datetime.now()}}
    )


async def get_last_review(user_id: int) -> Optional[datetime]:
    doc = await collection.find_one({"user_id": user_id}, {"last_review": 1})
    return doc.get("last_review") if doc else None


async def inc_ref_count(user_id: int):
    await collection.update_one(
        {"user_id": user_id},
        {"$inc": {"ref_count": 1}},
        upsert=True
    )


chunks_collection = db.chunks


async def save_chunks(user_id: int, message_id: int, chunks: list):
    await chunks_collection.insert_one({
        "user_id": user_id,
        "message_id": message_id,
        "chunks": chunks,
        "created_at": datetime.now()
    })


async def get_chunks(message_id: int) -> list:
    doc = await chunks_collection.find_one({"message_id": message_id})
    return doc.get("chunks", []) if doc else []
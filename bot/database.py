from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Literal
from datetime import datetime


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.chat_db
collection = db.chat_history
group_collection = db.group_chat_history


async def get_all_users():
    cursor = collection.find()
    return cursor


async def get_user(user_id: int):
    doc = await collection.find_one(
        {'user_id': user_id}
    )
    return doc

async def get_group(group_id: int):
    doc = await group_collection.find_one(
        {'group_id': group_id}
    )
    return doc

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
    await group_collection.update_one(
        {
            "group_id": group_id,
            "collection": {"$exists": False}
        },
        {
            "$set": {"collection": "ennea"}
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


async def clear_group_history(group_id: str):
    await group_collection.update_one(
        {"group_id": group_id},
        {
            "$set": {"history": [], "last_request": None}
        },
        upsert=True
    )


async def save_message(user_id: str, role: str, content: str, premium: bool = False):
    message = {"role": role, "content": content}

    await collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"history": message},
            "$setOnInsert": {"busy": False}
        },
        upsert=True
    )
    await collection.update_one(
        {
            'user_id': user_id,
            'collection': {'$exists': False}
        },
        {
            '$set': {'collection': 'dynamic'}
        }
    )
    await collection.update_one(
        {
            'user_id': user_id,
            'premium': {'$exists': False}
        },
        {
            '$set': {'premium': False}
        }
    )
    doc = await group_collection.find_one(
        {"user_id": user_id},
        {"history": 1}
    )
    if doc and "history" in doc:
        chat_history_length = len(doc["history"])
        limit = 160 if premium else 80
        while chat_history_length > limit:
            await group_collection.update_one(
                {"user_id": user_id},
                {"$pop": {"history": -1}}
            )
            chat_history_length -= 1
    return doc


async def get_history(user_id: str) -> List[Dict[str, str]]:
    doc = await collection.find_one({"user_id": user_id})
    if doc and "history" in doc:
        return doc["history"]
    return []


async def clear_history(user_id: str):
    await collection.update_one(
        {"user_id": user_id},
        {
            "$set": {"history": [], "busy": False, "tags": ""}
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


async def set_collection(user_id: int, new_collection: Literal['ennea', 'socionics', 'psychosophy'], group: bool = False):
    if group:
        await group_collection.update_one(
            {'group_id': user_id},
            {'$set': {'collection': new_collection}}
        )
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"collection": new_collection}},
        upsert=True
    )

async def get_collection(user_id: int, group: bool = False):
    if group:
        doc = await group_collection.find_one({'group_id': user_id}, {'collection': 1})
        return doc.get("collection", "ennea") if doc else "ennea"
    else:
        doc = await collection.find_one({"user_id": user_id}, {"collection": 1})
        return doc.get("collection", "dynamic") if doc else "dynamic"


async def set_status(user_id: int, premium: bool = True, period = None):
    if period:
        end_date = datetime.now() + period
        user = await get_user(user_id)
        if (user_end_date := user.get('end_date')):
            user_days_left = user_end_date - datetime.now()
            end_date += user_days_left
    else:
        end_date = None
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"premium": premium, "end_date": end_date}},
        upsert=True
    )

async def get_status(user_id: int):
    doc = await collection.find_one({"user_id": user_id}, {"premium": 1, "end_date": 1})
    end_date = doc.get("end_date", None)
    if end_date and datetime.now() > end_date:
        await set_status(user_id, False)
        return False
    return doc.get("premium", False) if doc else False


async def set_tags(user_id: int, tags: str):
    await collection.update_one(
        {"user_id": user_id},
        {"$set": {"tags": tags}},
        upsert=True
    )

async def get_tags(user_id: int):
    doc = await collection.find_one({"user_id": user_id}, {"tags": 1})
    return doc.get("tags", '')


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

async def get_long_memory(user_id: int, group: bool = False):
    if group:
        doc = await group_collection.find_one({"group_id": user_id}, {"long_memory": 1})
    else:
        doc = await collection.find_one({"user_id": user_id}, {"long_memory": 1})
    return doc.get("long_memory", '')


async def inc_ref_count(user_id: int):
    await collection.update_one(
            {"user_id": user_id},
            {"$inc": {"ref_count": 1}},
            upsert=True
        )
    

async def delete(user_id: int):
    if user_id == 0:
        return
    collection.delete_many({'user_id': user_id})
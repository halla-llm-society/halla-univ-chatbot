from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from bson import ObjectId
import pymongo

from app.core.config import settings


def _preprocess_for_db(data: dict, collectionName: str) -> tuple[dict, str]:
    data = _add_date(data)
    collectionName = _add_suffix(collectionName)
    return data, collectionName


def _add_suffix(collectionName: str) -> str:
    return collectionName + settings.MONGODB_SUFFIX


def _add_date(data: dict) -> dict:
    utc_now = datetime.now(timezone.utc)
    return {"date": utc_now, **data}


async def save_to_mongodb(mongo_client: AsyncIOMotorDatabase, data: dict, collection_name: str):
    data, collection_name = _preprocess_for_db(data, collection_name)
    collection = mongo_client[collection_name]
    await collection.insert_one(data)


async def save_chat_and_return_id(mongo_client: AsyncIOMotorDatabase, data: dict, collection_name: str) -> ObjectId:
    data, collection_name = _preprocess_for_db(data, collection_name)
    collection = mongo_client[collection_name]

    result = await collection.insert_one(data)

    return result.inserted_id

async def get_chat_history(mongo_client: AsyncIOMotorDatabase, chat_id: str, limit: int = 6):
    if not chat_id: return []
    
    collection = mongo_client[_add_suffix("chat")]
    try:
        
        cursor = collection.find({"chatId": ObjectId(chat_id)}).sort("_id", -1).limit(limit)
        
        history = []
        async for doc in cursor:
            if "answer" in doc: history.append({"role": "assistant", "content": doc["answer"]})
            if "question" in doc: history.append({"role": "user", "content": doc["question"]})
        
        return history[::-1]
    except: return []

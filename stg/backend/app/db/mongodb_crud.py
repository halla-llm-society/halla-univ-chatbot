from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from bson import ObjectId
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


async def save_to_mongodb(db: AsyncIOMotorDatabase, data: dict, collection_name: str):
    data, collection_name = _preprocess_for_db(data, collection_name)
    collection = db[collection_name]
    await collection.insert_one(data)


async def save_chat_and_return_id(db: AsyncIOMotorDatabase, data: dict, collection_name: str) -> ObjectId:
    data, collection_name = _preprocess_for_db(data, collection_name)
    collection = db[collection_name]
    result = await collection.insert_one(data)

    return result.inserted_id

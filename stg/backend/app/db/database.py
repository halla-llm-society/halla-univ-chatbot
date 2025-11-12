import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from app.configure import STG_MONGODB_URI, MONGODB_SUFFIX


client = AsyncIOMotorClient(STG_MONGODB_URI)
db = client["halla-chatbot" + MONGODB_SUFFIX]


async def save_to_mongodb(data, collectionName):
    data, collectionName = preprocess_for_db(data, collectionName)
    collection = db[collectionName]
    await collection.insert_one(data)


async def save_chat_and_return_id(data, collectionName):    
    data, collectionName = preprocess_for_db(data, collectionName)
    collection = db[collectionName]
    result = await collection.insert_one(data)
    return result.inserted_id


def preprocess_for_db(data, collectionName):
    data = add_date(data)
    collectionName = add_suffix(collectionName)
    return data, collectionName


def add_date(data):
    utc_now = datetime.now(timezone.utc)
    data = {"date": utc_now, **data}
    return data


def add_suffix(collectionName):
    return collectionName + MONGODB_SUFFIX
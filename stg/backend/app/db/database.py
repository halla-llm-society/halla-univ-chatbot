from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os

load_dotenv()
MONGODB_URI = os.getenv("BACKEND_MONGODB_URI")

client = AsyncIOMotorClient(MONGODB_URI)
db = client["halla-chatbot-stg"]

def add_date(data):
    utc_now = datetime.now(timezone.utc)
    data = {"date": utc_now, **data}
    return data


async def save_to_mongodb(data, collectionName):
    data = add_date(data)
    collection = db[collectionName]
    await collection.insert_one(data)


async def save_chat_and_return_id(data, collectionName):    
    data = add_date(data)
    collection = db[collectionName]
    result = await collection.insert_one(data)
    return result.inserted_id
from dotenv import load_dotenv
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from ..schemas.survey_schemans import SurveyRequest
import os


load_dotenv()
MONGODB_URI = os.getenv("BACKEND_MONGODB_URI")

client = AsyncIOMotorClient(MONGODB_URI)
db = client["halla-chatbot-stg"]


async def save_survey(data):
    collection = db["stg-survey"]
    collection.insert_one(data)


async def save_chat(data):
    collection = db["stg-chat"]


async def save_token(data):
    collection = db["stg-token"]


async def save_meatadata(data):
    collection = db["stg-meatadata"]
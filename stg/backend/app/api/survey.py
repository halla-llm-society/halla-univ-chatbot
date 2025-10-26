from dotenv import load_dotenv
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from ..schemas.survey_schemans import SurveyRequest
import os

router = APIRouter()

load_dotenv()
MONGODB_URI = os.getenv("BACKEND_MONGODB_URI")

client = AsyncIOMotorClient(MONGODB_URI)
db = client["halla-chatbot-stg"]
collection = db["stg-survey"]

@router.post("/")
async def submit_survey(request: SurveyRequest):
    data = request.model_dump()

    kst = timezone(timedelta(hours=9))
    timestamp = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    data = {"timestamp": timestamp, **data}

    await collection.insert_one(data)

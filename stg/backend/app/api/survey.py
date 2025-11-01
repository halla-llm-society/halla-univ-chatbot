from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from ..schemas.survey_schemans import SurveyRequest
from ..db.database import save_to_mongodb

router = APIRouter()


@router.post("")
async def submit_survey(request: SurveyRequest):
    survey_data = request.model_dump()
    await save_to_mongodb(survey_data, "survey")
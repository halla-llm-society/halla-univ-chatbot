from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from app.schemas.survey_schema import SurveyRequest
from app.db.mongodb import get_mongo_db
from app.db.mongodb_crud import save_to_mongodb


router = APIRouter()
logger = logging.getLogger(__name__) 

@router.post("")
async def submit_survey(request: SurveyRequest, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    try:
        survey_data = request.model_dump()
        await save_to_mongodb(db, survey_data, "survey")

    except Exception as e:
        logger.error(f"Failed to save survey to MongoDB: {e}", exc_info=True)
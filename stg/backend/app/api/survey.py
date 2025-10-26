from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from ..schemas.survey_schemans import SurveyRequest
from ..db.database import save_survey

router = APIRouter()


@router.post("")
async def submit_survey(request: SurveyRequest):
    data = request.model_dump()

    utc_now = datetime.now(timezone.utc)
    data = {"date": utc_now, **data}

    await save_survey(data)
from fastapi import APIRouter
from app.api.chat import router as chat_router
from app.api.survey import router as survey_router

router = APIRouter()

router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(survey_router, prefix="/survey", tags=["Survey"])
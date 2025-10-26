from fastapi import APIRouter
from . import chat
from . import survey

router = APIRouter()

router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(survey.router, prefix="/survey", tags=["Survey"])
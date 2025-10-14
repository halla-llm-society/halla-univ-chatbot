from fastapi import APIRouter
from . import conversations, surveys, metrics

router = APIRouter()

router.include_router(
    conversations.router,
    prefix="/api",
    tags=["Conversations"]
)
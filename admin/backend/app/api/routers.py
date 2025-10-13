from fastapi import APIRouter
from . import conversations, surveys, metrics

routers = APIRouter()

routers.include_router(
    conversations.router,
    prefix="/api",
    tags=["Conversations"]
)
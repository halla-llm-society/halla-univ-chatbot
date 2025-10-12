from fastapi import APIRouter
from . import conversations, surveys, metrics

api_router = APIRouter()

api_router.include_router(conversations.router)
api_router.include_router(surveys.router)
api_router.include_router(metrics.router)

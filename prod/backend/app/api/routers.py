from fastapi import APIRouter
from . import chat

router = APIRouter()

router.include_router(
    chat.router,
    prefix="/api",
    tags=["Chat"]
)
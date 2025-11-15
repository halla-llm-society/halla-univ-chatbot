from fastapi import APIRouter
from . import conversations, surveys, metrics
from . import user_query

router = APIRouter()

router.include_router(
    conversations.router,
    prefix="/api",
    tags=["Conversations"]
)

router.include_router(
    user_query.router,
    prefix="/api",  # /api/user-query-data 경로로 API가 노출됩니다.
    tags=["UserQuery"]
)
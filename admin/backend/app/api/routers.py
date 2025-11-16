from fastapi import APIRouter, Depends
from . import conversations, surveys, metrics
from app.core.security import get_current_admin

from . import user_query
from . import surveys
from . import stats
from . import metrics
from . import database

router = APIRouter()

router.include_router(
    conversations.router,
    prefix="/api",
    tags=["Conversations"],
    dependencies=[Depends(get_current_admin)]
)

router.include_router(
    user_query.router,
    prefix="/api",
    tags=["UserQuery"],
    dependencies=[Depends(get_current_admin)]
)

router.include_router(
    surveys.router,
    prefix="/api",
    tags=["Surveys"],
    dependencies=[Depends(get_current_admin)]
)

router.include_router(
    stats.router,
    prefix="/api",
    tags=["Stats"],
    dependencies=[Depends(get_current_admin)]
)

router.include_router(
    metrics.router,
    prefix="/api",
    tags=["Metrics"],
    dependencies=[Depends(get_current_admin)]
)

router.include_router(
    database.router,
    prefix="/api",
    tags=["Database"],
    dependencies=[Depends(get_current_admin)]
)
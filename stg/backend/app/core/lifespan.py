from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.mongodb import init_mongo_client, close_mongo_client
from app.db.redis import init_redis_client, close_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 실행
    await init_mongo_client(app)
    await init_redis_client(app)
    
    yield
    
    # 앱 종료
    await close_mongo_client(app)
    await close_redis_client(app)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.mongodb import init_mongo_client, close_mongo_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 실행
    await init_mongo_client(app)
    
    yield
    
    # 앱 종료
    await close_mongo_client(app)
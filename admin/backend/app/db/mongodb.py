from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import HTTPException, status, Request, FastAPI
import logging
from app.core.config import settings


logger = logging.getLogger(__name__)
STG_DB_NAME = "halla-chatbot-stg"

# MongoDB 커넥션 풀 초기화
async def init_mongo_client(app: FastAPI):
    try:
        # MongoDB 클라이언트 생성
        app.state.mongo_client = AsyncIOMotorClient( 
            settings.STG_MONGODB_URI,
            serverSelectionTimeoutMS=5000,  
            maxPoolSize=10, 
            minPoolSize=5
        )
        
        # 연결 테스트
        await app.state.mongo_client.admin.command('ping')
        app.state.mongo_db = app.state.mongo_client[STG_DB_NAME]
        logger.info(f"MongoDB connected. Database: {STG_DB_NAME}")
        
    except Exception as e:
        logger.error(f"Failed to connect MongoDB: {e}", exc_info=True)
        app.state.mongo_client = None
        app.state.mongo_db = None   


# MongoDB 커넥션 풀 닫기
async def close_mongo_client(app: FastAPI):
    if app.state.mongo_client:
        app.state.mongo_client.close()


# MongoDB 객체 가져오기
async def get_mongo_db(request: Request) -> AsyncIOMotorDatabase:
    if not hasattr(request.app.state, 'mongo_db') or request.app.state.mongo_db is None: 
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to get MongoDB connection"
        )

    return request.app.state.mongo_db 
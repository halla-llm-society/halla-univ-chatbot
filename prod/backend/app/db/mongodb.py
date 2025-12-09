from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import HTTPException, status, Request, FastAPI
import logging
from app.core.config import settings


logger = logging.getLogger(__name__)

# MongoDB 인덱스 생성
async def init_indexes(app: FastAPI):
    if app.state.mongo_db is None: 
        return
    try:
        db_suffix = settings.MONGODB_SUFFIX
        # chatId 필드에 인덱스 생성 (조회 속도 보장)
        await app.state.mongo_db[f"chat{db_suffix}"].create_index([("chatId", 1)], background=True)
        await app.state.mongo_db[f"token{db_suffix}"].create_index([("chatId", 1)], background=True)
        await app.state.mongo_db[f"metadata{db_suffix}"].create_index([("chatId", 1)], background=True)
        logger.info("MongoDB Indexes created.")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")


# MongoDB 커넥션 풀 초기화
async def init_mongo_client(app: FastAPI):
    try:
        # MongoDB 클라이언트 생성
        app.state.mongo_client = AsyncIOMotorClient( 
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=10000,  
            maxPoolSize=10, 
            minPoolSize=5
            
        )
        
        # 연결 테스트
        await app.state.mongo_client.admin.command('ping') 
        
        # DB 이름 동적 생성
        db_name = "halla-chatbot" + settings.MONGODB_SUFFIX
        app.state.mongo_db = app.state.mongo_client[db_name]

        #인덱스 생성 호출
        await init_indexes(app)
        
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
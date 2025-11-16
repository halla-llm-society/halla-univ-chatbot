from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from fastapi import HTTPException, status, Request, FastAPI, Depends
import logging
import certifi

from app.core.config import settings

logger = logging.getLogger(__name__)

# MongoDB 커넥션 풀 초기화
async def init_mongo_client(app: FastAPI):
    try:
        # STG MongoDB 클라이언트 생성
        app.state.stg_mongo_client = AsyncIOMotorClient( 
            settings.STG_MONGODB_URI,
            serverSelectionTimeoutMS=5000,  
            maxPoolSize=10, 
            minPoolSize=5,
            tlsCAFile=certifi.where()
        )
        # STG 연결 테스트
        await app.state.stg_mongo_client.admin.command('ping')
        app.state.stg_db = app.state.stg_mongo_client[settings.STG_DB_NAME]
        logger.info(f"STG MongoDB connected. Database: {settings.STG_DB_NAME}")
        
        # ================================================================== # 
        
        # PROD MongoDB 클라이언트 생성
        app.state.prod_mongo_client = AsyncIOMotorClient( 
            settings.PROD_MONGODB_URI,
            serverSelectionTimeoutMS=5000,  
            maxPoolSize=10, 
            minPoolSize=5,
            tlsCAFile=certifi.where()
        )
        # PROD 연결 테스트
        await app.state.prod_mongo_client.admin.command('ping')
        app.state.prod_db = app.state.prod_mongo_client[settings.PROD_DB_NAME]
        logger.info(f"PROD MongoDB connected. Database: {settings.PROD_DB_NAME}")
        
        # 기본 DB 환경을 'stg'로 설정
        app.state.current_db_env = "prod"
        
    except Exception as e:
        logger.error(f"Failed to connect MongoDB: {e}", exc_info=True)
        app.state.stg_mongo_client = None
        app.state.stg_db = None
        app.state.prod_mongo_client = None
        app.state.prod_db = None   


# MongoDB 커넥션 풀 닫기
async def close_mongo_client(app: FastAPI):
    if hasattr(app.state, 'stg_mongo_client') and app.state.stg_mongo_client:
        app.state.stg_mongo_client.close()
    if hasattr(app.state, 'prod_mongo_client') and app.state.prod_mongo_client:
        app.state.prod_mongo_client.close()


# MongoDB 객체 가져오기
async def get_mongo_db(request: Request) -> AsyncIOMotorDatabase:
    # 현재 설정된 DB 환경('stg' 또는 'prod')을 확인
    env = getattr(request.app.state, 'current_db_env', 'stg') 

    db_instance = None
    if env == "stg":
        db_instance = getattr(request.app.state, 'stg_db', None)
    elif env == "prod":
        db_instance = getattr(request.app.state, 'prod_db', None)

    if db_instance is None:
        logger.error(f"Failed to get MongoDB connection for env: {env}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get MongoDB connection for {env}"
        )

    return db_instance

def get_collection(logical_base_name: str) -> callable:
    """
    FastAPI 의존성 주입 팩토리.
    현재 app.state.current_db_env ('stg'/'prod')에 따라
    올바른 DB의 올바른 컬렉션(예: 'chat-stg' or 'chat-prod')을 반환합니다.
    
    Args:
        logical_base_name (str): DB 이름의 기본 파트 (예: "chat", "metadata", "survey")
    """
    async def get_collection_dependency(
        request: Request,
        db: AsyncIOMotorDatabase = Depends(get_mongo_db) # 3번 함수에 의존
    ) -> AsyncIOMotorCollection:
        
        # 1. 현재 환경 상태 확인 ('stg' 또는 'prod')
        env = getattr(request.app.state, 'current_db_env', 'stg')
        
        # 2. 환경 접미사 결정 ('-stg' 또는 '-prod')
        env_suffix = "-prod" if env == "prod" else "-stg"
        
        # 3. 컬렉션 이름 조합 (예: "chat" + "-stg" -> "chat-stg")
        collection_name = f"{logical_base_name}{env_suffix}"
        
        # 4. 올바른 DB에서(db) 올바른 컬렉션(collection_name)을 반환
        return db[collection_name]

    return get_collection_dependency

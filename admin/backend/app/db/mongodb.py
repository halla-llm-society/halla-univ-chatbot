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
        
        # 기본 DB 환경을 'prod'로 설정
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
    # 헤더에서 환경 정보를 읽어옵니다. (기본값은 'prod' 으로 설정)
    env_header = request.headers.get("x-db-env", "prod").lower()
    
    # 유효성 검사 (stg, prod 외에는 기본값 처리 혹은 에러)
    env = "stg" if env_header == "stg" else "prod"

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
    async def get_collection_dependency(
        request: Request,
        db: AsyncIOMotorDatabase = Depends(get_mongo_db)
    ) -> AsyncIOMotorCollection:
        
        # 1. 헤더에서 환경 정보 확인 (get_mongo_db와 동일한 로직)
        env_header = request.headers.get("x-db-env", "prod").lower()
        env = "stg" if env_header == "stg" else "prod"
        
        # 2. 환경 접미사 결정
        env_suffix = "-prod" if env == "prod" else "-stg"
        
        # 3. 컬렉션 이름 조합
        collection_name = f"{logical_base_name}{env_suffix}"
        
        # 4. 올바른 DB에서(db) 올바른 컬렉션(collection_name)을 반환
        return db[collection_name]

    return get_collection_dependency

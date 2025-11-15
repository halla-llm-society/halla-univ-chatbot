import redis.asyncio as redis
from fastapi import HTTPException, status, Request, FastAPI
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


# Redis 커넥션 풀 초기화
async def init_redis_client(app: FastAPI):
    try:
        # redis 클라이언트 생성
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"

        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10,
            max_connections=10
        )

        # 연결 테스트
        await client.ping()
        
        # redis 클라이언트 저장
        app.state.redis_client = client

        # 키 초기화
        await client.setnx("global:monthly_cost_total", 0)
        await client.setnx("global:cost_tracking_month", 11)

    except Exception as e:
        logger.error(f"Failed to connect Redis: {e}", exc_info=True)
        app.state.redis_client = None


# Redis 커넥션 풀 닫기
async def close_redis_client(app: FastAPI):
    if app.state.redis_client:
        await app.state.redis_client.close()


# Redis 객체 가져오기
async def get_redis_client(request: Request) -> redis.Redis:
    if not hasattr(request.app.state, 'redis_client') or request.app.state.redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to get Redis connection"
        )
    
    return request.app.state.redis_client
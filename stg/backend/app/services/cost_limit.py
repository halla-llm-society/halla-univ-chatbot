import redis.asyncio as redis
from fastapi import HTTPException, status
from datetime import datetime, timezone
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

COST_TOTAL_KEY = "global:monthly_cost_total"
TRACKING_MONTH_KEY = "global:cost_tracking_month"
MONTHLY_LIMIT_USD = settings.MONTHLY_COST_LIMIT 


# 비용 한도 확인
async def check_cost_limit(redis_client: redis.Redis):
    try:
        await reset_month(redis_client)

        current_cost_str = await redis_client.get(COST_TOTAL_KEY)
        current_cost = float(current_cost_str or 0.0)
        
        logger.info(f"Current cost: ${current_cost}")
        
        if current_cost >= MONTHLY_LIMIT_USD:
            logger.warning(f"Request blocked due to exceeding monthly cost limit (${MONTHLY_LIMIT_USD}). (Current: ${current_cost})")
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
            
    except redis.RedisError as e:
        logger.error(f"Failed to check cost limit: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


# 월 초기화 함수
async def reset_month(redis_client: redis.Redis):
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    tracking_month = await redis_client.get(TRACKING_MONTH_KEY)

    logger.info(f"Current month: ${current_month}, Tracking month: {tracking_month}")

    if tracking_month != current_month:
        logger.info(f"Reset month {tracking_month} to {current_month}")

        async with redis_client.pipeline() as pipe:
            pipe.set(COST_TOTAL_KEY, 0) 
            pipe.set(TRACKING_MONTH_KEY, current_month) 
            await pipe.execute()


# 비용 누적 함수
async def increment_global_cost(redis_client: redis.Redis, cost_usd: float):
    try:
        await redis_client.incrbyfloat(COST_TOTAL_KEY, cost_usd)
    
    except Exception as e:
        logger.error(f"Failed to increase cost: {e}", exc_info=True)
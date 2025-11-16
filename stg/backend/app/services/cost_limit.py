import redis.asyncio as redis
from fastapi import HTTPException, status
from datetime import datetime, timezone
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

MONTHLY_TOTAL_COST_KEY = "global:monthly_total_cost"
TRACKING_MONTH_KEY = "global:cost_tracking_month"
MONTHLY_LIMIT_USD = settings.MONTHLY_COST_LIMIT 


# total cost 확인
async def get_monthly_total_cost(redis_client: redis.Redis) -> float:
    monthly_total_cost_str = await redis_client.get(MONTHLY_TOTAL_COST_KEY)
    monthly_total_cost = float(monthly_total_cost_str or 0.0)
    return monthly_total_cost


# 비용 한도 확인
async def check_cost_limit(redis_client: redis.Redis):
    try:
        await reset_month(redis_client)

        monthly_total_cost = await get_monthly_total_cost(redis_client)
        
        if monthly_total_cost >= MONTHLY_LIMIT_USD:
            logger.warning(f"Request blocked due to exceeding monthly cost limit (${MONTHLY_LIMIT_USD}). (Total: ${monthly_total_cost})")
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
            
    except redis.RedisError as e:
        logger.error(f"Failed to check cost limit: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


# 월 초기화 함수
async def reset_month(redis_client: redis.Redis):
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    tracking_month = await redis_client.get(TRACKING_MONTH_KEY)

    if tracking_month != current_month:
        logger.info(f"Reset month {tracking_month} to {current_month}")

        async with redis_client.pipeline() as pipe:
            pipe.set(MONTHLY_TOTAL_COST_KEY, 0) 
            pipe.set(TRACKING_MONTH_KEY, current_month) 
            await pipe.execute()


# 비용 누적 함수
async def increment_monthly_total_cost(redis_client: redis.Redis, cost_usd: float):
    if cost_usd < 0:
        raise ValueError("cost_usd must be non-negative")

    try:
        await redis_client.incrbyfloat(MONTHLY_TOTAL_COST_KEY, cost_usd)
        monthly_total_cost = await get_monthly_total_cost(redis_client)

        logger.info(f"Current cost: ${cost_usd}, Total cost: ${monthly_total_cost}")
    
    except Exception as e:
        logger.error(f"Failed to increase cost: {e}", exc_info=True)
import httpx
import redis.asyncio as redis
from fastapi import HTTPException, status
from datetime import datetime, timezone
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

MONTHLY_TOTAL_COST_KEY = "global:monthly_total_cost"
TRACKING_MONTH_KEY = "global:cost_tracking_month"
# COST_WARNING_SENT_KEY = "global:monthly_cost_warning_sent"

MONTHLY_LIMIT_USD = settings.MONTHLY_COST_LIMIT 
MONTHLY_WARNING_THRESHOLD = settings.MONTHLY_WARNING_THRESHOLD


# total cost 확인
async def get_monthly_total_cost(redis_client: redis.Redis) -> float:
    monthly_total_cost_str = await redis_client.get(MONTHLY_TOTAL_COST_KEY)
    monthly_total_cost = float(monthly_total_cost_str or 0.0)
    return monthly_total_cost


# 경고 메시지 전송
async def send_cost_warning(redis_client: redis.Redis, monthly_total_cost: float):
    # 이번 달에 경고를 보낸 경우, 더 이상 보내지 않음
    # warning_sent = await redis_client.get(COST_WARNING_SENT_KEY)

    # if warning_sent == "true":
    #     return  

    try:
        webhook_url = settings.DISCORD_WEBHOOK_URL

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                webhook_url,
                json={
                    "content": (
                        f"이번 달 API 사용 비용이 ${monthly_total_cost:.2f} "
                        f"를 초과했습니다. (한도: ${MONTHLY_LIMIT_USD:.2f})"
                    )
                },
            )
    except Exception as e:
        logger.error(f"Failed to send cost warning to Discord: {e}", exc_info=True)
        return

    # await redis_client.set(COST_WARNING_SENT_KEY, "true")


# 비용 한도 확인
async def check_cost_limit(redis_client: redis.Redis):
    try:
        await reset_month(redis_client)

        monthly_total_cost = await get_monthly_total_cost(redis_client)

        # 90% 이상 사용
        if monthly_total_cost >= MONTHLY_WARNING_THRESHOLD:
            await send_cost_warning(redis_client, monthly_total_cost)
        
        # 100% 이상 사용
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
            # pipe.set(COST_WARNING_SENT_KEY, "false")
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
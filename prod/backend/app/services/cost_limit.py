import httpx
from fastapi import HTTPException, status
from datetime import datetime, timezone
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


MONTHLY_LIMIT_USD = settings.MONTHLY_COST_LIMIT 
MONTHLY_WARNING_THRESHOLD = MONTHLY_LIMIT_USD * 0.9

OPENAI_ADMIN_KEY = settings.OPENAI_ADMIN_KEY
OPENAI_PROJECT_ID = settings.OPENAI_PROJECT_ID
COSTS_API_URL = settings.COSTS_API_URL


# 비용 한도 확인
async def check_cost_limit():
    monthly_total_cost = await get_monthly_total_cost()
    logger.info(f"Monthly Total Cost = (${monthly_total_cost}), Monthly Limit = ${MONTHLY_LIMIT_USD})")

    # 90% 이상 사용 (90% ~ (90% + $1) 사이에만 메시지 전송)
    if (MONTHLY_WARNING_THRESHOLD <= monthly_total_cost) and (monthly_total_cost <= MONTHLY_WARNING_THRESHOLD + 1):
        await send_cost_warning(monthly_total_cost)
        return
    
    # 100% 이상 사용
    if monthly_total_cost >= MONTHLY_LIMIT_USD:
        logger.warning(f"Request blocked due to exceeding monthly cost limit (${MONTHLY_LIMIT_USD}). (Total: ${monthly_total_cost})")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)


# total cost 확인
async def get_monthly_total_cost() -> float:
    now = datetime.now(timezone.utc)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    start_time = int(start_of_month.timestamp())
    end_time = int(now.timestamp())

    headers = {
        "Authorization": f"Bearer {OPENAI_ADMIN_KEY}",
        "Content-Type": "application/json",
    }

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "bucket_width": "1d",
        "limit": 31,
        "project_ids": [OPENAI_PROJECT_ID],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(COSTS_API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    total_cost = 0.0

    for bucket in data.get("data", []):
        for result in bucket.get("results", []):
            amount = result.get("amount", {}).get("value")

            if amount is not None:
                total_cost += float(amount)

    return total_cost


# 경고 메시지 전송
async def send_cost_warning(monthly_total_cost: float):
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
from fastapi import APIRouter, Depends, Query, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.db.mongodb import get_mongo_db, get_collection
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta, time
from enum import Enum
import asyncio # 3개의 DB 집계를 동시에 실행하기 위함

router = APIRouter()
logger = logging.getLogger(__name__)

# --- 1. 기간(Period) 필터 Enum ---
class Period(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

# --- 2. Pydantic 응답 모델 정의 ---

# 차트 데이터 포인트 (time: 라벨, value: 값)
# UsageCostInquiry.jsx의 ChartComponent는 'value'를 props로 받음
class CostPoint(BaseModel):
    time: str
    value: float # 프론트엔드에서 'value'를 사용

# LLM, Server, DB 각각의 데이터
class PeriodCostData(BaseModel):
    total: float
    points: List[CostPoint]

# 기간별 비용 묶음
class PeriodCosts(BaseModel):
    llm: PeriodCostData
    server: PeriodCostData
    db: PeriodCostData

# 월 예상 비용
class EstimatedMonthlyCost(BaseModel):
    total: float
    points: List[CostPoint]

# cost.js의 getCosts가 기대하는 최종 응답 형태
class CostsResponse(BaseModel):
    grandTotal: float
    periodCosts: PeriodCosts
    estimatedMonthlyCost: EstimatedMonthlyCost


# --- 3. 날짜 처리 헬퍼 함수 (year 제외) ---
def get_date_range_and_group(period: Period) -> (datetime, datetime, str, str):
    """
    기간(period)에 따라 MongoDB 집계에 필요한
    시작/종료 날짜, 그룹 포맷, 라벨 포맷을 반환합니다.
    """
    now = datetime.now() 
    
    if period == Period.DAY:
        start_date = now - timedelta(days=1)
        group_format = "%Y-%m-%dT%H:00" 
        label_format = "%H시"
    elif period == Period.WEEK:
        start_date = now - timedelta(days=7)
        start_date = datetime.combine(start_date.date(), time.min)
        group_format = "%Y-%m-%d"
        label_format = "%m-%d"
    elif period == Period.MONTH:
        start_date = now - timedelta(days=30)
        start_date = datetime.combine(start_date.date(), time.min)
        group_format = "%Y-%m-%d"
        label_format = "%m-%d"

    return start_date, now, group_format, label_format


# --- 4. API 엔드포인트: /api/costs ---

get_metadata_collection = get_collection("metadata")

@router.get(
    "/costs", # cost.js가 호출하는 엔드포인트
    response_model=CostsResponse,
    summary="[비용] 기간별 모든 비용 데이터 (UsageCostInquiry용)"
)
async def get_costs_endpoint(
    collection: AsyncIOMotorCollection = Depends(get_metadata_collection),
    period: Period = Query(..., description="조회 기간 (day, week, month)")
):
    """
    프론트의 '사용비용 조회' 페이지가 요청하는 모든 데이터를 반환합니다.
    - DB 컬렉션: `meta-stg`
    - 집계: `metadata.token_usage.total_cost_usd` (LLM 비용)
    - 참고: 서버/DB 비용은 meta-stg에 없으므로 0으로 반환합니다.
    """
    try:
        start_date, end_date, group_format, label_format = get_date_range_and_group(period)
        
        # *** 집계할 필드 경로 ***
        COST_FIELD = "metadata.token_usage.total_cost_usd"

        # 1. 기간별(Period) 데이터 집계 (LLM 비용)
        pipeline_period = [
            {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
            {
                "$group": {
                    "_id": {"$dateToString": {
                        "format": group_format, 
                        "date": "$date", 
                        "timezone": "Asia/Seoul"
                    }},
                    "cost": {"$sum": f"${COST_FIELD}"}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        # 2. 전체(Grand Total) 비용 집계
        year_ago = datetime.now() - timedelta(days=365)
        pipeline_grand_total = [
            {"$match": {"date": {"$gte": year_ago}}},
            {"$group": {"_id": None, "totalCost": {"$sum": f"${COST_FIELD}"}}}
        ]
        
        # 3. 주간(Weekly) 비용 집계 (월 예상 비용 계산용)
        week_ago = datetime.now() - timedelta(days=7)
        pipeline_weekly = [
            {"$match": {"date": {"$gte": week_ago}}},
            {"$group": {"_id": None, "weeklyCost": {"$sum": f"${COST_FIELD}"}}}
        ]

        # 4. 3개 집계 동시 실행
        (period_result, grand_total_result, weekly_result) = await asyncio.gather(
            collection.aggregate(pipeline_period).to_list(length=None),
            collection.aggregate(pipeline_grand_total).to_list(length=1),
            collection.aggregate(pipeline_weekly).to_list(length=1)
        )

        # 5-1. grandTotal 계산
        grand_total = grand_total_result[0].get("totalCost", 0) if grand_total_result else 0

        # 5-2. periodCosts (LLM) 계산
        llm_points = []
        llm_total = 0
        for item in period_result:
            if not item.get("_id"): continue
            try:
                if period == Period.DAY:
                    time_obj = datetime.strptime(item["_id"], "%Y-%m-%dT%H:00")
                else: # week, month
                    time_obj = datetime.strptime(item["_id"], "%Y-%m-%d")
                time_label = time_obj.strftime(label_format)
            except ValueError:
                time_label = item["_id"]
            
            cost = item.get("cost", 0)
            llm_total += cost
            llm_points.append(CostPoint(time=time_label, value=cost)) # 'value' 사용

        # 5-3. Server, DB 비용 (데이터 없으므로 0)
        empty_period_data = PeriodCostData(total=0, points=[])

        # 5-4. estimatedMonthlyCost (월 예상 비용) 계산
        # cost.js의 로직(주간*4)
        weekly_total = weekly_result[0].get("weeklyCost", 0) if weekly_result else 0
        estimated_total = weekly_total * 4
        
        # 4주치 포인트 생성
        estimated_points = [
            CostPoint(time='1주차', value=estimated_total * 0.25),
            CostPoint(time='2주차', value=estimated_total * 0.5),
            CostPoint(time='3주차', value=estimated_total * 0.75),
            CostPoint(time='4주차', value=estimated_total * 1.0),
        ]

        # 6. 최종 응답 조립
        return CostsResponse(
            grandTotal=grand_total,
            periodCosts=PeriodCosts(
                llm=PeriodCostData(total=llm_total, points=llm_points),
                server=empty_period_data,
                db=empty_period_data
            ),
            estimatedMonthlyCost=EstimatedMonthlyCost(
                total=estimated_total,
                points=estimated_points
            )
        )

    except Exception as e:
        logger.error(f"Error fetching cost data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
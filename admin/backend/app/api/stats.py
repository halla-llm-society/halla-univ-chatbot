from fastapi import APIRouter, Depends, Query, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import get_mongo_db
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta, time
from enum import Enum

router = APIRouter()
logger = logging.getLogger(__name__)

# --- 1. 프론트엔드에서 사용하는 기간(Period) 필터 ---
class Period(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

# --- 2. 프론트엔드 응답 모델 정의 ---
# TrafficInquiry.jsx의 ChartComponent가 기대하는 "points" 형태
class TrafficPoint(BaseModel):
    time: str       # 차트 라벨 (예: "15시", "11-16")
    count: int = 0  # "질문 수" 차트용
    usage: int = 0  # "사용 토큰량" 차트용

# TrafficInquiry.jsx가 API로부터 기대하는 최종 응답 형태
class TrafficResponse(BaseModel):
    total: int
    points: List[TrafficPoint]


# --- 3. 날짜 처리 헬퍼 함수 ---
def get_date_range_and_group(period: Period) -> (datetime, datetime, str, str):
    """
    기간(period)에 따라 MongoDB 집계에 필요한
    시작/종료 날짜, 그룹 포맷, 라벨 포맷을 반환합니다.
    (시간대는 한국 "Asia/Seoul" 기준)
    """
    # KST (UTC+9)
    # 참고: FastAPI/Motor는 datetime 객체를 UTC로 자동 변환하여 DB에 쿼리합니다.
    now = datetime.now() 
    
    if period == Period.DAY:
        # 1일: 지난 24시간, 시간별
        start_date = now - timedelta(days=1)
        # MongoDB 그룹 포맷 (시간까지)
        group_format = "%Y-%m-%dT%H:00" 
        # 프론트 라벨 포맷 (예: "14시")
        label_format = "%H시"
    
    elif period == Period.WEEK:
        # 1주: 지난 7일, 일별
        start_date = now - timedelta(days=7)
        start_date = datetime.combine(start_date.date(), time.min) # 7일 전 00:00
        group_format = "%Y-%m-%d"
        label_format = "%m-%d" # 예: "11-16"

    elif period == Period.MONTH:
        # 1개월: 지난 30일, 일별
        start_date = now - timedelta(days=30)
        start_date = datetime.combine(start_date.date(), time.min) # 30일 전 00:00
        group_format = "%Y-%m-%d"
        label_format = "%m-%d" # 예: "10-17"

    elif period == Period.YEAR:
        # 1년: 지난 12개월, 월별
        start_date = now - timedelta(days=365)
        start_date = datetime.combine(start_date.date().replace(day=1), time.min) # 1년 전 1일 00:00
        group_format = "%Y-%m"
        label_format = "%Y-%m" # 예: "2024-11"

    return start_date, now, group_format, label_format


# --- 4. 범용 집계 함수 ---
async def _get_traffic_data(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    period: Period,
    field_to_sum: str | None = None # None이면 개수(count), 필드명이면 합계(sum)
) -> TrafficResponse:
    
    try:
        start_date, end_date, group_format, label_format = get_date_range_and_group(period)
        
        # 합계할 대상: 1 (문서 개수) 또는 $필드명 (필드 값)
        aggregator = {"$sum": 1} if field_to_sum is None else {"$sum": f"${field_to_sum}"}
        # 프론트 모델 필드명: "count" 또는 "usage"
        point_field_name = "count" if field_to_sum is None else "usage"

        pipeline = [
            # 1. 날짜 범위 필터링 (DB의 'date' 필드 사용)
            {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
            
            # 2. $facet으로 'total'과 'points'를 한 번에 계산
            {
                "$facet": {
                    # 2-1. 전체 합계/개수
                    "total": [
                        {"$group": {"_id": None, "total": aggregator}}
                    ],
                    # 2-2. 시간대별 합계/개수
                    "points": [
                        {
                            "$group": {
                                "_id": {"$dateToString": {
                                    "format": group_format, 
                                    "date": "$date", 
                                    "timezone": "Asia/Seoul" # KST 기준 그룹화
                                }},
                                point_field_name: aggregator
                            }
                        },
                        {"$sort": {"_id": 1}} # 시간순 정렬
                    ]
                }
            }
        ]
        
        collection = db[collection_name]
        cursor = collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        # 3. 결과 포맷팅
        if not result or not result[0]:
            return TrafficResponse(total=0, points=[]) # 데이터 없음

        data = result[0]
        
        # 'total' 값 추출 (결과가 없으면 0)
        total = data.get("total", [{}])[0].get("total", 0) if data.get("total") else 0
        
        # 'points' 값 추출 및 라벨 포맷팅
        points_data = data.get("points", [])
        points = []
        for item in points_data:
            if not item.get("_id"): continue # 날짜가 없는 데이터 스킵

            try:
                # MongoDB에서 온 날짜 문자열(_id)을 datetime 객체로 변환
                if period == Period.DAY:
                    time_obj = datetime.strptime(item["_id"], "%Y-%m-%dT%H:00")
                elif period == Period.YEAR:
                    time_obj = datetime.strptime(item["_id"], "%Y-%m")
                else: # week, month
                    time_obj = datetime.strptime(item["_id"], "%Y-%m-%d")
                
                # 프론트엔드가 원하는 라벨 포맷으로 변환
                time_label = time_obj.strftime(label_format)

            except ValueError:
                time_label = item["_id"] # 파싱 실패 시 원본 사용

            # TrafficPoint 모델에 맞게 데이터 추가
            point_data = {"time": time_label}
            if field_to_sum is None:
                point_data["count"] = item["count"]
            else:
                point_data["usage"] = item[point_field_name]
            
            points.append(TrafficPoint(**point_data))

        return TrafficResponse(total=total, points=points)

    except Exception as e:
        logger.error(f"Error fetching traffic data ({collection_name}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}"
        )

# --- 5. API 엔드포인트 정의 ---

@router.get(
    "/traffic/queries", 
    response_model=TrafficResponse,
    summary="[트래픽] 기간별 질문 수"
)
async def get_traffic_queries_endpoint(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    period: Period = Query(..., description="조회 기간 (day, week, month, year)")
):
    """
    프론트의 '질문 수' 차트 데이터를 반환합니다.
    - DB 컬렉션: `chat-stg` (사용자 요청)
    - 집계: 문서 개수 (count)
    """
    return await _get_traffic_data(
        db=db,
        collection_name="chat-stg", # 1. *** 질문 수(chat-stg) 컬렉션 ***
        period=period,
        field_to_sum=None # None은 문서 개수(count)를 의미
    )


@router.get(
    "/traffic/tokens", 
    response_model=TrafficResponse,
    summary="[트래픽] 기간별 토큰 사용량"
)
async def get_traffic_tokens_endpoint(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    period: Period = Query(..., description="조회 기간 (day, week, month, year)")
):
    """
    프론트의 '사용 토큰량' 차트 데이터를 반환합니다.
    - DB 컬렉션: `metadata-stg` (사용자 요청)
    - 집계: `metadata.token_usage.total_tokens` 필드의 합계
    """
    return await _get_traffic_data(
        db=db,
        collection_name="metadata-stg", # 2. *** 토큰(metadata-stg) 컬렉션 ***
        period=period,
        field_to_sum="metadata.token_usage.total_tokens" # 3. *** 토큰 필드 경로 ***
    )
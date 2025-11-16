from fastapi import APIRouter, Depends, Query, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.db.mongodb import get_mongo_db, get_collection
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# "만족도 점수 분포"용 (1점~5점)
class RatingDistribution(BaseModel):
    labels: List[str] = ["1점", "2점", "3점", "4점", "5점"]
    counts: List[int] = [0, 0, 0, 0, 0]

# "응답 속도/품질 분포"용 (high, medium, low)
class CategoryDistribution(BaseModel):
    labels: List[str]
    counts: List[int]

# "코멘트" 테이블용
class FeedbackEntry(BaseModel):
    id: str
    rating: int
    feedback: str # 프론트에서 item.feedback을 사용하므로 필드명 일치

# 최종 응답 Pydantic 모델
# 프론트가 요청하는 모든 필드 포함
class SurveyStatsResponse(BaseModel):
    averageRating: float
    totalParticipants: int
    ratingDistribution: RatingDistribution
    feedbackEntries: List[FeedbackEntry]
    responseSpeedHighPercent: float
    responseQualityHighPercent: float
    responseSpeedDistribution: CategoryDistribution
    responseQualityDistribution: CategoryDistribution
    
# --- 프론트엔드 필터 값과 DB 필드 값 매핑 ---
USER_GROUP_MAP = {
    "grade1": "1학년",
    "grade2": "2학년",
    "grade3": "3학년",
    "grade4": "4학년",
    "grad_student": "대학원생",
    "faculty": "교직원",
    "external": "외부인",
}

# --- 헬퍼 함수: 카테고리 분포 처리용 ---
def _process_category_distribution(
    raw_data: List[Dict], 
    labels: List[str], 
    total_count: int
) -> (CategoryDistribution, float):
    """
    MongoDB 집계 결과를 Pydantic 모델과 High 비율(%)로 변환합니다.
    """
    counts_dict = {item["_id"]: item["count"] for item in raw_data if item["_id"]}
    counts_list = [counts_dict.get(label, 0) for label in labels]
    
    high_count = counts_dict.get("high", 0)
    high_percent = (high_count / total_count) * 100 if total_count > 0 else 0
    
    dist_model = CategoryDistribution(labels=labels, counts=counts_list)
    return dist_model, high_percent

get_survey_collection = get_collection("survey")

# --- API 엔드포인트 ---
@router.get(
    "/statistics-survey", 
    response_model=SurveyStatsResponse,
    summary="사용자 설문조사 통계"
)
async def get_survey_statistics(
    collection: AsyncIOMotorCollection = Depends(get_survey_collection),
    userGroup: str = Query('all', description="필터링할 사용자 그룹") 
):

    # 2. 기본 필터링 단계($match) 구축
    match_stage = {}
    if userGroup != 'all' and userGroup in USER_GROUP_MAP:
        match_stage = {"userCategory": USER_GROUP_MAP[userGroup]}

    # 3. MongoDB Aggregation Pipeline 정의
    pipeline = [
        {"$match": match_stage},
        {
            "$facet": {
                # 3-1. 기본 통계 (평균, 총원)
                "stats": [
                    {
                        "$group": {
                            "_id": None,
                            "averageRating": {"$avg": "$rating"}, 
                            "totalParticipants": {"$sum": 1}
                        }
                    }
                ],
                # 3-2. 만족도 점수 분포
                "ratingDistribution": [
                    {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
                    {"$sort": {"_id": 1}}
                ],
                # 3-3. 주관식 답변 (코멘트)
                "feedbackEntries": [
                    {"$match": {"comment": {"$exists": True, "$ne": None, "$ne": ""}}},
                    {"$sort": {"date": -1}}, 
                    {"$limit": 100},
                    {
                        "$project": {
                            "_id": 1,
                            "rating": 1,
                            "feedback": "$comment"
                        }
                    }
                ],
                
                # 응답 속도 분포
                "responseSpeedDistribution": [
                    {"$group": {"_id": "$responseSpeed", "count": {"$sum": 1}}}
                ],
                # 응답 품질 분포
                "responseQualityDistribution": [
                    {"$group": {"_id": "$responseQuality", "count": {"$sum": 1}}}
                ]
            }
        }
    ]

    try:
        # 4. 집계 실행
        cursor = collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if not result or not result[0]:
             # 매칭되는 데이터가 아예 없는 경우 (API 호출은 성공)
             raise HTTPException(status_code=404, detail="No data found for the given filter")

        data = result[0]

        # 5-1. stats(평균, 총원) 처리 (IndexError 방지 로직 포함)
        stats_list = data.get("stats", [])
        if stats_list:
            stats_result = stats_list[0]
        else:
            # 필터링된 결과가 0건인 경우
            stats_result = {"averageRating": 0.0, "totalParticipants": 0}
        
        avg_rating = stats_result.get("averageRating", 0)
        total_participants = stats_result.get("totalParticipants", 0)

        # 5-2. ratingDistribution(점수 분포) 처리
        dist_result = data.get("ratingDistribution", [])
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for item in dist_result:
            if item["_id"] in rating_counts:
                rating_counts[item["_id"]] = item["count"]
        
        rating_distribution = RatingDistribution(
            counts=[rating_counts[i] for i in range(1, 6)]
        )

        # 5-3. feedbackEntries(피드백) 처리
        feedback_result = data.get("feedbackEntries", [])
        feedback_entries = [
            FeedbackEntry(
                id=str(item["_id"]),
                rating=item["rating"],
                feedback=item["feedback"]
            )
            for item in feedback_result
        ]
        
        # 응답 속도 처리
        speed_labels = ["low", "medium", "high"]
        speed_dist, speed_high_percent = _process_category_distribution(
            data.get("responseSpeedDistribution", []),
            speed_labels,
            total_participants
        )
        
        # 응답 품질 처리
        quality_labels = ["low", "medium", "high"]
        quality_dist, quality_high_percent = _process_category_distribution(
            data.get("responseQualityDistribution", []),
            quality_labels,
            total_participants
        )
        # ================================

        # 6. 최종 응답 반환
        return SurveyStatsResponse(
            averageRating=avg_rating,
            totalParticipants=total_participants,
            ratingDistribution=rating_distribution,
            feedbackEntries=feedback_entries,
            responseSpeedHighPercent=speed_high_percent,
            responseQualityHighPercent=quality_high_percent,
            responseSpeedDistribution=speed_dist,
            responseQualityDistribution=quality_dist
        )

    except Exception as e:
        logger.error(f"Error fetching survey statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}"
        )
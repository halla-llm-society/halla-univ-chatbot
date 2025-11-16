from fastapi import APIRouter, Depends, Request, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.db.mongodb import get_mongo_db, get_collection
from pydantic import BaseModel
from typing import List, Any, Dict
import math
import logging
from datetime import datetime, time

router = APIRouter()
logger = logging.getLogger(__name__)

# API 응답 모델 정의
class UserQueryResponse(BaseModel):
    data: List[Dict[str, Any]] # 프론트엔드가 받을 데이터 리스트
    totalPages: int

get_chat_collection = get_collection("chat")

@router.get("/user-query-data", response_model=UserQueryResponse)
async def get_user_query_data(
    
    collection: AsyncIOMotorCollection = Depends(get_chat_collection),
    # 프론트엔드에서 보내는 파라미터를 받음
    page: int = Query(1, ge=1),
    cnt: int = Query(20, ge=1),
    sort: str = Query('asc', enum=['asc', 'desc']),
    search: str | None = Query(None),
    category: str = Query('all', enum=['all', 'question', 'answer', 'decision']),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None)
):
    """
    사용자 질의 데이터를 필터링, 정렬, 페이지네이션하여 반환합니다.
    """
    

    # 2. 검색 필터 구축 (MongoDB 쿼리)
    query: Dict[str, Any] = {}
    
    # 3. 날짜 범위 검색 (필드명 'date'로 변경 및 datetime 객체로 변환)
    date_field = "date"
    if startDate and endDate:
        try:
            # 프론트에서 받은 'YYYY-MM-DD' 문자열을 datetime 객체로 변환
            # startDate는 00:00:00
            start_datetime = datetime.combine(datetime.fromisoformat(startDate), time.min) 
            # endDate는 23:59:59
            end_datetime = datetime.combine(datetime.fromisoformat(endDate), time.max)
            
            query[date_field] = {"$gte": start_datetime, "$lte": end_datetime}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # 4. 키워드 검색 (필드명 'question', 'answer', 'decision' 확인)
    if search:
        search_fields = []
        # 예시의 필드명과 일치하는지 확인
        if category == 'all' or category == 'question':
            search_fields.append({"question": {"$regex": search, "$options": "i"}})
        if category == 'all' or category == 'answer':
            search_fields.append({"answer": {"$regex": search, "$options": "i"}})
        if category == 'all' or category == 'decision':
            search_fields.append({"decision": {"$regex": search, "$options": "i"}})
        
        if search_fields:
            query["$or"] = search_fields
            
    # 5. 정렬 순서
    sort_order = 1 if sort == 'asc' else -1
    sort_field = "date"

    try:
        # 6. 총 문서 수 계산
        total_documents = await collection.count_documents(query)
        if total_documents == 0:
            return UserQueryResponse(data=[], totalPages=0)
        
        totalPages = math.ceil(total_documents / cnt)

        # 7. 데이터 가져오기 (페이지네이션 적용)
        skip = (page - 1) * cnt
        cursor = collection.find(query).sort(sort_field, sort_order).skip(skip).limit(cnt)
        
        results = []
        for doc in await cursor.to_list(length=cnt):
            doc["_id"] = str(doc["_id"])
            
            # DB에서 온 datetime 객체를 프론트가 읽기 좋은 문자열로 변환
            doc_date = doc.get(date_field)
            
            results.append({
                "date": doc_date.strftime('%Y-%m-%d %H:%M:%S') if doc_date else None,
                "question": doc.get("question"),
                "answer": doc.get("answer"),
                "decision": doc.get("decision")
            })

        return UserQueryResponse(data=results, totalPages=totalPages)

    except Exception as e:
        logger.error(f"Error fetching user query data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
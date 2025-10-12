import json
from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter(prefix="/surveys", tags=["surveys"])

# 절대 경로로 통일
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "surveys.jsonl"

# 설문 목록 조회
@router.get("/")
def get_surveys():
    """모든 설문 응답 조회"""
    items = []
    
    if not DATA_FILE.exists():
        return {"count": 0, "items": []}
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():  # 빈 줄 무시
                    items.append(json.loads(line))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 읽기 오류: {str(e)}")
    
    return {"count": len(items), "items": items}


# 설문 통계
@router.get("/stats")
def get_survey_stats():
    """설문 응답 통계 조회"""
    total = 0
    gender_count = {"남성": 0, "여성": 0}
    role_count = {"학생": 0, "교직원": 0}
    grade_count = {"1학년": 0, "2학년": 0, "3학년": 0, "4학년": 0}
    rating_count = {"1점": 0, "2점": 0, "3점": 0, "4점": 0, "5점": 0}

    if not DATA_FILE.exists():
        return {
            "total": 0,
            "gender": gender_count,
            "role": role_count,
            "grade": grade_count,
            "rating": rating_count
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():  # 빈 줄 무시
                    continue
                    
                record = json.loads(line)
                total += 1
                
                # 안전한 카운팅
                if record.get("gender") in gender_count:
                    gender_count[record["gender"]] += 1
                
                if record.get("role") in role_count:
                    role_count[record["role"]] += 1

                if record.get("role") == "학생" and record.get("grade") in grade_count:
                    grade_count[record["grade"]] += 1

                if record.get("rating") in rating_count:
                    rating_count[record["rating"]] += 1

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 계산 오류: {str(e)}")

    return {
        "total": total,
        "gender": gender_count,
        "role": role_count,
        "grade": grade_count,
        "rating": rating_count
    }

from fastapi import APIRouter
from pathlib import Path
import json
from datetime import datetime, timedelta

router = APIRouter(prefix="/stats", tags=["stats"])

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "sample.jsonl"

# 최근 N분 사용자 수
@router.get("/recent-users")
def recent_users(minutes: int = 5):
    if not DATA_FILE.exists():
        return {"count": 0}

    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)
    users = set()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            ts = datetime.strptime(record["created_at"], "%Y-%m-%d %H:%M:%S")
            if ts >= cutoff:
                users.add(record.get("is_user", True))  # 유저 ID 있으면 바꾸세요

    return {"minutes": minutes, "count": len(users)}

# 시간별 질문 수
@router.get("/hourly-questions")
def hourly_questions():
    counter = {}
    if not DATA_FILE.exists():
        return counter

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            ts = datetime.strptime(record["created_at"], "%Y-%m-%d %H:%M:%S")
            hour = ts.strftime("%H:00")
            counter[hour] = counter.get(hour, 0) + 1
    return counter

# 일별 토큰 사용량
@router.get("/daily-tokens")
def daily_tokens():
    counter = {}
    if not DATA_FILE.exists():
        return counter

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            # 토큰 정보는 ask_question에서 저장했다고 가정
            tokens = record.get("tokens", {}).get("total", 0)
            date = record["created_at"].split(" ")[0]
            counter[date] = counter.get(date, 0) + tokens
    return counter

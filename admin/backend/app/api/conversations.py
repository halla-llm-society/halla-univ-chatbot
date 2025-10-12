import json
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
from app.core.logger import log_conversation   # 로그 저장 함수 임포트

# =========================
# 라우터
# =========================
router = APIRouter(tags=["conversations"])

# =========================
# 환경변수 로드
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("⚠️ Warning: OPENAI_API_KEY not set in environment variables")
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# 데이터 파일 경로
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app
DATA_FILE = BASE_DIR / "data" / "sample.jsonl"

# =========================
# Pydantic 모델
# =========================
class Conversation(BaseModel):
    question: str
    answer: str | None = None
    is_user: bool = True

# =========================
# 1) 대화 기록 수동 추가
# =========================
@router.post("/conversations")
def add_conversation(conv: Conversation):
    record = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question": conv.question,
        "answer": conv.answer or "",
        "is_user": conv.is_user,
    }
    try:
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}")

    return {"status": "saved", "record": record}

# =========================
# 2) 대화 기록 조회
# =========================
@router.get("/conversations")
def get_conversations(q: str | None = Query(None)):
    items = []
    if not DATA_FILE.exists():
        return {"count": 0, "items": []}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    items.append(record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 읽기 오류: {str(e)}")

    if q:
        items = [
            r for r in items
            if q.lower() in r.get("question", "").lower()
            or q.lower() in r.get("answer", "").lower()
        ]

    return {"count": len(items), "items": items}

# =========================
# 3) 챗봇 호출 + 자동 로그 저장
# =========================
@router.post("/conversations/ask")
def ask_question(user_id: str, question: str):
    if not client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env"
        )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}]
        )

        tokens = {
            "prompt": resp.usage.prompt_tokens,
            "completion": resp.usage.completion_tokens,
            "total": resp.usage.total_tokens
        }

        answer = resp.choices[0].message.content

        # 로그 저장
        log_conversation(user_id, question, tokens)

        return {"answer": answer, "tokens": tokens}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API 오류: {str(e)}")

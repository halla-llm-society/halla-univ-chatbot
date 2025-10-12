# backend/app/core/logger.py
import json
from datetime import datetime
import os

LOG_FILE = "data/logs.jsonl"

def log_conversation(user_id: str, question: str, tokens: dict):
    """대화 기록 + 토큰 사용량 저장"""
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_id": user_id,
        "question": question,
        "tokens": tokens
    }
    os.makedirs("data", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

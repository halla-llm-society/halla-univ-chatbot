# backend/app/api/metrics.py
from fastapi import APIRouter
from datetime import datetime, timedelta
from pathlib import Path
import json

router = APIRouter(prefix="/metrics", tags=["metrics"])

# 데이터 파일 경로
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample.jsonl"

# OpenAI 가격 (2024년 기준)
MODELS = {
    "gpt-4o-mini": {
        "input": 0.150,   # $ per 1M tokens
        "output": 0.600,  # $ per 1M tokens
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
    }
}

# 서버 비용 (월 예상)
SERVER_COST_MONTHLY = 50.0  # AWS/GCP 기본 인스턴스
DB_COST_MONTHLY = 20.0      # 소규모 DB


def get_conversations_from_logs():
    """로그 파일에서 대화 기록 가져오기"""
    if not DATA_FILE.exists():
        return []
    
    conversations = []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    conversations.append(json.loads(line))
    except Exception:
        pass
    
    return conversations


def calculate_llm_cost(conversations, model="gpt-4o-mini"):
    """LLM 비용 계산"""
    if model not in MODELS:
        model = "gpt-4o-mini"
    
    prices = MODELS[model]
    total_input_tokens = 0
    total_output_tokens = 0
    
    for conv in conversations:
        # 실제 토큰 정보가 있으면 사용, 없으면 추정
        if "tokens" in conv and isinstance(conv["tokens"], dict):
            total_input_tokens += conv["tokens"].get("prompt", 100)
            total_output_tokens += conv["tokens"].get("completion", 200)
        else:
            # 추정값 (대화당 평균)
            total_input_tokens += 100
            total_output_tokens += 200
    
    input_cost = (total_input_tokens / 1_000_000) * prices["input"]
    output_cost = (total_output_tokens / 1_000_000) * prices["output"]
    total_cost = input_cost + output_cost
    
    return {
        "model": model,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "price_per_1m_input": prices["input"],
        "price_per_1m_output": prices["output"],
        "conversations_count": len(conversations)
    }


@router.get("/llm-usage")
def llm_usage(period: str = "day"):
    """
    LLM 토큰 사용량: 일(day) / 주(week) / 월(month)
    실제 로그 데이터 기반
    """
    conversations = get_conversations_from_logs()
    now = datetime.now()
    data = {}

    # 기간별 데이터 집계
    for conv in conversations:
        if not conv.get("created_at"):
            continue
        
        try:
            created_at = datetime.strptime(conv["created_at"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        # 토큰 정보 가져오기
        if "tokens" in conv and isinstance(conv["tokens"], dict):
            tokens = conv["tokens"].get("total", 300)
        else:
            tokens = 300  # 기본값 (입력 100 + 출력 200)

        # 기간에 따라 키 생성
        if period == "day":
            # 시간별 (24시간)
            if (now - created_at).days == 0:
                key = f"{created_at.hour}시"
                data[key] = data.get(key, 0) + tokens
        elif period == "week":
            # 일별 (7일)
            if (now - created_at).days < 7:
                key = created_at.strftime("%Y-%m-%d")
                data[key] = data.get(key, 0) + tokens
        elif period == "month":
            # 일별 (30일)
            if (now - created_at).days < 30:
                key = created_at.strftime("%Y-%m-%d")
                data[key] = data.get(key, 0) + tokens

    # 데이터 포맷팅
    if period == "day":
        result = [{"time": f"{h}시", "tokens": data.get(f"{h}시", 0)} for h in range(24)]
    elif period == "week":
        result = []
        for d in range(6, -1, -1):
            day = (now - timedelta(days=d)).strftime("%Y-%m-%d")
            result.append({"date": day, "tokens": data.get(day, 0)})
    elif period == "month":
        result = []
        for d in range(29, -1, -1):
            day = (now - timedelta(days=d)).strftime("%Y-%m-%d")
            result.append({"date": day, "tokens": data.get(day, 0)})
    else:
        result = []

    return {"period": period, "items": result}


@router.get("/costs")
def get_costs(model: str = "gpt-4o-mini"):
    """
    실제 비용 계산
    - OpenAI API 토큰 사용량 기반
    - 서버/DB 월 고정 비용
    """
    conversations = get_conversations_from_logs()
    
    # LLM 비용 계산
    llm_stats = calculate_llm_cost(conversations, model)
    
    # 일할 계산 (월 비용을 현재 날짜 기준으로)
    days_in_month = 30
    current_day = datetime.now().day
    server_cost = (SERVER_COST_MONTHLY / days_in_month) * current_day
    db_cost = (DB_COST_MONTHLY / days_in_month) * current_day
    
    total_cost = llm_stats["total_cost"] + server_cost + db_cost
    
    return {
        "llm": round(llm_stats["total_cost"], 4),
        "server": round(server_cost, 2),
        "db": round(db_cost, 2),
        "total": round(total_cost, 4),
        "llm_details": {
            "model": llm_stats["model"],
            "input_tokens": llm_stats["input_tokens"],
            "output_tokens": llm_stats["output_tokens"],
            "total_tokens": llm_stats["total_tokens"],
            "input_cost": round(llm_stats["input_cost"], 4),
            "output_cost": round(llm_stats["output_cost"], 4),
            "price_per_1m_input": llm_stats["price_per_1m_input"],
            "price_per_1m_output": llm_stats["price_per_1m_output"],
            "conversations_count": llm_stats["conversations_count"]
        }
    }


@router.get("/llm-cost-breakdown")
def get_llm_cost_breakdown():
    """
    모든 모델별 비용 비교
    """
    conversations = get_conversations_from_logs()
    
    breakdown = {}
    for model_name in MODELS.keys():
        stats = calculate_llm_cost(conversations, model_name)
        breakdown[model_name] = {
            "total_cost": round(stats["total_cost"], 4),
            "input_cost": round(stats["input_cost"], 4),
            "output_cost": round(stats["output_cost"], 4),
            "total_tokens": stats["total_tokens"],
            "price_per_1m_input": stats["price_per_1m_input"],
            "price_per_1m_output": stats["price_per_1m_output"]
        }
    
    return {
        "models": breakdown,
        "conversations_count": len(conversations)
    }


@router.get("/daily-llm-costs")
def get_daily_llm_costs(days: int = 30, model: str = "gpt-4o-mini"):
    """
    일별 LLM 비용 추이
    """
    conversations = get_conversations_from_logs()
    now = datetime.now()
    daily_data = {}
    
    if model not in MODELS:
        model = "gpt-4o-mini"
    
    prices = MODELS[model]
    
    # 일별로 데이터 집계
    for conv in conversations:
        if not conv.get("created_at"):
            continue
        
        try:
            created_at = datetime.strptime(conv["created_at"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        
        if (now - created_at).days >= days:
            continue
        
        date_key = created_at.strftime("%Y-%m-%d")
        
        if date_key not in daily_data:
            daily_data[date_key] = {
                "input_tokens": 0,
                "output_tokens": 0
            }
        
        # 토큰 정보 가져오기
        if "tokens" in conv and isinstance(conv["tokens"], dict):
            daily_data[date_key]["input_tokens"] += conv["tokens"].get("prompt", 100)
            daily_data[date_key]["output_tokens"] += conv["tokens"].get("completion", 200)
        else:
            daily_data[date_key]["input_tokens"] += 100
            daily_data[date_key]["output_tokens"] += 200
    
    # 비용 계산 및 포맷팅
    result = []
    for d in range(days - 1, -1, -1):
        date = (now - timedelta(days=d)).strftime("%Y-%m-%d")
        data = daily_data.get(date, {"input_tokens": 0, "output_tokens": 0})
        
        input_cost = (data["input_tokens"] / 1_000_000) * prices["input"]
        output_cost = (data["output_tokens"] / 1_000_000) * prices["output"]
        
        result.append({
            "date": date,
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
            "total_tokens": data["input_tokens"] + data["output_tokens"],
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(input_cost + output_cost, 4)
        })
    
    return {
        "model": model,
        "days": days,
        "data": result,
        "total_cost": round(sum(item["total_cost"] for item in result), 4)
    }

from fastapi import APIRouter, Query 
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import json, yaml, os, boto3

router = APIRouter(prefix="/metrics", tags=["metrics"])

# =========================
# ✅ 파일 경로 설정
# =========================
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample.jsonl"   # LLM 사용 로그
PRICING_FILE = Path(__file__).resolve().parent.parent / "config" / "pricing.yaml"  # 모델 단가 설정

# =========================
# ✅ YAML 가격 파일 로드
# =========================
def load_pricing():
    """pricing.yaml 파일에서 모델별 단가를 읽어옵니다."""
    if not PRICING_FILE.exists():
        return []
    try:
        with open(PRICING_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("models", [])
    except Exception as e:
        print(f"Error loading pricing.yaml: {e}")
        return []

# =========================
# ✅ 대화 로그 로드
# =========================
def get_conversations():
    """LLM 호출 로그(JSONL)를 불러와 파싱합니다."""
    if not DATA_FILE.exists():
        return []
    convs = []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    convs.append(json.loads(line))
    except Exception as e:
        print(f"Error loading sample.jsonl: {e}")
    return convs

# =========================
# ✅ 토큰 사용량 데이터 추출
# =========================
def extract_token_usage(conv: Dict[str, Any]) -> Dict[str, Any]:
    """대화 데이터에서 토큰 사용량과 비용을 추출합니다."""
    token_usage = conv.get("token_usage", {})

    return {
        "input_tokens": token_usage.get("input_tokens", 0),
        "output_tokens": token_usage.get("output_tokens", 0),
        "total_cost_usd": token_usage.get("total_cost_usd", 0)
    }

# =========================
# ✅ AWS 비용 계산 (Cost Explorer API)
# =========================
def get_aws_costs(days: int = 7):
    """
    AWS Cost Explorer API로 최근 n일간의 EC2, S3, DynamoDB 등 비용을 가져옵니다.
    API 오류가 발생하면 기본값(0원)을 반환합니다.
    """
    try:
        client = boto3.client("ce", region_name="us-east-1")

        end = datetime.utcnow().date()
        start = end - timedelta(days=days)

        response = client.get_cost_and_usage(
            TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end.strftime("%Y-%m-%d")},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        service_costs = {}
        daily_points = {}

        for result in response.get("ResultsByTime", []):
            date = result["TimePeriod"]["Start"]
            for group in result.get("Groups", []):
                service = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                service_costs[service] = service_costs.get(service, 0) + amount
                if service not in daily_points:
                    daily_points[service] = []
                daily_points[service].append({"time": date, "value": round(amount, 4)})

        total_cost = round(sum(service_costs.values()), 4)

        return {
            "total_cost_usd": total_cost,
            "by_service": service_costs,
            "daily_points": daily_points,  
            }

    except Exception as e:
        print(f"[AWS ERROR] {e}")
        # 실패해도 구조는 유지해야 함
        return {
            "total_cost_usd": 0,
            "by_service": {},
            "daily_points": {},  
        }
# =========================
# ✅ LLM (토큰 기반) 비용 계산
# =========================
def get_llm_costs(days: int = 7):
    """
    sample.jsonl 로그를 기반으로 LLM API 호출 비용을 계산합니다.
    기간(days) 동안의 총합 및 일별 데이터 포인트를 반환합니다.
    """
    now = datetime.now()
    convs = get_conversations()
    total_cost = 0.0
    points = {}

    for c in convs:
        if not c.get("created_at"):
            continue
        try:
            t = datetime.strptime(c["created_at"], "%Y-%m-%d %H:%M:%S")
        except:
            continue
        # N일 이상 지난 데이터는 제외
        if (now - t).days >= days:
            continue
        usage = extract_token_usage(c)
        total_cost += usage["total_cost_usd"]
        date_key = t.strftime("%Y-%m-%d")
        points[date_key] = points.get(date_key, 0) + usage["total_cost_usd"]

    # 날짜순 정렬 후 그래프용 포맷으로 변환
    data_points = [{"time": k, "value": round(v, 4)} for k, v in sorted(points.items())]
    return {"total": round(total_cost, 4), "points": data_points}

# =========================
# ✅ FastAPI 엔드포인트
# =========================
@router.get("/costs")
def get_combined_costs(period: str = Query("week", enum=["day", "week", "month"])):
    """
    LLM + AWS 서버 + DB 사용 비용을 통합 계산합니다.
    프론트엔드의 UsageCostInquiry.jsx에서 이 엔드포인트를 사용합니다.
    """
    # 기간 → 일수 변환
    days = {"day": 1, "week": 7, "month": 30}.get(period, 7)

    # LLM 및 AWS 비용 조회
    llm = get_llm_costs(days)
    aws = get_aws_costs(days)

    # AWS 서비스별 비용 분리
    server_cost = aws["by_service"].get("AmazonEC2", 0)  # 서버 (EC2)
    # DB: S3 + RDS 모두 포함
    db_cost = aws["by_service"].get("AmazonS3", 0) + aws["by_service"].get("AmazonRDS", 0)
    llm_cost = llm["total"]

    # 총합 계산
    total = round(llm_cost + server_cost + db_cost, 4)

    # 월 예상비용 (30일 기준 환산)
    estimated_monthly = round(total * (30 / days), 4)

    # =====================
    # ✅ 프론트엔드 구조에 맞는 응답
    # =====================
    return {
        "period": period,
        "grandTotal": total,
        "periodCosts": {
            "llm": llm,  # LLM 토큰 비용
            "server": {
                "total": round(server_cost, 4),
                "points": aws["daily_points"].get("AmazonEC2", [])
            },
            "db": {
                "total": round(db_cost, 4),
                "points": (
                    aws["daily_points"].get("AmazonS3", [])
                    + aws["daily_points"].get("AmazonRDS", [])
                )
            }
        },
        "estimatedMonthlyCost": {
            "total": estimated_monthly,
            "points": []
        }
    }

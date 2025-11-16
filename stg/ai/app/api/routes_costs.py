"""비용 추적 API 엔드포인트

OpenAI Costs API를 사용하여 실제 청구 비용을 조회하는 관리자 전용 엔드포인트입니다.

사용법:
    main.py에 다음 추가:
    ```python
    from api.routes_costs import router as costs_router
    app.include_router(costs_router, tags=["admin-costs"])
    ```

환경변수:
    OPENAI_ADMIN_KEY: Organization Owner/Admin API 키 (필수)
    OPENAI_PROJECT_ID: 프로젝트 ID (선택, 없으면 전체 조회)
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Dict, Any
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (openai_cost_api import를 위해)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# openai_cost_api.py를 직접 로드 (ai 패키지 의존성 우회)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "openai_cost_api",
    project_root / "ai" / "utils" / "openai_cost_api.py"
)
openai_cost_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(openai_cost_api)
OpenAICostAPI = openai_cost_api.OpenAICostAPI

router = APIRouter(prefix="/api/admin/costs")


@router.get("/yesterday")
async def get_yesterday_cost() -> Dict[str, Any]:
    """어제 하루 비용 조회 (모델별 상세)

    Returns:
        {
            "date": "2025-11-15",
            "total_cost": 0.4587,
            "models": [
                {"name": "o3-mini-2025-01-31, output", "cost": 0.2605, "percentage": 56.8},
                {"name": "gpt-4.1-2025-04-14, input", "cost": 0.0583, "percentage": 12.7},
                ...
            ]
        }

    Raises:
        HTTPException(500): OPENAI_ADMIN_KEY 미설정 또는 API 호출 실패
    """
    try:
        api = OpenAICostAPI()
        cost = api.get_yesterday_cost(group_by=["line_item"])

        # 모델별 비율 계산
        models = []
        for result in sorted(cost.results, key=lambda x: x.amount, reverse=True):
            percentage = (result.amount / cost.total_amount * 100) if cost.total_amount > 0 else 0
            models.append({
                "name": result.line_item or "Unknown",
                "cost": round(result.amount, 4),
                "percentage": round(percentage, 1)
            })

        return {
            "date": datetime.fromtimestamp(cost.start_time).strftime("%Y-%m-%d"),
            "total_cost": round(cost.total_amount, 4),
            "models": models
        }

    except ValueError as e:
        # OPENAI_ADMIN_KEY 미설정
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # API 호출 실패
        raise HTTPException(status_code=500, detail=f"비용 조회 실패: {str(e)}")


@router.get("/week")
async def get_week_cost() -> Dict[str, Any]:
    """최근 7일 비용 조회 (일별 + 모델별 상세)

    Returns:
        {
            "total_cost": 2.47,
            "days": 7,
            "average_per_day": 0.35,
            "daily": [
                {
                    "date": "2025-11-14",
                    "cost": 0.4587,
                    "models": [...]
                },
                ...
            ],
            "top_models": [
                {"name": "o3-mini-2025-01-31, output", "total_cost": 1.106},
                ...
            ]
        }

    Raises:
        HTTPException(500): OPENAI_ADMIN_KEY 미설정 또는 API 호출 실패
    """
    try:
        api = OpenAICostAPI()
        costs = api.get_last_n_days_cost(days=7, group_by=["line_item"])

        # 일별 비용
        daily = []
        for bucket in costs:
            models = [
                {
                    "name": r.line_item or "Unknown",
                    "cost": round(r.amount, 4)
                }
                for r in sorted(bucket.results, key=lambda x: x.amount, reverse=True)
            ]
            daily.append({
                "date": datetime.fromtimestamp(bucket.start_time).strftime("%Y-%m-%d"),
                "cost": round(bucket.total_amount, 4),
                "models": models
            })

        # 전체 통계
        total = sum(b.total_amount for b in costs)
        avg = total / len(costs) if costs else 0

        # 모델별 합계 (주간)
        model_totals = {}
        for bucket in costs:
            for result in bucket.results:
                model = result.line_item or "Unknown"
                model_totals[model] = model_totals.get(model, 0.0) + result.amount

        top_models = [
            {"name": model, "total_cost": round(cost, 4)}
            for model, cost in sorted(model_totals.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "total_cost": round(total, 4),
            "days": len(costs),
            "average_per_day": round(avg, 4),
            "daily": daily,
            "top_models": top_models[:10]  # 상위 10개만
        }

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비용 조회 실패: {str(e)}")


@router.get("/month")
async def get_month_cost() -> Dict[str, Any]:
    """이번 달 누적 비용 조회 (모델별 합계)

    Returns:
        {
            "year": 2025,
            "month": 11,
            "total_cost": 2.47,
            "days": 16,
            "average_per_day": 0.15,
            "models": [
                {"name": "o3-mini-2025-01-31, output", "cost": 1.106, "percentage": 44.8},
                {"name": "gpt-4.1-2025-04-14, input", "cost": 0.389, "percentage": 15.7},
                ...
            ]
        }

    Raises:
        HTTPException(500): OPENAI_ADMIN_KEY 미설정 또는 API 호출 실패
    """
    try:
        api = OpenAICostAPI()
        now = datetime.now()
        costs = api.get_month_cost(year=now.year, month=now.month, group_by=["line_item"])

        # 모델별 합계
        model_totals = {}
        for bucket in costs:
            for result in bucket.results:
                model = result.line_item or "Unknown"
                model_totals[model] = model_totals.get(model, 0.0) + result.amount

        # 전체 통계
        total = sum(b.total_amount for b in costs)
        avg = total / len(costs) if costs else 0

        # 모델별 비율 계산
        models = []
        for model, cost in sorted(model_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / total * 100) if total > 0 else 0
            models.append({
                "name": model,
                "cost": round(cost, 4),
                "percentage": round(percentage, 1)
            })

        return {
            "year": now.year,
            "month": now.month,
            "total_cost": round(total, 4),
            "days": len(costs),
            "average_per_day": round(avg, 4),
            "models": models
        }

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비용 조회 실패: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """헬스 체크 (OPENAI_ADMIN_KEY 설정 여부 확인)

    Returns:
        {"status": "ok", "message": "OpenAI Admin API 연결 가능"}
        또는
        {"status": "error", "message": "OPENAI_ADMIN_KEY 미설정"}
    """
    try:
        api = OpenAICostAPI()
        return {
            "status": "ok",
            "message": "OpenAI Admin API 연결 가능"
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e)
        }

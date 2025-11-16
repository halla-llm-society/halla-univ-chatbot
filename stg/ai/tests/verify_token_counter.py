"""TokenCounter 정확도 검증 스크립트

로컬에서 계산한 토큰 비용과 실제 OpenAI 청구 비용을 비교하여
TokenCounter의 정확도를 검증합니다.

주요 검증 항목:
1. 토큰 카운팅 정확도 (tiktoken vs 실제 API 사용량)
2. 비용 계산 정확도 (pricing.yaml vs 실제 청구 금액)
3. 모델별 비용 추적 정확도

사용법:
    # 어제 하루 검증
    python scripts/verify_token_counter.py

    # 특정 날짜 검증
    python scripts/verify_token_counter.py --date 2025-11-15

    # 최근 N일 검증
    python scripts/verify_token_counter.py --days 7

환경변수:
    OPENAI_ADMIN_KEY: Organization Owner/Admin API 키 필요
    MONGODB_URI: MongoDB 연결 문자열 (토큰 추적 로그 조회용)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import argparse

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent  # stg/ai/
app_root = project_root / "app"
sys.path.insert(0, str(app_root))

# apikey.env 파일 로드 (있으면)
try:
    from dotenv import load_dotenv
    env_file = app_root / "apikey.env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv가 없으면 환경변수 사용

# openai_cost_api.py를 직접 로드 (ai 패키지 의존성 우회)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "openai_cost_api",
    app_root / "ai" / "utils" / "openai_cost_api.py"
)
openai_cost_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(openai_cost_api)
OpenAICostAPI = openai_cost_api.OpenAICostAPI


def print_separator(title: str = "", char: str = "="):
    """구분선 출력"""
    if title:
        print(f"\n{char*70}")
        print(f"  {title}")
        print(f"{char*70}")
    else:
        print(f"{char*70}")


def calculate_accuracy(calculated: float, actual: float) -> Tuple[float, str]:
    """정확도 계산

    Returns:
        (차이율, 상태 이모지)
    """
    if actual == 0:
        return 0.0, "⚠️"

    diff_percent = abs((calculated - actual) / actual * 100)

    if diff_percent < 1:
        status = "✅"  # 매우 정확 (1% 미만 오차)
    elif diff_percent < 5:
        status = "✔️"  # 정확 (5% 미만 오차)
    elif diff_percent < 10:
        status = "⚠️"  # 주의 (10% 미만 오차)
    else:
        status = "❌"  # 부정확 (10% 이상 오차)

    return diff_percent, status


def verify_yesterday():
    """어제 하루 검증"""
    print_separator("📊 TokenCounter 정확도 검증 - 어제")

    api = OpenAICostAPI()

    # 실제 OpenAI 청구 비용
    yesterday_actual = api.get_yesterday_cost(group_by=["line_item"])

    date_str = datetime.fromtimestamp(yesterday_actual.start_time).strftime("%Y-%m-%d")
    print(f"\n  검증 날짜: {date_str}")
    print(f"  실제 OpenAI 청구: ${yesterday_actual.total_amount:.4f}")

    # TODO: MongoDB에서 로컬 계산 비용 조회
    # 현재는 로컬 비용 추적 시스템이 없으므로 안내 메시지만 출력
    print(f"\n  ℹ️  로컬 비용 추적 기능:")
    print(f"     - 현재 TokenCounter는 요청별 비용을 계산하지만 MongoDB에 저장하지 않습니다.")
    print(f"     - 비교 검증을 위해서는 다음 기능이 필요합니다:")
    print(f"       1. 각 API 요청의 토큰 사용량 및 계산된 비용을 MongoDB에 로깅")
    print(f"       2. 일별/모델별로 집계하여 OpenAI 실제 비용과 비교")
    print(f"       3. 차이가 큰 경우 알림 및 원인 분석")

    if yesterday_actual.results:
        print(f"\n  {'모델':<35} {'실제 비용 (USD)':<20} {'메모'}")
        print(f"  {'-'*68}")
        for result in sorted(yesterday_actual.results, key=lambda x: x.amount, reverse=True):
            model = result.line_item or "기타"
            print(f"  {model:<35} ${result.amount:<19.4f} 실제 청구")


def verify_last_n_days(days: int):
    """최근 N일 검증"""
    print_separator(f"📊 TokenCounter 정확도 검증 - 최근 {days}일")

    api = OpenAICostAPI()

    # 실제 OpenAI 청구 비용
    week_costs = api.get_last_n_days_cost(days=days, group_by=["line_item"])

    total_actual = sum(b.total_amount for b in week_costs)

    print(f"\n  검증 기간: 최근 {days}일")
    print(f"  실제 OpenAI 총 청구: ${total_actual:.4f}")

    # 일별 비용
    print(f"\n  {'날짜':<15} {'실제 비용 (USD)':<20} {'주요 모델'}")
    print(f"  {'-'*68}")

    for bucket in week_costs:
        date_str = datetime.fromtimestamp(bucket.start_time).strftime("%Y-%m-%d")

        # 주요 모델 (가장 비용이 큰 것)
        top_model = "없음"
        if bucket.results:
            top_result = max(bucket.results, key=lambda x: x.amount)
            top_model = top_result.line_item or "기타"

        print(f"  {date_str:<15} ${bucket.total_amount:<19.4f} {top_model}")

    # 모델별 합계
    model_totals = {}
    for bucket in week_costs:
        for result in bucket.results:
            model = result.line_item or "기타"
            model_totals[model] = model_totals.get(model, 0.0) + result.amount

    if model_totals:
        print(f"\n  {'모델별 합계':<35} {'실제 비용 (USD)':<20} {'비율'}")
        print(f"  {'-'*68}")
        for model, cost in sorted(model_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / total_actual * 100) if total_actual > 0 else 0
            print(f"  {model:<35} ${cost:<19.4f} {percentage:>5.1f}%")


def verify_specific_date(date_str: str):
    """특정 날짜 검증"""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"❌ 잘못된 날짜 형식: {date_str} (올바른 형식: YYYY-MM-DD)")
        sys.exit(1)

    print_separator(f"📊 TokenCounter 정확도 검증 - {date_str}")

    api = OpenAICostAPI()

    # 해당 날짜의 시작/끝 타임스탬프
    start = int(target_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    end = int(target_date.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())

    # 실제 OpenAI 청구 비용
    buckets = api.get_costs(
        start_time=start,
        end_time=end,
        group_by=["line_item"],
        limit=1
    )

    if not buckets:
        print(f"\n  ℹ️  {date_str}에 대한 비용 데이터가 없습니다.")
        return

    bucket = buckets[0]
    print(f"\n  검증 날짜: {date_str}")
    print(f"  실제 OpenAI 청구: ${bucket.total_amount:.4f}")

    if bucket.results:
        print(f"\n  {'모델':<35} {'실제 비용 (USD)':<20} {'비율'}")
        print(f"  {'-'*68}")
        for result in sorted(bucket.results, key=lambda x: x.amount, reverse=True):
            model = result.line_item or "기타"
            percentage = (result.amount / bucket.total_amount * 100) if bucket.total_amount > 0 else 0
            print(f"  {model:<35} ${result.amount:<19.4f} {percentage:>5.1f}%")


def print_recommendations():
    """개선 권장사항 출력"""
    print_separator("💡 TokenCounter 개선 권장사항")

    recommendations = [
        {
            "title": "1. 토큰 사용량 로깅 시스템 구축",
            "details": [
                "- 각 API 요청의 토큰 사용량 및 계산된 비용을 MongoDB에 저장",
                "- 컬렉션: token_usage_logs",
                "- 필드: timestamp, role, provider, model, input_tokens, output_tokens, calculated_cost"
            ]
        },
        {
            "title": "2. 일별 비용 집계 및 비교",
            "details": [
                "- 매일 자정에 전날 로컬 계산 비용 집계",
                "- OpenAI Costs API로 실제 청구 비용 조회",
                "- 차이가 5% 이상이면 알림 (Slack/이메일)"
            ]
        },
        {
            "title": "3. 토큰 오버헤드 검증",
            "details": [
                "- llm_config.yaml의 token_overhead 값 검증",
                "- 실제 API 응답의 usage 필드와 tiktoken 계산값 비교",
                "- 필요시 오버헤드 값 조정"
            ]
        },
        {
            "title": "4. 모델별 가격 정보 업데이트",
            "details": [
                "- pricing.yaml의 가격 정보가 최신인지 주기적 확인",
                "- OpenAI 공식 가격표: https://openai.com/pricing",
                "- 신규 모델 추가 시 자동 알림"
            ]
        }
    ]

    for rec in recommendations:
        print(f"\n  {rec['title']}")
        for detail in rec["details"]:
            print(f"     {detail}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="TokenCounter 정확도 검증")
    parser.add_argument("--date", help="검증할 날짜 (YYYY-MM-DD 형식)")
    parser.add_argument("--days", type=int, help="검증할 최근 일수")

    args = parser.parse_args()

    try:
        if args.date:
            # 특정 날짜 검증
            verify_specific_date(args.date)
        elif args.days:
            # 최근 N일 검증
            verify_last_n_days(args.days)
        else:
            # 기본: 어제 검증
            verify_yesterday()

        # 개선 권장사항
        print_recommendations()

        print_separator()
        print()

    except ValueError as e:
        print(f"\n⚠️  설정 오류: {e}")
        print("\nOPENAI_ADMIN_KEY 환경변수를 설정하세요:")
        print("  export OPENAI_ADMIN_KEY='sk-proj-...'")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

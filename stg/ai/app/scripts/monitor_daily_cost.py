"""일일 OpenAI 비용 모니터링 스크립트

로컬 테스트를 포함한 모든 OpenAI API 사용 비용을 모니터링합니다.
매일 실행하여 어제 비용, 최근 7일 비용, 이번 달 누적 비용을 확인할 수 있습니다.

사용법:
    python scripts/monitor_daily_cost.py

환경변수:
    OPENAI_ADMIN_KEY: Organization Owner/Admin API 키 필요
"""

import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# apikey.env 파일 로드 (있으면)
try:
    from dotenv import load_dotenv
    env_file = project_root / "apikey.env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv가 없으면 환경변수 사용

# openai_cost_api.py를 직접 로드 (ai 패키지 의존성 우회)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "openai_cost_api",
    project_root / "ai" / "utils" / "openai_cost_api.py"
)
openai_cost_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(openai_cost_api)
OpenAICostAPI = openai_cost_api.OpenAICostAPI


def print_separator(title: str = ""):
    """구분선 출력"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print(f"{'='*60}")


def print_cost_table(buckets, title: str):
    """비용 테이블 출력"""
    if not buckets:
        print(f"  데이터 없음")
        return

    total = sum(b.total_amount for b in buckets)

    print(f"\n  총 비용: ${total:.4f}")
    print(f"  {'날짜':<12} {'비용 (USD)':<15} {'모델별 상세'}")
    print(f"  {'-'*55}")

    for bucket in buckets:
        date_str = datetime.fromtimestamp(bucket.start_time).strftime("%Y-%m-%d")

        # 메인 라인
        print(f"  {date_str:<12} ${bucket.total_amount:<14.4f}", end="")

        # 모델별 상세
        if bucket.results:
            # 첫 번째 모델
            first = bucket.results[0]
            model_name = first.line_item or "기타"
            print(f" {model_name}: ${first.amount:.4f}")

            # 나머지 모델들 (들여쓰기)
            for result in bucket.results[1:]:
                model_name = result.line_item or "기타"
                print(f"  {' '*28} {model_name}: ${result.amount:.4f}")
        else:
            print()


def main():
    """메인 함수"""
    try:
        print_separator("📊 OpenAI 일일 비용 모니터링")
        print(f"  생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # API 클라이언트 초기화
        api = OpenAICostAPI()

        # 1. 어제 비용 (모델별 상세)
        print_separator("1️⃣  어제 비용 (모델별)")
        yesterday = api.get_yesterday_cost(group_by=["line_item"])

        if yesterday.total_amount > 0:
            print(f"\n  📅 {datetime.fromtimestamp(yesterday.start_time).strftime('%Y-%m-%d')} (어제)")
            print(f"  💰 총 비용: ${yesterday.total_amount:.4f}")

            if yesterday.results:
                print(f"\n  {'모델':<30} {'비용 (USD)':<15} {'비율'}")
                print(f"  {'-'*55}")
                for result in sorted(yesterday.results, key=lambda x: x.amount, reverse=True):
                    model = result.line_item or "기타"
                    percentage = (result.amount / yesterday.total_amount * 100) if yesterday.total_amount > 0 else 0
                    print(f"  {model:<30} ${result.amount:<14.4f} {percentage:>5.1f}%")
        else:
            print(f"\n  ℹ️  어제 사용 비용이 없습니다.")

        # 2. 최근 7일 비용
        print_separator("2️⃣  최근 7일 비용")
        week_costs = api.get_last_n_days_cost(days=7, group_by=["line_item"])
        print_cost_table(week_costs, "최근 7일")

        # 3. 이번 달 누적 비용
        print_separator("3️⃣  이번 달 누적 비용")
        now = datetime.now()
        month_costs = api.get_month_cost(year=now.year, month=now.month, group_by=["line_item"])

        if month_costs:
            total_month = sum(b.total_amount for b in month_costs)
            days_in_month = len(month_costs)
            avg_per_day = total_month / days_in_month if days_in_month > 0 else 0

            print(f"\n  📅 {now.year}년 {now.month}월")
            print(f"  💰 총 비용: ${total_month:.4f}")
            print(f"  📊 일수: {days_in_month}일")
            print(f"  📈 하루 평균: ${avg_per_day:.4f}")

            # 모델별 합계
            model_totals = {}
            for bucket in month_costs:
                for result in bucket.results:
                    model = result.line_item or "기타"
                    model_totals[model] = model_totals.get(model, 0.0) + result.amount

            if model_totals:
                print(f"\n  {'모델별 월 누적':<30} {'비용 (USD)':<15} {'비율'}")
                print(f"  {'-'*55}")
                for model, cost in sorted(model_totals.items(), key=lambda x: x[1], reverse=True):
                    percentage = (cost / total_month * 100) if total_month > 0 else 0
                    print(f"  {model:<30} ${cost:<14.4f} {percentage:>5.1f}%")

        # 4. 비용 알람 (선택사항)
        print_separator("4️⃣  비용 알람")

        DAILY_THRESHOLD = 5.0  # $5/day
        MONTHLY_THRESHOLD = 100.0  # $100/month

        warnings = []

        if yesterday.total_amount > DAILY_THRESHOLD:
            warnings.append(f"⚠️  어제 비용이 ${yesterday.total_amount:.2f}로 일일 임계값 ${DAILY_THRESHOLD:.2f}을 초과했습니다.")

        if month_costs:
            total_month = sum(b.total_amount for b in month_costs)
            if total_month > MONTHLY_THRESHOLD:
                warnings.append(f"⚠️  이번 달 누적 비용이 ${total_month:.2f}로 월간 임계값 ${MONTHLY_THRESHOLD:.2f}을 초과했습니다.")

        if warnings:
            for warning in warnings:
                print(f"\n  {warning}")
        else:
            print(f"\n  ✅ 모든 비용이 정상 범위 내에 있습니다.")

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

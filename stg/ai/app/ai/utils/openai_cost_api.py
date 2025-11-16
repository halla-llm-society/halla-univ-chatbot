"""OpenAI Costs API 클라이언트

조직의 실제 비용을 조회하는 공식 API 래퍼입니다.
로컬 테스트 비용 추적, 예산 모니터링, TokenCounter 검증 등에 활용됩니다.

참고: https://platform.openai.com/docs/api-reference/usage/costs
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CostResult:
    """비용 조회 결과"""
    line_item: Optional[str]  # 비용 항목 (예: "GPT-4 Turbo")
    project_id: Optional[str]  # 프로젝트 ID
    amount: float  # 비용 (USD)


@dataclass
class CostBucket:
    """시간 버킷별 비용"""
    start_time: int  # Unix timestamp
    end_time: int
    total_amount: float
    results: List[CostResult]


class OpenAICostAPI:
    """OpenAI Costs API 클라이언트

    조직의 실제 청구 비용을 조회합니다.

    환경 변수:
        OPENAI_ADMIN_KEY: Organization Owner/Admin API 키 (필수)

    예시:
        >>> api = OpenAICostAPI()
        >>> costs = api.get_yesterday_cost()
        >>> print(f"어제 비용: ${costs.total_amount:.2f}")
    """

    BASE_URL = "https://api.openai.com/v1/organization"

    def __init__(self, admin_key: Optional[str] = None, project_id: Optional[str] = None):
        """초기화

        Args:
            admin_key: OpenAI Admin API 키 (없으면 환경변수 OPENAI_ADMIN_KEY 사용)
            project_id: OpenAI 프로젝트 ID (없으면 환경변수 OPENAI_PROJECT_ID 사용, 없으면 전체 조회)

        Raises:
            ValueError: Admin Key가 없으면 발생
        """
        self.admin_key = admin_key or os.getenv("OPENAI_ADMIN_KEY")
        if not self.admin_key:
            raise ValueError(
                "OPENAI_ADMIN_KEY 환경변수가 설정되지 않았습니다. "
                "Organization Owner/Admin API 키가 필요합니다."
            )

        self.project_id = project_id or os.getenv("OPENAI_PROJECT_ID")

        self.headers = {
            "Authorization": f"Bearer {self.admin_key}",
            "Content-Type": "application/json"
        }

    def get_costs(
        self,
        start_time: int,
        end_time: Optional[int] = None,
        bucket_width: str = "1d",
        group_by: Optional[List[str]] = None,
        project_ids: Optional[List[str]] = None,
        limit: int = 7
    ) -> List[CostBucket]:
        """비용 조회 (범용)

        Args:
            start_time: 시작 시간 (Unix timestamp, inclusive)
            end_time: 종료 시간 (Unix timestamp, exclusive)
            bucket_width: 시간 단위 ("1d"만 지원, 기본값: "1d")
            group_by: 그룹화 필드 (["project_id", "line_item"] 등)
            project_ids: 프로젝트 ID 필터
            limit: 버킷 개수 제한 (1-180, 기본값: 7)

        Returns:
            시간 버킷별 비용 리스트

        Raises:
            requests.HTTPError: API 호출 실패 시
        """
        params = {
            "start_time": start_time,
            "bucket_width": bucket_width,
            "limit": limit
        }

        if end_time:
            params["end_time"] = end_time

        if group_by:
            params["group_by"] = group_by

        # project_ids가 명시되지 않았지만 인스턴스에 project_id가 있으면 사용
        if project_ids:
            params["project_ids"] = project_ids
        elif self.project_id:
            params["project_ids"] = [self.project_id]

        response = requests.get(
            f"{self.BASE_URL}/costs",
            headers=self.headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        buckets = []
        for bucket_data in data.get("data", []):
            results = []
            for result in bucket_data.get("results", []):
                # amount는 {"value": "0.123", "currency": "usd"} 형태
                amount_data = result.get("amount", {})
                amount_value = float(amount_data.get("value", 0.0)) if isinstance(amount_data, dict) else 0.0

                results.append(CostResult(
                    line_item=result.get("line_item"),
                    project_id=result.get("project_id"),
                    amount=amount_value
                ))

            # bucket의 total amount도 동일하게 처리
            bucket_amount_data = bucket_data.get("amount", {})
            bucket_amount = float(bucket_amount_data.get("value", 0.0)) if isinstance(bucket_amount_data, dict) else 0.0

            buckets.append(CostBucket(
                start_time=bucket_data["start_time"],
                end_time=bucket_data["end_time"],
                total_amount=bucket_amount,
                results=results
            ))

        return buckets

    def get_yesterday_cost(
        self,
        group_by: Optional[List[str]] = None
    ) -> CostBucket:
        """어제 하루 비용 조회

        Args:
            group_by: 그룹화 필드 (["line_item"] 등)

        Returns:
            어제 비용 버킷

        예시:
            >>> api = OpenAICostAPI()
            >>> cost = api.get_yesterday_cost(group_by=["line_item"])
            >>> for result in cost.results:
            ...     print(f"{result.line_item}: ${result.amount:.4f}")
        """
        yesterday = datetime.now() - timedelta(days=1)
        start = int(yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end = int(yesterday.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())

        buckets = self.get_costs(
            start_time=start,
            end_time=end,
            group_by=group_by,
            limit=1
        )

        return buckets[0] if buckets else CostBucket(
            start_time=start,
            end_time=end,
            total_amount=0.0,
            results=[]
        )

    def get_last_n_days_cost(
        self,
        days: int = 7,
        group_by: Optional[List[str]] = None
    ) -> List[CostBucket]:
        """최근 N일 비용 조회

        Args:
            days: 일수 (1-180)
            group_by: 그룹화 필드

        Returns:
            일별 비용 버킷 리스트
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        start = int(start_time.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end = int(end_time.timestamp())

        return self.get_costs(
            start_time=start,
            end_time=end,
            group_by=group_by,
            limit=days
        )

    def get_month_cost(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        group_by: Optional[List[str]] = None
    ) -> List[CostBucket]:
        """특정 월의 비용 조회

        Args:
            year: 연도 (기본값: 올해)
            month: 월 (1-12, 기본값: 이번 달)
            group_by: 그룹화 필드

        Returns:
            일별 비용 버킷 리스트
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        # 월의 첫날과 마지막날
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(seconds=1)

        start = int(first_day.timestamp())
        end = int(last_day.timestamp())

        days_in_month = (last_day - first_day).days + 1

        return self.get_costs(
            start_time=start,
            end_time=end,
            group_by=group_by,
            limit=min(days_in_month, 31)  # 최대 31일
        )

    def print_cost_summary(
        self,
        bucket: CostBucket,
        title: str = "비용 요약"
    ):
        """비용 요약 출력

        Args:
            bucket: 비용 버킷
            title: 제목
        """
        start_date = datetime.fromtimestamp(bucket.start_time).strftime("%Y-%m-%d")
        end_date = datetime.fromtimestamp(bucket.end_time).strftime("%Y-%m-%d")

        print(f"\n=== {title} ===")
        print(f"기간: {start_date} ~ {end_date}")
        print(f"총 비용: ${bucket.total_amount:.4f}")

        if bucket.results:
            print("\n상세:")
            for result in bucket.results:
                label = result.line_item or result.project_id or "기타"
                print(f"  - {label}: ${result.amount:.4f}")


def main():
    """테스트 및 예시"""
    try:
        api = OpenAICostAPI()

        # 어제 비용 (line_item별)
        print("1. 어제 비용 조회 (line_item별)")
        yesterday_cost = api.get_yesterday_cost(group_by=["line_item"])
        api.print_cost_summary(yesterday_cost, "어제 비용")

        # 최근 7일 비용
        print("\n\n2. 최근 7일 비용 조회")
        week_costs = api.get_last_n_days_cost(days=7)
        total_week = sum(b.total_amount for b in week_costs)
        print(f"총 비용: ${total_week:.4f}")
        for bucket in week_costs:
            date = datetime.fromtimestamp(bucket.start_time).strftime("%Y-%m-%d")
            print(f"  {date}: ${bucket.total_amount:.4f}")

        # 이번 달 비용
        print("\n\n3. 이번 달 비용 조회")
        month_costs = api.get_month_cost()
        total_month = sum(b.total_amount for b in month_costs)
        print(f"총 비용: ${total_month:.4f}")
        print(f"일수: {len(month_costs)}일")

    except ValueError as e:
        print(f"⚠️ 설정 오류: {e}")
        print("\nOPENAI_ADMIN_KEY 환경변수를 설정하세요:")
        print("  export OPENAI_ADMIN_KEY='sk-...'")
    except requests.HTTPError as e:
        print(f"❌ API 호출 실패: {e}")
        print(f"응답: {e.response.text if e.response else 'N/A'}")
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

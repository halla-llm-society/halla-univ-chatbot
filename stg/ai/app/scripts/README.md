# OpenAI 비용 추적 스크립트

이 디렉토리에는 OpenAI API 사용 비용을 추적하고 모니터링하는 스크립트가 포함되어 있습니다.

## 개요

로컬 테스트를 포함한 모든 OpenAI API 사용에 대해 **실제 청구 비용**을 추적합니다.
OpenAI Costs API를 사용하여 조직의 실제 청구 금액을 조회하고 분석합니다.

## 환경 설정

### 필수 환경변수

```bash
export OPENAI_ADMIN_KEY='sk-proj-...'
```

**OPENAI_ADMIN_KEY 발급 방법:**
1. [OpenAI Platform](https://platform.openai.com/) 접속
2. Organization Settings → Members
3. 본인 계정이 **Owner** 또는 **Admin** 권한인지 확인
4. API Keys 페이지에서 새 키 생성 (Admin 권한 필요)

⚠️ **주의:** 일반 API 키가 아닌 **Admin API 키**가 필요합니다.

## 스크립트 사용법

### 1. 일일 비용 모니터링 (`monitor_daily_cost.py`)

매일 실행하여 OpenAI 사용 비용을 확인합니다.

**기본 사용:**
```bash
cd stg/ai/app
python scripts/monitor_daily_cost.py
```

**출력 내용:**
- 어제 비용 (모델별 상세)
- 최근 7일 비용 (일별 + 모델별)
- 이번 달 누적 비용
- 비용 알람 (임계값 초과 시)

**예시 출력:**
```
📊 OpenAI 일일 비용 모니터링
  생성 시각: 2025-11-16 09:00:00

1️⃣  어제 비용 (모델별)
  📅 2025-11-15 (어제)
  💰 총 비용: $2.3456

  모델                            비용 (USD)      비율
  ---------------------------------------------------------------
  GPT-4 Turbo                    $1.8900         80.6%
  GPT-3.5 Turbo                  $0.4556         19.4%

2️⃣  최근 7일 비용
  총 비용: $15.2345
  ...
```

**크론 작업 설정 (매일 자동 실행):**
```bash
# 매일 오전 9시 실행
0 9 * * * cd /path/to/halla-univ-chatbot/stg/ai/app && /usr/bin/python3 scripts/monitor_daily_cost.py >> /var/log/openai_cost.log 2>&1
```

### 2. TokenCounter 검증 (`verify_token_counter.py`)

로컬에서 계산한 비용과 실제 OpenAI 청구 비용을 비교합니다.

**기본 사용 (어제 검증):**
```bash
cd stg/ai/app
python scripts/verify_token_counter.py
```

**특정 날짜 검증:**
```bash
python scripts/verify_token_counter.py --date 2025-11-15
```

**최근 N일 검증:**
```bash
python scripts/verify_token_counter.py --days 7
```

**출력 내용:**
- 실제 OpenAI 청구 비용 (모델별)
- 로컬 계산 비용 (향후 구현 예정)
- 정확도 분석 및 차이 원인
- 개선 권장사항

## API 직접 사용

Python 코드에서 직접 사용할 수도 있습니다:

```python
from ai.utils.openai_cost_api import OpenAICostAPI

api = OpenAICostAPI()

# 어제 비용 조회
yesterday = api.get_yesterday_cost(group_by=["line_item"])
print(f"어제 총 비용: ${yesterday.total_amount:.4f}")

for result in yesterday.results:
    print(f"{result.line_item}: ${result.amount:.4f}")

# 최근 7일 비용
week_costs = api.get_last_n_days_cost(days=7)
total = sum(b.total_amount for b in week_costs)
print(f"주간 총 비용: ${total:.4f}")

# 이번 달 비용
month_costs = api.get_month_cost()
print(f"월간 총 비용: ${sum(b.total_amount for b in month_costs):.4f}")
```

## 비용 알람 설정

`monitor_daily_cost.py`에서 임계값을 수정할 수 있습니다:

```python
DAILY_THRESHOLD = 5.0      # 일일 임계값 ($)
MONTHLY_THRESHOLD = 100.0  # 월간 임계값 ($)
```

임계값을 초과하면 경고 메시지가 출력됩니다.

## 향후 개선 계획

### 1. 토큰 사용량 로깅 시스템
- 각 API 요청의 토큰 사용량과 계산된 비용을 MongoDB에 저장
- 실시간 비용 추적 및 분석

### 2. 자동화된 비용 검증
- 로컬 계산 비용과 실제 청구 비용 자동 비교
- 차이가 5% 이상이면 Slack/이메일 알림

### 3. 대시보드
- 일별/주별/월별 비용 트렌드 시각화
- 모델별 사용 패턴 분석
- 예산 초과 예측

## 문제 해결

### "OPENAI_ADMIN_KEY 환경변수가 설정되지 않았습니다"

환경변수가 설정되어 있는지 확인:
```bash
echo $OPENAI_ADMIN_KEY
```

없다면 `.env` 파일에 추가하거나 직접 export:
```bash
export OPENAI_ADMIN_KEY='sk-proj-...'
```

### "403 Forbidden" 에러

API 키에 Admin 권한이 없는 경우입니다.
- Organization Settings에서 본인 계정 권한 확인
- Owner 또는 Admin 권한이 있는 API 키로 재생성

### "No data available" (데이터 없음)

- OpenAI Costs API는 최대 180일 전 데이터까지만 제공
- 해당 날짜에 실제로 API 사용이 없었을 수 있음
- 시간대 차이로 인해 데이터가 아직 업데이트되지 않았을 수 있음 (최대 24시간 지연)

## 참고 문서

- [OpenAI Costs API](https://platform.openai.com/docs/api-reference/usage/costs)
- [OpenAI Pricing](https://openai.com/pricing)
- [Organization Settings](https://platform.openai.com/settings/organization)

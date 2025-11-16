# 비용 추적 API 사용 가이드

## 개요

OpenAI Costs API를 사용하여 실제 청구 비용을 조회하는 관리자 전용 엔드포인트입니다.

## 백엔드 통합

### 1. main.py에 라우터 추가

```python
from api.routes_costs import router as costs_router

# 기존 라우터들
app.include_router(chat_router, tags=["chat"])
app.include_router(admin_router, tags=["admin"])

# 비용 추적 라우터 추가
app.include_router(costs_router, tags=["admin-costs"])
```

### 2. 환경변수 설정

`apikey.env` 파일에 추가:

```bash
# OpenAI Admin API 키 (Organization Owner/Admin 권한 필요)
OPENAI_ADMIN_KEY=sk-admin-F0xntz...

# (선택) 프로젝트 ID 필터링
OPENAI_PROJECT_ID=proj_abc123...
```

### 3. 완료!

이제 다음 엔드포인트들이 사용 가능합니다:

- `GET /api/admin/costs/yesterday` - 어제 비용
- `GET /api/admin/costs/week` - 최근 7일
- `GET /api/admin/costs/month` - 이번 달
- `GET /api/admin/costs/health` - 헬스 체크

---

## API 명세

### 1. 어제 비용 조회

**Endpoint:** `GET /api/admin/costs/yesterday`

**Response:**
```json
{
  "date": "2025-11-15",
  "total_cost": 0.4587,
  "models": [
    {
      "name": "o3-mini-2025-01-31, output",
      "cost": 0.2605,
      "percentage": 56.8
    },
    {
      "name": "gpt-4.1-2025-04-14, input",
      "cost": 0.0583,
      "percentage": 12.7
    },
    {
      "name": "gpt-4.1-2025-04-14, output",
      "cost": 0.0430,
      "percentage": 9.4
    }
  ]
}
```

### 2. 최근 7일 비용 조회

**Endpoint:** `GET /api/admin/costs/week`

**Response:**
```json
{
  "total_cost": 2.47,
  "days": 7,
  "average_per_day": 0.35,
  "daily": [
    {
      "date": "2025-11-14",
      "cost": 0.4587,
      "models": [
        {"name": "o3-mini-2025-01-31, output", "cost": 0.2605},
        {"name": "gpt-4.1-2025-04-14, input", "cost": 0.0583}
      ]
    },
    {
      "date": "2025-11-13",
      "cost": 0.6788,
      "models": [...]
    }
  ],
  "top_models": [
    {"name": "o3-mini-2025-01-31, output", "total_cost": 1.106},
    {"name": "gpt-4.1-2025-04-14, input", "total_cost": 0.389}
  ]
}
```

### 3. 이번 달 비용 조회

**Endpoint:** `GET /api/admin/costs/month`

**Response:**
```json
{
  "year": 2025,
  "month": 11,
  "total_cost": 2.47,
  "days": 16,
  "average_per_day": 0.15,
  "models": [
    {
      "name": "o3-mini-2025-01-31, output",
      "cost": 1.106,
      "percentage": 44.8
    },
    {
      "name": "gpt-4.1-2025-04-14, input",
      "cost": 0.389,
      "percentage": 15.7
    }
  ]
}
```

### 4. 헬스 체크

**Endpoint:** `GET /api/admin/costs/health`

**Response (성공):**
```json
{
  "status": "ok",
  "message": "OpenAI Admin API 연결 가능"
}
```

**Response (실패):**
```json
{
  "status": "error",
  "message": "OPENAI_ADMIN_KEY 환경변수가 설정되지 않았습니다."
}
```

---

## 프론트엔드 사용 예시

### React/TypeScript

```typescript
// types/costs.ts
export interface CostModel {
  name: string;
  cost: number;
  percentage?: number;
}

export interface YesterdayCost {
  date: string;
  total_cost: number;
  models: CostModel[];
}

export interface WeekCost {
  total_cost: number;
  days: number;
  average_per_day: number;
  daily: Array<{
    date: string;
    cost: number;
    models: CostModel[];
  }>;
  top_models: Array<{
    name: string;
    total_cost: number;
  }>;
}

// api/costs.ts
export const costsApi = {
  getYesterday: async (): Promise<YesterdayCost> => {
    const res = await fetch('/api/admin/costs/yesterday');
    if (!res.ok) throw new Error('비용 조회 실패');
    return res.json();
  },

  getWeek: async (): Promise<WeekCost> => {
    const res = await fetch('/api/admin/costs/week');
    if (!res.ok) throw new Error('비용 조회 실패');
    return res.json();
  },

  getMonth: async () => {
    const res = await fetch('/api/admin/costs/month');
    if (!res.ok) throw new Error('비용 조회 실패');
    return res.json();
  },
};

// components/CostDashboard.tsx
import { useEffect, useState } from 'react';
import { costsApi } from '../api/costs';

export const CostDashboard = () => {
  const [yesterday, setYesterday] = useState(null);
  const [week, setWeek] = useState(null);

  useEffect(() => {
    costsApi.getYesterday().then(setYesterday);
    costsApi.getWeek().then(setWeek);
  }, []);

  return (
    <div>
      <h2>어제 비용: ${yesterday?.total_cost.toFixed(2)}</h2>
      <h3>모델별 상세</h3>
      <ul>
        {yesterday?.models.map(m => (
          <li key={m.name}>
            {m.name}: ${m.cost.toFixed(4)} ({m.percentage}%)
          </li>
        ))}
      </ul>

      <h2>주간 비용: ${week?.total_cost.toFixed(2)}</h2>
      <p>일평균: ${week?.average_per_day.toFixed(2)}</p>
    </div>
  );
};
```

### Vue.js

```vue
<template>
  <div class="cost-dashboard">
    <h2>어제 비용: ${{ yesterday?.total_cost.toFixed(2) }}</h2>
    <ul>
      <li v-for="model in yesterday?.models" :key="model.name">
        {{ model.name }}: ${{ model.cost.toFixed(4) }} ({{ model.percentage }}%)
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const yesterday = ref(null);

onMounted(async () => {
  const res = await fetch('/api/admin/costs/yesterday');
  yesterday.value = await res.json();
});
</script>
```

---

## 테스트

### curl

```bash
# 어제 비용
curl http://localhost:8000/api/admin/costs/yesterday

# 최근 7일
curl http://localhost:8000/api/admin/costs/week

# 이번 달
curl http://localhost:8000/api/admin/costs/month

# 헬스 체크
curl http://localhost:8000/api/admin/costs/health
```

### Postman

1. GET 요청 생성
2. URL: `http://localhost:8000/api/admin/costs/yesterday`
3. Send 클릭

---

## 에러 처리

### 500 Error: OPENAI_ADMIN_KEY 미설정

```json
{
  "detail": "OPENAI_ADMIN_KEY 환경변수가 설정되지 않았습니다. Organization Owner/Admin API 키가 필요합니다."
}
```

**해결:**
- `apikey.env`에 `OPENAI_ADMIN_KEY` 추가
- 서버 재시작

### 500 Error: API 호출 실패

```json
{
  "detail": "비용 조회 실패: 403 Forbidden"
}
```

**해결:**
- API 키에 Admin 권한이 있는지 확인
- Organization Settings에서 권한 확인

---

## 보안 고려사항

⚠️ **중요:**

1. **Admin API 키는 절대 프론트엔드로 전송하지 말 것**
   - 백엔드 환경변수로만 관리
   - `.env` 파일은 `.gitignore`에 포함

2. **관리자 권한 체크**
   - 엔드포인트에 인증 미들웨어 추가 권장
   - 예시:
   ```python
   from fastapi import Depends
   from api.auth import get_current_admin_user

   @router.get("/yesterday")
   async def get_yesterday_cost(admin=Depends(get_current_admin_user)):
       # ...
   ```

3. **Rate Limiting**
   - OpenAI API 호출 횟수 제한
   - 캐싱 고려 (24시간 지연이므로 캐싱 가능)

---

## 향후 개선 사항

1. **캐싱**
   - Redis에 1시간 캐싱
   - API 호출 횟수 절약

2. **알림**
   - 일일 임계값 초과 시 Slack/이메일 알림

3. **시각화**
   - Chart.js/D3.js로 트렌드 그래프
   - 모델별 비용 비율 파이 차트

4. **예산 관리**
   - 월간 예산 설정
   - 예상 초과 시 경고

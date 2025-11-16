// src/services/cost.js

import apiClient from './apiClient';
import { getMockCostData } from './test_data/cost_data';

const USE_MOCK_DATA = false;

/**
 * 기간별 모든 비용 데이터를 한 번에 가져오는 함수
 */
export const getCosts = async (params) => {
  if (USE_MOCK_DATA) {
    return new Promise(resolve => {
      setTimeout(() => {
        const calculateTotal = (points) => parseFloat(points.reduce((sum, point) => sum + point.value, 0).toFixed(2));

        // --- 기간별 데이터 생성 ---
        const llmPeriodPoints = getMockCostData('llm', params.period);
        const serverPeriodPoints = getMockCostData('server', params.period);
        const dbPeriodPoints = getMockCostData('db', params.period);

        // --- 전체 총금액 계산 ---
        const allLlmPoints = getMockCostData('llm', 'year');
        const allServerPoints = getMockCostData('server', 'year');
        const allDbPoints = getMockCostData('db', 'year');
        const grandTotal = calculateTotal(allLlmPoints) + calculateTotal(allServerPoints) + calculateTotal(allDbPoints);

        // --- 월 예상 비용 계산 (백엔드 역할) ---
        const recentWeekLlm = getMockCostData('llm', 'week');
        const recentWeekServer = getMockCostData('server', 'week');
        const recentWeekDb = getMockCostData('db', 'week');
        const weeklyTotal = calculateTotal(recentWeekLlm) + calculateTotal(recentWeekServer) + calculateTotal(recentWeekDb);
        const estimatedTotal = parseFloat((weeklyTotal * 4).toFixed(2));
        
        const estimatedPoints = [
            { time: '1주차', value: estimatedTotal * 0.2 },
            { time: '2주차', value: estimatedTotal * 0.5 },
            { time: '3주차', value: estimatedTotal * 0.7 },
            { time: '4주차', value: estimatedTotal * 1.0 },
        ];

        // --- 최종 응답 데이터 조립 ---
        resolve({
          grandTotal: parseFloat(grandTotal.toFixed(2)),
          periodCosts: {
            llm: { total: calculateTotal(llmPeriodPoints), points: llmPeriodPoints },
            server: { total: calculateTotal(serverPeriodPoints), points: serverPeriodPoints },
            db: { total: calculateTotal(dbPeriodPoints), points: dbPeriodPoints },
          },
          // ▼▼▼ 이 부분이 빠져서 에러가 났습니다 ▼▼▼
          estimatedMonthlyCost: {
            total: estimatedTotal,
            points: estimatedPoints
          }
        });
      }, 300);
    });
  }

  try {
    const response = await apiClient.get('/api/costs', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching all costs:", error);
    throw error;
  }
};
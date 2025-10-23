import apiClient from './apiClient';
import { getMockTrafficData } from './test_data/traffic_data';

// Mock 데이터 사용 여부를 결정하는 변수
const USE_MOCK_DATA = false;

/**
 * 기간별 질문 수 데이터를 가져오는 API 함수
 * @param {object} params - { period } (예: 'day', 'week', 'month', 'year')
*/

export const getTrafficQueries = async (params) => {
  if (USE_MOCK_DATA) {
    console.log("Mocking API: getTrafficQueries with params:", params);
    return new Promise(resolve => {
      setTimeout(() => {
        resolve(getMockTrafficData('queries', params.period));
      }, 300); // 0.3초 지연
    });
  }

  try {
    const response = await apiClient.get('/traffic/queries', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching traffic queries:", error);
    throw error;
  }
};

// ========================================================================
// ========================================================================

/**
 * 기간별 토큰 사용량 데이터를 가져오는 API 함수
 * @param {object} params - { period } (예: 'day', 'week', 'month', 'year')
*/

export const getTrafficTokens = async (params) => {
  if (USE_MOCK_DATA) {
    console.log("Mocking API: getTrafficTokens with params:", params);
    return new Promise(resolve => {
      setTimeout(() => {
        resolve(getMockTrafficData('tokens', params.period));
      }, 300); // 0.3초 지연
    });
  }

  try {
    const response = await apiClient.get('/traffic/tokens', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching traffic tokens:", error);
    throw error;
  }
};
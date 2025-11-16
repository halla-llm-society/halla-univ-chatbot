// src/services/survey.js

import apiClient from './apiClient';
import { getMockSurveyData } from './test_data/servey_data'; // 분리된 목업 데이터 import

// true이면 목업 데이터 사용, false이면 실제 API 호출
const USE_MOCK_DATA = false; 

/**
 * 사용자 설문 통계 데이터를 가져오는 API 함수
 * @param {object} params - { userGroup }
 * @param {string} params.userGroup - 필터링할 사용자 그룹 (예: 'all', 'grade1', 'faculty')
 */
export const getSurveyStatistics = async (params) => {
  
  if (USE_MOCK_DATA) {
    // 목업 데이터를 비동기 API처럼 0.5초 뒤에 반환
    return new Promise(resolve => {
      setTimeout(() => {
        // 분리된 목업 데이터 생성 함수를 호출
        resolve(getMockSurveyData(params.userGroup));
      }, 500);
    });
  }

  // ----------------------------------------------------
  // 실제 백엔드 API 연동 시 사용할 코드
  // ----------------------------------------------------
  try {
    // 예시: GET /api/statistics/survey?userGroup=all
    const response = await apiClient.get('/api/statistics-survey', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching survey statistics:", error);
    throw error;
  }
};
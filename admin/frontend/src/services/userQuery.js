// src/services/userQuery.js

import apiClient from './apiClient';

/**
 * 사용자 질의 데이터를 가져오는 API 함수
 * @param {object} params - { page, cnt, sort, search, category, startDate, endDate }
 * @param {string} params.category - 검색할 카테고리 ('all', 'question', 'answer', 'decision')
 * @param {string} params.search - 검색어
 * @param {string} params.startDate - 조회 시작일 (YYYY-MM-DD 형식)
 * @param {string} params.endDate - 조회 종료일 (YYYY-MM-DD 형식)
 */

export const getUserQueryData = async (params) => {

  // ----------------------------------------------------
  // 나중에 백엔드가 완성되면 USE_MOCK_DATA를 false로 바꾸거나
  // 아래 코드만 남기고 위 if문을 삭제하면 됩니다.
  // ----------------------------------------------------

  try {
    // 예시: /user-query-data?page=1&cnt=20&sort=asc&search=날씨
    // 예시: GET /user-query-data?page=1&sort=desc&startDate=2025-10-10&endDate=2025-10-13
    const response = await apiClient.get('/api/user-query-data', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching user query data:", error);
    throw error;
  }
};
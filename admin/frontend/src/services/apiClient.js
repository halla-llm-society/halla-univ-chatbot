// .env 파일로 변경할 임시 파일입니다.

import axios from 'axios';

// 백엔드 API의 기본 주소
// .env 파일로 관리하는 것이 가장 좋습니다.
const BASE_URL = '/admin/api'; // 예시 URL

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 향후 여기에 JWT 토큰을 헤더에 자동으로 추가하는 등의
// 공통 로직(인터셉터)을 추가할 수 있습니다.

export default apiClient;
import axios from 'axios';

// 백엔드 API의 기본 주소
const API_BASE_URL = '/admin';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터: 401(토큰 만료 등) 에러 시 자동으로 로그아웃 처리합니다.
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 401 에러는 세션 만료를 의미
    if (error.response && error.response.status === 401) {
      // 무한 리다이렉트 방지를 위해 로그인 페이지가 아닐 때만 이동
      if (window.location.pathname !== '/admin/login' && window.location.pathname !== '/login') {
         window.location.href = '/admin/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
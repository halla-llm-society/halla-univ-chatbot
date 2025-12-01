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

// 요청 인터셉터
// 모든 API 요청이 전송되기 직전에 실행됩니다.
apiClient.interceptors.request.use(
  (config) => {
    // 브라우저의 localStorage에서 사용자가 선택한 환경을 꺼냅니다.
    // (값이 없으면 기본값으로 'prod'를 사용합니다)
    const currentDbEnv = localStorage.getItem('current_db_env') || 'prod';
    
    // http 요청 헤더에 'x-db-env' 값을 추가합니다.
    // 서버(backend)는 이 헤더를 보고 stg/prod를 판단합니다.
    config.headers['x-db-env'] = currentDbEnv;
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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
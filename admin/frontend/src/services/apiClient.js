import axios from 'axios';

// 백엔드 API의 기본 주소
const API_BASE_URL = '/admin';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 1. 요청 인터셉터: 모든 요청에 토큰을 자동으로 추가합니다.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 2. 응답 인터셉터: 401(토큰 만료 등) 에러 시 자동으로 로그아웃 처리합니다.
apiClient.interceptors.response.use(
  (response) => {
    // 정상 응답은 그대로 반환
    return response;
  },
  (error) => {
    // 401 Unauthorized 에러 발생 시
    if (error.response && error.response.status === 401) {
      console.warn("401 Unauthorized. 토큰이 만료되었거나 유효하지 않습니다. 로그아웃합니다.");
      
      // 토큰 삭제
      localStorage.removeItem('admin_token');
      
      // apiClient의 기본 헤더에서도 삭제
      delete apiClient.defaults.headers.common['Authorization'];

      // 로그인 페이지로 강제 이동
      // router 밖이므로 window.location을 사용합니다.
      // /admin/은 package.json의 homepage나 vite.config.js의 base에 설정되어 있어야 합니다.
      // 여기서는 basename이 /admin/ 이므로 /admin/login으로 이동시킵니다.
      if (window.location.pathname !== '/admin/login') {
         window.location.href = '/admin/login';
         alert('세션이 만료되었습니다. 다시 로그인해주세요.');
      }
    }
    
    // 다른 에러는 그대로 반환
    return Promise.reject(error);
  }
);

export default apiClient;
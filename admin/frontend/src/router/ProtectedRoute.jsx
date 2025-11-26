import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import apiClient from '../services/apiClient.js';

const ProtectedRoute = ({ children }) => {
  // null: 초기 상태 (확인 중), true: 로그인됨, false: 로그인 안됨
  const [isAuthenticated, setIsAuthenticated] = useState(null); 
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // 백엔드에 쿠키가 유효한지 확인 요청 (/auth/me)
        await apiClient.get('/auth/me');
        setIsAuthenticated(true);
      } catch (error) {
        // 401 에러 등 실패 시
        console.warn("Authentication failed or session expired");
        setIsAuthenticated(false);
      }
    };
    checkAuth();
  }, []);

  // 1. 인증 확인 중일 때 (로딩 화면)
  if (isAuthenticated === null) {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            Checking authentication...
        </div>
    );
  }

  // 2. 인증 실패 시 (로그인 페이지로 이동)
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 3. 인증 성공 시 (자식 컴포넌트 렌더링)
  return children;
};

export default ProtectedRoute;
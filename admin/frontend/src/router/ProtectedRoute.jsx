import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('admin_token');
  const location = useLocation();

  if (!token) {
    // 로그인되어 있지 않으면 로그인 페이지로 리다이렉트
    // 현재 경로를 `from`으로 전달하여 로그인 후 돌아올 수 있게 함
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 로그인되어 있으면 요청한 페이지(children)를 렌더링
  return children;
};

export default ProtectedRoute;
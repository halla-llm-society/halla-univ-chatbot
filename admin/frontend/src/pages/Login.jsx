import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // apiClient를 사용해도 됩니다.

// 이 페이지를 위한 간단한 CSS (인라인 스타일로 대체 가능)
import styles from './styles/Login.module.css';
import logo from '../assets/images/logo_2.png'; // 로고가 있다면

// apiClient.js에 정의된 baseURL을 사용합니다.
// 여기서는 /admin/ prefix가 이미 apiClient에 설정되어 있다고 가정합니다.
import apiClient from '../services/apiClient';

const LoginPage = () => {
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      // credentialResponse.credential이 Google의 ID 토큰(JWT)입니다.
      const id_token = credentialResponse.credential;

      // 이 토큰을 우리 백엔드로 보내 검증 및 앱 JWT 발급 요청
      const response = await apiClient.post('/auth/google/login', {
        id_token: id_token
      });

      // 백엔드에서 우리 앱 전용 토큰을 받음
      const { access_token } = response.data;

      // 토큰을 localStorage에 저장 (보안상 쿠키가 더 나을 수 있으나, 여기서는 localStorage 사용)
      localStorage.setItem('admin_token', access_token);
      
      // apiClient의 기본 헤더를 설정합니다. (다음 단계에서 인터셉터로 개선)
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // 로그인 성공 시 어드민 메인 페이지로 이동
      navigate('/', { replace: true });

    } catch (error) {
      console.error('로그인 실패:', error);
      // 사용자에게 에러 메시지 표시 (예: "허용되지 않은 계정입니다.")
      if (error.response && error.response.status === 403) {
        alert('접근이 허용되지 않은 계정입니다.');
      } else {
        alert('로그인 중 오류가 발생했습니다.');
      }
    }
  };

  const handleGoogleError = () => {
    console.error('Google 로그인 실패');
    alert('Google 로그인에 실패했습니다.');
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginBox}>
        <img src={logo} alt="로고" className={styles.logo} />
        <h2>관리자 페이지</h2>
        <p>로그인이 필요합니다.</p>
        <div className={styles.googleButtonWrapper}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap
          />
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
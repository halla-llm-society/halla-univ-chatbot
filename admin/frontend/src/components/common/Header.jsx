import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import styles from '../styles/Header.module.css';
import logoImage from '../../assets/images/logo_2.png';
import apiClient from '../../services/apiClient';

const Header = ({ curEnv, onEnvToggle }) => {

  const navigate = useNavigate();
  const [timeLeft, setTimeLeft] = useState(null); // 남은 시간 (초 단위)
  const [userEmail, setUserEmail] = useState('');

  // 1. 로그인 정보 및 만료 시간 가져오기
  useEffect(() => {
    const fetchAuthInfo = async () => {
      try {
        const response = await apiClient.get('/auth/me');
        console.log("Auth Info:", response.data);
        const { email, exp } = response.data;
        setUserEmail(email);

        if (exp) {
          const expSec = Math.floor(exp); 
          const nowSec = Math.floor(Date.now() / 1000);
          const remaining = expSec - nowSec;

          setTimeLeft(remaining > 0 ? remaining : 0);
        }
      } catch (error) {
        console.error("Failed to fetch auth info", error);
      }
    };

    fetchAuthInfo();
  }, []);

  // 2. 타이머 작동 (1초마다 감소)
  useEffect(() => {
    if (timeLeft === null) return;

    const timerId = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null || prev <= 0) {
          clearInterval(timerId);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timerId);
  }, [timeLeft !== null]);

  // 3. 시간 포맷팅 (MM:SS)
  const formatTime = (seconds) => {
    if (seconds === null) return "...";
    
    // [수정] 정수값 보장
    const s = Math.floor(seconds);

    const days = Math.floor(s / (60 * 60 * 24));
    const hours = Math.floor((s % (60 * 60 * 24)) / (60 * 60));
    const minutes = Math.floor((s % (60 * 60)) / 60);
    const secs = s % 60;

    // 24시간 이상 남았으면 '일' 단위 표시
    if (days > 0) {
      return `${days}일 ${hours}시간`;
    }
    // 1시간 이상 남았으면 '시간:분' 표시
    if (hours > 0) {
      return `${hours}시간 ${minutes}분 ${secs}초`;
    }
    // 그 외 '분:초'
    return `${minutes}분 ${secs < 10 ? '0' : ''}${secs}초`;
  };

    // 4. 로그아웃 처리
  const handleLogout = async () => {
    if (!window.confirm('로그아웃 하시겠습니까?')) return;

    try {
      await apiClient.post('/auth/logout');
      navigate('/login');
    } catch (error) {
      console.error('Logout failed', error);
      alert('로그아웃 중 오류가 발생했습니다.');
    }
  };

  return (
    <header className={styles.header}>
      {/* 왼쪽 섹션: 토글 버튼, 로고, 사이트 이름 */}
      <div className={styles.leftSection}>

        <NavLink to="/" className={styles.logo}>
          <img src={logoImage} alt="사이트 로고" className={styles.logoImage} />
          <span className={styles.siteName}>한라 LLM 관리자 페이지</span>
        </NavLink>

      </div>

      {/* 오른쪽 섹션: 네비게이션 메뉴, 사용자 액션 */}
      <div className={styles.rightSection}>

        {/* 타이머 표시 */}
        {timeLeft !== null && (
          <div className={styles.sessionInfo}>
            <span className={styles.timerLabel}>세션 만료:</span>
            <span className={`${styles.timerValue} ${timeLeft < 300 ? styles.warning : ''}`}>
              {formatTime(timeLeft)}
            </span>
          </div>
        )}

        {/* 2. 환경 토글 버튼을 스위치 UI로 변경 */}
        <div className={styles.userActions}>
          <div className={styles.envToggleContainer}>
            {/* PROD 라벨 */}
            <span className={`${styles.envLabel} ${curEnv === 'prod' ? styles.active : ''}`}>
              PROD
            </span>
            
            {/* 토글 스위치 */}
            <label className={styles.envToggleSwitch}>
              <input 
                type="checkbox" 
                className={styles.envToggleInput}
                // curEnv가 'stg'일 때 체크된 상태(on)가 됩니다.
                checked={curEnv === 'stg'}
                onChange={onEnvToggle}
              />
              <span className={styles.envToggleSlider}></span>
            </label>
            
            {/* STG 라벨 */}
            <span className={`${styles.envLabel} ${curEnv === 'stg' ? styles.active : ''}`}>
              STG
            </span>
          </div>
        </div>

        {/* 로그아웃 버튼 */}
        <button onClick={handleLogout} className={styles.logoutButton}>
          로그아웃
        </button>

      </div>
    </header>

  );
};

export default Header;
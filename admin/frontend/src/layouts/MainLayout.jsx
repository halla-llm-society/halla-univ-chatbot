// Header, Sidemenu, Footer를 포함하는 레이아웃

import { useState, useEffect } from 'react';
import Header from '../components/common/Header';
import Sidemenu from '../components/common/Sidemenu';
import { Outlet } from 'react-router-dom';
import { getCurrentDatabaseEnv, switchDatabaseEnv } from '../services/database';
import { useNavigate } from 'react-router-dom';

import styles from './MainLayout.module.css';

const MainLayout = () => {

  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);

  // 1. "전역 변수" 역할을 할 state를 MainLayout에 생성 (기본값 "stg")
  const [curEnv, setCurEnv] = useState("stg");
  const [isLoading, setIsLoading] = useState(true);

  const handleSidebarToggle = () => {
    setIsSidebarExpanded(prevState => !prevState);
  };

    // 2. "prod" <-> "stg" 토글 함수
  const handleEnvToggle = async () => {
    const newEnv = curEnv === 'stg' ? 'prod' : 'stg';
    
    try {
      await switchDatabaseEnv(newEnv);
      setCurEnv(newEnv); // 상태 업데이트
      
      // 중요: DB가 변경되었으므로 데이터를 새로고침해야 합니다.
      // 방법 1: 페이지 전체 새로고침 (가장 간단함)
      window.location.reload(); 
      
      // 방법 2: 현재 페이지를 다시 로드 (React-Router 사용 시)
      // navigate('.', { replace: true }); // 이 방법은 데이터 fetching 로직이 라우트 변경에 따라 다시 실행될 때 유효
      
    } catch (error) {
      console.error("Failed to switch DB env", error);
      // 실패 시 사용자에게 알림 (예: alert('DB 전환에 실패했습니다.'))
    }
  };

  useEffect(() => {
    const fetchEnv = async () => {
      setIsLoading(true);
      try {
        const data = await getCurrentDatabaseEnv();
        setCurEnv(data.environment || 'stg');
      } catch (error) {
        console.error("Failed to load DB env", error);
        setCurEnv('stg'); // 실패 시 stg로 기본 설정
      } finally {
        setIsLoading(false);
      }
    };
    fetchEnv();
  }, []);

  if (isLoading) {
    return <div>Loading...</div>; // 로딩 중 표시
  }

  return (
    <div className={styles.layoutContainer}>
      {/* 4. 상태와 상태 변경 함수를 Sidemenu에 props로 전달합니다. */}
      <Sidemenu isExpanded={isSidebarExpanded} onToggle={handleSidebarToggle} curEnv={curEnv} />
      
      {/* 5. 메인 콘텐츠 영역을 감싸는 div를 추가합니다. */}
      <div className={styles.mainContentWrapper}>

        <Header 
          curEnv={curEnv} 
          onEnvToggle={handleEnvToggle}
        />

        <main className={styles.main}>
          <Outlet />
        </main>
        {/* <Footer /> */}
      </div>
    </div>
  );
};

export default MainLayout;
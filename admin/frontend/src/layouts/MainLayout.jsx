// Header, Sidemenu, Footer를 포함하는 레이아웃

import { useState } from 'react';
import Header from '../components/common/Header';
import Sidemenu from '../components/common/Sidemenu';
import { Outlet } from 'react-router-dom';

import styles from './MainLayout.module.css';

const MainLayout = () => {

  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);

  // 1. "전역 변수" 역할을 할 state를 MainLayout에 생성 (기본값 "stg")
  const [curEnv, setCurEnv] = useState(() => {
    return localStorage.getItem('current_db_env') || 'prod';
  });

  const handleSidebarToggle = () => {
    setIsSidebarExpanded(prevState => !prevState);
  };

    // 2. "prod" <-> "stg" 토글 함수
  const handleEnvToggle = () => {
    const newEnv = curEnv === 'stg' ? 'prod' : 'stg';
    
    // (중요) 서버 API를 호출하지 않고, 로컬 스토리지 값만 변경합니다.
    localStorage.setItem('current_db_env', newEnv);
    
    // 상태 업데이트 (새로고침 전 UI 반영용)
    setCurEnv(newEnv); 

    // (중요) apiClient가 새로운 헤더 값을 물고 API를 호출할 수 있도록 페이지를 새로고침합니다.
    window.location.reload(); 
  };

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
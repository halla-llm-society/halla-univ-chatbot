// Header, Sidemenu, Footer를 포함하는 레이아웃
// src/layouts/MainLayout.jsx

import { useState } from 'react';
import Header from '../components/common/Header';
import Sidemenu from '../components/common/Sidemenu';
// import Footer from '../components/common/Footer';
import { Outlet } from 'react-router-dom';

import styles from './MainLayout.module.css';

const MainLayout = () => {

  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);

  // 1. "전역 변수" 역할을 할 state를 MainLayout에 생성 (기본값 "prod")
  const [curEnv, setCurEnv] = useState("prod");

  const handleSidebarToggle = () => {
    setIsSidebarExpanded(prevState => !prevState);
  };

    // 2. "prod" <-> "stg" 토글 함수
  const handleEnvToggle = () => {
    setCurEnv(prevEnv => (prevEnv === "prod" ? "stg" : "prod"));
    // 참고: 실제 환경을 바꾸는 로직(e.g., API endpoint 변경)이
    // 필요하다면 이 함수 내부에 구현할 수 있음
  };

  return (
    <div className={styles.layoutContainer}>
      {/* 4. 상태와 상태 변경 함수를 Sidemenu에 props로 전달합니다. */}
      <Sidemenu isExpanded={isSidebarExpanded} onToggle={handleSidebarToggle} />
      
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
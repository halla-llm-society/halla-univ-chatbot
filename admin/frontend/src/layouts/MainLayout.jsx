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

  const handleSidebarToggle = () => {
    setIsSidebarExpanded(prevState => !prevState);
  };

  return (
    <div className={styles.layoutContainer}>
      {/* 4. 상태와 상태 변경 함수를 Sidemenu에 props로 전달합니다. */}
      <Sidemenu isExpanded={isSidebarExpanded} onToggle={handleSidebarToggle} />
      
      {/* 5. 메인 콘텐츠 영역을 감싸는 div를 추가합니다. */}
      <div className={styles.mainContentWrapper}>
        <Header />
        <main className={styles.main}>
          <Outlet />
        </main>
        {/* <Footer /> */}
      </div>
    </div>
  );
};

export default MainLayout;
// src/components/common/Sidemenu.jsx

import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { PiRobotBold } from "react-icons/pi";


import styles from '../styles/Sidemenu.module.css';


// isExpanded와 onToggle 함수를 props로 받음
const Sidemenu = ({ isExpanded, onToggle }) => {

    // 마우스 호버 상태를 관리하는 새로운 state
    const [isHovered, setIsHovered] = useState(false);

    // 메뉴가 '접혀있을 때만' 호버 효과를 활성화하는 함수
    const handleMouseEnter = () => {
        if (!isExpanded) {
        setIsHovered(true);
        }
    };

    // 마우스가 컴포넌트 영역 밖으로 나갔을 때 실행될 함수
    const handleMouseLeave = () => {
        setIsHovered(false);
    };

    // 최종적으로 메뉴를 펼칠지 결정함
    // '고정' 상태이거나 '호버' 상태이면 true
    const shouldExpand = isExpanded || isHovered;

  return (

    <aside 
        className={`${styles.sidebar} ${shouldExpand ? styles.expanded : styles.collapsed}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
    >

    {/* 메뉴 토글 버튼 */}
      <div className={styles.toggleButtonContainer}>
        <button onClick={onToggle} className={styles.toggleButton}>
            {/* 햄버거 버튼: 3개의 줄로 구성 */}
            <div className={`${styles.hamburger} ${shouldExpand ? styles.open : ''}`}>
                <div className={styles.bar}></div>
                <div className={styles.bar}></div>
                <div className={styles.bar}></div>
            </div>
        </button>
      </div>
      
      {/* 메뉴 리스트 */}
      <nav className={styles.nav}>
        <ul>
          {/* 윗쪽 그룹 */}
          <li>
            <NavLink to="/chatbot"> {/* 경로는 예시입니다 */}
              <PiRobotBold className={styles.icon} /> <span className={styles.text}>챗봇으로 가기 </span>
            </NavLink>
          </li>

          {/* 구분선 */}
          <li className={styles.divider}></li>

          {/* 아래 그룹 */}
          <li>
            <NavLink to="/" className={({isActive}) => isActive ? styles.active : ''}>
              <span className={styles.text}>사용자 질의 데이터 분석</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/statistics" className={({isActive}) => isActive ? styles.active : ''}>
              <span className={styles.text}>사용자 통계 확인</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/traffic" className={({isActive}) => isActive ? styles.active : ''}>
              <span className={styles.text}>트래픽 조회</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/cost" className={({isActive}) => isActive ? styles.active : ''}>
              <span className={styles.text}>사용 비용 조회</span>
            </NavLink>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidemenu;
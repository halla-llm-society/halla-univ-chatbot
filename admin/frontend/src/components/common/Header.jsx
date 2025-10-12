// src/components/common/Header.jsx

import { NavLink } from 'react-router-dom';
import styles from '../styles/Header.module.css';

import logoImage from '../../assets/images/logo.png'; 


const Header = () => {

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
        <div className={styles.userActions}>
          <button>로그인</button>
        </div>
      </div>
    </header>

  );
};

export default Header;
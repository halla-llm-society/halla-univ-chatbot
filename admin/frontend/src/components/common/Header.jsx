// src/components/common/Header.jsx

import { NavLink } from 'react-router-dom';
import styles from '../styles/Header.module.css';
import logoImage from '../../assets/images/logo_2.png'; 

const Header = ({ curEnv, onEnvToggle }) => {

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
      </div>
    </header>

  );
};

export default Header;
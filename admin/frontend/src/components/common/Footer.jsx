// src/components/common/Footer.jsx

// 푸터는 어떻게 쓸지 고민좀 해볼게요

import styles from '../styles/Footer.module.css';

const Footer = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerContent}>
        <p className={styles.copyright}>
          © 2025 Your Company Name. All Rights Reserved.
        </p>
        <div className={styles.footerLinks}>
          <a href="/privacy">Privacy Policy</a>
          <span>|</span>
          <a href="/terms">Terms of Service</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
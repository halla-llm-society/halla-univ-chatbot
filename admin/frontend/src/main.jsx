import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';
import { GoogleOAuthProvider } from '@react-oauth/google'; // <--- 임포트

// .env 파일이나 vite 환경 변수에서 클라이언트 ID를 가져옵니다.
// Vite에서는 .env 파일에 VITE_GOOGLE_CLIENT_ID="..." 로 저장하고
// 여기서 import.meta.env.VITE_GOOGLE_CLIENT_ID 로 접근합니다.
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

if (!GOOGLE_CLIENT_ID) {
  console.error("VITE_GOOGLE_CLIENT_ID가 설정되지 않았습니다. .env 파일을 확인하세요.");
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}> {/* <--- 앱 감싸기 */}
      <App />
    </GoogleOAuthProvider>
  </React.StrictMode>
);

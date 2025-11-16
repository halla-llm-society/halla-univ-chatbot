import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/admin/',
  
  server: {
    proxy: {
      // '/api'로 시작하는 요청은 target 주소로 전달됩니다.
      '^/admin/(api|auth)': {
        target: 'http://127.0.0.1:8000', // 백엔드 서버 주소
        changeOrigin: true,
      },
    }
  }

})

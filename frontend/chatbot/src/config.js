// API 설정
const config = {
  // 개발 환경
  development: {
    API_BASE_URL: 'http://localhost:8000'
  },
  // 프로덕션 환경 (Vercel 배포)
  production: {
    API_BASE_URL: 'https://regulation-production.up.railway.app' // Railway 백엔드 URL
  }
};

// 현재 환경에 따른 API URL 반환
const getApiBaseUrl = () => {
  // Vite 환경 변수 사용
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  const env = import.meta.env.MODE || 'development';
  return config[env]?.API_BASE_URL || config.development.API_BASE_URL;
};

export const API_BASE_URL = getApiBaseUrl();
export default config;

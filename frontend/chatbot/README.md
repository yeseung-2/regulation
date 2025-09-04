# Regulation Chatbot Frontend

## 개발 환경 설정

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## Vercel 배포

이 프로젝트는 Vercel에 최적화되어 있습니다.

### 배포 전 확인사항:
1. `vercel.json` 파일이 프로젝트 루트에 있는지 확인
2. `package.json`의 빌드 스크립트가 올바른지 확인
3. 모든 의존성이 설치되어 있는지 확인

### 배포 후 404 에러 해결:
- `vercel.json`의 rewrites 설정이 SPA 라우팅을 처리합니다
- 모든 경로가 `index.html`로 리다이렉트되어 React Router가 작동합니다

## 주요 기능
- ESG 지표 관리
- 채팅 기능
- 템플릿 관리
- 사용자 인증

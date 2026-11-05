# 생활법률 모바일 프론트엔드

React Native + Expo SDK 58 + TypeScript. 실행/모바일 연결/서버 전환은 루트 `README.md`를 먼저 읽어 주세요.

```bash
npm ci
npm start
```

`src/app`은 라우트, `src/screens`는 실제 화면, `src/components`는 공통 UI입니다. 화면 수 11개, 하단 탭 3개입니다. 사건 수정은 상세 화면 안의 편집 상태입니다.

`.env`를 만들지 않거나 `EXPO_PUBLIC_USE_API=false`이면 서버 없이 데모로 실행됩니다. 서버 연결은 `.env.example`을 참고하세요.

`npm run android`는 이미 설치된 Android 개발 도구/에뮬레이터를 사용하며, Python은 프론트엔드 실행에 필요하지 않습니다.

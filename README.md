# 판례 기반 실생활 법률 상담 앱 (22S)

고급모바일프로그래밍 팀 프로젝트. 사용자가 법률 카테고리(전세사기, 중고거래사기, 교통사고 등)를 고르고
상황을 입력하면, AI가 추가 질문을 한 뒤 **근거 판례와 함께** 상담 결과를 알려주는 앱입니다.

- 팀: 김지민(팀장), 이규형, 김민성
- 구조: 앱(React Native) ↔ REST(JSON) ↔ 서버(Python) ↔ 벡터DB / Gemini API

> 기술 스택은 11주차 구현 기술 확정 보고서에서 최종 확정합니다. 아래는 현재 합의된 방향입니다.

## 폴더 구조

```
.
├─ app/      React Native(Expo) 앱 — 아직 없음. 아래 "앱 폴더 만들기" 참고
├─ server/   Python 서버 (상담 API, 판례 검색, Gemini 호출)
├─ data/     판례 수집·전처리·벡터DB 생성 스크립트
├─ docs/     API 명세, 보고서, 다이어그램
├─ .gitignore
└─ README.md
```

| 폴더 | 내용 | 주 담당(초안) |
|---|---|---|
| `app/` | 화면 11개, 서버 호출 | 공동 |
| `server/` | 상담 API, RAG, 회원·사건 API | 김지민 · 이규형 |
| `data/` | 판례 데이터 파이프라인 | 김민성 |
| `docs/` | 명세·문서 | 공동 |

## 앱 폴더 만들기

`app/` 폴더는 Expo가 직접 생성하도록 비워 두었습니다. 레포 최상위에서 한 번만 실행하세요.
(팀원 중 한 명이 만들어 올리고, 나머지는 pull 받으면 됩니다.)

```bash
npx create-expo-app@latest app
```

## 작업 규칙

- `main`에는 직접 push하지 않습니다. 작업마다 `feature/...` 브랜치를 만들고 Pull Request로 합칩니다.
  - 예: `feature/app-consult-screen`, `feature/server-consult-api`, `feature/data-pipeline`
- 작업을 시작하기 전에 항상 `pull`을 먼저 합니다.
- 비밀 키(`.env`)는 절대 커밋하지 않습니다. 필요한 키 이름은 `server/.env.example`에 적습니다.
- API 형식(요청·응답)은 `docs/api.md`에 먼저 적고, 앱과 서버가 그 형식을 기준으로 개발합니다.

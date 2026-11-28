# 판례 기반 실생활 법률 상담 앱 (22S)

고급모바일프로그래밍 팀 프로젝트. 사용자가 법률 카테고리(전세사기, 중고거래사기, 교통사고 등)를 고르고
상황을 입력하면, AI가 추가 질문을 한 뒤 **근거 판례와 함께** 상담 결과를 알려주는 앱입니다.

- 팀: 김지민(팀장), 이규형, 김민성
- 구조: 앱(React Native) ↔ REST(JSON) ↔ 서버(Python) ↔ 벡터DB / Gemini API

## 바로 실행하기 (clone 후 처음 한 번)

준비물: Git, Node.js 22.13 이상, Python 3.11 이상, 휴대폰의 Expo Go. PC와 휴대폰은 **같은 Wi-Fi**에 연결합니다.
판례 DB(`data/vector_db/precedents.sqlite3`, 90건·임베딩 포함)는 저장소에 들어 있어 따로 받을 필요가 없습니다.

1. 받기: `git clone https://github.com/GMiiiN/AMP.git` 후 `cd AMP`
2. **`.env` 위치**: 팀장에게 받은 `.env`(GEMINI_API_KEY가 든 파일)를 **`server/.env`** 로 둡니다. 루트나 `app/` 아래가 아닙니다.
   - `.env`에 적힌 값이 코드 기본값보다 우선합니다. `GEMINI_MODEL=gemini-3.8-flash` 줄이 있으면 504 오류가 잦으니 `gemini-3.6-flash`로 고치거나 줄을 지웁니다(기본값이 `gemini-3.6-flash`).
   - 판례 근거 답변을 쓰려면 `CONSULTATION_MODE=rag`여야 합니다(`demo`는 AI 없이 동작).
3. 설치(의존성 설치 + `app/.env` 생성 + 휴대폰이 접속할 PC IP 자동 입력)
   - Windows PowerShell: `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1`
   - macOS: `bash scripts/setup.sh`
4. 서버 실행(터미널 1)
   - Windows: `cd server` → `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - macOS: `cd server` → `.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Windows 방화벽 창이 뜨면 **개인 네트워크** 허용.
5. 앱 실행(터미널 2): `cd app` → `npx expo start --clear` → 휴대폰 Expo Go(iPhone은 카메라)로 QR 스캔
6. **휴대폰에서 서버 주소**: `app/.env`의 `EXPO_PUBLIC_API_URL=http://<PC IPv4>:8000` 입니다. 3번 setup이 자동으로 넣고 출력에 "탐지한 IPv4"를 보여 줍니다.
   틀렸으면 직접 고칩니다. PC IP 확인: Windows `ipconfig`의 Wi-Fi "IPv4 주소", macOS `ipconfig getifaddr en0`. 휴대폰에서 `localhost`는 PC가 아닙니다. 고친 뒤에는 `npx expo start --clear`로 다시 시작합니다.

확인: 서버를 켠 뒤 저장소 루트에서 `server\.venv\Scripts\python.exe scripts\check_env.py --health`(macOS `server/.venv/bin/python scripts/check_env.py --health`). 자세한 옵션·문제 해결은 [`docs/SETUP.md`](docs/SETUP.md).

> 기술 스택은 11주차 구현 기술 확정 보고서에서 최종 확정합니다. 아래는 현재 합의된 방향입니다.

## 폴더 구조

```
.
├─ app/      React Native(Expo) 앱
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

실행 방법은 [`docs/SETUP.md`](docs/SETUP.md)를 참고하세요.

## 작업 규칙

- `main`에는 직접 push하지 않습니다. 작업마다 `feature/...` 브랜치를 만들고 Pull Request로 합칩니다.
  - 예: `feature/app-consult-screen`, `feature/server-consult-api`, `feature/data-pipeline`
- 작업을 시작하기 전에 항상 `pull`을 먼저 합니다.
- 비밀 키(`.env`)는 절대 커밋하지 않습니다. 필요한 키 이름은 `server/.env.example`에 적습니다.
- API 형식(요청·응답)은 `docs/api.md`에 먼저 적고, 앱과 서버가 그 형식을 기준으로 개발합니다.

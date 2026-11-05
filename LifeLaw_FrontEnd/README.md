# 생활법률 · React Native 모바일 앱


```text
LifeLaw-Repo/
├─ app/       React Native + Expo + TypeScript, 화면 11개
├─ server/    Python FastAPI 상담 API, 검색 및 선택적 RAG
├─ data/      국가법령정보 API 수집·전처리·SQLite 벡터DB 구축
├─ docs/      화면 명세·API 명세·아키텍처·검증 보고서
├─ README.md
└─ .gitignore
```

## 1. 모바일 앱 실행 — 서버 없이 먼저 체험

준비: Node.js 22.13 이상(검증 환경은 Node 24), npm, 휴대폰의 SDK 57 호환 Expo Go. 이 패키지는 SDK 57로 고정
ZIP을 모두 압축 해제한 뒤 VS Code에서 `LifeLaw-Repo` 폴더를 열기. 터미널에서:

```bash
cd app
npm ci
npm start
```

- PC와 휴대폰을 같은 Wi-Fi에 연결하세요.
- Android: Expo Go에서 터미널의 QR 코드를 스캔합니다.
- iPhone: 카메라로 QR 코드를 스캔합니다. Expo Go의 요구에 따라 PC의 `npx expo login`과 앱을 같은 Expo 계정으로 로그인하세요.
- SDK 호환 오류가 나면 https://expo.dev/go 에서 SDK 57 지원 여부/실행 방법을 확인하세요. Android에는 SDK별 Expo Go가 제공될 수 있으며 iPhone은 설치 가능한 Expo Go 버전에 따라 개발 빌드가 필요할 수 있습니다.
- Android 에뮬레이터: Android Studio의 가상 기기를 켜고 `npm run android`.
- iOS 시뮬레이터: macOS와 Xcode에서 `npm run ios`.
- Windows에서 iOS 시뮬레이터는 실행할 수 없습니다. 실물 iPhone 실행 경로를 이용하세요.
- `npm run web`은 개발 중 화면 확인용이며 본 산출물은 모바일 앱 소스입니다.

기본은 **로컬 데모 모드**입니다. AI 키나 서버 없이 11개 화면, 입력 검증, 질문, 사건 저장/수정/삭제를 체험할 수 있습니다. 처음 실행할 때 테스트 계정 없이 바로 홈으로 진입합니다.

## 2. Python FastAPI 서버 실행

Python 3.12 권장. 별도의 터미널을 저장소 루트에서 열고:

```bash
cd server
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

macOS / Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API 문서: http://127.0.0.1:8000/docs / 상태: http://127.0.0.1:8000/health

`0.0.0.0`은 같은 Wi-Fi의 휴대폰이 PC 서버에 접속하기 위한 개발 설정입니다. 인증·속도 제한 없는 개발용 API이므로 인터넷 공개 운영용 설정이 아닙니다.

## 3. 모바일 앱과 서버 연결

`app/.env.example`을 `app/.env`로 복사하고:

```dotenv
EXPO_PUBLIC_USE_API=true
EXPO_PUBLIC_API_URL=http://192.168.0.10:8000
```

`192.168.0.10`은 **PC의 실제 Wi-Fi IPv4 주소**로 바꿉니다. Windows에서 `ipconfig`로 확인합니다. 휴대폰의 `localhost`는 PC가 아닙니다.

- Android 에뮬레이터: `http://10.0.2.2:8000`
- macOS의 iOS 시뮬레이터: `http://127.0.0.1:8000`
- 휴대폰 브라우저에서 `http://PC_IP:8000/health`가 열리는지 확인하세요. 필요하면 Windows 방화벽에서 해당 Python 프로그램의 개인 네트워크 접근을 허용하세요.
- 환경변수 변경 후 Expo를 중지하고 `npx expo start --clear`로 다시 실행합니다.
- `server/.env`의 `CONSULTATION_MODE=demo` 상태에서도 실제 HTTP 요청/응답을 테스트할 수 있습니다.
- 설치용 앱에서 외부 서버에 접속할 때는 HTTPS API를 사용하세요. 개발용 HTTP가 OS 네트워크 정책에 의해 제한될 수 있습니다.

`EXPO_PUBLIC_*`는 앱 번들에 공개되는 값입니다. 인증키·AI 키를 넣지 마세요.

## 4. 판례 수집·전처리·벡터 DB

인증값은 국가법령정보 공동활용에서 직접 신청·발급받아 `server/.env`의 `LAW_API_OC`에 입력합니다. 실제 인증값/판례 데이터/DB는 ZIP에 들어 있지 않습니다.

아래 명령은 **저장소 루트**에서 실행하며 Windows 기준입니다. macOS/Linux에서는 `server/.venv/Scripts/python.exe` 대신 `server/.venv/bin/python`을 사용하세요.

```powershell
server/.venv/Scripts/python.exe data/scripts/collect.py --category 임금체불 --query 임금 --pages 1 --output data/raw/wages.jsonl
```

수집된 JSONL의 분야와 원문 메타데이터를 검토한 뒤, 사용할 행의 `reviewed`를 `true`로 바꿉니다. 자동 수집만으로 법률 분류가 정확하다고 간주하지 않습니다.

```powershell
server/.venv/Scripts/python.exe data/scripts/preprocess.py data/raw/wages.jsonl
server/.venv/Scripts/python.exe data/scripts/build_index.py
```

- 전처리는 미검토 행을 제외하고 HTML/중복을 정리합니다.
- 판시사항·판결요지 중심으로 저장하며 판결 전문은 저장하지 않습니다.
- `data/vector_db/precedents.sqlite3`에 벡터와 메타데이터를 저장합니다.
- 기본 검색은 한국어 문자 2~4그램 TF-IDF + 코사인 유사도입니다. **의미 임베딩 모델이 아니며**, 소규모 과제용 기준 구현입니다. 분야 내 검색만 수행합니다.
- `기타`는 검색하지 않습니다. 결과가 없으면 근거 없음 상태를 반환합니다.

## 5. RAG 선택 실행

`server/.env`를 `CONSULTATION_MODE=rag`로 바꾸고 서버를 다시 시작합니다.

- `OLLAMA_MODEL`이 비어 있으면 실제 DB 검색 결과와 원문 메타데이터를 반환합니다. AI 요약은 하지 않습니다.
- 로컬 Ollama를 설치하고 사용할 모델을 준비한 경우 `OLLAMA_URL`과 `OLLAMA_MODEL`을 설정하면 **검색 → 근거 프롬프트 구성 → 모델 생성 → JSON/인용 ID 검증** 흐름이 실행됩니다.
- 모델은 자동 다운로드하지 않습니다. 모델 선택은 PC 메모리와 성능에 따라 달라집니다.
- 근거 없음 상태에서는 생성 모델을 호출하지 않습니다.
- 답변의 인용 ID가 검색 결과에 없으면 오류로 처리합니다. 이 검증만으로 법률적 정확성을 보장하지는 않습니다.

실제 법제처 인증 및 Ollama 모델 실행은 이 환경에서 검증하지 않았습니다. 수집기는 공식 API 스키마에 맞춰 작성했으며 모델 어댑터는 모의 응답으로 검증했습니다.

## 6. 설치용 Android APK 빌드

이 ZIP은 **소스 프로젝트**이며 완성 APK/IPA는 포함하지 않습니다. `app/eas.json`에는 Android APK용 preview 프로필이 준비되어 있습니다.

```bash
cd app
npx eas-cli@latest login
npx eas-cli@latest build:configure
npx eas-cli@latest build --platform android --profile preview
```

사용자 Expo 계정과 서명 설정이 필요합니다. 클라우드 빌드의 제공량/요금은 해당 계정의 현재 조건을 확인하세요. iOS 설치·배포는 Apple 서명과 배포 방식 설정이 별도로 필요합니다. 스토어에 올릴 경우 `app.json`의 bundleIdentifier/package를 본인 고유 값으로 변경하세요.

## 7. 테스트

```bash
cd app
npm run typecheck
npm run lint
npm test
npm run export:android
npm run export:ios
```

서버 폴더에서:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

검증 범위 및 실제 기기에서 확인할 항목은 `docs/TEST_REPORT.md`에 정리했습니다.

## 구현 범위

- 구현: 모바일 11개 화면, Expo Router 탭/스택, 기기 저장, 사건 CRUD·체크리스트·상담 결과 보관, 첨부파일 선택 및 메타데이터 보관, HTTP API 전환, FastAPI, 수집/전처리/벡터 검색, Ollama RAG 어댑터.
- 체험 구현: 회원가입·로그인. 비밀번호는 실행 메모리에만 유지하며 실제 인증 서버가 아닙니다. 앱 재시작 시 체험 계정을 다시 만들어야 합니다. 저장된 프로필은 UI 표시용입니다.
- 미포함: 서버 회원인증/JWT, 계정별 사건 DB, 원본 증거 업로드, 소셜 로그인, 이메일 복구, 푸시 알림, 실제 판례 말뭉치, 모델 파일, APK/IPA.
- 사건은 이 기기의 AsyncStorage에 저장됩니다. 공용 기기에서 실제 법률상담 개인정보를 입력하지 마세요. 로그아웃해도 사건 기록은 기기에 남습니다.

자세한 화면 목록은 `docs/SCREENS.md`, API는 `docs/API.md` 및 `docs/openapi.json`, 구성도는 `docs/ARCHITECTURE.md`를 참고하세요.

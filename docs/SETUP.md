# 생활법률 · React Native 모바일 앱


```text
.
├─ app/       React Native + Expo + TypeScript, 화면 11개
├─ server/    Python FastAPI 상담 API, 검색 및 선택적 RAG
├─ data/      국가법령정보 API 수집·전처리·SQLite 벡터DB 구축
├─ docs/      화면 명세·API 명세·아키텍처·검증 보고서
├─ scripts/   개발 환경 준비(setup.ps1 / setup.sh)·점검(check_env.py)
├─ README.md
└─ .gitignore
```

## 0. 빠른 시작 (setup.ps1 / setup.sh)

처음 받은 노트북은 저장소 루트에서 스크립트를 한 번 실행해 준비합니다. 준비물: Git, Node.js 22.13 이상, Python 3.11 이상(3.12 권장).

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

macOS:

```bash
bash scripts/setup.sh
```

어느 폴더에서 실행해도 저장소 루트를 기준으로 다음을 합니다.

1. `server/.env`, `app/.env`가 **없을 때만** 각 `.env.example`에서 복사합니다. 이미 있으면 절대 덮어쓰지 않습니다.
2. PC의 Wi-Fi/이더넷 IPv4를 찾아 `app/.env`의 `EXPO_PUBLIC_API_URL` **한 줄만** `http://<IPv4>:8000`으로 바꿉니다. 가상 어댑터(WSL·Hyper-V·VPN 등)와 169.254.x.x는 제외하고, 다른 줄은 그대로 둡니다.
3. `server/.venv`를 만들고 `pip install -r requirements.txt`를 실행합니다. 이미 있으면 그 venv를 다시 씁니다.
4. `app`에서 `npm ci`를 실행합니다.
5. `scripts/check_env.py`로 점검합니다. 모드별 필요한 키, 판례 DB, `app/.env` 주소 형식, 설치 상태를 보며 **키 값은 출력하지 않고 있음/없음만** 보여 줍니다.

| Windows (`setup.ps1`) | macOS (`setup.sh`) | 설명 |
|---|---|---|
| `-ApiUrl <주소>` | `--api-url <주소>` | 자동 탐지 대신 직접 지정. 예) 다른 팀원 PC `http://192.168.0.31:8000`, 터널 `https://xxxx.trycloudflare.com` |
| `-KeepApiUrl` | `--keep-api-url` | `EXPO_PUBLIC_API_URL`을 바꾸지 않음(다시 실행할 때 지금 주소 유지) |
| `-Port 8000` | `--port 8000` | 자동 탐지 주소에 붙일 서버 포트 |
| `-Python <경로>` | `--python <경로>` | venv를 만들 Python 지정. 예) `-Python "py -3.12"` |
| `-SkipServer` | `--skip-server` | venv 생성·pip 설치 건너뜀 |
| `-SkipApp` | `--skip-app` | `npm ci` 건너뜀 |
| `-SkipCheck` | `--skip-check` | 마지막 점검 건너뜀 |

준비가 끝나면 터미널 두 개를 열어 저장소 루트에서 실행합니다(macOS는 `.\.venv\Scripts\python.exe` 대신 `.venv/bin/python`).

```powershell
# 터미널 1: 서버
cd server
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 터미널 2: 앱 (.env를 바꾼 뒤에는 꼭 --clear)
cd app
npx expo start --clear
```

- 서버를 켠 뒤 저장소 루트에서 `server\.venv\Scripts\python.exe scripts\check_env.py --health`(macOS `server/.venv/bin/python scripts/check_env.py --health`)를 실행하면 앱이 가리키는 주소의 `/health`까지 확인합니다.
- 서버를 처음 켤 때 Windows 방화벽 창이 뜨면 **개인 네트워크**를 허용합니다.
- 다시 실행해도 안전합니다(`.env`를 덮어쓰지 않고 venv를 재사용). 단 `npm ci`는 `node_modules`를 새로 설치하므로 필요 없으면 `-SkipApp`을 붙입니다.
- PowerShell에서 "스크립트를 실행할 수 없습니다" 오류가 나면 위처럼 `-ExecutionPolicy Bypass -File`로 실행합니다.

### 비밀 키는 git 밖에서 받기, 판례 DB는 저장소에 포함

비밀 키는 `GEMINI_API_KEY` 하나입니다. 팀장에게 받은 `.env` 파일을 **`server/.env`** 에 둡니다(`.gitignore` 대상이라 커밋되지 않음). 판례 DB `data/vector_db/precedents.sqlite3`(90건, 임베딩 포함)는 저장소에 들어 있어 따로 받을 필요가 없습니다.

| 받을 것 | 둘 위치 | 필요한 경우 |
|---|---|---|
| `.env` (`GEMINI_API_KEY` 포함) | `server/.env` | rag 모드 서버 |
| 판례 DB | 이미 `data/vector_db/precedents.sqlite3`에 있음 | rag 모드 서버 |

- 받은 `.env`를 `server/.env`로 먼저 두고 setup 스크립트를 실행하면 덮어쓰지 않습니다. setup이 먼저 만들었다면 받은 파일로 바꿉니다. `CONSULTATION_MODE` 값을 확인합니다.
- `.env`의 값이 코드 기본값보다 우선합니다. 받은 `.env`에 `GEMINI_MODEL=gemini-3.8-flash`가 있으면 504가 잦으므로 `gemini-3.6-flash`로 바꾸거나 그 줄을 지웁니다(기본값 `gemini-3.6-flash`).
- `LAW_API_OC`는 판례 수집(4장)에만 쓰며 지금은 필요 없습니다.
- 키는 메신저·이슈·커밋·스크린숏에 붙이지 않고, `app/.env`의 `EXPO_PUBLIC_*`(앱 번들에 그대로 들어감)에도 넣지 않습니다.
- 넣은 뒤 저장소 루트에서 `python scripts/check_env.py`(macOS는 `python3`)로 확인합니다. demo 모드는 키 없이 동작합니다.

## 1. 모바일 앱 실행 — 서버 없이 먼저 체험

준비: Node.js 22.13 이상(검증 환경은 Node 24), npm, 휴대폰의 SDK 58 호환 Expo Go. 이 패키지는 SDK 58로 고정
VS Code에서 저장소 루트 폴더를 열기. 터미널에서:

```bash
cd app
npm ci
npm start
```

- PC와 휴대폰을 같은 Wi-Fi에 연결하세요.
- Android: Expo Go에서 터미널의 QR 코드를 스캔합니다.
- iPhone: 카메라로 QR 코드를 스캔합니다. Expo Go의 요구에 따라 PC의 `npx expo login`과 앱을 같은 Expo 계정으로 로그인하세요.
- SDK 호환 오류가 나면 https://expo.dev/go 에서 SDK 58 지원 여부/실행 방법을 확인하세요. Android에는 SDK별 Expo Go가 제공될 수 있으며 iPhone은 설치 가능한 Expo Go 버전에 따라 개발 빌드가 필요할 수 있습니다.
- Android 에뮬레이터: Android Studio의 가상 기기를 켜고 `npm run android`.
- iOS 시뮬레이터: macOS와 Xcode에서 `npm run ios`.
- Windows에서 iOS 시뮬레이터는 실행할 수 없습니다. 실물 iPhone 실행 경로를 이용하세요.
- `npm run web`은 개발 중 화면 확인용이며 본 산출물은 모바일 앱 소스입니다.

기본은 **로컬 데모 모드**입니다. AI 키나 서버 없이 11개 화면, 입력 검증, 질문, 사건 저장/수정/삭제를 체험할 수 있습니다. 처음 실행할 때 테스트 계정 없이 바로 홈으로 진입합니다.

setup 스크립트(0장)를 실행했다면 `app/.env`에 `EXPO_PUBLIC_USE_API=true`가 들어가 앱이 서버를 호출합니다. 서버(2장)를 먼저 켜거나, 서버 없이 보려면 `false`로 바꾸고 `npx expo start --clear`로 다시 시작하세요.

## 2. Python FastAPI 서버 실행

Python 3.12 권장. 별도의 터미널을 저장소 루트에서 열고:

```bash
cd server
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

macOS / Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
[ -e .env ] || cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`.env`가 이미 있으면 복사하지 않습니다(키가 들어 있는 파일을 덮어쓰지 않도록).

API 문서: http://127.0.0.1:8000/docs / 상태: http://127.0.0.1:8000/health

`0.0.0.0`은 같은 Wi-Fi의 휴대폰이 PC 서버에 접속하기 위한 개발 설정입니다. 인증·속도 제한 없는 개발용 API이므로 인터넷 공개 운영용 설정이 아닙니다.

## 3. 모바일 앱과 서버 연결

0장의 setup 스크립트가 이 과정을 자동으로 합니다(`app/.env` 생성, `EXPO_PUBLIC_API_URL`을 PC IPv4로 설정). 직접 하려면 저장소 루트에서 `app/.env.example`을 `app/.env`로 복사합니다(이미 있으면 복사하지 않음).

```powershell
if (-not (Test-Path app\.env)) { Copy-Item app\.env.example app\.env }   # Windows
```

```bash
[ -e app/.env ] || cp app/.env.example app/.env   # macOS / Linux
```

`app/.env.example`에 들어 있는 값(주석 제외):

```dotenv
EXPO_PUBLIC_USE_API=true
EXPO_PUBLIC_API_URL=http://192.168.0.10:8000
```

- `EXPO_PUBLIC_USE_API=true`일 때만 서버를 호출합니다. `false`이거나 `app/.env`가 없으면 서버 없이 로컬 데모로 동작합니다(1장).
- `192.168.0.10`은 예시입니다. **PC의 실제 Wi-Fi/이더넷 IPv4**로 바꿉니다(setup 스크립트가 자동으로 바꿉니다). Windows는 `ipconfig`, macOS는 `ipconfig getifaddr en0`으로 확인합니다. 휴대폰의 `localhost`는 PC가 아닙니다. 주소 끝에 `/`를 붙이지 않습니다.
- Android 에뮬레이터: `http://10.0.2.2:8000`
- macOS의 iOS 시뮬레이터: `http://127.0.0.1:8000`
- 같은 Wi-Fi에서 안 붙으면 터널 HTTPS 주소를 넣을 수 있습니다(8장).
- 휴대폰 브라우저에서 `http://PC_IP:8000/health`가 열리는지 확인하세요. PC에서는 저장소 루트에서 `python scripts/check_env.py --health`(macOS는 `python3`)로 확인합니다. 필요하면 Windows 방화벽에서 해당 Python 프로그램의 개인 네트워크 접근을 허용하세요.
- 환경변수 변경 후 Expo를 중지하고 `npx expo start --clear`로 다시 실행합니다.
- `server/.env`의 `CONSULTATION_MODE=demo` 상태에서도 실제 HTTP 요청/응답을 테스트할 수 있습니다.
- 설치용 앱에서 외부 서버에 접속할 때는 HTTPS API를 사용하세요. 개발용 HTTP가 OS 네트워크 정책에 의해 제한될 수 있습니다.

`EXPO_PUBLIC_*`는 앱 번들에 공개되는 값입니다. 인증키·AI 키를 넣지 마세요.

## 4. 판례 수집·전처리·벡터 DB

인증값은 국가법령정보 공동활용에서 직접 신청·발급받아 `server/.env`의 `LAW_API_OC`에 입력합니다. 실제 인증값/판례 데이터/DB는 저장소에 들어 있지 않습니다.

아래 명령은 **저장소 루트**에서 실행하며 Windows 기준입니다. macOS/Linux에서는 `server/.venv/Scripts/python.exe` 대신 `server/.venv/bin/python`을 사용하세요.

```powershell
server/.venv/Scripts/python.exe data/scripts/collect.py --category 임금체불 --query 임금 --pages 1 --output data/raw/wages.jsonl
```

수집된 JSONL의 분야와 원문 메타데이터를 검토한 뒤, 사용할 행의 `reviewed`를 `true`로 바꿉니다. 자동 수집만으로 법률 분류가 정확하다고 간주하지 않습니다.

```powershell
server/.venv/Scripts/python.exe data/scripts/preprocess.py data/raw/wages.jsonl
server/.venv/Scripts/python.exe data/scripts/build_index.py --embed
```

- 전처리는 미검토 행을 제외하고 HTML/중복을 정리합니다.
- 판시사항·판결요지 중심으로 저장하며 판결 전문은 저장하지 않습니다.
- `data/vector_db/precedents.sqlite3`에 판례 메타데이터, TF-IDF 벡터, 임베딩 벡터를 저장합니다.
- `--embed`는 `server/.env`의 `GEMINI_API_KEY`로 `gemini-embedding-001`(768차원) 임베딩을 함께 저장합니다. 빼면 TF-IDF만 저장하며 외부 호출이 없습니다.
- 검색은 임베딩 코사인 유사도(의미 검색)가 기본이고, 임베딩을 쓸 수 없으면 문자 2~4그램 TF-IDF로 대체합니다. 분야 내 검색만 수행합니다.
- `기타`는 검색하지 않습니다. 결과가 없으면 근거 없음 상태를 반환합니다.

## 5. RAG 실행 (Gemini)

`server/.env`를 `CONSULTATION_MODE=rag`로 바꾸고 `GEMINI_API_KEY`를 넣은 뒤 서버를 다시 시작합니다.

- `GEMINI_API_KEY`가 비어 있으면 질문은 분야별 고정 질문, 결과는 TF-IDF 검색 결과와 원문 메타데이터만 반환합니다.
- 키가 있으면 **추가 질문 생성 → 질의 임베딩 → 판례 검색 → 근거 프롬프트 구성 → Gemini 생성 → JSON/인용 ID 검증** 흐름이 실행됩니다.
- Gemini로 보내기 전에 전화번호·계좌번호·주민등록번호·이메일 형태의 문자열을 가립니다.
- 호출이 실패하거나 한도를 넘으면 1회 재시도하고, 그래도 실패하면 502 `AI_UNAVAILABLE`을 반환합니다(질문 생성은 고정 질문으로 대체).
- 근거 없음 상태에서는 생성 모델을 호출하지 않습니다. `기타`는 판례 없이 일반 정보로 답합니다.
- 답변의 인용 ID가 검색 결과에 없으면 오류로 처리합니다. 이 검증만으로 법률적 정확성을 보장하지는 않습니다.
- 자세한 내용은 `server/README.md`, `docs/api.md`.

실제 법제처 인증과 Gemini 호출은 이 환경에서 검증하지 않았습니다. 수집기는 공식 API 스키마에 맞춰 작성했으며 Gemini 연계는 가짜 클라이언트로 검증했습니다.

## 6. 설치용 Android APK 빌드

이 저장소는 **소스 프로젝트**이며 완성 APK/IPA는 포함하지 않습니다. `app/eas.json`에는 Android APK용 preview 프로필이 준비되어 있습니다.

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

## 8. 팀원 노트북 최종 확인 (2단계)

모든 노트북에서 0장 setup 스크립트를 먼저 실행합니다. 키와 판례 DB는 **1대에만** 둡니다.

**1단계: 전원 demo 모드**

1. `server/.env`는 `CONSULTATION_MODE=demo` 그대로 둡니다. 키·DB가 필요 없습니다.
2. 각자 서버를 켜고(0장) `server\.venv\Scripts\python.exe scripts\check_env.py --health`가 `mode=demo`로 통과하는지 봅니다.
3. `npx expo start --clear` → 휴대폰 Expo Go로 QR 스캔 → 상담 흐름(분야 → 상황 입력 → 추가 질문 → 결과)을 끝까지 진행합니다. 결과 화면이 뜨면 앱과 서버가 연결된 것입니다.

**2단계: 키 보유 노트북 1대만 rag, 나머지는 그 서버로 연결**

1. 서버 PC(키 보유 노트북): 받은 `.env`를 `server/.env`에 둡니다(0장, 판례 DB는 저장소에 포함). `CONSULTATION_MODE=rag`로 바꾸고 서버를 다시 시작합니다.
2. 서버 PC에서 `check_env.py --health`로 `mode=rag`, 판례 DB 있음, `GEMINI_API_KEY` 있음을 확인하고, setup 출력의 "탐지한 IPv4"(또는 `ipconfig`)를 팀원에게 알립니다.
3. 나머지 노트북: 자기 서버는 끄고, 앱 주소만 서버 PC로 바꿉니다.

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -SkipServer -SkipApp -ApiUrl http://<서버 PC IPv4>:8000
   ```

   macOS: `bash scripts/setup.sh --skip-server --skip-app --api-url http://<서버 PC IPv4>:8000`
4. `check_env.py --health`가 `mode=rag`로 통과하고 휴대폰 브라우저에서도 `http://<서버 PC IPv4>:8000/health`가 열리면, `npx expo start --clear`로 앱을 다시 시작해 상담 흐름을 진행합니다. demo 때와 달리 AI 요약이나 근거 판례가 보이면 rag 서버에 연결된 것입니다(기준 점수를 넘는 판례가 없으면 "판례 근거 없음"이 나올 수 있습니다). 이때 "응답 모드가 이 PC의 server/.env 모드와 다릅니다"라는 참고 메시지는 정상입니다.
5. 끝나면 `-ApiUrl` 없이 setup을 다시 실행해 자기 PC 주소로 돌아갑니다. 서버 PC 주소를 계속 쓰려면 다시 실행할 때 `-KeepApiUrl`을 붙입니다.

### 같은 Wi-Fi에서 안 붙을 때 (터널)

학교·공용 Wi-Fi는 기기끼리의 통신을 막는 경우가 많습니다(휴대폰 브라우저에서 `http://<PC IPv4>:8000/health`가 안 열림). 이때는 터널을 씁니다. 두 터널은 맡는 일이 다릅니다.

| 막힌 것 | 명령 | 하는 일 |
|---|---|---|
| 앱이 API 서버(8000)에 못 붙음 | `cloudflared tunnel --url http://localhost:8000` | 서버 PC의 API를 `https://<임의 이름>.trycloudflare.com`으로 공개 |
| Expo Go가 QR을 열지 못함(앱 번들을 못 받음) | `npx expo start --tunnel` | Expo 개발 서버(Metro)를 터널로 연결 |

1. 서버 PC에서 서버를 켠 채로 `cloudflared tunnel --url http://localhost:8000`을 실행하고 출력된 `https://...trycloudflare.com` 주소를 확인합니다. 설치: Windows `winget install --id Cloudflare.cloudflared`, macOS `brew install cloudflared`.
2. 앱을 실행할 PC에서 그 주소를 넣습니다: `setup.ps1 -SkipServer -SkipApp -ApiUrl https://<임의 이름>.trycloudflare.com` (macOS `--api-url`).
3. `check_env.py --health`로 터널 주소의 `/health`를 확인한 뒤 `npx expo start --tunnel --clear`로 앱을 실행합니다. SDK 58의 `--tunnel`은 기본으로 Expo 터널을 쓰며, 처음 실행할 때 안내(설치·로그인 등)가 나오면 따릅니다.

- 터널 주소는 실행할 때마다 바뀌고, 주소를 아는 누구나 접속할 수 있습니다. 개발용 API에는 인증이 없으니 확인이 끝나면 `Ctrl+C`로 끕니다. rag 서버를 열어 두면 외부 요청으로도 Gemini 사용량이 소모될 수 있습니다.
- 휴대폰 핫스팟에 PC와 휴대폰을 함께 연결하는 방법도 있습니다. 네트워크가 바뀌면 setup을 다시 실행해 IP를 갱신합니다.

## 구현 범위

- 구현: 모바일 11개 화면, Expo Router 탭/스택, 기기 저장, 사건 CRUD·체크리스트·상담 결과 보관, 첨부파일 선택 및 메타데이터 보관, HTTP API 전환, FastAPI, 수집/전처리/벡터 검색, Gemini RAG(추가 질문 생성·임베딩 검색·답변 생성).
- 체험 구현: 회원가입·로그인. 비밀번호는 실행 메모리에만 유지하며 실제 인증 서버가 아닙니다. 앱 재시작 시 체험 계정을 다시 만들어야 합니다. 저장된 프로필은 UI 표시용입니다.
- 미포함: 서버 회원인증/JWT, 계정별 사건 DB, 원본 증거 업로드, 소셜 로그인, 이메일 복구, 푸시 알림, 실제 판례 말뭉치, 모델 파일, APK/IPA.
- 사건은 이 기기의 AsyncStorage에 저장됩니다. 공용 기기에서 실제 법률상담 개인정보를 입력하지 마세요. 로그아웃해도 사건 기록은 기기에 남습니다.

자세한 화면 목록은 `docs/SCREENS.md`, API는 `docs/api.md` 및 `docs/openapi.json`, 구성도는 `docs/ARCHITECTURE.md`를 참고하세요.

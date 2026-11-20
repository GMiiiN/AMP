# AMP 회원 인증 임시 증분 (독립 실행)

이 폴더는 두 ZIP 브랜치 모두의 `server/` 하위에 **새로 추가**하는 독립 미리보기입니다.
기존 `server/app/main.py`, `server/requirements.txt`, 프론트엔드와 기존 설정을 수정하지 않습니다.
기존 앱의 로그인 화면에도 아직 연결되지 않습니다.

## 설치 (Windows PowerShell, 저장소의 server 폴더에서)

```powershell
py -m pip install -r requirements.txt
py -m pip install -r auth_preview/requirements-preview.txt
# 아래 값은 예시가 아니라 매 실행 환경에서 생성한 비밀키를 사용하세요.
$env:AMP_AUTH_JWT_SECRET = (py -c "import secrets; print(secrets.token_urlsafe(48))")
$env:AMP_AUTH_PREVIEW_AUTOSTART = "1"
py -m uvicorn auth_preview.app:app --reload --port 8001
```

- 독립 인증 Swagger: http://127.0.0.1:8001/docs
- 기존 상담 서버는 별도 창에서 기존 방식대로 8000 포트로 실행할 수 있습니다.
- 생성되는 DB: `server/auth_preview/.local/auth.sqlite3` (Git에 올리지 않음)
- 일회성 비회원 정책은 추후 프론트엔드 단계의 작업입니다. 이 미리보기는 비회원 경로에 영향을 주지 않습니다.

## API

- `POST /api/auth/register`: `{"name":"홍길동","email":"test@example.com","password":"password123"}` -> 201 사용자(비밀번호 제외)
- `POST /api/auth/login`: `{"email":"test@example.com","password":"password123"}` -> access_token
- `GET /api/users/me`: `Authorization: Bearer <access_token>` -> 본인 정보
- `GET /health`: 단독 서버 상태

## 테스트

```powershell
# server 폴더에서
py -m pip install pytest
py -m pytest auth_preview/tests -q
```

## 병합 시 주의

- **현재 ZIP의 파일을 덮어쓰지 마세요.** `auth_preview` 폴더 전체만 `server/`로 복사하세요.
- 이미 `server/auth_preview/`가 있는 경우 자동으로 덮어쓰지 말고 복사를 중단하고 변경을 비교하세요.
- 기존 FastAPI 앱에 합치는 작업은 나중에 검토합니다. 현재 서버와 URL 경로는 분리된 포트 8001에서 동작합니다.
- `AMP_AUTH_JWT_SECRET`은 32자 이상의 고난도 랜덤 키를 사용합니다. 샘플 키나 `.env.preview.example`의 안내 문자열로 실행하지 마세요.
- 실제 배포 전에는 운영용 DB, HTTPS, 토큰 폐기·재발급 정책, 사용자 탈퇴·삭제 정책, 로그인 속도 제한, DB 마이그레이션 등이 추가로 필요합니다.

# server — Python 서버

앱의 요청을 받아 상담 흐름(추가 질문 → 판례 검색 → AI 답변)을 처리합니다.

## 예정 구조

```
server/
├─ main.py          서버 진입점
├─ routers/         API 경로 (consult.py = 상담, 이후 auth.py, cases.py)
├─ services/        rag.py (판례 검색), gemini.py (AI 호출)
├─ schemas.py       요청·응답 형식
├─ requirements.txt 필요한 패키지
└─ .env.example     필요한 환경 변수 이름
```

처음에는 상담 엔드포인트 하나(`POST /consult`)만 만들고, 앱을 붙여 가며 늘립니다.
확장성·배포 구성은 지금 단계에서 고려하지 않습니다.

## 현재 구현

상세 실행 방법과 환경변수는 `docs/SETUP.md` 2~5번을 참고하세요.

이 폴더에서 `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` 실행.
테스트: `python -m unittest discover -s tests -v`.
필요 패키지: `python -m pip install -r requirements.txt`.

`.env.example` → `.env` 복사. 기본 `demo`는 외부 키 없이 동작합니다.
`rag` 모드는 data 도구로 만든 SQLite가 필요합니다. 모델 이름이 비어 있으면 검색만 하며 Ollama 모델을 지정하면 생성·인용 검증까지 실행합니다.

# server — Python 서버 (FastAPI)

앱의 요청을 받아 상담 흐름(추가 질문 → 판례 검색 → AI 답변)을 처리합니다.
기술 선정 근거는 11주차 구현 기술 확정 보고서, API 형식은 `docs/api.md`를 따릅니다.

## 구조

```
server/
├─ app/
│  ├─ main.py              진입점: 미들웨어, 오류 처리, 라우터 등록
│  ├─ config.py            환경변수 읽기
│  ├─ deps.py              의존성 주입 (구현 선택은 환경변수로)
│  ├─ errors.py            공통 오류 형식 {"error":{"code","message"}}
│  ├─ schemas.py           요청·응답 형식
│  ├─ routers/             요청 처리부
│  │  └─ consultations.py  카테고리, 추가 질문, 상담 결과
│  ├─ services/            검색·생성부
│  │  ├─ consultation.py   상담 흐름
│  │  ├─ rag.py            질의 구성·임베딩, 근거 판례 선정
│  │  ├─ gemini.py         Gemini 생성·임베딩, 1회 재시도, 응답·인용 검증
│  │  └─ privacy.py        외부 전송 전 개인정보 가림
│  └─ repositories/        저장소 (인터페이스 + 구현)
│     └─ vector_store.py   판례 색인 SQLite (임베딩 + TF-IDF)
├─ tests/                  unittest (Gemini는 가짜 클라이언트로 대체)
├─ requirements.txt
└─ .env.example
```

## 실행

Python 3.12 권장(3.11 이상 필요). 이 폴더에서:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

테스트: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

## 모드와 환경변수

| 설정 | 동작 |
|---|---|
|`CONSULTATION_MODE=demo`|외부 호출 없이 입력 내용만 정리. 키 없이 앱 개발 가능|
|`rag` + `GEMINI_API_KEY` 없음|판례 검색 결과만 반환 (질의 임베딩을 만들 수 없으므로 TF-IDF 검색)|
|`rag` + `GEMINI_API_KEY`|질문 생성 → 임베딩 검색 → Gemini 답변. 임베딩 실패 시 TF-IDF로 대체|

전체 목록과 설명은 `.env.example`을 참고하세요. 회원·인증은 계정 흐름 담당이 별도로 추가합니다.

## 판례 색인 (임베딩)

임베딩 검색을 쓰려면 색인을 `--embed`로 만들어야 합니다(저장소 루트에서):

```powershell
server/.venv/Scripts/python.exe data/scripts/build_index.py --embed
```

- 색인과 질의는 같은 임베딩 모델·차원이어야 합니다. 서버 설정과 색인이 다르면 경고를 남기고 TF-IDF로 검색합니다.
- `EMBEDDING_MIN_SCORE`(기본 0.60)는 임시값입니다. 색인 구축 후 시험 질의로 측정해 확정합니다.

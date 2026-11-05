# 상담 API

상세 실행 방법과 환경변수는 저장소 루트 README 2~5번을 참고하세요.

이 폴더에서 `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` 실행.
테스트: `python -m unittest discover -s tests -v`.
필요 패키지: `python -m pip install -r requirements.txt`.

`.env.example` → `.env` 복사. 기본 `demo`는 외부 키 없이 동작합니다.
`rag` 모드는 data 도구로 만든 SQLite가 필요합니다. 모델 이름이 비어 있으면 검색만 하며 Ollama 모델을 지정하면 생성·인용 검증까지 실행합니다.

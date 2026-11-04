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

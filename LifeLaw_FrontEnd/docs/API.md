# FastAPI 명세

개발 기본 주소 `http://127.0.0.1:8000`. Swagger UI `/docs`, 기계 판독 명세 `/openapi.json`.

| 메서드 | 경로 | 용도 |
|---|---|---|
|GET|/health|서버 상태와 설정된 모드|
|GET|/api/categories|분야 10개|
|POST|/api/consultations/questions|분야별 질문 3개|
|POST|/api/consultations/result|데모/검색/선택적 RAG 결과|

## 공통 상담 요청

```json
{"category":"임금체불","date":"2026-01-01","amount":"20000","description":"급여 지급이 지연된 예시 상황입니다.","answers":["네","아니요","자료 확인"]}
```

category는 고정 분야 중 하나, date는 오늘 이전 실제 날짜, amount는 선택 숫자 문자열(최대 12자리), description은 공백 제외 내용 필요·최대 1,000자, answers는 최대 3개·각 1,000자입니다. 정의하지 않은 필드는 422입니다. 첨부 원본과 사용자 계정 정보를 이 API로 전송하지 않습니다.

## 질문 응답

```json
{"questions":["약속한 급여와 지급일을 확인할 수 있나요?","상대방에게 상황을 알리거나 대화를 시도했나요?","지금 가장 먼저 정리하고 싶은 것은 무엇인가요?"],"mode":"template"}
```

추가 질문은 분야별 템플릿입니다. AI 동적 질문 생성은 구현하지 않았습니다.

## 결과 응답

```json
{"mode":"demo","summary":"사용자가 입력한 내용","precedents":[],"notice":"판례 근거 없음: 데모 모드에서는 AI 분석과 판례 검색을 실행하지 않습니다."}
```

- mode=`demo`: 입력 내용 정리.
- mode=`retrieval`: 실제 DB 검색 또는 근거 없음. 생성 모델 미사용.
- mode=`rag`: 실제 검색 결과를 바탕으로 Ollama 모델 응답을 검증한 결과.
- precedents 항목: `id`, `title`, `caseNumber`, `court`, `judgmentDate`, `summary`, `sourceUrl`.
- `sourceUrl`은 국가법령정보센터 HTTPS 링크입니다. 임의 링크나 인증값 포함 URL은 전처리에서 거부합니다.
- `기타`는 검색 및 모델 호출을 하지 않습니다.
- 점수 기준을 넘는 근거가 없으면 법률 결론을 생성하지 않습니다.

## 오류

```json
{"error":{"code":"VALIDATION_ERROR","message":"입력 항목과 형식을 확인해 주세요."}}
```

| 상태 | 상황 |
|---|---|
|422|입력 검증 실패, 입력 원문을 오류에 반사하지 않음|
|503|RAG DB 미구축/읽기 오류, 모드 설정 오류|
|502|모델 통신 실패, JSON 형식 오류, 검색되지 않은 인용 ID|

모바일 HTTP 제한 시간은 60초, 모델 요청은 45초입니다. API 실패를 자동 데모 성공으로 바꾸지 않고 재시도 화면을 표시합니다. 입력 데이터는 기기에 유지합니다.

## 인증 및 저장 범위

현재 인증 헤더가 없는 개발 API입니다. 회원가입/로그인/사건 CRUD/증거 업로드 API는 아직 제공하지 않습니다. 해당 UI는 체험 계정 또는 기기 저장을 사용합니다.

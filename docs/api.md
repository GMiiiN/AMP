# 서버 API 명세

개발 기본 주소 `http://127.0.0.1:8000`. Swagger UI `/docs`, 기계 판독 명세 `/openapi.json` (저장본 `docs/openapi.json`).

앱과 서버가 이 문서의 형식을 기준으로 개발합니다. 형식을 바꿀 때는 이 문서를 먼저 고치고 팀에 알립니다.

## 개요

| 메서드 | 경로 | 용도 |
|---|---|---|
|GET|/health|서버 상태와 설정된 모드|
|GET|/api/categories|분야 10개|
|POST|/api/consultations/questions|추가 질문 3개|
|POST|/api/consultations/result|상담 결과와 근거 판례|

회원·인증 API는 계정 흐름 담당(이규형)이 추가합니다. 상담 API에 인증을 붙일 때도 이 문서에 함께 적습니다.

사건·상담 기록은 기기(AsyncStorage)에 저장하므로 사건 API는 없습니다. 첨부 원본은 서버로 보내지 않습니다.

## 상담

### 공통 상담 요청

```json
{"category":"임금체불","date":"2026-01-01","amount":"20000","description":"급여 지급이 지연된 예시 상황입니다.","questions":["질문1","질문2","질문3"],"answers":["네","아니요","자료 확인"]}
```

- category는 고정 분야 중 하나, date는 오늘 이전 실제 날짜, amount는 선택 숫자 문자열(최대 12자리), description은 공백 제외 내용 필요·최대 1,000자.
- answers는 최대 3개·각 1,000자. **questions는 선택**(최대 3개)이며, 질문 API로 받은 질문을 그대로 보내면 서버가 질문과 답을 짝지어 AI에 전달합니다. 생성 질문은 매번 다르므로 결과 요청 때 보내는 것을 권장합니다.
- 정의하지 않은 필드는 422입니다. 첨부 원본과 사용자 계정 정보를 이 API로 보내지 않습니다.
- 서버는 Gemini로 보내기 전에 전화번호·계좌번호·주민등록번호·이메일 형태의 문자열을 가립니다(SER-004).

### POST /api/consultations/questions → 200

```json
{"questions":["근로계약서를 작성하셨나요?","퇴사하셨나요?","지금 가장 먼저 정리하고 싶은 것은 무엇인가요?"],"mode":"generated"}
```

- 질문은 항상 3개입니다. 1·2번은 Gemini가 상황을 보고 만든 "네/아니요" 확인 질문, 3번은 고정 질문입니다.
- `mode=generated`: AI 생성. `mode=template`: 데모 모드, AI 미설정, 또는 생성 실패 시 분야별 고정 질문. 질문 생성 실패는 오류로 돌려주지 않고 고정 질문으로 대체합니다.

### POST /api/consultations/result → 200

```json
{"mode":"rag","summary":"AI가 정리한 요약","precedents":[{"id":"...","title":"...","caseNumber":"...","court":"대법원","judgmentDate":"20200101","summary":"판결요지","sourceUrl":"https://www.law.go.kr/...","cited":true}],"notice":"법률정보 제공이며 자문이 아닙니다. AI 요약은 원문 대조 및 전문가 검토가 필요합니다.","searchMethod":"embedding"}
```

- mode=`demo`: 입력 내용 정리(외부 호출 없음). 수록 판례 90건(`data/seed/precedents90.jsonl`)에서 표현이 유사한 판례를 최대 3건 반환합니다. 기준 점수를 넘는 판례가 없으면 notice가 "판례 근거 없음"으로 시작합니다.
- mode=`retrieval`: 판례 검색 결과만 반환하거나 근거 없음. AI 미설정.
- mode=`rag`: 검색된 판례를 근거로 Gemini가 만든 답변. `precedents`에는 검색된 판례(최대 3건)를 유사도 순으로 모두 담습니다. AI 답변이 인용한 판례는 `cited: true`이며(그 밖의 모드와 판례는 `false`), 앱은 "답변에서 인용"으로 표시합니다. 앱은 첫 건을 "가장 유사한 판례", 나머지를 "비슷한 판례"로 보여 줍니다. 검색 결과에 없는 인용 ID는 거부합니다.
- `searchMethod`(선택 필드): `embedding` 의미 검색 또는 `tfidf` 문자 검색. 임베딩을 쓸 수 없으면 `tfidf`로 대체합니다. 검색을 하지 않으면 없습니다.
- `sourceUrl`은 국가법령정보센터 HTTPS 링크입니다. `judgmentDate`는 법령정보 API의 선고일자 그대로(yyyymmdd)이며 앱이 `2020.01.01` 형식으로 표시합니다.
- `기타`: 판례 검색을 하지 않습니다. rag 모드에서는 별도 모델(`GEMINI_SEARCH_MODEL`, 기본 `gemini-2.5-flash-lite`)이 Google 검색(grounding)을 참고해 답하고, 출처를 `sources`(`[{"title":"...","url":"https://..."}]`, 최대 5건)에 담습니다. `sources[].url`은 https, 호스트 있음, 사용자 정보(`user@host`) 없음 규칙으로 서버가 검증·정규화하며 앱도 같은 규칙으로 다시 검증합니다. 웹 검색이 실패하면(한도 초과 429, 모델 접근 거부 403/404, `GEMINI_SEARCH_TIMEOUT_MS`(기본 15초) 초과, 유효한 출처 없음, 빈 답변) 출처 없이 일반 법률 정보 답변으로 대체합니다. 403/404를 한 번 받으면 서버 프로세스가 도는 동안 웹 검색을 건너뜁니다. 기타 분야 응답 전체는 50초 안에 끝나도록 묶어 앱 요청 제한(60초) 안에 대체 답변이나 502가 도착합니다. 웹 검색으로 답한 경우에만 Google Search Suggestions HTML(`searchEntryPoint.renderedContent`)을 `searchSuggestionsHtml`에 담습니다. Gemini API 약관상 웹 검색 답변은 이 Search Suggestions와 함께 보여 줘야 하므로, Search Suggestions가 없는 웹 검색 응답은 실패로 보고 일반 답변으로 대체합니다. 앱은 이를 WebView로 답변 아래에 그대로 표시하고, 그 안의 링크는 외부 브라우저로 열며 그 밖의 탐색은 막습니다. 웹 출처 링크는 약관의 중간 화면 금지에 따라 확인 창 없이 바로 엽니다(판례 원문 링크는 확인 창 유지). 사건 기록에는 웹 검색 답변 텍스트만 저장하고 `sources`와 `searchSuggestionsHtml`은 저장하지 않습니다. 어느 경우든 notice가 "판례 근거 없음"으로 시작합니다. 그 밖의 경우 `sources`는 빈 배열이고 `searchSuggestionsHtml`은 응답에 없습니다.
- 기준 점수를 넘는 판례가 없으면 AI 답변을 만들지 않고 notice가 "판례 근거 없음"으로 시작합니다.
- 앱의 해야 할 일(체크 3개)·도움받을 곳은 앱의 고정 내용을 씁니다.

## 오류

```json
{"error":{"code":"VALIDATION_ERROR","message":"입력 항목과 형식을 확인해 주세요."}}
```

`message`는 사용자에게 그대로 보여 줄 수 있는 문구입니다. 오류 응답에 입력 원문을 넣지 않습니다.

| 상태 | code | 상황 |
|---|---|---|
|404|NOT_FOUND|없는 경로|
|422|VALIDATION_ERROR|입력 검증 실패|
|500|SERVER_ERROR|예상하지 못한 서버 오류|
|502|AI_UNAVAILABLE|Gemini 호출 실패(한도 초과 포함). 서버가 1회 재시도한 뒤에도 실패. 앱은 "다시 시도"를 표시|
|503|INDEX_UNAVAILABLE|판례 색인 미구축·읽기 오류|
|503|CONFIG_ERROR|서버 모드 설정 오류|

제한 시간: 앱 60초, Gemini 요청 45초(`GEMINI_TIMEOUT_MS`). API 실패를 데모 결과로 바꾸지 않고 재시도 화면을 표시합니다. 입력 데이터는 기기에 유지합니다(QUR-005).

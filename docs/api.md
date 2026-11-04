# API 명세 (초안 — 작성 필요)

앱과 서버가 이 문서의 형식을 기준으로 개발합니다. 형식을 바꿀 때는 이 문서를 먼저 고치고 팀에 알립니다.

## POST /consult

상담 한 단계를 진행합니다.

### 요청

```json
{
  "category": "",
  "situation": "",
  "answers": []
}
```

### 응답

```json
{
  "type": "question | result",
  "question": "",
  "result": {
    "summary": "",
    "precedents": []
  }
}
```

> 위 필드는 예시입니다. 팀이 확정하는 대로 고쳐 주세요.

## 이후 추가 예정

- 회원: 가입 / 로그인
- 사건: 저장 / 목록 / 상세 / 삭제

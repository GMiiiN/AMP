# data — 판례 데이터 파이프라인

국가법령정보 공동활용 오픈API(open.law.go.kr)에서 판례를 수집해 전처리한 뒤 벡터DB를 만듭니다.
상담할 때마다 도는 것이 아니라 **사전에 한 번 실행**하는 스크립트입니다.

## 예정 구조

```
data/
├─ scripts/
│  ├─ fetch_cases.py       판례 수집 (오픈API)
│  ├─ preprocess.py        판시사항·판결요지 정리, 카테고리 태깅
│  └─ build_vectordb.py    임베딩 후 벡터DB 생성
├─ raw/          수집한 원본   (깃에 올리지 않음)
├─ processed/    전처리 결과   (깃에 올리지 않음)
└─ vector_db/    판례 DB precedents.sqlite3 (깃에 포함, 그 밖의 파일은 제외)
```

## 합의된 방침

- 임베딩 대상: 판시사항 + 판결요지
- 메타데이터로 저장: 사건명, 사건번호, 법원명, 선고일자, 사건종류, 참조조문, 판례일련번호
- 판례 전문은 DB에 넣지 않고 원문 링크로만 처리
- `raw/`, `processed/`는 깃에서 제외합니다. 판례 DB `vector_db/precedents.sqlite3`(약 4.5MB)는 clone 후 바로 실행되도록 깃에 포함합니다.

## 공유 방법

- 판례 DB `data/vector_db/precedents.sqlite3`는 저장소에 들어 있습니다. `data/seed/precedents90.jsonl` 90건으로 `build_index.py --input data/seed/precedents90.jsonl --embed`를 실행해 만든 것이며 TF-IDF와 `gemini-embedding-001`(768차원) 임베딩을 함께 담고 있어, 팀원은 임베딩 API를 부르지 않고 바로 rag 모드를 쓸 수 있습니다.
- `server/.env`의 키 값(`GEMINI_API_KEY`)은 팀장이 따로 전달합니다. 깃·메신저 공개 채널·이슈에는 올리지 않습니다. `LAW_API_OC`와 `collect.py`(판례 수집)는 지금 쓰지 않습니다.
- 저장소 루트에서 `python scripts/check_env.py`(macOS는 `python3`)를 실행하면 DB 존재, 판례 건수, 임베딩 포함 여부를 확인합니다(키 값은 출력하지 않음).
- 판례를 바꿔 DB를 다시 만들었으면(`build_index.py`) 같은 경로의 파일을 PR로 올리고 `--embed` 사용 여부를 PR에 적습니다.

## 현재 구현

`docs/SETUP.md` 4번 순서를 따릅니다. Python 의존성은 `server/requirements.txt`에 모았습니다.

- `scripts/collect.py`: 공식 목록/본문 XML을 읽어 요지와 메타데이터만 JSONL로 저장. `--output` 파일은 해당 수집 실행 결과로 덮어쓰므로 분야별 파일명을 사용하세요.
- `scripts/preprocess.py`: 검토 완료(`reviewed: true`)만 채택, 중복 정리, HTML 제거, 메타데이터 검증, 전문 필드 제거. 여러 JSONL 입력을 함께 받을 수 있습니다.
- `scripts/build_index.py`: SQLite에 문서/문자 TF-IDF 벡터/모델 메타데이터를 기록. 기존 DB는 정상 구축 후 교체됩니다.

`raw/`, `processed/`의 내용은 Git에서 제외합니다(`vector_db/`는 `precedents.sqlite3`만 포함). 원본 인증 응답이나 판결 전문은 저장하지 않습니다. 수집/분류 검토 기준과 API 이용 조건은 팀이 별도로 확인해야 합니다. 실제 API 인증은 미검증입니다.

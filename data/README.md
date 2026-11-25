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
└─ vector_db/    벡터DB 파일   (깃에 올리지 않음)
```

## 합의된 방침

- 임베딩 대상: 판시사항 + 판결요지
- 메타데이터로 저장: 사건명, 사건번호, 법원명, 선고일자, 사건종류, 참조조문, 판례일련번호
- 판례 전문은 DB에 넣지 않고 원문 링크로만 처리
- `raw/`, `processed/`, `vector_db/`는 용량 때문에 깃에서 제외합니다. 공유는 아래 "공유 방법"(팀 비공개 Drive)을 따릅니다.

## 공유 방법

- 판례 DB `precedents.sqlite3`는 **팀 비공개 Drive**에서 받아 `data/vector_db/precedents.sqlite3`에 둡니다. 다른 위치에 두면 `server/.env`의 `VECTOR_DB_PATH`를 그 경로로 바꿉니다.
- `server/.env`의 키 값(`GEMINI_API_KEY`, `LAW_API_OC`)도 같은 비공개 Drive에서 받습니다. 깃·메신저·이슈에는 올리지 않고, Drive 링크는 팀원끼리만 공유합니다.
- 받은 뒤 저장소 루트에서 `python scripts/check_env.py`(macOS는 `python3`)를 실행하면 DB 존재, 판례 건수, 임베딩 포함 여부를 확인합니다(키 값은 출력하지 않음). rag 모드에는 DB가 필요하고 demo 모드에는 필요 없습니다.
- DB를 새로 만들었으면(`build_index.py`) 같은 Drive 위치에 올리고 `--embed` 사용 여부와 만든 날짜를 팀에 알립니다. `raw/`, `processed/`는 DB를 다시 만들 사람만 필요하며, 필요하면 같은 Drive 폴더에 둡니다.

## 현재 구현

`docs/SETUP.md` 4번 순서를 따릅니다. Python 의존성은 `server/requirements.txt`에 모았습니다.

- `scripts/collect.py`: 공식 목록/본문 XML을 읽어 요지와 메타데이터만 JSONL로 저장. `--output` 파일은 해당 수집 실행 결과로 덮어쓰므로 분야별 파일명을 사용하세요.
- `scripts/preprocess.py`: 검토 완료(`reviewed: true`)만 채택, 중복 정리, HTML 제거, 메타데이터 검증, 전문 필드 제거. 여러 JSONL 입력을 함께 받을 수 있습니다.
- `scripts/build_index.py`: SQLite에 문서/문자 TF-IDF 벡터/모델 메타데이터를 기록. 기존 DB는 정상 구축 후 교체됩니다.

`raw/`, `processed/`, `vector_db/`의 내용은 Git에서 제외합니다. 원본 인증 응답이나 판결 전문은 저장하지 않습니다. 수집/분류 검토 기준과 API 이용 조건은 팀이 별도로 확인해야 합니다. 실제 API 인증은 미검증입니다.

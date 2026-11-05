# 판례 데이터 도구

루트 README의 4번 순서를 따릅니다. Python 의존성은 `server/requirements.txt`에 모았습니다.

- `scripts/collect.py`: 공식 목록/본문 XML을 읽어 요지와 메타데이터만 JSONL로 저장. `--output` 파일은 해당 수집 실행 결과로 덮어쓰므로 분야별 파일명을 사용하세요.
- `scripts/preprocess.py`: 검토 완료(`reviewed: true`)만 채택, 중복 정리, HTML 제거, 메타데이터 검증, 전문 필드 제거. 여러 JSONL 입력을 함께 받을 수 있습니다.
- `scripts/build_index.py`: SQLite에 문서/문자 TF-IDF 벡터/모델 메타데이터를 기록. 기존 DB는 정상 구축 후 교체됩니다.

`raw/`, `processed/`, `vector_db/`의 내용은 Git에서 제외합니다. 원본 인증 응답이나 판결 전문은 저장하지 않습니다. 수집/분류 검토 기준과 API 이용 조건은 팀이 별도로 확인해야 합니다. 실제 API 인증은 미검증입니다.

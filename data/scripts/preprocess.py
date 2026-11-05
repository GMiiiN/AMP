import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'server'))
from app.models import CATEGORIES


def clean(value):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(str(value)))).strip()


def preprocess(paths, output):
    records, skipped = {}, 0
    for path in paths:
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get('reviewed') is not True:
                skipped += 1
                continue
            required = ['id', 'category', 'title', 'caseNumber', 'court', 'judgmentDate', 'sourceUrl']
            if any(not clean(row.get(k, '')) for k in required):
                raise ValueError('필수 메타데이터가 누락되었습니다.')
            if row['category'] not in CATEGORIES[:-1]:
                raise ValueError('카테고리를 확인하세요.')
            url = urlparse(row['sourceUrl'])
            if url.scheme != 'https' or url.hostname not in ('www.law.go.kr', 'law.go.kr') or 'OC=' in url.query.upper():
                raise ValueError('공식 HTTPS 원문 링크만 허용하며 인증값을 포함하면 안 됩니다.')
            record = {k: clean(row[k]) for k in required}
            record['summary'] = clean(row.get('summary') or row.get('issues') or '')
            if not record['summary']:
                skipped += 1
                continue
            # Only allowlisted summary fields survive; full judgment body is discarded.
            records[(record['id'], record['category'])] = record
    if not records:
        raise ValueError('검토 완료된 요지가 없습니다. reviewed=true 및 분류를 확인하세요.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records.values()), encoding='utf-8')
    print(f'{len(records)}건 정제, 미검토/빈 요지 {skipped}건 제외: {output}')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('inputs', type=Path, nargs='+')
    p.add_argument('--output', type=Path, default=ROOT / 'data/processed/precedents.jsonl')
    a = p.parse_args()
    preprocess(a.inputs, a.output)

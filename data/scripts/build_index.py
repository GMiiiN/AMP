import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'server'))
from app.vector_store import build_store

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, default=ROOT / 'data/processed/precedents.jsonl')
    p.add_argument('--output', type=Path, default=ROOT / 'data/vector_db/precedents.sqlite3')
    a = p.parse_args()
    rows = [json.loads(line) for line in a.input.read_text(encoding='utf-8').splitlines() if line.strip()]
    build_store(rows, a.output)
    print(f'{len(rows)}건 SQLite 벡터 색인 생성: {a.output}')

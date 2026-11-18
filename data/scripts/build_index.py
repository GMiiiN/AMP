"""전처리된 판례(JSONL)로 SQLite 색인을 만든다.

기본: TF-IDF 벡터만 저장 (외부 호출 없음).
--embed: gemini-embedding-001 임베딩도 함께 저장 (server/.env 의 GEMINI_API_KEY 필요).
서버는 임베딩이 있으면 의미 검색, 없거나 임베딩 API가 실패하면 TF-IDF 검색을 쓴다.
"""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'server'))
from app import config
from app.repositories.vector_store import build_store

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, default=ROOT / 'data/processed/precedents.jsonl')
    p.add_argument('--output', type=Path, default=ROOT / 'data/vector_db/precedents.sqlite3')
    p.add_argument('--embed', action='store_true', help='Gemini 임베딩을 함께 저장')
    p.add_argument('--batch-delay', type=float, default=1.0, help='임베딩 묶음 사이 대기 시간(초). 무료 한도 대응')
    a = p.parse_args()
    rows = [json.loads(line) for line in a.input.read_text(encoding='utf-8').splitlines() if line.strip()]
    embedder = None
    if a.embed:
        from app.services.gemini import GeminiService
        settings = config.gemini_settings()
        if not settings['api_key']:
            sys.exit('server/.env 에 GEMINI_API_KEY 를 설정해 주세요.')
        service = GeminiService(**settings)

        class Embedder:
            embedding_model = service.embedding_model
            dimensions = service.dimensions

            @staticmethod
            def embed_documents(texts):
                return service.embed_documents(texts, batch_delay=a.batch_delay)
        embedder = Embedder()
    build_store(rows, a.output, embedder)
    kind = f'TF-IDF + 임베딩({config.gemini_settings()["embedding_model"]})' if a.embed else 'TF-IDF'
    print(f'{len(rows)}건 SQLite 색인 생성 [{kind}]: {a.output}')

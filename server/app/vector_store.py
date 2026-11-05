"""Small-corpus SQLite vector store. TF-IDF char ngrams, cosine retrieval.
No pickle files or downloaded model are needed. Not semantic embeddings.
"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def build_store(records: list[dict], path: Path):
    if not records:
        raise ValueError('전처리된 판례가 없습니다.')
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), max_features=12000)
    matrix = vectorizer.fit_transform([f"{r['title']} {r['summary']}" for r in records]).toarray().astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.sqlite3')
    os.close(fd)
    try:
        with sqlite3.connect(temporary) as db:
            db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('CREATE TABLE documents (id TEXT, category TEXT, payload TEXT NOT NULL, vector BLOB NOT NULL, PRIMARY KEY(id, category))')
            metadata = {'vocabulary': {k: int(v) for k, v in vectorizer.vocabulary_.items()}, 'idf': vectorizer.idf_.tolist(), 'dimensions': matrix.shape[1], 'format': 1}
            db.execute('INSERT INTO metadata VALUES (?, ?)', ('model', json.dumps(metadata)))
            for record, vector in zip(records, matrix):
                db.execute('INSERT INTO documents VALUES (?, ?, ?, ?)', (record['id'], record['category'], json.dumps(record, ensure_ascii=False), vector.tobytes()))
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def search_store(path: Path, category: str, query: str, limit: int = 3, minimum_score: float = 0.12):
    if category == '기타' or not path.exists():
        return []
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        model = json.loads(db.execute("SELECT value FROM metadata WHERE key='model'").fetchone()[0])
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), vocabulary=model['vocabulary'])
        vectorizer.idf_ = np.asarray(model['idf'])
        query_vector = vectorizer.transform([query]).toarray()[0]
        scored = []
        for payload, blob in db.execute('SELECT payload, vector FROM documents WHERE category=?', (category,)):
            vector = np.frombuffer(blob, dtype=np.float32)
            score = float(np.dot(query_vector, vector))
            if score >= minimum_score:
                scored.append((score, json.loads(payload)))
        return [record for _, record in sorted(scored, key=lambda x: x[0], reverse=True)[:limit]]

"""판례 색인 저장소 (DFD D2).

SQLite 파일 하나에 판례 메타데이터, TF-IDF 벡터, 임베딩 벡터를 함께 저장한다.
- 임베딩(의미 검색)이 기본이고, 임베딩을 쓸 수 없으면 TF-IDF(문자 2~4그램)로 대체한다.
- 판례 약 1,000건 규모이므로 카테고리 안의 판례를 모두 비교한다(근사 검색 인덱스 불필요).
- 임베딩 컬럼이 없는 예전 색인 파일도 TF-IDF로 그대로 읽는다.
"""
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

SearchMethod = Literal['embedding', 'tfidf']


class DocumentEmbedder(Protocol):
    """색인 구축 때 판례 요지를 임베딩하는 객체 (services.gemini.GeminiService 가 구현)."""
    embedding_model: str
    dimensions: int

    def embed_documents(self, texts: Sequence[str]) -> list[np.ndarray]: ...


@dataclass(frozen=True)
class EmbeddingInfo:
    model: str
    dimensions: int


@dataclass
class SearchResult:
    records: list[dict]
    method: SearchMethod


class VectorStore(Protocol):
    def embedding_info(self) -> EmbeddingInfo | None: ...

    def search(self, category: str, query: str, query_embedding: np.ndarray | None = None, limit: int = 3) -> SearchResult: ...


def document_text(record: dict) -> str:
    return f"{record['title']} {record['summary']}"


def _tfidf(vocabulary=None) -> TfidfVectorizer:
    return TfidfVectorizer(analyzer='char', ngram_range=(2, 4), max_features=None if vocabulary else 12000, vocabulary=vocabulary)


def build_store(records: list[dict], path: Path, embedder: DocumentEmbedder | None = None) -> None:
    if not records:
        raise ValueError('전처리된 판례가 없습니다.')
    texts = [document_text(r) for r in records]
    vectorizer = _tfidf()
    matrix = vectorizer.fit_transform(texts).toarray().astype(np.float32)

    embeddings: list[np.ndarray | None] = [None] * len(records)
    if embedder is not None:
        # 한 판례가 여러 카테고리에 속하면 행이 여러 개이므로, id 기준으로 한 번만 임베딩한다.
        unique: dict[str, str] = {}
        for record, text in zip(records, texts):
            unique.setdefault(record['id'], text)
        vectors = embedder.embed_documents(list(unique.values()))
        if len(vectors) != len(unique):
            raise ValueError('임베딩 개수가 판례 수와 다릅니다.')
        by_id = dict(zip(unique.keys(), vectors))
        embeddings = [np.asarray(by_id[r['id']], dtype=np.float32) for r in records]

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.sqlite3')
    os.close(fd)
    try:
        # with sqlite3.connect(...) 는 커밋만 하고 연결을 닫지 않는다. Windows에서는 열린 파일을 교체할 수 없으므로 명시적으로 닫는다.
        with closing(sqlite3.connect(temporary)) as db, db:
            db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('CREATE TABLE documents (id TEXT, category TEXT, payload TEXT NOT NULL, vector BLOB NOT NULL, embedding BLOB, PRIMARY KEY(id, category))')
            model = {'vocabulary': {k: int(v) for k, v in vectorizer.vocabulary_.items()}, 'idf': vectorizer.idf_.tolist(), 'dimensions': matrix.shape[1], 'format': 2}
            db.execute('INSERT INTO metadata VALUES (?, ?)', ('model', json.dumps(model)))
            if embedder is not None:
                info = {'model': embedder.embedding_model, 'dimensions': embedder.dimensions}
                db.execute('INSERT INTO metadata VALUES (?, ?)', ('embedding', json.dumps(info)))
            for record, vector, embedding in zip(records, matrix, embeddings):
                db.execute('INSERT INTO documents VALUES (?, ?, ?, ?, ?)', (
                    record['id'], record['category'], json.dumps(record, ensure_ascii=False),
                    vector.tobytes(), None if embedding is None else embedding.tobytes()))
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class SqliteVectorStore:
    def __init__(self, path: Path, tfidf_min_score: float = 0.12, embedding_min_score: float = 0.60):
        if not path.exists():
            raise FileNotFoundError(path)
        self.path = path
        self.tfidf_min_score = tfidf_min_score
        self.embedding_min_score = embedding_min_score

    def _connect(self):
        return closing(sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True))

    def _metadata(self, db, key: str):
        row = db.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def embedding_info(self) -> EmbeddingInfo | None:
        with self._connect() as db:
            info = self._metadata(db, 'embedding')
        return EmbeddingInfo(info['model'], int(info['dimensions'])) if info else None

    def search(self, category: str, query: str, query_embedding: np.ndarray | None = None, limit: int = 3) -> SearchResult:
        if category == '기타':
            return SearchResult([], 'tfidf')
        with self._connect() as db:
            if query_embedding is not None and self._metadata(db, 'embedding'):
                return SearchResult(self._search_embedding(db, category, query_embedding, limit), 'embedding')
            return SearchResult(self._search_tfidf(db, category, query, limit), 'tfidf')

    def _search_embedding(self, db, category, query_embedding, limit):
        query = np.asarray(query_embedding, dtype=np.float32)
        query = query / (np.linalg.norm(query) or 1.0)
        rows = db.execute('SELECT payload, embedding FROM documents WHERE category=? AND embedding IS NOT NULL', (category,))
        scored = []
        for payload, blob in rows:
            vector = np.frombuffer(blob, dtype=np.float32)
            if vector.shape != query.shape:
                continue
            score = float(np.dot(query, vector))  # 저장된 벡터는 정규화되어 있으므로 내적 = 코사인 유사도
            if score >= self.embedding_min_score:
                scored.append((score, json.loads(payload)))
        return _top(scored, limit)

    def _search_tfidf(self, db, category, query, limit):
        model = self._metadata(db, 'model')
        vectorizer = _tfidf(model['vocabulary'])
        vectorizer.idf_ = np.asarray(model['idf'])
        query_vector = vectorizer.transform([query]).toarray()[0]
        scored = []
        for payload, blob in db.execute('SELECT payload, vector FROM documents WHERE category=?', (category,)):
            score = float(np.dot(query_vector, np.frombuffer(blob, dtype=np.float32)))
            if score >= self.tfidf_min_score:
                scored.append((score, json.loads(payload)))
        return _top(scored, limit)


def _top(scored: list[tuple[float, dict]], limit: int) -> list[dict]:
    return [record for _, record in sorted(scored, key=lambda x: x[0], reverse=True)[:limit]]

import unittest
from collections import Counter
from app.services.catalog import records, search_catalog
from app.repositories.vector_store import build_store, SqliteVectorStore
from pathlib import Path
from tempfile import TemporaryDirectory

class CatalogTests(unittest.TestCase):
    def test_corpus_and_seed_index(self):
        rows = records()
        self.assertEqual(len(rows), 90)
        self.assertEqual(len({r['id'] for r in rows}), 90)
        self.assertEqual(list(Counter(r['category'] for r in rows).values()), [10] * 9)
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'index.sqlite3'
            build_store(rows, path)
            for row in rows:
                hits = SqliteVectorStore(path).search(row['category'], row['title'] + ' ' + row['summary'], limit=1).records
                self.assertEqual(len(hits), 1)
                self.assertEqual(hits[0]['id'], row['id'])

    def test_irrelevant_and_empty(self):
        self.assertEqual(search_catalog('기타', '임금 급여'), [])
        self.assertEqual(search_catalog('상속', '노트북 배터리 교체'), [])
        self.assertEqual(search_catalog('중고사기', ''), [])
        self.assertEqual(len(search_catalog('중고사기', '중고나라 아이폰 판매 대금 송금')), 1)

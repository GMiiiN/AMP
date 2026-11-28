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
        self.assertTrue(search_catalog('중고사기', '중고나라 아이폰 판매 대금 송금'))

    def test_returns_top_three_above_threshold_in_order(self):
        hits = search_catalog('전세사기', '중개사가 선순위 보증금을 제대로 설명하지 않았어요')
        self.assertEqual([h['id'] for h in hits], ['613169', '160247', '613097'])
        # 기준점(0.12)을 넘는 판례가 1건뿐이면 1건만 반환한다.
        self.assertEqual([h['id'] for h in search_catalog('소음공해', '윗집 층간소음 때문에 임대차 계약 해지와 보증금 반환을 요구하고 싶습니다')], ['601889'])

    def test_seed_format(self):
        for row in records():
            # 수집 스크립트(collect.py)가 저장하는 법령정보 API 선고일자 형식(yyyymmdd)
            self.assertRegex(row['judgmentDate'], r'^\d{8}$')
            self.assertTrue(row['title'].endswith('에 관한 판례'), row['id'])
            self.assertRegex(row['summary'], r'(판례|결정례)가 있습니다\.')

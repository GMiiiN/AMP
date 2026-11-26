import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.deps import get_ai_service
from app.main import app
from app.repositories.vector_store import SqliteVectorStore, build_store
from helpers import REQUEST, FakeAI, FakeEmbedder, record


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.env = patch.dict(os.environ, {'CONSULTATION_MODE': 'demo', 'GEMINI_API_KEY': ''})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(app.dependency_overrides.clear)

    def use_ai(self, ai):
        app.dependency_overrides[get_ai_service] = lambda: ai
        return ai

    def make_index(self, records, embedder=None):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / 'index.sqlite3'
        build_store(records, path, embedder)
        return path


class DemoAndValidationTests(ApiTestCase):
    def test_demo_and_questions(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        self.assertEqual(len(self.client.get('/api/categories').json()['categories']), 10)
        questions = self.client.post('/api/consultations/questions', json=REQUEST).json()
        self.assertEqual(len(questions['questions']), 3)
        self.assertEqual(questions['mode'], 'template')
        data = self.client.post('/api/consultations/result', json=REQUEST).json()
        self.assertEqual(data['summary'], REQUEST['description'])
        self.assertEqual(len(data['precedents']), 2)
        self.assertEqual(data['mode'], 'demo')

    def test_validation_does_not_echo_input(self):
        secret = 'PRIVATE-EXAMPLE'
        response = self.client.post('/api/consultations/result', json={**REQUEST, 'category': secret})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.text)
        self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(self.client.post('/api/consultations/result', json={**REQUEST, 'date': '2999-01-01'}).status_code, 422)

    def test_unknown_route_uses_common_error_format(self):
        response = self.client.get('/api/nope')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error']['code'], 'NOT_FOUND')

    def test_missing_index_and_other(self):
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': '/nonexistent/test.sqlite3'}):
            response = self.client.post('/api/consultations/result', json=REQUEST)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()['error']['code'], 'INDEX_UNAVAILABLE')
            response = self.client.post('/api/consultations/result', json={**REQUEST, 'category': '기타'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['precedents'], [])


class RetrievalTests(ApiTestCase):
    def test_tfidf_category_filter_and_retrieval_response(self):
        path = self.make_index([record(), record('fixture-2', '교통사고')])
        store = SqliteVectorStore(path)
        self.assertEqual([r['id'] for r in store.search('임금체불', '임금 급여 지급 지연').records], ['fixture-1'])
        self.assertEqual(store.search('상속', '임금 급여 지급').records, [])
        self.assertEqual(store.search('기타', '임금 급여 지급').records, [])
        self.assertIsNone(store.embedding_info())
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': str(path)}):
            response = self.client.post('/api/consultations/result', json=REQUEST)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['mode'], 'retrieval')
            self.assertEqual(response.json()['searchMethod'], 'tfidf')
            self.assertEqual(response.json()['precedents'][0]['id'], 'fixture-1')

    def test_embedding_search_finds_meaning_and_respects_threshold(self):
        # 같은 카테고리에 주제가 다른 판례 두 건. 임베딩 검색은 의미가 가까운 것만 기준값을 넘는다.
        path = self.make_index([record('wage'), record('other', summary='부동산 매매 계약 해제')], FakeEmbedder())
        store = SqliteVectorStore(path, embedding_min_score=0.6)
        self.assertEqual(store.embedding_info().dimensions, 4)
        found = store.search('임금체불', '아무 문자열', FakeEmbedder().embed_documents(['임금'])[0])
        self.assertEqual(found.method, 'embedding')
        self.assertEqual([r['id'] for r in found.records], ['wage'])

    def test_rag_flow_with_embedding_and_citation_filter(self):
        path = self.make_index([record('wage'), record('wage-2'), record('wage-3'), record('wage-4')], FakeEmbedder())
        ai = self.use_ai(FakeAI(cite=['wage']))
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': str(path)}):
            data = self.client.post('/api/consultations/result', json=REQUEST).json()
        self.assertEqual(data['mode'], 'rag')
        self.assertEqual(data['searchMethod'], 'embedding')
        self.assertEqual(data['summary'], 'AI 요약')
        self.assertEqual([p['id'] for p in data['precedents']], ['wage', 'wage-2', 'wage-3'])
        self.assertEqual(len(ai.calls[-1][2]), 1)
        self.assertIn('자문이 아닙니다', data['notice'])
        self.assertEqual([c[0] for c in ai.calls], ['embed', 'answer'])

    def test_embedding_failure_falls_back_to_tfidf(self):
        path = self.make_index([record()], FakeEmbedder())
        self.use_ai(FakeAI(fail_embed=True))
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': str(path)}):
            data = self.client.post('/api/consultations/result', json=REQUEST).json()
        self.assertEqual(data['searchMethod'], 'tfidf')
        self.assertEqual(data['mode'], 'rag')

    def test_answer_failure_returns_retry_error(self):
        path = self.make_index([record()])
        self.use_ai(FakeAI(fail_generate=True))
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': str(path)}):
            response = self.client.post('/api/consultations/result', json=REQUEST)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['error']['code'], 'AI_UNAVAILABLE')

    def test_no_match_does_not_call_generation(self):
        path = self.make_index([record(category='교통사고')])
        ai = self.use_ai(FakeAI())
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': str(path)}):
            data = self.client.post('/api/consultations/result', json=REQUEST).json()
        self.assertEqual(data['precedents'], [])
        self.assertTrue(data['notice'].startswith('판례 근거 없음'))
        self.assertNotIn('answer', [c[0] for c in ai.calls])

    def test_other_category_general_answer_without_search(self):
        ai = self.use_ai(FakeAI())
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': '/nonexistent/test.sqlite3'}):
            data = self.client.post('/api/consultations/result', json={**REQUEST, 'category': '기타'}).json()
        self.assertEqual(data['summary'], '일반 안내')
        self.assertEqual(data['precedents'], [])
        self.assertTrue(data['notice'].startswith('판례 근거 없음'))
        self.assertEqual([c[0] for c in ai.calls], ['general'])


class QuestionTests(ApiTestCase):
    def test_generated_questions_keep_fixed_third(self):
        ai = self.use_ai(FakeAI())
        data = self.client.post('/api/consultations/questions', json={**REQUEST, 'description': '연락처 010-1234-5678 로 받았어요'}).json()
        self.assertEqual(data['mode'], 'generated')
        self.assertEqual(data['questions'][2], '지금 가장 먼저 정리하고 싶은 것은 무엇인가요?')
        sent = ai.calls[0][1]
        self.assertNotIn('010-1234-5678', json.dumps(sent, ensure_ascii=False))

    def test_question_generation_failure_uses_template(self):
        self.use_ai(FakeAI(fail_generate=True))
        data = self.client.post('/api/consultations/questions', json=REQUEST).json()
        self.assertEqual(data['mode'], 'template')
        self.assertEqual(data['questions'][0], '약속한 급여와 지급일을 확인할 수 있나요?')

    def test_questions_are_paired_with_answers(self):
        path = self.make_index([record()])
        ai = self.use_ai(FakeAI())
        body = {**REQUEST, 'questions': ['계약서를 받으셨나요?'], 'answers': ['아니요']}
        with patch.dict(os.environ, {'CONSULTATION_MODE': 'rag', 'VECTOR_DB_PATH': str(path)}):
            self.client.post('/api/consultations/result', json=body)
        situation = ai.calls[-1][1]
        self.assertEqual(situation['followUp'], [{'question': '계약서를 받으셨나요?', 'answer': '아니요'}])


class DataScriptTests(unittest.TestCase):
    def test_preprocess_strips_full_body_and_skips_unreviewed(self):
        script = Path(__file__).resolve().parents[2] / 'data/scripts/preprocess.py'
        spec = importlib.util.spec_from_file_location('preprocess', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            input = Path(folder) / 'input.jsonl'
            output = Path(folder) / 'output.jsonl'
            input.write_text(json.dumps({**record(), 'reviewed': True, '판례내용': 'DO NOT STORE'}) + '\n' + json.dumps({**record('skip'), 'reviewed': False}), encoding='utf-8')
            module.preprocess([input], output)
            content = output.read_text(encoding='utf-8')
            self.assertNotIn('DO NOT STORE', content)
            self.assertNotIn('skip', content)


if __name__ == '__main__':
    unittest.main()

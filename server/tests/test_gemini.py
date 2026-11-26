"""GeminiService 단위 시험. 실제 API 대신 가짜 클라이언트를 넣어 한도를 쓰지 않는다."""
import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import numpy as np
from google.genai import errors

from app.services.gemini import AiUnavailable, GeminiService
from helpers import record


def text_response(payload):
    return SimpleNamespace(text=json.dumps(payload, ensure_ascii=False))


def quota_error():
    return errors.ClientError(429, {'error': {'code': 429, 'message': 'quota', 'status': 'RESOURCE_EXHAUSTED'}})


def service(generate=None, embed=None):
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(side_effect=generate)
    client.aio.models.embed_content = AsyncMock(side_effect=embed)
    return GeminiService('unused', 'test-model', dimensions=3, retry_delay=0, client=client, search_model='search-model'), client


def client_error(code, status):
    return errors.ClientError(code, {'error': {'code': code, 'message': status, 'status': status}})


def grounded_response(text, uris):
    chunks = [SimpleNamespace(web=SimpleNamespace(uri=uri, title=f'title-{i}', domain=None)) for i, uri in enumerate(uris)]
    return SimpleNamespace(text=text, candidates=[SimpleNamespace(grounding_metadata=SimpleNamespace(grounding_chunks=chunks))])


class GeminiServiceTests(unittest.TestCase):
    def test_retries_once_after_quota_error(self):
        ai, client = service(generate=[quota_error(), text_response({'summary': '요약', 'citedIds': ['fixture-1']})])
        answer = asyncio.run(ai.generate_answer({}, [record()]))
        self.assertEqual(answer.citedIds, ['fixture-1'])
        self.assertEqual(client.aio.models.generate_content.await_count, 2)

    def test_unknown_citation_rejected_after_retry(self):
        bad = text_response({'summary': '요약', 'citedIds': ['invented']})
        ai, client = service(generate=[bad, bad])
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_answer({}, [record()]))
        self.assertEqual(client.aio.models.generate_content.await_count, 2)

    def test_evidence_sent_without_source_url_or_case_number(self):
        ai, client = service(generate=[text_response({'summary': '요약', 'citedIds': ['fixture-1']})])
        asyncio.run(ai.generate_answer({'description': '상황'}, [record()]))
        sent = json.loads(client.aio.models.generate_content.await_args.kwargs['contents'])
        self.assertEqual(set(sent['precedents'][0]), {'id', 'title', 'court', 'judgmentDate', 'summary'})

    def test_questions_must_be_two_distinct(self):
        ai, _ = service(generate=[text_response({'questions': ['같은 질문인가요?', '같은 질문인가요?']}),
                                  text_response({'questions': ['첫 질문인가요?', '둘째 질문인가요?']})])
        self.assertEqual(asyncio.run(ai.generate_questions({})), ['첫 질문인가요?', '둘째 질문인가요?'])

    def test_embed_query_normalizes_and_checks_dimensions(self):
        ok = SimpleNamespace(embeddings=[SimpleNamespace(values=[3.0, 4.0, 0.0])])
        ai, _ = service(embed=[ok])
        vector = asyncio.run(ai.embed_query('질의'))
        self.assertTrue(np.allclose(vector, [0.6, 0.8, 0.0]))
        wrong = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0, 0.0])])
        ai, _ = service(embed=[wrong, wrong])
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.embed_query('질의'))



class SearchAnswerTests(unittest.TestCase):
    """기타 분야 웹 검색: 성공하면 출처를 담고, 실패·한도 초과·접근 거부는 재시도 없이 AiUnavailable(일반 답변으로 대체)."""

    def test_success_uses_search_model_with_google_search_and_returns_sources(self):
        uris = ['https://a.example/1', 'https://a.example/1', 'http://plain.example', 'https://b.example/2']
        ai, client = service(generate=[grounded_response(' 안내 ', uris)])
        answer = asyncio.run(ai.generate_search_answer({'description': '상황'}))
        self.assertEqual(answer.summary, '안내')
        self.assertEqual([s.url for s in answer.sources], ['https://a.example/1', 'https://b.example/2'])
        kwargs = client.aio.models.generate_content.await_args.kwargs
        self.assertEqual(kwargs['model'], 'search-model')
        self.assertIsNotNone(kwargs['config'].tools[0].google_search)

    def test_answer_without_grounding_sources_is_failure(self):
        ai, _ = service(generate=[grounded_response('안내', [])])
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_search_answer({}))

    def test_quota_and_access_errors_fail_without_retry(self):
        for error in (quota_error(), client_error(403, 'PERMISSION_DENIED'), client_error(404, 'NOT_FOUND'),
                      errors.ServerError(500, {'error': {'code': 500, 'message': 'x', 'status': 'INTERNAL'}})):
            with self.subTest(code=error.code):
                ai, client = service(generate=[error])
                with self.assertRaises(AiUnavailable):
                    asyncio.run(ai.generate_search_answer({}))
                self.assertEqual(client.aio.models.generate_content.await_count, 1)


if __name__ == '__main__':
    unittest.main()

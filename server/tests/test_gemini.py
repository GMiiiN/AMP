"""GeminiService 단위 시험. 실제 API 대신 가짜 클라이언트를 넣어 한도를 쓰지 않는다."""
import asyncio
import json
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import numpy as np
from google.genai import errors, types

from app.services.gemini import (EMBED_QUERY_BUDGET_SECONDS, GENERATE_BUDGET_SECONDS, AiUnavailable, GeminiService,
                                 normalize_web_url)
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


SUGGESTIONS_HTML = '<style>.chip{}</style><div class="chip"><a href="https://www.google.com/search?q=x">x</a></div>'


def grounded_response(text, uris, suggestions=SUGGESTIONS_HTML):
    """실제 SDK 응답 타입(google.genai.types)으로 grounding 응답을 만든다."""
    chunks = [types.GroundingChunk(web=types.GroundingChunkWeb(uri=uri, title=f'title-{i}')) for i, uri in enumerate(uris)]
    entry = types.SearchEntryPoint(rendered_content=suggestions) if suggestions is not None else None
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(role='model', parts=[types.Part(text=text)]),
        grounding_metadata=types.GroundingMetadata(grounding_chunks=chunks, search_entry_point=entry))])


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



class TimeBudgetTests(unittest.TestCase):
    """Gemini가 응답하지 않아도 재시도 포함 전체 대기가 상한 안에 끝나 대체 응답을 앱 제한(60초) 안에 줄 수 있다."""

    def test_budgets_fit_app_limit(self):
        # 상담 결과 요청은 질의 임베딩 → 답변 생성을 차례로 부른다. 앱 제한 60초보다 여유 있게 작아야 한다.
        self.assertLessEqual(EMBED_QUERY_BUDGET_SECONDS + GENERATE_BUDGET_SECONDS, 55)

    def test_hanging_generate_stops_at_budget(self):
        async def hang(**kwargs):
            await asyncio.sleep(10)
        ai, client = service(generate=hang)
        ai.generate_budget = 0.05
        started = time.monotonic()
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_questions({}))
        self.assertLess(time.monotonic() - started, 0.5)

    def test_slow_first_attempt_leaves_time_for_retry(self):
        calls = []

        async def first_slow(**kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise quota_error()
            return text_response({'questions': ['첫 질문인가요?', '둘째 질문인가요?']})
        ai, _ = service(generate=first_slow)
        ai.generate_budget = 1
        self.assertEqual(len(asyncio.run(ai.generate_questions({}))), 2)

    def test_retry_delay_never_exceeds_budget(self):
        # 1차 시도가 예산을 다 쓰면 재시도 대기(retry_delay)를 하지 않고 바로 끝내야 한다.
        async def hang(**kwargs):
            await asyncio.sleep(10)
        for kind in ('generate', 'embed'):
            with self.subTest(kind=kind):
                ai, client = service(**{kind: hang})
                ai.retry_delay = 1
                ai.generate_budget = ai.embed_query_budget = 0.05
                call = ai.generate_questions({}) if kind == 'generate' else ai.embed_query('질의')
                started = time.monotonic()
                with self.assertRaises(AiUnavailable):
                    asyncio.run(call)
                self.assertLess(time.monotonic() - started, 0.5)
                method = client.aio.models.generate_content if kind == 'generate' else client.aio.models.embed_content
                self.assertEqual(method.await_count, 1)

    def test_retry_skipped_when_delay_would_pass_deadline(self):
        # 1차가 빨리 실패해도 남은 시간이 retry_delay 이하면 재시도하지 않는다.
        ai, client = service(generate=[quota_error(), text_response({'questions': ['첫 질문인가요?', '둘째 질문인가요?']})])
        ai.retry_delay = 1
        ai.generate_budget = 0.5
        started = time.monotonic()
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_questions({}))
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertEqual(client.aio.models.generate_content.await_count, 1)

    def test_hanging_embed_query_stops_at_budget(self):
        async def hang(**kwargs):
            await asyncio.sleep(10)
        ai, _ = service(embed=hang)
        ai.embed_query_budget = 0.05
        started = time.monotonic()
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.embed_query('질의'))
        self.assertLess(time.monotonic() - started, 0.5)


class SearchAnswerTests(unittest.TestCase):
    """기타 분야 웹 검색: 성공하면 출처를 담고, 실패·한도 초과·접근 거부는 재시도 없이 AiUnavailable(일반 답변으로 대체)."""

    def test_success_uses_search_model_with_google_search_and_returns_sources(self):
        uris = ['https://a.example/1', 'https://a.example/1', 'http://plain.example', 'HTTPS://B.Example/2',
                'https://law.go.kr@evil.example/x', 'https://']
        ai, client = service(generate=[grounded_response(' 안내 ', uris)])
        answer = asyncio.run(ai.generate_search_answer({'description': '상황'}))
        self.assertEqual(answer.summary, '안내')
        self.assertEqual([s.url for s in answer.sources], ['https://a.example/1', 'https://b.example/2'])
        self.assertEqual(answer.sources[0].title, 'title-0')
        self.assertEqual(answer.suggestionsHtml, SUGGESTIONS_HTML)
        kwargs = client.aio.models.generate_content.await_args.kwargs
        self.assertEqual(kwargs['model'], 'search-model')
        self.assertIsNotNone(kwargs['config'].tools[0].google_search)

    def test_answer_without_search_suggestions_is_failure(self):
        for suggestions in (None, '   '):
            with self.subTest(suggestions=suggestions):
                ai, _ = service(generate=[grounded_response('안내', ['https://a.example/1'], suggestions)])
                with self.assertRaises(AiUnavailable):
                    asyncio.run(ai.generate_search_answer({}))

    def test_answer_without_grounding_sources_is_failure(self):
        ai, _ = service(generate=[grounded_response('안내', [])])
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_search_answer({}))

    def test_only_invalid_sources_is_failure(self):
        bad_uri = types.GroundingChunk.model_construct(web=types.GroundingChunkWeb.model_construct(uri=123, title='x'))
        response = grounded_response('안내', ['https://law.go.kr@evil.example/x', 'https://', 'http://plain.example'])
        response.candidates[0].grounding_metadata.grounding_chunks.append(bad_uri)
        ai, _ = service(generate=[response])
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_search_answer({}))

    def test_blank_summary_is_failure(self):
        ai, _ = service(generate=[grounded_response('   ', ['https://a.example/1'])])
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_search_answer({}))

    def test_timeout_is_failure(self):
        async def slow(**kwargs):
            await asyncio.sleep(1)
        ai, client = service()
        client.aio.models.generate_content = AsyncMock(side_effect=slow)
        ai.search_timeout = 0.01
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_search_answer({}))

    def test_access_denied_skips_search_for_the_process(self):
        for code, status in ((403, 'PERMISSION_DENIED'), (404, 'NOT_FOUND')):
            with self.subTest(code=code):
                ai, client = service(generate=[client_error(code, status)])
                for _ in range(2):
                    with self.assertRaises(AiUnavailable):
                        asyncio.run(ai.generate_search_answer({}))
                self.assertEqual(client.aio.models.generate_content.await_count, 1)

    def test_quota_error_does_not_block_next_search(self):
        ai, client = service(generate=[quota_error(), grounded_response('안내', ['https://a.example/1'])])
        with self.assertRaises(AiUnavailable):
            asyncio.run(ai.generate_search_answer({}))
        self.assertEqual(asyncio.run(ai.generate_search_answer({})).summary, '안내')

    def test_normalize_web_url(self):
        self.assertEqual(normalize_web_url('HTTPS://Example.COM/Path?q=1'), 'https://example.com/Path?q=1')
        self.assertEqual(normalize_web_url('https://example.com:8443/a'), 'https://example.com:8443/a')
        for bad in ('https://', 'http://example.com', 'https://user@example.com', 'https://law.go.kr@evil.example/x',
                    'https://example.com:99999', 'javascript:alert(1)', None, 123):
            with self.subTest(bad=bad):
                self.assertIsNone(normalize_web_url(bad))

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

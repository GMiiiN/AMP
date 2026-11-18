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
    return GeminiService('unused', 'test-model', dimensions=3, retry_delay=0, client=client), client


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


if __name__ == '__main__':
    unittest.main()

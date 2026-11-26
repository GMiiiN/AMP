"""테스트 공용 도구. 외부 API(Gemini)는 호출하지 않는다."""
import numpy as np

from app.schemas import GeneralAnswer, GeneratedAnswer, SearchAnswer, WebSource
from app.services.gemini import AiUnavailable

REQUEST = {'category': '임금체불', 'date': '2026-01-01', 'amount': '20000', 'description': '임금 급여 지급이 지연되었습니다', 'answers': ['네']}


# Synthetic records ONLY for unit testing; never shipped as a production corpus.
def record(id='fixture-1', category='임금체불', summary='임금 급여 지급 지연 자료 확인 테스트'):
    return {'id': id, 'category': category, 'title': '테스트용 급여 자료', 'caseNumber': 'TEST-NOT-A-CASE', 'court': '테스트 법원',
            'judgmentDate': '2026-01-01', 'summary': summary, 'sourceUrl': 'https://www.law.go.kr/precInfoP.do?precSeq=0'}


def topic_vector(text: str) -> np.ndarray:
    """'임금'이 들어가면 축 0, 아니면 축 1 방향인 4차원 단위 벡터."""
    return np.array([1, 0, 0, 0] if '임금' in text else [0, 1, 0, 0], dtype=np.float32)


class FakeEmbedder:
    embedding_model = 'gemini-embedding-001'
    dimensions = 4

    def embed_documents(self, texts):
        return [topic_vector(t) for t in texts]


class FakeAI:
    """GeminiService 와 같은 메서드를 가진 가짜 AI."""
    embedding_model = 'gemini-embedding-001'
    dimensions = 4

    def __init__(self, fail_generate=False, fail_embed=False, cite=None, fail_search=False):
        self.fail_generate = fail_generate
        self.fail_search = fail_search
        self.fail_embed = fail_embed
        self.cite = cite
        self.calls = []

    async def generate_questions(self, situation):
        self.calls.append(('questions', situation))
        if self.fail_generate:
            raise AiUnavailable()
        return ['계약서를 받으셨나요?', '퇴사하셨나요?']

    async def generate_answer(self, situation, precedents):
        self.calls.append(('answer', situation, precedents))
        if self.fail_generate:
            raise AiUnavailable()
        return GeneratedAnswer(summary='AI 요약', citedIds=self.cite or [precedents[0]['id']])

    async def generate_search_answer(self, situation):
        self.calls.append(('search', situation))
        if self.fail_search:
            raise AiUnavailable()
        return SearchAnswer(summary='웹 검색 안내', sources=[WebSource(title='example.go.kr', url='https://example.go.kr/guide')])

    async def generate_general_answer(self, situation):
        self.calls.append(('general', situation))
        if self.fail_generate:
            raise AiUnavailable()
        return GeneralAnswer(summary='일반 안내')

    async def embed_query(self, text):
        self.calls.append(('embed', text))
        if self.fail_embed:
            raise AiUnavailable()
        return topic_vector(text)

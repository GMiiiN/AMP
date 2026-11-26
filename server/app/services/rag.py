"""검색·생성부: 질의 구성, 질의 임베딩, 근거 판례 선정 (SFR-012, DFD 4.0)."""
import logging

from starlette.concurrency import run_in_threadpool

from ..repositories.vector_store import SearchResult, VectorStore
from ..schemas import ConsultationRequest
from .gemini import AiUnavailable, GeminiService
from .privacy import mask_text

logger = logging.getLogger('lifelaw')


def query_text(request: ConsultationRequest) -> str:
    """사용자가 작성한 상황 설명으로 구성한 검색 질의. 외부 임베딩 API로 가므로 개인정보를 가린다."""
    return mask_text(request.description.strip())


def situation_payload(request: ConsultationRequest) -> dict:
    """생성형 AI에 보낼 상황 정보. 첨부자료와 계정 정보는 포함하지 않는다(DAR-005)."""
    if request.questions:
        follow_up = [{'question': mask_text(q), 'answer': mask_text(a)} for q, a in zip(request.questions, request.answers)]
    else:
        follow_up = [{'answer': mask_text(a)} for a in request.answers]
    return {
        'category': request.category,
        'date': request.date.isoformat(),
        'amount': f'{request.amount}원' if request.amount else None,
        'description': mask_text(request.description),
        'followUp': follow_up,
    }


async def retrieve(request: ConsultationRequest, store: VectorStore, ai: GeminiService | None) -> SearchResult:
    query = query_text(request)
    embedding = None
    info = await run_in_threadpool(store.embedding_info)
    if ai is not None and info is not None:
        if (info.model, info.dimensions) != (ai.embedding_model, ai.dimensions):
            # 판례와 질의는 같은 모델·차원이어야 한다. 다르면 색인을 다시 만들어야 하므로 TF-IDF로 대체한다.
            logger.warning('embedding model mismatch index=%s/%d server=%s/%d', info.model, info.dimensions, ai.embedding_model, ai.dimensions)
        else:
            try:
                embedding = await ai.embed_query(query)
            except AiUnavailable:
                logger.warning('query embedding unavailable, falling back to tfidf')
    return await run_in_threadpool(store.search, request.category, query, embedding, 3)

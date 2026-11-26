"""상담 흐름: 추가 질문 → 근거 판례 검색 → 답변 생성 (DFD 3.0~5.0)."""
import asyncio
import logging
import sqlite3
import time
from typing import Callable

from ..errors import ApiError, ai_unavailable
from ..repositories.vector_store import VectorStore
from ..schemas import (CATEGORIES, FIRST_QUESTIONS, SECOND_QUESTION, THIRD_QUESTION, ConsultationRequest,
                       ConsultationResult, Precedent, QuestionsResponse)
from . import rag
from .catalog import search_catalog
from .gemini import AiUnavailable, GeminiService

logger = logging.getLogger('lifelaw')

NOTICE = '법률정보 제공이며 자문이 아닙니다.'
# 기타 분야는 웹 검색 → (실패 시) 일반 답변을 차례로 부르므로, 앱 요청 제한(60초) 안에 응답이 닿도록 전체 시간을 묶는다.
OTHER_CATEGORY_BUDGET_SECONDS = 50
AI_NOTICE = 'AI 요약은 원문 대조 및 전문가 검토가 필요합니다.'


def template_questions(category: str) -> list[str]:
    return [FIRST_QUESTIONS[CATEGORIES.index(category)], SECOND_QUESTION, THIRD_QUESTION]


async def make_questions(request: ConsultationRequest, ai: GeminiService | None) -> QuestionsResponse:
    """1·2번은 상황을 보고 생성, 3번은 고정. 생성에 실패하면 분야별 고정 질문을 쓴다(보고서 8장)."""
    if ai is not None:
        try:
            generated = await ai.generate_questions(rag.situation_payload(request))
            return QuestionsResponse(questions=[*generated, THIRD_QUESTION], mode='generated')
        except AiUnavailable:
            logger.warning('question generation unavailable, using template')
    return QuestionsResponse(questions=template_questions(request.category), mode='template')


async def make_result(request: ConsultationRequest, mode: str, ai: GeminiService | None,
                      open_store: Callable[[], VectorStore]) -> ConsultationResult:
    if mode not in ('demo', 'rag'):
        raise ApiError(503, 'CONFIG_ERROR', '서버 모드 설정을 확인해 주세요.')
    if request.category == '기타':
        return await _other_category(request, mode, ai)
    if mode == 'demo':
        found = search_catalog(request.category, request.description)
        notice = ('수록 판례 90건에서 표현이 유사한 판례를 최대 3건 검색합니다. AI 분석은 포함되지 않습니다.' if found else
                  '판례 근거 없음: 수록 판례 90건에서 기준 점수를 넘는 동일 분야 판례를 찾지 못했습니다. AI 분석은 포함되지 않습니다.')
        return ConsultationResult(mode='demo', summary=request.description, precedents=[Precedent(**r) for r in found], notice=notice)

    try:
        store = open_store()
    except FileNotFoundError:
        raise ApiError(503, 'INDEX_UNAVAILABLE', '판례 검색 DB가 없습니다. 수집·전처리·색인 구축을 먼저 실행해 주세요.') from None
    try:
        found = await rag.retrieve(request, store, ai)
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        raise ApiError(503, 'INDEX_UNAVAILABLE', '판례 검색 DB를 읽지 못했습니다. 색인을 다시 구축해 주세요.') from None

    if not found.records:
        return ConsultationResult(mode='retrieval', summary=request.description, searchMethod=found.method,
                                  notice='판례 근거 없음: 기준 점수를 넘는 동일 분야 판례를 찾지 못했습니다. 법적 결론을 생성하지 않습니다.')
    if ai is None:
        basis = '내용이 비슷한' if found.method == 'embedding' else '문자열 표현이 유사한'
        return ConsultationResult(
            mode='retrieval', searchMethod=found.method, precedents=[Precedent(**r) for r in found.records],
            summary=f'입력한 상황과 {basis} 판례 요지를 찾았습니다. 사건에 그대로 적용된다는 의미는 아닙니다. 아래 원문과 사실관계 차이를 확인해 주세요.',
            notice=f'{NOTICE} AI 미설정: 검색 결과만 제공합니다.')

    try:
        answer = await ai.generate_answer(rag.situation_payload(request), found.records)
    except AiUnavailable:
        raise ai_unavailable() from None
    # 화면은 유사도 순으로 '가장 유사한 판례' 1건과 '비슷한 판례'를 함께 보여 주므로 검색된 판례를 모두 돌려주고,
    # AI 답변이 인용한 판례에는 cited 를 표시한다. 인용 ID는 generate_answer 에서 검색된 판례 안에 있는지 이미 검증한다.
    return ConsultationResult(mode='rag', summary=answer.summary, searchMethod=found.method,
                              precedents=[Precedent(**r, cited=r['id'] in answer.citedIds) for r in found.records],
                              notice=f'{NOTICE} {AI_NOTICE}')


async def _other_category(request: ConsultationRequest, mode: str, ai: GeminiService | None) -> ConsultationResult:
    """기타 분야: 판례 검색 없이 Google 검색(grounding)을 참고해 답하고 출처를 함께 준다. 웹 검색이 실패하면
    (한도 초과·모델 접근 거부 포함) 일반 법률 정보 답변으로 대체한다. 어느 쪽이든 '판례 근거 없음'을 표시한다(SFR-004, SFR-012, INR-004)."""
    if mode == 'demo' or ai is None:
        return ConsultationResult(mode='demo' if mode == 'demo' else 'retrieval', summary=request.description,
                                  notice='판례 근거 없음: 기타 분야는 판례 검색에서 제외되며 현재는 입력 내용을 정리합니다.')
    situation = rag.situation_payload(request)  # 개인정보를 가린 상황 정보
    started = time.monotonic()
    try:
        found = await ai.generate_search_answer(situation)
        return ConsultationResult(mode='rag', summary=found.summary, sources=found.sources,
                                  notice=f'판례 근거 없음: 기타 분야는 판례 검색 없이 Google 검색 결과를 참고해 안내합니다. '
                                         f'출처 링크의 내용을 직접 확인해 주세요. {NOTICE} {AI_NOTICE}')
    except AiUnavailable:
        logger.warning('web search answer unavailable, using general answer')
    remaining = OTHER_CATEGORY_BUDGET_SECONDS - (time.monotonic() - started)
    try:
        answer = await asyncio.wait_for(ai.generate_general_answer(situation), timeout=max(remaining, 1))
    except (AiUnavailable, asyncio.TimeoutError):
        raise ai_unavailable() from None
    return ConsultationResult(mode='rag', summary=answer.summary,
                              notice=f'판례 근거 없음: 기타 분야는 판례 검색 없이 일반 법률 정보로 안내합니다. {NOTICE} {AI_NOTICE}')

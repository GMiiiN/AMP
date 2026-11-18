"""요청 처리부: 카테고리·상담 API."""
from typing import Callable

from fastapi import APIRouter, Depends

from .. import config
from ..deps import get_ai_service, get_store_opener
from ..repositories.vector_store import VectorStore
from ..schemas import CATEGORIES, ConsultationRequest, ConsultationResult, QuestionsResponse
from ..services import consultation
from ..services.gemini import GeminiService

router = APIRouter(prefix='/api', tags=['consultations'])


@router.get('/categories')
def categories():
    return {'categories': CATEGORIES}


@router.post('/consultations/questions', response_model=QuestionsResponse)
async def questions(request: ConsultationRequest, ai: GeminiService | None = Depends(get_ai_service)):
    return await consultation.make_questions(request, ai)


@router.post('/consultations/result', response_model=ConsultationResult, response_model_exclude_none=True)
async def result(request: ConsultationRequest, ai: GeminiService | None = Depends(get_ai_service),
                 open_store: Callable[[], VectorStore] = Depends(get_store_opener)):
    return await consultation.make_result(request, config.consultation_mode(), ai, open_store)

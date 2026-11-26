"""의존성 주입 (DIP). 라우터는 인터페이스만 받고, 실제 구현은 여기서 환경변수로 고른다.
테스트는 app.dependency_overrides 로 가짜 구현을 넣는다."""
from functools import lru_cache
from typing import Callable

from . import config
from .repositories.vector_store import SqliteVectorStore, VectorStore
from .services.gemini import GeminiService


@lru_cache(maxsize=4)
def _gemini(api_key: str, model: str, embedding_model: str, dimensions: int, timeout_ms: int, retry_delay: float,
            search_model: str, search_timeout_ms: int) -> GeminiService:
    return GeminiService(api_key, model, embedding_model, dimensions, timeout_ms, retry_delay,
                         search_model=search_model, search_timeout_ms=search_timeout_ms)


def get_ai_service() -> GeminiService | None:
    """rag 모드이고 GEMINI_API_KEY 가 있을 때만 AI를 쓴다. demo 모드는 외부 호출을 하지 않는다."""
    if config.consultation_mode() != 'rag':
        return None
    settings = config.gemini_settings()
    if not settings['api_key']:
        return None
    return _gemini(**settings)


def get_store_opener() -> Callable[[], VectorStore]:
    def open_store() -> VectorStore:
        thresholds = config.search_thresholds()
        return SqliteVectorStore(config.vector_db_path(), thresholds['tfidf'], thresholds['embedding'])
    return open_store

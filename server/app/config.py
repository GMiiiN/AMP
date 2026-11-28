"""환경변수 읽기. 테스트에서 os.environ을 바꿔도 반영되도록 매번 읽는다."""
import os
from pathlib import Path

from dotenv import load_dotenv

SERVER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVER_ROOT.parent
load_dotenv(SERVER_ROOT / '.env')


def env(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


def env_float(name: str, default: float) -> float:
    try:
        return float(env(name) or default)
    except ValueError:
        return default


def env_int(name: str, default: int) -> int:
    try:
        return int(env(name) or default)
    except ValueError:
        return default


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def consultation_mode() -> str:
    return env('CONSULTATION_MODE', 'demo')


def vector_db_path() -> Path:
    return repo_path(env('VECTOR_DB_PATH', 'data/vector_db/precedents.sqlite3'))


def gemini_settings() -> dict:
    return {
        'api_key': env('GEMINI_API_KEY'),
        'model': env('GEMINI_MODEL', 'gemini-3.8-flash'),
        'embedding_model': env('GEMINI_EMBEDDING_MODEL', 'gemini-embedding-001'),
        'dimensions': env_int('GEMINI_EMBEDDING_DIMENSIONS', 768),
        'timeout_ms': env_int('GEMINI_TIMEOUT_MS', 45000),
        'retry_delay': env_float('GEMINI_RETRY_DELAY_SECONDS', 1.0),
        # 기타 분야 웹 검색 전용. 무료 등급에서 Google Search grounding을 쓸 수 있는 모델(하루 500건).
        'search_model': env('GEMINI_SEARCH_MODEL', 'gemini-2.5-flash-lite'),
        # 웹 검색이 늦으면 일반 답변으로 넘어가야 앱 제한(60초) 안에 응답할 수 있어 짧게 둔다.
        'search_timeout_ms': env_int('GEMINI_SEARCH_TIMEOUT_MS', 15000),
    }


def search_thresholds() -> dict:
    return {
        # TF-IDF 기준값은 프로토타입 값. 임베딩 기준값은 임시값이며 시험 질의로 측정해 확정한다(보고서 14장 6번).
        'tfidf': env_float('TFIDF_MIN_SCORE', 0.12),
        'embedding': env_float('EMBEDDING_MIN_SCORE', 0.60),
    }

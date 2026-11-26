"""DB 구축 전 데모 모드에서 사용하는 출처 확인된 90건의 판례."""
import json
from functools import lru_cache
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

@lru_cache(maxsize=1)
def records():
    path = Path(__file__).resolve().parents[3] / 'data/seed/precedents90.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def search_catalog(category: str, description: str, limit: int = 3) -> list[dict]:
    """같은 분야에서 기준점(0.12)을 넘는 판례를 유사도 높은 순으로 최대 limit건 반환한다."""
    candidates = [r for r in records() if r['category'] == category]
    if not candidates or not description.strip():
        return []
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
    matrix = vectorizer.fit_transform([r['title'] + ' ' + r['summary'] for r in candidates])
    scores = (matrix @ vectorizer.transform([description]).T).toarray().ravel()
    ranked = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)
    return [candidates[i] for i in ranked[:limit] if scores[i] >= 0.12]

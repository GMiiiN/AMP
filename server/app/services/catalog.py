"""DB 구축 전 데모 모드에서 사용하는 출처 확인된 90건의 판례."""
import json
from functools import lru_cache
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

@lru_cache(maxsize=1)
def records():
    path = Path(__file__).resolve().parents[3] / 'data/seed/precedents90.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def search_catalog(category: str, description: str) -> list[dict]:
    candidates = [r for r in records() if r['category'] == category]
    if not candidates or not description.strip():
        return []
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
    matrix = vectorizer.fit_transform([r['title'] + ' ' + r['summary'] for r in candidates])
    scores = (matrix @ vectorizer.transform([description]).T).toarray().ravel()
    ranked = sorted(range(len(candidates)), key=lambda index: float(scores[index]), reverse=True)
    return [candidates[index] for index in ranked if scores[index] >= 0.12][:3]

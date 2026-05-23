from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def cosine_drift(text_a: str, text_b: str) -> float:
    """Cosine distance (1 - cosine similarity) between two texts."""

    vec = TfidfVectorizer(stop_words="english", max_features=25_000)
    X = vec.fit_transform([text_a, text_b])
    sim = cosine_similarity(X[0:1], X[1:2])[0, 0]
    return float(1.0 - sim)

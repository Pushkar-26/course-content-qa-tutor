from dataclasses import dataclass
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.retrieval.rrf import FusedResult


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@dataclass
class RerankedResult:
    chunk: FusedResult
    score: float


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(
        MODEL_NAME,
        max_length=512,
    )


def build_reranker_text(result: FusedResult) -> str:
    chunk = result.chunk

    if chunk.section:
        return f"{chunk.section}\n\n{chunk.text}"

    return chunk.text


def rerank_results(
    query: str,
    candidates: list[FusedResult],
    limit: int = 5,
    batch_size: int = 16,
) -> list[RerankedResult]:

    query = " ".join(query.split()).strip()

    if not query or not candidates:
        return []

    model = get_reranker()

    pairs = [
        (
            query,
            build_reranker_text(candidate),
        )
        for candidate in candidates
    ]

    scores = model.predict(
        pairs,
        batch_size=batch_size,
        show_progress_bar=False,
    )

    results = [
        RerankedResult(
            chunk=candidate,
            score=float(score),
        )
        for candidate, score in zip(candidates, scores)
    ]

    results.sort(
        key=lambda result: result.score,
        reverse=True,
    )

    return results[:limit]
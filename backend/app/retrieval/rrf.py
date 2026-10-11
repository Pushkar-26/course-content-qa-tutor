from collections import defaultdict
from dataclasses import dataclass

from app.db.models import Chunk


@dataclass
class FusedResult:
    chunk: Chunk
    score: float


def reciprocal_rank_fusion(
    result_lists: list[list[tuple[Chunk, float]]],
    k: int = 60,
    limit: int = 10,
) -> list[FusedResult]:
    scores = defaultdict(float)
    chunks = {}

    for results in result_lists:
        for rank, (chunk, _) in enumerate(results, start=1):
            scores[chunk.id] += 1 / (k + rank)
            chunks[chunk.id] = chunk

    ranked_ids = sorted(
        scores,
        key=lambda chunk_id: scores[chunk_id],
        reverse=True,
    )[:limit]

    return [
        FusedResult(
            chunk=chunks[chunk_id],
            score=scores[chunk_id],
        )
        for chunk_id in ranked_ids
    ]
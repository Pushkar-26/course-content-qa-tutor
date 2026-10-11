from app.retrieval.reranker import RerankedResult


def filter_by_score(
    results: list[RerankedResult],
    min_score: float | None = None,
    limit: int | None = None,
) -> list[RerankedResult]:
    if not results:
        return []

    if min_score is None:
        filtered = list(results)
    else:
        filtered = [
            result
            for result in results
            if result.score >= min_score
        ]

    if limit is not None:
        filtered = filtered[:limit]

    return filtered
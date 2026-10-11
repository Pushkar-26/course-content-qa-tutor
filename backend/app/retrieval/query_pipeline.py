from dataclasses import dataclass

from app.retrieval.query_analyzer import (
    QueryAnalysis,
    analyze_query,
    build_fts_query,
)
from app.retrieval.query_transformer import (
    QueryTransformation,
    transform_query,
)


@dataclass
class QueryPipelineResult:
    analysis: QueryAnalysis
    transformation: QueryTransformation
    retrieval_queries: list[str]
    fts_queries: list[str]


def process_query(
    query: str,
    previous_query: str | None = None,
    history: list[str] | None = None,
) -> QueryPipelineResult:

    analysis = analyze_query(
        query=query,
        previous_query=previous_query,
        history=history,
    )

    transformation = transform_query(
        query=query,
        analysis=analysis,
        previous_query=previous_query,
        history=history,
    )

    retrieval_queries = transformation.retrieval_queries()

    fts_queries = []
    seen = set()

    for item in retrieval_queries:
        fts_query = build_fts_query(item)

        if not fts_query:
            continue

        key = fts_query.lower()

        if key not in seen:
            seen.add(key)
            fts_queries.append(fts_query)

    return QueryPipelineResult(
        analysis=analysis,
        transformation=transformation,
        retrieval_queries=retrieval_queries,
        fts_queries=fts_queries,
    )
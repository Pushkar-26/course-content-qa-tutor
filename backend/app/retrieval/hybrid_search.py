
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import Chunk
from app.retrieval.full_text_search import search_full_text
from app.retrieval.query_pipeline import process_query
from app.retrieval.rrf import FusedResult, reciprocal_rank_fusion
from app.retrieval.semantic_search import search_similar_chunks


@dataclass
class HybridSearchResult:
    results: list[FusedResult]
    retrieval_queries: list[str]
    fts_queries: list[str]


def hybrid_search(
    db: Session,
    query: str,
    owner_id: str,
    previous_query: str | None = None,
    history: list[str] | None = None,
    retrieval_limit: int = 30,
    final_limit: int = 10,
) -> HybridSearchResult:
    pipeline_result = process_query(
        query=query,
        previous_query=previous_query,
        history=history,
    )

    result_lists: list[list[tuple[Chunk, float]]] = []

    for retrieval_query in pipeline_result.retrieval_queries:
        vector_results = search_similar_chunks(
            db=db,
            query=retrieval_query,
            owner_id=owner_id,
            limit=retrieval_limit,
        )

        result_lists.append(vector_results)

    for fts_query in pipeline_result.fts_queries:
        fts_results = search_full_text(
            db=db,
            query=fts_query,
            owner_id=owner_id,
            limit=retrieval_limit,
        )

        result_lists.append(fts_results)

    fused_results = reciprocal_rank_fusion(
        result_lists=result_lists,
        k=60,
        limit=final_limit,
    )

    return HybridSearchResult(
        results=fused_results,
        retrieval_queries=pipeline_result.retrieval_queries,
        fts_queries=pipeline_result.fts_queries,
    )

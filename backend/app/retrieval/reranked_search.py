
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import RerankedResult, rerank_results


@dataclass
class RerankedSearchResult:
    results: list[RerankedResult]
    retrieval_queries: list[str]
    fts_queries: list[str]


def reranked_search(
    db: Session,
    query: str,
    owner_id: str,
    previous_query: str | None = None,
    history: list[str] | None = None,
    retrieval_limit: int = 30,
    candidate_limit: int = 20,
    final_limit: int = 5,
) -> RerankedSearchResult:

    hybrid_result = hybrid_search(
        db=db,
        query=query,
        owner_id=owner_id,
        previous_query=previous_query,
        history=history,
        retrieval_limit=retrieval_limit,
        final_limit=candidate_limit,
    )

    reranked = rerank_results(
        query=query,
        candidates=hybrid_result.results,
        limit=final_limit,
    )

    return RerankedSearchResult(
        results=reranked,
        retrieval_queries=hybrid_result.retrieval_queries,
        fts_queries=hybrid_result.fts_queries,
    )

from app.db.database import SessionLocal
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import rerank_results


def main():
    db = SessionLocal()

    try:
        query = "How did the Internet begin?"

        hybrid_result = hybrid_search(
            db=db,
            query=query,
            retrieval_limit=30,
            final_limit=20,
        )

        candidates = hybrid_result.results

        print("=" * 60)
        print("Candidates from hybrid search:", len(candidates))

        for rank, result in enumerate(candidates, start=1):
            print(
                f"{rank}. "
                f"{result.chunk.source} | "
                f"page {result.chunk.page_number}-"
                f"{result.chunk.page_end} | "
                f"RRF={result.score:.6f}"
            )

        reranked = rerank_results(
            query=query,
            candidates=candidates,
            limit=5,
        )

        print("\n" + "=" * 60)
        print("Reranked results:")

        for rank, result in enumerate(reranked, start=1):
            chunk = result.chunk.chunk

            print(
                f"{rank}. "
                f"{chunk.source} | "
                f"page {chunk.page_number}-"
                f"{chunk.page_end} | "
                f"CrossEncoder={result.score:.4f}"
            )

        assert candidates
        assert reranked
        assert len(reranked) <= 5

        scores = [result.score for result in reranked]

        assert scores == sorted(
            scores,
            reverse=True,
        )

        print("\n" + "=" * 60)
        print("Reranker test passed")

    finally:
        db.close()


if __name__ == "__main__":
    main()
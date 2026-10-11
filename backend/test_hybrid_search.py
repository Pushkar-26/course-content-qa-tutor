from app.db.database import SessionLocal
from app.retrieval.hybrid_search import hybrid_search


def main():
    db = SessionLocal()

    try:
        query = "How did the Internet begin?"

        result = hybrid_search(
            db=db,
            query=query,
            retrieval_limit=30,
            final_limit=5,
        )

        print("=" * 60)
        print("Original query:", query)

        print("\nRetrieval queries:")
        for item in result.retrieval_queries:
            print(" -", item)

        print("\nFTS queries:")
        for item in result.fts_queries:
            print(" -", item)

        print("\nFinal hybrid results:")

        for rank, item in enumerate(result.results, start=1):
            chunk = item.chunk

            print(
                f"{rank}. "
                f"{chunk.source} | "
                f"page {chunk.page_number}-{chunk.page_end} | "
                f"RRF={item.score:.6f}"
            )

        assert result.retrieval_queries
        assert result.fts_queries
        assert result.results

        scores = [item.score for item in result.results]

        assert scores == sorted(scores, reverse=True)
        assert len(result.results) <= 5

        print("\n" + "=" * 60)
        print("Hybrid search test passed")

    finally:
        db.close()


if __name__ == "__main__":
    main()
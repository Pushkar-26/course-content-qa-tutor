from app.db.database import SessionLocal
from app.retrieval.reranked_search import reranked_search


def main():
    db = SessionLocal()

    try:
        query = "How did the Internet begin?"

        result = reranked_search(
            db=db,
            query=query,
            retrieval_limit=30,
            candidate_limit=20,
            final_limit=5,
        )

        print("=" * 60)
        print("Query:", query)

        print("\nRetrieval queries:")
        for item in result.retrieval_queries:
            print(" -", item)

        print("\nFTS queries:")
        for item in result.fts_queries:
            print(" -", item)

        print("\nFinal reranked results:")

        for rank, item in enumerate(result.results, start=1):
            chunk = item.chunk.chunk

            print(
                f"{rank}. "
                f"{chunk.source} | "
                f"page {chunk.page_number}-"
                f"{chunk.page_end} | "
                f"score={item.score:.4f}"
            )

        assert result.results
        assert len(result.results) <= 5

        scores = [item.score for item in result.results]

        assert scores == sorted(scores, reverse=True)

        print("\n" + "=" * 60)
        print("Reranked search test passed")

    finally:
        db.close()


if __name__ == "__main__":
    main()
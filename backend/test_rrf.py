from app.db.database import SessionLocal
from app.retrieval.full_text_search import search_full_text
from app.retrieval.rrf import reciprocal_rank_fusion
from app.retrieval.semantic_search import search_similar_chunks


def main():
    db = SessionLocal()

    try:
        query = "How did the Internet begin?"

        vector_results = search_similar_chunks(
            db=db,
            query=query,
            limit=5,
        )

        fts_results = search_full_text(
            db=db,
            query=query,
            limit=5,
        )

        fused_results = reciprocal_rank_fusion(
            result_lists=[
                vector_results,
                fts_results,
            ],
            k=60,
            limit=5,
        )

        print("=" * 60)
        print("Query:", query)

        print("\nVector results:")
        for rank, (chunk, score) in enumerate(vector_results, start=1):
            print(
                f"{rank}. {chunk.source} | "
                f"page {chunk.page_number}-{chunk.page_end} | "
                f"score={score:.4f}"
            )

        print("\nFTS results:")
        for rank, (chunk, score) in enumerate(fts_results, start=1):
            print(
                f"{rank}. {chunk.source} | "
                f"page {chunk.page_number}-{chunk.page_end} | "
                f"score={score:.4f}"
            )

        print("\nRRF results:")
        for rank, result in enumerate(fused_results, start=1):
            print(
                f"{rank}. {result.chunk.source} | "
                f"page {result.chunk.page_number}-"
                f"{result.chunk.page_end} | "
                f"RRF={result.score:.6f}"
            )

        assert vector_results
        assert fts_results
        assert fused_results

        ids = [result.chunk.id for result in fused_results]

        assert len(ids) == len(set(ids))
        assert len(fused_results) <= 5

        scores = [result.score for result in fused_results]
        assert scores == sorted(scores, reverse=True)

        print("\n" + "=" * 60)
        print("RRF test passed")

    finally:
        db.close()


if __name__ == "__main__":
    main()
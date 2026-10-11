from app.db.database import SessionLocal
from app.retrieval.context_builder import build_context
from app.retrieval.reranked_search import reranked_search

def main():
    db = SessionLocal()

    try:
        query = "How did the Internet begin?"

        reranked_result = reranked_search(
            db=db,
            query=query,
            retrieval_limit=30,
            candidate_limit=20,
            final_limit=5,
        )

        context = build_context(
            db=db,
            reranked_results=reranked_result.results,
            window=1,
            max_chunks=12,
        )

        print("=" * 60)
        print("Final context chunks:", len(context.chunks))

        for index, item in enumerate(context.chunks, start=1):
            chunk = item.chunk

            print(
                f"{index}. "
                f"{chunk.source} | "
                f"page {chunk.page_number}-{chunk.page_end} | "
                f"chunk_index={chunk.chunk_index} | "
                f"anchor={item.is_anchor}"
            )

        print("\n" + "=" * 60)
        print("CONTEXT")
        print(context.text)

        assert context.chunks
        assert context.text

        ids = [item.chunk.id for item in context.chunks]

        assert len(ids) == len(set(ids))
        assert len(context.chunks) <= 12

        print("\n" + "=" * 60)
        print("Context builder test passed")

    finally:
        db.close()


if __name__ == "__main__":
    main()
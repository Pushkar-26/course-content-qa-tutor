from app.db.database import SessionLocal
from app.generation.answer_generator import generate_final_answer
from app.retrieval.context_builder import build_context
from app.retrieval.reranked_search import reranked_search


def main():
    db = SessionLocal()

    try:
        query = "How did the Internet begin?"

        print("=" * 60)
        print("QUERY")
        print(query)

        print("\nRunning retrieval pipeline...")

        reranked_result = reranked_search(
            db=db,
            query=query,
            retrieval_limit=30,
            candidate_limit=20,
            final_limit=5,
        )

        assert reranked_result.results

        print("Reranked results:", len(reranked_result.results))

        print("\nBuilding context...")

        context = build_context(
            db=db,
            reranked_results=reranked_result.results,
            window=1,
            max_chunks=12,
        )

        assert context.chunks
        assert context.text

        print("Context chunks:", len(context.chunks))

        print("\nGenerating grounded answer...")

        answer = generate_final_answer(
            query=query,
            context=context,
        )

        assert answer
        assert isinstance(answer, str)
        assert "Sources:" in answer

        print("\n" + "=" * 60)
        print("FINAL ANSWER")
        print(answer)

        print("\n" + "=" * 60)
        print("END-TO-END TEST PASSED")

    finally:
        db.close()


if __name__ == "__main__":
    main()
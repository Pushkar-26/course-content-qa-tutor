from app.db.database import SessionLocal
from app.retrieval.full_text_search import search_full_text


QUERIES = [
    "Internet",
    "solar system",
    "planet",
]


def main():
    db = SessionLocal()

    try:
        passed = 0

        for query in QUERIES:
            results = search_full_text(
                db=db,
                query=query,
                limit=5,
            )

            print("\n" + "=" * 60)
            print("Query:", query)
            print("Results:", len(results))

            for index, (chunk, score) in enumerate(results, start=1):
                print(f"\n{index}. Score: {score:.4f}")
                print("Source:", chunk.source)
                print("Page:", chunk.page_number, "-", chunk.page_end)
                print("Section:", chunk.section)
                print("Text:", chunk.text[:300])

            assert results, f"No results found for query: {query}"
            assert all(score > 0 for _, score in results)

            passed += 1

        print("\n" + "=" * 60)
        print(f"{passed}/{len(QUERIES)} cases passed")

    finally:
        db.close()


if __name__ == "__main__":
    main()
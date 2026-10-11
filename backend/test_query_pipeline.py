from app.retrieval.query_pipeline import process_query


CASES = [
    {
        "query": "What is price war?",
        "previous_query": None,
        "history": None,
    },
    {
        "query": "monopoly kya hai",
        "previous_query": None,
        "history": None,
    },
    {
        "query": "cartel kya hai aur kaise kaam karta hai",
        "previous_query": None,
        "history": None,
    },
    {
        "query": "what about monopoly?",
        "previous_query": "What is perfect competition?",
        "history": ["What is perfect competition?"],
    },
]


def main():
    passed = 0

    for case in CASES:
        result = process_query(
            query=case["query"],
            previous_query=case["previous_query"],
            history=case["history"],
        )

        print("\n" + "=" * 60)
        print("Original:", result.analysis.query)
        print("Tasks:", result.analysis.tasks)
        print("Needs LLM:", result.analysis.needs_llm)
        print("LLM Optional:", result.analysis.llm_optional)

        print("\nRetrieval queries:")
        for query in result.retrieval_queries:
            print(" -", query)

        print("\nFTS queries:")
        for query in result.fts_queries:
            print(" -", query)

        assert result.analysis.query == case["query"].strip()
        assert result.retrieval_queries
        assert result.fts_queries

        assert len(result.retrieval_queries) == len(
            set(query.lower() for query in result.retrieval_queries)
        )

        assert len(result.fts_queries) == len(
            set(query.lower() for query in result.fts_queries)
        )

        passed += 1

    print("\n" + "=" * 60)
    print(f"{passed}/{len(CASES)} cases passed")


if __name__ == "__main__":
    main()
from app.retrieval.query_analyzer import analyze_query
from app.retrieval.query_transformer import transform_query


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
        query = case["query"]

        analysis = analyze_query(
            query=query,
            previous_query=case["previous_query"],
            history=case["history"],
        )

        result = transform_query(
            query=query,
            analysis=analysis,
            previous_query=case["previous_query"],
            history=case["history"],
        )

        print("\n" + "=" * 60)
        print("Original:", result.original_query)
        print("Tasks:", analysis.tasks)
        print("Needs LLM:", analysis.needs_llm)
        print("LLM Optional:", analysis.llm_optional)
        print("Rewritten:", result.rewritten_query)
        print("Normalized:", result.normalized_query)
        print("Sub-queries:", result.sub_queries)
        print("Retrieval queries:", result.retrieval_queries())

        assert result.original_query == query.strip()

        assert isinstance(result.rewritten_query, str)
        assert isinstance(result.normalized_query, str)
        assert isinstance(result.sub_queries, list)

        retrieval_queries = result.retrieval_queries()
        assert len(retrieval_queries) == len(set(q.lower() for q in retrieval_queries))

        passed += 1

    print("\n" + "=" * 60)
    print(f"{passed}/{len(CASES)} cases passed")


if __name__ == "__main__":
    main()
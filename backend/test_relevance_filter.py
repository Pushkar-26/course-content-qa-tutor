from types import SimpleNamespace

from app.retrieval.relevance_filter import filter_by_score


def make_result(score: float):
    return SimpleNamespace(score=score)


def main():
    results = [
        make_result(4.5),
        make_result(3.2),
        make_result(1.1),
        make_result(-0.5),
        make_result(-1.7),
    ]

    filtered = filter_by_score(
        results,
        min_score=1.0,
    )

    assert len(filtered) == 3
    assert [item.score for item in filtered] == [
        4.5,
        3.2,
        1.1,
    ]

    no_threshold = filter_by_score(results)

    assert len(no_threshold) == 5

    limited = filter_by_score(
        results,
        min_score=1.0,
        limit=2,
    )

    assert len(limited) == 2
    assert limited[0].score == 4.5
    assert limited[1].score == 3.2

    print("Relevance filter test passed")


if __name__ == "__main__":
    main()
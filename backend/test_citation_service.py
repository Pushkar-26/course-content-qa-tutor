from types import SimpleNamespace

from app.generation.citation_service import (
    extract_citation_ids,
    format_final_answer,
    resolve_citations,
    validate_citations,
    validate_claim_support,
)
from app.retrieval.context_builder import BuiltContext, ContextChunk


def build_test_context() -> BuiltContext:
    chunk1 = SimpleNamespace(
        id="chunk-1",
        source="course1.pdf",
        page_number=3,
        page_end=3,
        section="Introduction",
        text=(
            "The internet is a global network of connected computers "
            "that share information using common rules called protocols."
        ),
    )

    chunk2 = SimpleNamespace(
        id="chunk-2",
        source="course1.pdf",
        page_number=7,
        page_end=8,
        section="Advanced Concepts",
        text=(
            "Advanced concepts explain how different systems "
            "communicate and interact with each other."
        ),
    )

    chunks = [
        ContextChunk(
            chunk=chunk1,
            relevance_score=4.2,
            is_anchor=True,
            citation_id="C1",
        ),
        ContextChunk(
            chunk=chunk2,
            relevance_score=3.5,
            is_anchor=True,
            citation_id="C2",
        ),
    ]

    return BuiltContext(
        chunks=chunks,
        text="",
    )


def main():
    context = build_test_context()

    answer = (
        "The internet is discussed first as a global network [C1]. "
        "Advanced concepts explain how systems communicate [C2]."
    )

    ids = extract_citation_ids(answer)

    assert ids == ["C1", "C2"]

    citations = resolve_citations(
        answer=answer,
        context=context,
    )

    assert len(citations) == 2
    assert citations[0].source == "course1.pdf"
    assert citations[0].page_start == 3
    assert citations[1].page_start == 7

    validation = validate_citations(
        answer=answer,
        context=context,
    )

    assert validation.valid
    assert validation.cited_ids == ["C1", "C2"]
    assert validation.invalid_ids == []

    invalid_answer = (
        "This statement is supported [C1], "
        "but this one uses a fake citation [C99]."
    )

    invalid_result = validate_citations(
        answer=invalid_answer,
        context=context,
    )

    assert not invalid_result.valid
    assert invalid_result.invalid_ids == ["C99"]

    duplicate_answer = "Fact one [C1]. Fact two [C1]."

    duplicate_ids = extract_citation_ids(duplicate_answer)

    assert duplicate_ids == ["C1"]

    formatted = format_final_answer(
        answer=answer,
        validation=validation,
    )

    assert "[1]" in formatted
    assert "[2]" in formatted
    assert "[C1]" not in formatted
    assert "[C2]" not in formatted
    assert "Sources:" in formatted
    assert "course1.pdf" in formatted
    assert "Page 3" in formatted
    assert "Page 7-8" in formatted

    print("\n" + formatted)

    supported_answer = (
        "The internet is a global network of connected computers [C1]. "
        "Advanced concepts explain how systems communicate [C2]."
    )

    claim_results = validate_claim_support(
        answer=supported_answer,
        context=context,
    )

    assert len(claim_results) == 2
    assert all(
        result.supported
        for result in claim_results
    )

    unsupported_answer = (
        "The internet was invented in 1969 [C1]."
    )

    unsupported_results = validate_claim_support(
        answer=unsupported_answer,
        context=context,
    )

    assert len(unsupported_results) == 1
    assert not unsupported_results[0].supported

    print("\nClaim validation passed")
    print("Citation service test passed")


if __name__ == "__main__":
    main()
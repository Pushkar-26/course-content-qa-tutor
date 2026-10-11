from types import SimpleNamespace

from app.generation.answer_generator import generate_final_answer
from app.retrieval.context_builder import BuiltContext, ContextChunk


def build_test_context() -> BuiltContext:
    chunk1 = SimpleNamespace(
        id="chunk-1",
        source="history_of_internet.pdf",
        page_number=1,
        page_end=1,
        section="The History of the Internet",
        text=(
            "The internet is a global network of connected computers "
            "that share information using common rules called protocols."
        ),
    )

    chunk2 = SimpleNamespace(
        id="chunk-2",
        source="history_of_internet.pdf",
        page_number=1,
        page_end=1,
        section="The Birth of TCP/IP",
        text=(
            "By the early 1970s, many separate networks existed, "
            "and they could not easily communicate with each other. "
            "Vint Cerf and Bob Kahn designed a new set of rules "
            "to solve this problem. Their work led to the "
            "Transmission Control Protocol and the Internet Protocol, "
            "usually written together as TCP/IP."
        ),
    )

    chunk3 = SimpleNamespace(
        id="chunk-3",
        source="history_of_internet.pdf",
        page_number=1,
        page_end=1,
        section="The World Wide Web",
        text=(
            "In 1989, Tim Berners-Lee proposed a system "
            "for sharing documents over the internet."
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
            relevance_score=3.8,
            is_anchor=True,
            citation_id="C2",
        ),
        ContextChunk(
            chunk=chunk3,
            relevance_score=3.1,
            is_anchor=True,
            citation_id="C3",
        ),
    ]

    context_text = """
[C1]
Source: history_of_internet.pdf
Pages: 1
Section: The History of the Internet
Chunk ID: chunk-1
Content:
The internet is a global network of connected computers
that share information using common rules called protocols.

[C2]
Source: history_of_internet.pdf
Pages: 1
Section: The Birth of TCP/IP
Chunk ID: chunk-2
Content:
By the early 1970s, many separate networks existed,
and they could not easily communicate with each other.
Vint Cerf and Bob Kahn designed a new set of rules
to solve this problem. Their work led to the
Transmission Control Protocol and the Internet Protocol,
usually written together as TCP/IP.

[C3]
Source: history_of_internet.pdf
Pages: 1
Section: The World Wide Web
Chunk ID: chunk-3
Content:
In 1989, Tim Berners-Lee proposed a system
for sharing documents over the internet.
""".strip()

    return BuiltContext(
        chunks=chunks,
        text=context_text,
    )


def main():
    query = "How did the Internet begin?"

    context = build_test_context()

    result = generate_final_answer(
        query=query,
        context=context,
    )

    print("=" * 60)
    print("QUESTION")
    print(query)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print(result.answer)

    print("\n" + "=" * 60)
    print("CITATIONS")

    for index, citation in enumerate(result.citations, start=1):
        page_text = str(citation.page_start)

        if (
            citation.page_end is not None
            and citation.page_end != citation.page_start
        ):
            page_text = f"{citation.page_start}-{citation.page_end}"

        print(
            f"[{index}] "
            f"{citation.source}, "
            f"Page {page_text}, "
            f"{citation.section}"
        )

    assert result
    assert result.answer
    assert isinstance(result.answer, str)
    assert result.citations

    print("\n" + "=" * 60)
    print("Answer + Citation pipeline test passed")


if __name__ == "__main__":
    main()
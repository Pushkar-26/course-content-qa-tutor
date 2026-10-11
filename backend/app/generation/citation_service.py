import re
from dataclasses import dataclass

from app.retrieval.context_builder import BuiltContext

CITATION_PATTERN = re.compile(r"\[(C\d+)\]")


@dataclass
class Citation:
    citation_id: str
    source: str
    page_start: int
    page_end: int | None
    section: str | None
    chunk_id: str


@dataclass
class CitationValidation:
    valid: bool
    cited_ids: list[str]
    invalid_ids: list[str]
    resolved_citations: list[Citation]


@dataclass
class ClaimValidation:
    claim: str
    citation_ids: list[str]
    supported: bool
    overlap_score: float
    matched_terms: list[str]


CLAIM_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "be", "been", "being",
    "and", "or", "but",
    "of", "to", "in", "on", "for", "from",
    "with", "by", "as", "at",
    "this", "that", "these", "those",
    "it", "they", "their",
    "has", "have", "had",
    "does", "do", "did",
    "can", "could", "may", "might",
}


def build_citation_map(
    context: BuiltContext,
) -> dict[str, Citation]:
    citation_map = {}

    for item in context.chunks:
        chunk = item.chunk

        citation_map[item.citation_id] = Citation(
            citation_id=item.citation_id,
            source=chunk.source,
            page_start=chunk.page_number,
            page_end=chunk.page_end,
            section=chunk.section,
            chunk_id=chunk.id,
        )

    return citation_map


def extract_citation_ids(
    answer: str,
) -> list[str]:
    ids = CITATION_PATTERN.findall(answer)

    result = []
    seen = set()

    for citation_id in ids:
        if citation_id not in seen:
            seen.add(citation_id)
            result.append(citation_id)

    return result


def resolve_citations(
    answer: str,
    context: BuiltContext,
) -> list[Citation]:
    citation_map = build_citation_map(context)
    citation_ids = extract_citation_ids(answer)

    return [
        citation_map[citation_id]
        for citation_id in citation_ids
        if citation_id in citation_map
    ]


def validate_citations(
    answer: str,
    context: BuiltContext,
) -> CitationValidation:
    citation_map = build_citation_map(context)
    cited_ids = extract_citation_ids(answer)

    invalid_ids = [
        citation_id
        for citation_id in cited_ids
        if citation_id not in citation_map
    ]

    resolved_citations = [
        citation_map[citation_id]
        for citation_id in cited_ids
        if citation_id in citation_map
    ]

    return CitationValidation(
        valid=len(invalid_ids) == 0,
        cited_ids=cited_ids,
        invalid_ids=invalid_ids,
        resolved_citations=resolved_citations,
    )


def extract_claims_with_citations(
    answer: str,
) -> list[tuple[str, list[str]]]:
    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        answer.strip(),
    )

    claims = []

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        citation_ids = extract_citation_ids(sentence)

        if not citation_ids:
            continue

        claim = CITATION_PATTERN.sub(
            "",
            sentence,
        ).strip()

        if claim:
            claims.append(
                (claim, citation_ids)
            )

    return claims


def content_tokens(
    text: str,
) -> set[str]:
    tokens = re.findall(
        r"[A-Za-z0-9]+",
        text.lower(),
    )

    return {
        token
        for token in tokens
        if token not in CLAIM_STOPWORDS
        and len(token) > 1
    }


def validate_claim_support(
    answer: str,
    context: BuiltContext,
    min_overlap: float = 0.30,
) -> list[ClaimValidation]:
    citation_map = build_citation_map(context)

    evidence_map = {
        item.citation_id: item.chunk.text
        for item in context.chunks
    }

    claims = extract_claims_with_citations(answer)

    results = []

    for claim, citation_ids in claims:
        invalid_ids = [
            citation_id
            for citation_id in citation_ids
            if citation_id not in citation_map
        ]

        if invalid_ids:
            results.append(
                ClaimValidation(
                    claim=claim,
                    citation_ids=citation_ids,
                    supported=False,
                    overlap_score=0.0,
                    matched_terms=[],
                )
            )
            continue

        evidence_text = " ".join(
            evidence_map[citation_id]
            for citation_id in citation_ids
        )

        claim_terms = content_tokens(claim)
        evidence_terms = content_tokens(evidence_text)

        if not claim_terms:
            results.append(
                ClaimValidation(
                    claim=claim,
                    citation_ids=citation_ids,
                    supported=True,
                    overlap_score=1.0,
                    matched_terms=[],
                )
            )
            continue

        matched_terms = sorted(
            claim_terms & evidence_terms
        )

        overlap_score = (
            len(matched_terms) / len(claim_terms)
        )

        supported = (
            overlap_score >= min_overlap
            and (
                len(claim_terms) == 1
                or len(matched_terms) >= 2
            )
        )

        results.append(
            ClaimValidation(
                claim=claim,
                citation_ids=citation_ids,
                supported=supported,
                overlap_score=overlap_score,
                matched_terms=matched_terms,
            )
        )

    return results


def format_final_answer(
    answer: str,
    validation: CitationValidation,
) -> str:
    if not validation.valid:
        raise ValueError(
            f"Cannot format answer with invalid citations: "
            f"{validation.invalid_ids}"
        )

    if not validation.resolved_citations:
        return answer.strip()

    citation_numbers = {}

    for index, citation in enumerate(
        validation.resolved_citations,
        start=1,
    ):
        citation_numbers[citation.citation_id] = index

    def replace_citation(match):
        citation_id = match.group(1)
        number = citation_numbers.get(citation_id)

        if number is None:
            return match.group(0)

        return f"[{number}]"

    formatted_answer = CITATION_PATTERN.sub(
        replace_citation,
        answer,
    )

    source_lines = []

    for index, citation in enumerate(
        validation.resolved_citations,
        start=1,
    ):
        page_text = str(citation.page_start)

        if (
            citation.page_end is not None
            and citation.page_end != citation.page_start
        ):
            page_text = (
                f"{citation.page_start}-"
                f"{citation.page_end}"
            )

        section_text = (
            citation.section
            or "Unknown section"
        )

        source_lines.append(
            f"[{index}] {citation.source}, "
            f"Page {page_text}, "
            f"{section_text}"
        )

    sources = "\n".join(source_lines)

    return (
        f"{formatted_answer.strip()}\n\n"
        f"Sources:\n"
        f"{sources}"
    )


def format_answer_citations(
    answer: str,
    citations: list[Citation],
) -> str:
    citation_numbers = {
        citation.citation_id: index
        for index, citation in enumerate(
            citations,
            start=1,
        )
    }

    def replace_citation(match):
        citation_id = match.group(1)
        number = citation_numbers.get(citation_id)

        if number is None:
            return match.group(0)

        return f"[{number}]"

    return CITATION_PATTERN.sub(
        replace_citation,
        answer,
    )
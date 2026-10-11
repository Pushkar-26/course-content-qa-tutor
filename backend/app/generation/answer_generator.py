from app.generation.citation_service import (
    format_answer_citations,
    validate_citations,
    validate_claim_support,
)
from dataclasses import dataclass
from app.retrieval.context_builder import BuiltContext

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


class AnswerResponse(BaseModel):
    answer: str


def build_answer_prompt(
    query: str,
    context: str,
) -> str:
    return f"""
You are a course-content Q&A tutor.

Answer the user's question using ONLY the provided course context.

Citation rules:
1. Every factual statement based on the course context must include
   one or more supporting citation IDs such as [C1] or [C2].
2. Use ONLY citation IDs that actually appear in the provided context.
3. Put citation IDs immediately after the statement they support.
4. Do not invent citation IDs.
5. Do not cite a source that does not support the statement.
6. If a statement cannot be supported by the provided context,
   do not state it as a fact.
7. If the context does not contain enough information to answer,
   clearly say that the course material does not provide enough information.
8. Do not use outside knowledge.
9. Give a clear and concise answer.
10. Preserve important technical terminology, formulas, and names.

Example:
"The Internet uses common communication protocols [C1].
TCP/IP allowed different networks to communicate with each other [C2]."

User question:
{query}

Course context:
{context}
""".strip()


def generate_answer(
    query: str,
    context: str,
) -> str:
    query = " ".join(query.split()).strip()
    context = context.strip()

    if not query:
        raise ValueError("Query cannot be empty")

    if not context:
        return "The course material does not provide enough information to answer this question."

    prompt = build_answer_prompt(
        query=query,
        context=context,
    )

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnswerResponse,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low"
                    ),
                ),
            )
            break

        except errors.ServerError:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt
            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    if not response.text:
        raise ValueError("Gemini returned an empty response")

    parsed = AnswerResponse.model_validate_json(response.text)

    answer = parsed.answer.strip()

    if not answer:
        raise ValueError("Gemini returned an empty answer")

    return answer
@dataclass
class FinalAnswer:
    answer: str
    citations: list

def generate_final_answer(
    query: str,
    context: BuiltContext,
) -> FinalAnswer:
    if not context.text:
        return FinalAnswer(
            answer=(
                "The course material does not provide enough "
                "information to answer this question."
            ),
            citations=[],
        )

    answer = generate_answer(
        query=query,
        context=context.text,
    )

    citation_validation = validate_citations(
        answer=answer,
        context=context,
    )

    if not citation_validation.valid:
        raise ValueError(
            f"Invalid citation IDs: "
            f"{citation_validation.invalid_ids}"
        )

    claim_results = validate_claim_support(
        answer=answer,
        context=context,
    )

    unsupported_claims = [
        result
        for result in claim_results
        if not result.supported
    ]

    if unsupported_claims:
        raise ValueError(
            "Answer contains claims that are not sufficiently "
            "supported by the cited context."
        )

    formatted_answer = format_answer_citations(
        answer=answer,
        citations=citation_validation.resolved_citations,
    )

    return FinalAnswer(
        answer=formatted_answer,
        citations=citation_validation.resolved_citations,
    )

def generate_general_answer(query: str) -> str:
    query = " ".join(query.split()).strip()

    if not query:
        raise ValueError("Query cannot be empty")

    prompt = f"""
You are CourseQ AI, a helpful general-purpose study tutor.

Answer the user's question using your general knowledge.
You are not restricted to uploaded course documents.

Rules:
1. Explain concepts clearly and accurately.
2. Adapt the explanation to the user's question.
3. Do not invent facts, statistics, or references.
4. Do not generate document citation markers such as [C1] or [1].
5. If you are uncertain, clearly acknowledge the uncertainty.
6. Do not claim that you searched the internet or uploaded files.
7. For information that may have changed recently, explain that
   your answer may not reflect the latest developments.
8. Keep the answer useful and appropriately detailed.

User question:
{query}
""".strip()

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnswerResponse,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low"
                    ),
                ),
            )
            break

        except errors.ServerError:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt
            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    if not response.text:
        raise ValueError("Gemini returned an empty response")

    parsed = AnswerResponse.model_validate_json(response.text)
    answer = parsed.answer.strip()

    if not answer:
        raise ValueError("Gemini returned an empty answer")

    return answer

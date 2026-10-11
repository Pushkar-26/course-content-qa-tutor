import os
from dataclasses import dataclass
import time
from google.genai import errors
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.retrieval.query_analyzer import QueryAnalysis

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.7-flash"


class TransformationResponse(BaseModel):
    rewritten_query: str
    normalized_query: str
    sub_queries: list[str]


@dataclass
class QueryTransformation:
    original_query: str
    rewritten_query: str
    normalized_query: str
    sub_queries: list[str]

    def retrieval_queries(self) -> list[str]:
        queries = [
            self.original_query,
            self.rewritten_query,
            self.normalized_query,
            *self.sub_queries,
        ]

        result = []
        seen = set()

        for query in queries:
            query = " ".join(query.split()).strip()

            if not query:
                continue

            key = query.lower()

            if key not in seen:
                seen.add(key)
                result.append(query)

        return result


def build_prompt(
    query: str,
    analysis: QueryAnalysis,
    previous_query: str | None = None,
    history: list[str] | None = None,
) -> str:
    history_text = ""

    if previous_query:
        history_text += f"Previous query:\n{previous_query}\n\n"

    if history:
        history_text += "Recent conversation:\n"
        for item in history[-5:]:
            history_text += f"- {item}\n"
        history_text += "\n"

    return f"""
You are a query transformation component inside a course-content
retrieval system.

Your job is NOT to answer the user's question.

Transform the query only when needed for retrieval.

Goals:
1. Resolve follow-up references using the conversation context.
2. Convert Hinglish into clear English while preserving technical terms.
3. Rewrite the query into a retrieval-friendly form.
4. Split multi-part questions into atomic sub-queries when useful.
5. Do not invent facts or add information not implied by the user.
6. Preserve formulas, abbreviations, technical names and important terminology.
7. Keep sub-queries concise.

Current query:
{query}

Analyzer tasks:
{analysis.tasks}

Analyzer reasons:
{analysis.reasons}

{history_text}

Return:
- rewritten_query: one clear retrieval-friendly query
- normalized_query: English-normalized version if needed
- sub_queries: atomic retrieval queries; use an empty list if splitting is unnecessary
""".strip()


def transform_query(
    query: str,
    analysis: QueryAnalysis,
    previous_query: str | None = None,
    history: list[str] | None = None,
) -> QueryTransformation:
    query = " ".join(query.split()).strip()

    if not query:
        return QueryTransformation(
            original_query="",
            rewritten_query="",
            normalized_query="",
            sub_queries=[],
        )

    if not analysis.needs_llm or analysis.llm_optional:
        return QueryTransformation(
            original_query=query,
            rewritten_query=query,
            normalized_query=query,
            sub_queries=[],
        )

    prompt = build_prompt(
        query=query,
        analysis=analysis,
        previous_query=previous_query,
        history=history,
    )

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TransformationResponse,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low"
                    ),
                ),
            )
            break

        except errors.ServerError as exc:
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

    parsed = TransformationResponse.model_validate_json(response.text)

    return QueryTransformation(
        original_query=query,
        rewritten_query=parsed.rewritten_query.strip(),
        normalized_query=parsed.normalized_query.strip(),
        sub_queries=[
            item.strip()
            for item in parsed.sub_queries
            if item and item.strip()
        ],
    )
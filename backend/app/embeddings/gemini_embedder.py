import math
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIMENSION = 1536
MAX_RETRIES = 3


def normalize_vector(values: list[float]) -> list[float]:
    magnitude = math.sqrt(
        sum(value * value for value in values)
    )

    if magnitude == 0:
        raise ValueError("Cannot normalize a zero vector")

    return [
        value / magnitude
        for value in values
    ]


def should_retry(exc: Exception) -> bool:
    if isinstance(exc, errors.ServerError):
        return True

    if isinstance(exc, errors.ClientError):
        status_code = getattr(
            exc,
            "code",
            getattr(exc, "status_code", None),
        )

        return status_code == 429

    return False


def embed_with_retry(
    contents,
    task_type: str,
):
    for attempt in range(MAX_RETRIES):
        try:
            return client.models.embed_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIMENSION,
                ),
            )

        except (errors.ClientError, errors.ServerError) as exc:
            if not should_retry(exc):
                raise

            if attempt == MAX_RETRIES - 1:
                raise

            wait_time = 2 ** attempt

            print(
                f"Gemini embedding service temporarily unavailable "
                f"(attempt {attempt + 1}/{MAX_RETRIES}). "
                f"Retrying in {wait_time}s..."
            )

            time.sleep(wait_time)


def embed_document_batch(
    texts: list[str],
) -> list[list[float]]:
    if not texts:
        return []

    result = embed_with_retry(
        contents=texts,
        task_type="RETRIEVAL_DOCUMENT",
    )

    if len(result.embeddings) != len(texts):
        raise ValueError(
            f"Expected {len(texts)} embeddings, "
            f"got {len(result.embeddings)}"
        )

    embeddings = []

    for embedding in result.embeddings:
        values = embedding.values

        if len(values) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSION} dimensions, "
                f"got {len(values)}"
            )

        embeddings.append(
            normalize_vector(values)
        )

    return embeddings


def embed_document(
    text: str,
) -> list[float]:
    return embed_document_batch([text])[0]


def embed_query(
    text: str,
) -> list[float]:
    result = embed_with_retry(
        contents=text,
        task_type="RETRIEVAL_QUERY",
    )

    values = result.embeddings[0].values

    if len(values) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"got {len(values)}"
        )

    return normalize_vector(values)
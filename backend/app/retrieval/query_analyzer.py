from dataclasses import dataclass, field
import re


# Unambiguous Hinglish words: even ONE of these is enough to call a query Hinglish.
# (Words that are also normal English, like "me", "to", "do", "par", are left out on purpose.)
HINGLISH_WORDS = {
    "bhai", "yaar", "batao", "btao", "bata", "bataiye", "samjha", "samjhao",
    "samjhaao", "smjhao", "dikhao", "likho", "bolo", "karo", "kijiye",
    "kya", "kaise", "kese", "kyu", "kyun", "kyon", "kab", "kahan", "kaun",
    "kaunsa", "kitna", "kitne", "kitni",
    "hai", "hain", "hota", "hoti", "hote", "nahi", "nhi", "matlab", "farak",
    "fark", "chahiye", "wala", "wali", "wale", "mujhe", "mera", "meri",
    "isko", "iska", "iske", "iski", "uska", "uske", "uski", "usko",
    "isme", "usme", "inka", "unka", "yeh", "ye", "wo", "woh",
    "aur", "ya", "ke", "ka", "ki", "ko", "se", "mein", "bhi", "toh", "phir", "fir",
    "sirf", "zyada", "kuch", "sab",
}

# Dropped from the full text search query but not used to detect Hinglish.
HINGLISH_STRIP_ONLY = {"h"}

INTERROGATIVES = {
    "what", "why", "how", "kya", "kaise", "kese", "kyu", "kyun", "kyon",
    "kab", "kahan", "kaun", "kaunsa", "kitna", "kitne", "kitni",
}

FOLLOW_UP_STARTS = (
    "what about", "how about", "and ", "also ", "then ", "so ", "but ",
    "why so", "is it the same", "explain that", "explain this",
    "explain more", "give an example", "give example", "elaborate",
    "in detail", "aur ", "toh ", "phir ", "fir ",
)

FOLLOW_UP_PRONOUNS = {
    "it", "its", "this", "that", "these", "those", "they", "them", "their",
    "same", "above", "former", "latter", "previous",
    "ye", "yeh", "yah", "wo", "woh", "isko", "iska", "iske", "iski", "isme",
    "isse", "uska", "uske", "uski", "usko", "usme", "usse", "inka", "unka",
}

COMPARISON_PATTERN = re.compile(
    r"\bvs\.?(?=\s|$)|\bv/s\b|\bversus\b|\bdifferences? between\b|\bdifferentiate\b"
    r"|\bcompare\b|\bcomparison\b|\bcontrast\b|\bfarak\b|\bfark\b"
)

COMPLEX_PHRASES = (
    "pros and cons", "advantages and disadvantages", "why and how",
    "what and why", "how and why", "step by step", "relationship between",
    "explain with example",
)

LONG_QUERY_WORDS = 25
FOLLOW_UP_MAX_WORDS = 10
LLM_OPTIONAL_MAX_WORDS = 12

WORD_PATTERN = re.compile(r"[a-zA-Z]+")
FTS_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")
DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")


@dataclass
class QueryAnalysis:
    query: str
    is_follow_up: bool
    is_multi_part: bool
    is_hinglish: bool
    is_long: bool
    is_complex: bool
    needs_llm: bool
    tasks: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    fts_query: str = ""
    llm_optional: bool = False


def normalize_query(query: str | None) -> str:
    return " ".join((query or "").split())


def words_of(text: str) -> list[str]:
    return WORD_PATTERN.findall(text.lower())


def find_hinglish_reason(query: str) -> str | None:
    if DEVANAGARI_PATTERN.search(query):
        return "hinglish:devanagari"

    matches = [w for w in words_of(query) if w in HINGLISH_WORDS]

    if matches:
        return f"hinglish:{matches[0]}"

    return None


def find_follow_up_reason(query: str, has_history: bool) -> str | None:
    # A follow-up needs something to follow. No history = nothing to resolve.
    if not has_history:
        return None

    lowered = query.lower().strip()

    for start in FOLLOW_UP_STARTS:
        if lowered.startswith(start):
            return f"follow_up:starts_with({start.strip()})"

    words = words_of(lowered)

    if len(words) <= FOLLOW_UP_MAX_WORDS:
        for word in words:
            if word in FOLLOW_UP_PRONOUNS:
                return f"follow_up:pronoun({word})"

    return None


def find_multi_part_reason(query: str) -> str | None:
    lowered = query.lower()

    if query.count("?") >= 2:
        return "multi_part:two_question_marks"

    if COMPARISON_PATTERN.search(lowered):
        return "multi_part:comparison"

    words = words_of(lowered)
    interrogatives = [w for w in words if w in INTERROGATIVES]

    if len(interrogatives) >= 2:
        return "multi_part:two_question_words"

    conjunctions = sum(1 for w in words if w in ("and", "aur", "also", "plus"))

    if conjunctions >= 2:
        return "multi_part:many_conjunctions"

    if conjunctions >= 1 and lowered.count(",") >= 1:
        return "multi_part:list_with_and"

    if "or" in words:
        return "multi_part:or"

    return None


def find_complex_reason(query: str) -> str | None:
    lowered = query.lower()

    for phrase in COMPLEX_PHRASES:
        if phrase in lowered:
            return f"complex:phrase({phrase})"

    if query.count(",") >= 2 or query.count(";") >= 1:
        return "complex:multiple_clauses"

    return None


def build_fts_query(query: str) -> str:
    """English keywords only: Hinglish filler words never appear in English
    documents, so keeping them would make an AND style text search return nothing."""
    drop = HINGLISH_WORDS | HINGLISH_STRIP_ONLY
    tokens = []

    for token in FTS_TOKEN_PATTERN.findall(query):
        if token.lower() in drop:
            continue

        if len(token) == 1 and not token.isdigit():
            continue

        tokens.append(token)

    return " ".join(tokens)


# Public boolean helpers (same names as before)

def detect_hinglish(query: str) -> bool:
    return find_hinglish_reason(query) is not None


def detect_follow_up(query: str, previous_query: str | None = None) -> bool:
    return find_follow_up_reason(query, bool(previous_query)) is not None


def detect_multi_part(query: str) -> bool:
    return find_multi_part_reason(query) is not None


def detect_long_or_complex(query: str) -> tuple[bool, bool]:
    is_long = len(query.split()) >= LONG_QUERY_WORDS
    is_complex = is_long or find_complex_reason(query) is not None
    return is_long, is_complex


def analyze_query(
    query: str,
    previous_query: str | None = None,
    history: list[str] | None = None,
) -> QueryAnalysis:
    query = normalize_query(query)
    has_history = bool(previous_query or history)

    hinglish_reason = find_hinglish_reason(query)
    follow_up_reason = find_follow_up_reason(query, has_history)
    multi_part_reason = find_multi_part_reason(query)
    complex_reason = find_complex_reason(query)

    is_long = len(query.split()) >= LONG_QUERY_WORDS
    is_hinglish = hinglish_reason is not None
    is_follow_up = follow_up_reason is not None
    is_multi_part = multi_part_reason is not None
    is_complex = is_long or complex_reason is not None

    reasons = [
        reason
        for reason in (follow_up_reason, multi_part_reason, hinglish_reason, complex_reason)
        if reason
    ]

    if is_long:
        reasons.append("long_query")

    # What the LLM rewrite step should actually do (use these to build its prompt)
    tasks = []

    if is_follow_up:
        tasks.append("resolve_follow_up")

    if is_multi_part or is_complex:
        tasks.append("split_parts")

    if is_hinglish:
        tasks.append("translate")

    if is_long and "split_parts" not in tasks:
        tasks.append("condense")

    needs_llm = bool(tasks)

    # A short Hinglish-only query may work fine without the LLM
    # (Gemini embeddings are multilingual). Decide this using your eval set.
    llm_optional = tasks == ["translate"] and len(query.split()) <= LLM_OPTIONAL_MAX_WORDS

    return QueryAnalysis(
        query=query,
        is_follow_up=is_follow_up,
        is_multi_part=is_multi_part,
        is_hinglish=is_hinglish,
        is_long=is_long,
        is_complex=is_complex,
        needs_llm=needs_llm,
        tasks=tasks,
        reasons=reasons,
        fts_query=build_fts_query(query),
        llm_optional=llm_optional,
    )
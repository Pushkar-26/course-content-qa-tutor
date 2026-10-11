from app.retrieval.query_analyzer import analyze_query, detect_hinglish, detect_follow_up
from app.retrieval.query_analyzer import (
    analyze_query,
    detect_hinglish,
    detect_follow_up,
)
HISTORY = "What is perfect competition?"

# (query, history, field, expected)
CASES = [
    # Hinglish
    ("monopoly kya hai", None, "is_hinglish", True),
    ("price war samjhao", None, "is_hinglish", True),
    ("perfect competition ke features", None, "is_hinglish", True),
    ("\u092e\u094b\u0928\u094b\u092a\u094b\u0932\u0940 \u0915\u094d\u092f\u093e \u0939\u0948", None, "is_hinglish", True),
    ("What is monopoly?", None, "is_hinglish", False),
    ("tell me about price war", None, "is_hinglish", False),
    # Follow ups
    ("what about monopoly?", HISTORY, "is_follow_up", True),
    ("what about monopoly?", None, "is_follow_up", False),
    ("explain this", HISTORY, "is_follow_up", True),
    ("isko explain karo", HISTORY, "is_follow_up", True),
    ("and in the long run?", HISTORY, "is_follow_up", True),
    ("What is a cartel?", HISTORY, "is_follow_up", False),
    ("How does a cartel affect price?", HISTORY, "is_follow_up", False),
    # Multi part / comparison
    ("monopoly vs oligopoly", None, "is_multi_part", True),
    ("difference between monopoly and oligopoly", None, "is_multi_part", True),
    ("what is a cartel and how does it work", None, "is_multi_part", True),
    ("features of perfect competition, monopoly and oligopoly", None, "is_multi_part", True),
    ("monopoly aur oligopoly mein farak batao", None, "is_multi_part", True),
    ("cartel kya hai aur kaise kaam karta hai", None, "is_multi_part", True),
    ("What is a cartel?", None, "is_multi_part", False),
    ("Why is a firm a price taker?", None, "is_multi_part", False),
    ("What is a market in which one firm sells?", None, "is_multi_part", False),
    # Complex / long
    ("explain price war step by step", None, "is_complex", True),
    (" ".join(["word"] * 26), None, "is_long", True),
    # Simple queries must not call the LLM
    ("What is price war?", None, "needs_llm", False),
    ("price leadership", None, "needs_llm", False),
    ("Why is a firm a price taker?", None, "needs_llm", False),
    ("", None, "needs_llm", False),
    ("   ", None, "needs_llm", False),
]

failed = 0
for query, history, field, expected in CASES:
    result = analyze_query(query, previous_query=history)
    actual = getattr(result, field)
    if actual != expected:
        failed += 1
        print(f"FAIL {query!r} history={bool(history)} {field}: expected {expected}, got {actual} | {result.reasons}")

FTS_CASES = [
    ("monopoly ka long run equilibrium kya hai", "monopoly long run equilibrium"),
    ("perfect competition ke features", "perfect competition features"),
    ("monopoly kya h", "monopoly"),
    ("What is MR=MC condition?", "What is MR MC condition"),
]
for query, expected in FTS_CASES:
    actual = analyze_query(query).fts_query
    if actual != expected:
        failed += 1
        print(f"FAIL fts {query!r}: expected {expected!r}, got {actual!r}")

# normalization + tasks + backward compatible helpers
assert analyze_query("  What   is  monopoly? ").query == "What is monopoly?"
assert analyze_query("cartel kya hai aur kaise kaam karta hai").tasks == ["split_parts", "translate"]
assert analyze_query("monopoly kya hai").llm_optional is True
assert detect_hinglish("monopoly kya hai") and detect_follow_up("explain this", HISTORY)

total = len(CASES) + len(FTS_CASES)
print(f"{total - failed}/{total} cases passed")
raise SystemExit(1 if failed else 0)
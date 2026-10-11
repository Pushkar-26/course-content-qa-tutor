import re
from collections import Counter
from statistics import median
from uuid import uuid4

from app.ingestion.chunk_models import DocumentChunk
from app.ingestion.text_cleaner import join_lines


SENTENCE_END = (".", "!", "?")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
ABBREVIATIONS = ("mr.", "mrs.", "ms.", "dr.", "prof.", "e.g.", "i.e.", "vs.", "fig.")
SECTION_SEPARATOR = " > "


# ---------------------------------------------------------------------------
# Step 1: flatten pages and measure the document layout
# ---------------------------------------------------------------------------

def flatten_lines(pages: list[dict]) -> list[dict]:
    lines = []

    for page in pages:
        for line in page["lines"]:
            if not line["text"].strip():
                continue

            item = dict(line)
            item["page_number"] = page["page_number"]
            lines.append(item)

    return lines


def compute_stats(lines: list[dict]) -> dict:
    size_weight = Counter()

    for line in lines:
        size_weight[round(line["font_size"], 1)] += len(line["text"])

    body_size = size_weight.most_common(1)[0][0]

    left = min(line["x0"] for line in lines)
    right = max(line["x1"] for line in lines)

    pitches = []
    for first, second in zip(lines, lines[1:]):
        if first["page_number"] != second["page_number"]:
            continue

        pitch = second["y0"] - first["y0"]

        if 0 < pitch < body_size * 3:
            pitches.append(pitch)

    line_pitch = median(pitches) if pitches else body_size * 1.4

    return {
        "body_size": body_size,
        "left": left,
        "width": max(right - left, 1),
        "line_pitch": line_pitch,
    }


def width_fraction(line: dict, stats: dict) -> float:
    return (line["x1"] - stats["left"]) / stats["width"]


def ends_sentence(text: str) -> bool:
    return text.strip().endswith(SENTENCE_END)


# ---------------------------------------------------------------------------
# Step 2: heading detection (works even when heading font = body font)
# ---------------------------------------------------------------------------

def is_styled_heading(line: dict, stats: dict) -> bool:
    bigger = line["font_size"] >= stats["body_size"] * 1.1
    return bigger or line["bold"]


def is_heading_line(line: dict, previous: dict | None, stats: dict) -> bool:
    text = line["text"].strip()
    words = text.split()

    if not words or len(words) > 10 or len(text) > 90:
        return False

    if text.endswith((".", ",", ";", ":", "?", "!")):
        return False

    if not (text[0].isupper() or text[0].isdigit()):
        return False

    if is_styled_heading(line, stats):
        return True

    # Plain heading (same font as body): it must be a short line on its own.
    if width_fraction(line, stats) >= 0.75:
        return False

    if previous is None:
        return True

    if previous["page_number"] != line["page_number"]:
        return True

    # previous line is a full width line that did not end a sentence:
    # this short line is the tail of the same paragraph, not a heading.
    if width_fraction(previous, stats) >= 0.85 and not ends_sentence(previous["text"]):
        return False

    return True


def heading_level(line: dict, stats: dict, heading_sizes: list[float]) -> int:
    size = round(line["font_size"], 1)

    if size in heading_sizes:
        return heading_sizes.index(size) + 1

    return len(heading_sizes) + 1


# ---------------------------------------------------------------------------
# Step 3: lines -> paragraphs -> sections
# ---------------------------------------------------------------------------

def starts_new_paragraph(previous: dict, line: dict, stats: dict) -> bool:
    previous_closed = (
        ends_sentence(previous["text"]) and width_fraction(previous, stats) < 0.85
    )

    if previous["page_number"] != line["page_number"]:
        return previous_closed

    pitch = line["y0"] - previous["y0"]

    if pitch > stats["line_pitch"] * 1.35:
        return True

    return previous_closed


def add_paragraph(section: dict, paragraph_lines: list[dict]) -> None:
    if not paragraph_lines:
        return

    text = join_lines([line["text"] for line in paragraph_lines])

    if not text:
        return

    section["paragraphs"].append({
        "text": text,
        "page_start": paragraph_lines[0]["page_number"],
        "page_end": paragraph_lines[-1]["page_number"],
    })


def build_sections(lines: list[dict], stats: dict) -> list[dict]:
    heading_flags = []
    previous = None

    for line in lines:
        heading_flags.append(is_heading_line(line, previous, stats))
        previous = line

    heading_sizes = sorted(
        {
            round(line["font_size"], 1)
            for line, flag in zip(lines, heading_flags)
            if flag and line["font_size"] >= stats["body_size"] * 1.1
        },
        reverse=True,
    )

    sections = []
    stack = []
    current = {"path": None, "paragraphs": []}
    paragraph_lines = []

    for line, flag in zip(lines, heading_flags):
        if flag:
            add_paragraph(current, paragraph_lines)
            paragraph_lines = []

            if current["paragraphs"]:
                sections.append(current)

            level = heading_level(line, stats, heading_sizes)

            while stack and stack[-1][0] >= level:
                stack.pop()

            stack.append((level, line["text"].strip()))

            current = {
                "path": SECTION_SEPARATOR.join(title for _, title in stack),
                "paragraphs": [],
            }
            continue

        if paragraph_lines and starts_new_paragraph(paragraph_lines[-1], line, stats):
            add_paragraph(current, paragraph_lines)
            paragraph_lines = []

        paragraph_lines.append(line)

    add_paragraph(current, paragraph_lines)

    if current["paragraphs"]:
        sections.append(current)

    return sections


def merge_tiny_sections(sections: list[dict], min_chars: int, max_chars: int) -> list[dict]:
    merged = []

    for section in sections:
        size = sum(len(p["text"]) for p in section["paragraphs"])

        if merged and section["path"] and size < min_chars:
            previous = merged[-1]
            previous_size = sum(len(p["text"]) for p in previous["paragraphs"])

            if previous_size + size <= max_chars:
                heading = section["path"].split(SECTION_SEPARATOR)[-1]
                first = dict(section["paragraphs"][0])
                first["text"] = f"{heading}: {first['text']}"
                previous["paragraphs"].append(first)
                previous["paragraphs"].extend(section["paragraphs"][1:])
                continue

        merged.append(section)

    return merged


# ---------------------------------------------------------------------------
# Step 4: split a section into chunks (never mid sentence)
# ---------------------------------------------------------------------------

def split_sentences(text: str) -> list[str]:
    sentences = []

    for part in SENTENCE_SPLIT.split(text):
        part = part.strip()

        if not part:
            continue

        if sentences and sentences[-1].lower().endswith(ABBREVIATIONS):
            sentences[-1] = f"{sentences[-1]} {part}"
        else:
            sentences.append(part)

    return sentences


def section_units(section: dict, max_chars: int) -> list[dict]:
    units = []

    for index, paragraph in enumerate(section["paragraphs"]):
        if len(paragraph["text"]) <= max_chars:
            units.append({
                "text": paragraph["text"],
                "para": index,
                "sentence": False,
                "page_start": paragraph["page_start"],
                "page_end": paragraph["page_end"],
            })
            continue

        for sentence in split_sentences(paragraph["text"]):
            units.append({
                "text": sentence,
                "para": index,
                "sentence": True,
                "page_start": paragraph["page_start"],
                "page_end": paragraph["page_end"],
            })

    return units


def units_to_text(units: list[dict]) -> str:
    text = ""
    previous = None

    for unit in units:
        if previous is None:
            text = unit["text"]
        elif previous["para"] == unit["para"]:
            text = f"{text} {unit['text']}"
        else:
            text = f"{text}\n\n{unit['text']}"

        previous = unit

    return text


def pack_units(units: list[dict], max_chars: int, overlap_sentences: int) -> list[list[dict]]:
    groups = []
    current = []

    for unit in units:
        if not current:
            current = [unit]
            continue

        if len(units_to_text(current + [unit])) <= max_chars:
            current.append(unit)
            continue

        groups.append(current)

        carry = []
        if overlap_sentences > 0 and unit["sentence"] and current[-1]["sentence"]:
            carry = [
                u for u in current[-overlap_sentences:]
                if u["para"] == unit["para"]
            ]

        if carry and len(units_to_text(carry + [unit])) > max_chars:
            carry = []

        current = carry + [unit]

    if current:
        groups.append(current)

    return groups


# ---------------------------------------------------------------------------
# Public function (same signature as before, new optional settings)
# ---------------------------------------------------------------------------

def create_chunks(
    pages: list[dict],
    document_id: str,
    source: str,
    max_chars: int = 1500,
    min_chars: int = 150,
    overlap_sentences: int = 1,
) -> list[DocumentChunk]:

    lines = flatten_lines(pages)

    if not lines:
        return []

    stats = compute_stats(lines)
    sections = build_sections(lines, stats)
    sections = merge_tiny_sections(sections, min_chars, max_chars)

    chunks = []

    for section in sections:
        units = section_units(section, max_chars)

        for group in pack_units(units, max_chars, overlap_sentences):
            text = units_to_text(group).strip()

            if not text:
                continue

            chunks.append(
                DocumentChunk(
                    chunk_id=str(uuid4()),
                    document_id=document_id,
                    source=source,
                    page_number=min(u["page_start"] for u in group),
                    section=section["path"],
                    text=text,
                    page_end=max(u["page_end"] for u in group),
                    chunk_index=len(chunks),
                )
            )

    return chunks
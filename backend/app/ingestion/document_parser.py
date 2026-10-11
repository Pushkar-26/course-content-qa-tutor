from pathlib import Path
import pymupdf


def extract_pdf(path: Path) -> list[dict]:
    document = pymupdf.open(path)
    pages = []

    try:
        for page_number, page in enumerate(document, start=1):
            blocks = page.get_text("dict")["blocks"]
            lines = []

            for block in blocks:
                if block.get("type") != 0:
                    continue

                for line in block.get("lines", []):
                    spans = line.get("spans", [])

                    text = "".join(
                        span.get("text", "")
                        for span in spans
                    ).strip()

                    if not text:
                        continue

                    font_size = max(
                        (span.get("size", 0) for span in spans),
                        default=0
                    )

                    is_bold = any(
                        "bold" in span.get("font", "").lower()
                        for span in spans
                    )

                    bbox = line.get("bbox", [0, 0, 0, 0])

                    lines.append({
                        "text": text,
                        "font_size": font_size,
                        "bold": is_bold,
                        "x0": bbox[0],
                        "y0": bbox[1],
                        "x1": bbox[2],
                        "y1": bbox[3]
                    })

            if lines:
                pages.append({
                    "page_number": page_number,
                    "lines": lines
                })

    finally:
        document.close()

    return pages
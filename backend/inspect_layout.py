from pathlib import Path

from app.ingestion.document_parser import extract_pdf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
upload_dir = PROJECT_ROOT / "data" / "uploads"

pdf_files = list(upload_dir.glob("*.pdf"))

if not pdf_files:
    print("No PDF found in data/uploads")
    raise SystemExit(1)

pdf_path = max(pdf_files, key=lambda path: path.stat().st_mtime)

print("Using PDF:", pdf_path.name)

pages = extract_pdf(pdf_path)

for page in pages:
    print(f"\n========== PAGE {page['page_number']} ==========")

    for line in page["lines"]:
        print(
            f"text={line['text']!r} | "
            f"size={line['font_size']:.1f} | "
            f"bold={line['bold']} | "
            f"x0={line['x0']:.1f} | "
            f"y0={line['y0']:.1f}"
        )
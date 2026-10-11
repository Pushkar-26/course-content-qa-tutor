import re
from pathlib import Path

from app.ingestion.chunker import create_chunks
from app.ingestion.document_parser import extract_pdf
from app.ingestion.text_cleaner import clean_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
upload_dir = PROJECT_ROOT / "data" / "uploads"

pdf_files = list(upload_dir.glob("*.pdf"))

if not pdf_files:
    print("No PDF found in data/uploads")
    raise SystemExit(1)

pdf_path = max(pdf_files, key=lambda path: path.stat().st_mtime)

document_id = pdf_path.stem
source = pdf_path.name

print("Using PDF:", pdf_path.name)

pages = extract_pdf(pdf_path)

for page in pages:
    for line in page["lines"]:
        line["text"] = clean_text(line["text"])

chunks = create_chunks(
    pages=pages,
    document_id=document_id,
    source=source
)

print(f"Pages: {len(pages)}")
print(f"Chunks: {len(chunks)}")

for chunk in chunks:
    print(f"\n========== CHUNK {chunk.chunk_index + 1} ==========")
    print("Chunk ID:", chunk.chunk_id)
    print("Pages:", chunk.page_number, "-", chunk.page_end)
    print("Section:", chunk.section)
    print("Source:", chunk.source)
    print("Length:", len(chunk.text), "chars")
    print("\nText:")
    print(chunk.text)


# Coverage check:
# Verify that every extracted line is present somewhere
# in the generated chunks or section metadata.
def squash(value: str) -> str:
    return re.sub(r"\s+", "", value)


all_chunk_text = squash(
    "".join(
        (chunk.section or "") + chunk.text
        for chunk in chunks
    )
)

missing = [
    line["text"]
    for page in pages
    for line in page["lines"]
    if squash(line["text"]) not in all_chunk_text
]

print("\n========== COVERAGE CHECK ==========")
print("Missing lines:", len(missing))

for text in missing:
    print(" -", text)
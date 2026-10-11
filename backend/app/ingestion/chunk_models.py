from dataclasses import dataclass


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    source: str
    page_number: int
    section: str | None
    text: str
    page_end: int | None = None
    chunk_index: int = 0

    def embedding_text(self) -> str:
        """Text to send to the embedding model: section path + body."""
        if self.section:
            return f"{self.section}\n\n{self.text}"
        return self.text
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from docchunker import DocChunker
from transformers import dataclass

import enneai.ai.rag.storage as storage

logger = logging.getLogger("ingest")


@dataclass(slots=True)
class BookMetadata:
    book_id: str | None = None
    title: str | None = None
    author: str | None = None
    language: str | None = None
    category: str | None = None
    about: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "book_id": self.book_id,
                "title": self.title,
                "author": self.author,
                "language": self.language,
                "category": self.category,
                "about": self.about
            }.items()
            if value is not None
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        self.book_id = data.get("book_id")
        self.title = data.get("title")
        self.author = data.get("author")
        self.language = data.get("language")
        self.category = data.get("category")
        self.about = data.get("about")

def _slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\-]+", "-", text, flags=re.UNICODE)
    return re.sub(r"-{2,}", "-", text).strip("-")


async def ingest_one(
    path: Path,
    *,
    metadata: BookMetadata | None = None,
    chunk_size: int,
    overlap: int,
    replace: bool,
) -> int:
    if not path.exists():
        raise FileNotFoundError(path)

    if metadata is None:
        metadata = BookMetadata()

    metadata.book_id = metadata.book_id or _slug(path.stem)
    metadata.title = metadata.title or path.stem

    if replace:
        logger.info("Removing existing chunks for book_id=%r", metadata.book_id)
        await storage.delete_book(metadata.book_id)

    chunker = DocChunker(chunk_size=chunk_size, num_overlapping_elements=overlap)
    logger.info("Chunking %s ...", path)
    chunks = chunker.process_document(str(path))
    logger.info("%d raw chunks from %s", len(chunks), path.name)

    n = await storage.upsert_document_chunks(
        metadata=metadata.to_dict(),
        source_path=str(path),
        raw_chunks=chunks
    )
    logger.info("Indexed %d chunks for %r (book_id=%s)", n, metadata.title, metadata.book_id)
    return n
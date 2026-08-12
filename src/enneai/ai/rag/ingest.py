from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
from pathlib import Path

from docchunker import DocChunker

import enneai.ai.rag.storage as storage

logger = logging.getLogger("ingest")


def _slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\-]+", "-", text, flags=re.UNICODE)
    return re.sub(r"-{2,}", "-", text).strip("-")


async def ingest_one(
    path: Path,
    *,
    book_id: str,
    title: str,
    language: str | None,
    chunk_size: int,
    overlap: int,
    replace: bool,
) -> int:
    if not path.exists():
        raise FileNotFoundError(path)

    if replace:
        logger.info("Removing existing chunks for book_id=%r", book_id)
        await storage.delete_book(book_id)

    chunker = DocChunker(chunk_size=chunk_size, num_overlapping_elements=overlap)
    logger.info("Chunking %s ...", path)
    chunks = chunker.process_document(str(path))
    logger.info("%d raw chunks from %s", len(chunks), path.name)

    n = await storage.upsert_document_chunks(
        book_id=book_id,
        book_title=title,
        source_path=str(path),
        raw_chunks=chunks,
        language=language,
    )
    logger.info("Indexed %d chunks for %r (book_id=%s)", n, title, book_id)
    return n


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest books into the RAG Qdrant collection")
    parser.add_argument("path", nargs="?", help="Path to a single PDF/DOCX file")
    parser.add_argument("--book-id", help="Stable id for the book (default: slug of filename)")
    parser.add_argument("--title", help="Book title stored in payload (default: filename)")
    parser.add_argument("--language", help="ISO language code, e.g. ru / en")
    parser.add_argument("--manifest", help="JSON file listing multiple books to ingest")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=1)
    parser.add_argument("--replace", action="store_true", help="Delete existing chunks for this book_id first")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    await storage.ensure_collection()

    jobs: list[dict] = []
    if args.manifest:
        entries = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        for e in entries:
            p = Path(e["path"])
            jobs.append(
                dict(
                    path=p,
                    book_id=e.get("book_id") or _slug(p.stem),
                    title=e.get("title") or p.stem,
                    language=e.get("language"),
                )
            )
    elif args.path:
        p = Path(args.path)
        jobs.append(
            dict(
                path=p,
                book_id=args.book_id or _slug(p.stem),
                title=args.title or p.stem,
                language=args.language,
            )
        )
    else:
        parser.error("Provide either a file path or --manifest")

    total = 0
    for job in jobs:
        total += await ingest_one(
            job["path"],
            book_id=job["book_id"],
            title=job["title"],
            language=job["language"],
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            replace=args.replace,
        )

    logger.info("Done: %d chunks indexed across %d book(s).", total, len(jobs))


if __name__ == "__main__":
    asyncio.run(main())
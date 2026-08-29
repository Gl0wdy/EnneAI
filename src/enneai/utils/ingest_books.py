import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from enneai.ai.rag.storage import BookMetadata
from enneai.ai.rag.ingest import ingest_one

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def load_metadata(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: metadata.json should contain a JSON object")
    return data


def discover_books_dirs(data_dir: Path) -> list[Path]:
    if not data_dir.exists():
        raise FileNotFoundError(data_dir)
    return [
        typology_dir / "books"
        for typology_dir in sorted(data_dir.iterdir())
        if typology_dir.is_dir() and (typology_dir / "books").is_dir()
    ]


def metadata_from_dict(data: dict[str, Any]) -> BookMetadata:
    return BookMetadata(
        book_id=data.get("book_id"),
        title=data.get("title"),
        author=data.get("author"),
        language=data.get("language"),
        category=data.get("category"),
        about=data.get("about"),
    )


async def ingest_books_dir(books_dir: Path, *, chunk_size: int, overlap: int, replace: bool) -> int:
    metadata_path = books_dir / "metadata.json"
    if not metadata_path.exists():
        logger.warning("Skipping %s: metadata.json not found", books_dir)
        return 0

    metadata = load_metadata(metadata_path)
    total = 0

    for filename, book_data in metadata.items():
        if not isinstance(book_data, dict):
            logger.warning("Skipping %s: metadata should be a JSON object", filename)
            continue

        book_path = books_dir / filename
        if not book_path.exists():
            logger.warning("File from metadata.json not found: %s", book_path)
            continue

        if book_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.warning("Unsupported format: %s", book_path)
            continue

        logger.info("-> %s / %s", books_dir.parent.name, filename)
        try:
            count = await ingest_one(
                book_path,
                metadata=metadata_from_dict(book_data),
                chunk_size=chunk_size,
                overlap=overlap,
                replace=replace,
            )
        except Exception:
            logger.exception("Failed to ingest %s, skipping", book_path)
            continue

        total += count

    return total


async def ingest_all(*, data_dir: Path, chunk_size: int, overlap: int, replace: bool) -> None:
    books_dirs = discover_books_dirs(data_dir)
    if not books_dirs:
        logger.warning("Skipping %s: no books directories found", data_dir)
        return

    logger.info("Found typologies: %d", len(books_dirs))
    grand_total = 0

    for books_dir in books_dirs:
        typology = books_dir.parent.name
        logger.info("========== %s ==========", typology)
        total = await ingest_books_dir(books_dir, chunk_size=chunk_size, overlap=overlap, replace=replace)
        grand_total += total
        logger.info("%s: indexed %d chunks", typology, total)

    logger.info("========== DONE: %d chunks ==========", grand_total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default="data")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--overlap", type=int, default=100)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s | %(levelname)s | %(message)s")

    asyncio.run(ingest_all(
        data_dir=args.data_dir,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        replace=args.replace,
    ))


if __name__ == "__main__":
    main()
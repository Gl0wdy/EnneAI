import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable

from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qm

from enneai.ai.rag.embeddings import DENSE_VECTOR_SIZE, get_embedding_service

from enneai.utils.logger import logger

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
COLLECTION_NAME = os.getenv("RAG_COLLECTION", "typology_books")

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"

HNSW_M = int(os.getenv("RAG_HNSW_M", "16"))
HNSW_EF_CONSTRUCT = int(os.getenv("RAG_HNSW_EF_CONSTRUCT", "128"))
ON_DISK_PAYLOAD = os.getenv("RAG_ON_DISK_PAYLOAD", "false").lower() == "true"
INGEST_BATCH_SIZE = int(os.getenv("RAG_INGEST_BATCH_SIZE", "32"))
MIN_CHUNK_CHARS = int(os.getenv("RAG_MIN_CHUNK_CHARS", "150"))

_NAMESPACE = uuid.UUID("6f2f1d0a-9d2b-4c9b-8b6b-9a2f9e2c9d10")

_client: AsyncQdrantClient | None = None
_client_lock = asyncio.Lock()


@dataclass(slots=True)
class BookMetadata:
    book_id: str | None = None
    title: str | None = None
    author: str | None = None
    language: str | None = None
    category: str | None = None
    about: str | None = None


@dataclass(slots=True)
class ScoredChunk:
    chunk_id: str
    book_id: str
    book_title: str
    text: str
    embedded_text: str
    headings: list[str] = field(default_factory=list)
    node_type: str | None = None
    chunk_index: int = 0
    score: float = 0.0
    source_path: str | None = None
    language: str | None = None
    book_author: str | None = None
    category: str | None = None
    about: str | None = None


async def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        async with _client_lock:
            if _client is None:
                _client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return _client


async def ensure_collection() -> None:
    client = await get_client()

    if not await client.collection_exists(COLLECTION_NAME):
        logger.info("Creating Qdrant collection %r", COLLECTION_NAME)
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                DENSE_VECTOR_NAME: qm.VectorParams(
                    size=DENSE_VECTOR_SIZE,
                    distance=qm.Distance.COSINE,
                    hnsw_config=qm.HnswConfigDiff(m=HNSW_M, ef_construct=HNSW_EF_CONSTRUCT),
                ),
            },
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: qm.SparseVectorParams(
                    modifier=qm.Modifier.IDF,
                    index=qm.SparseIndexParams(on_disk=False),
                ),
            },
            on_disk_payload=ON_DISK_PAYLOAD,
        )

    for field_name, schema in (
        ("book_id", qm.PayloadSchemaType.KEYWORD),
        ("language", qm.PayloadSchemaType.KEYWORD),
        ("category", qm.PayloadSchemaType.KEYWORD),
        ("node_type", qm.PayloadSchemaType.KEYWORD),
        ("headings_text", qm.PayloadSchemaType.TEXT),
    ):
        try:
            await client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=schema,
            )
        except Exception:
            pass


def _chunk_point_id(book_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(_NAMESPACE, f"{book_id}:{chunk_index}"))


def _extract_headings(metadata: dict[str, Any]) -> list[str]:
    headings = metadata.get("headings") or []
    if isinstance(headings, str):
        headings = [headings]
    return [str(h).strip() for h in headings if str(h).strip()]


def _build_embedded_text(headings: list[str], text: str) -> str:
    if not headings:
        return text
    return " > ".join(headings) + "\n\n" + text


def _merge_small_chunks(prepared: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not prepared:
        return prepared

    merged: list[dict[str, Any]] = []
    i = 0
    n = len(prepared)
    while i < n:
        current = prepared[i]
        if len(current["text"].strip()) < MIN_CHUNK_CHARS:
            if i + 1 < n and prepared[i + 1]["headings"] == current["headings"]:
                nxt = prepared[i + 1]
                nxt["text"] = current["text"].strip() + "\n" + nxt["text"].strip()
                i += 1
                continue
            if merged and merged[-1]["headings"] == current["headings"]:
                merged[-1]["text"] = merged[-1]["text"].strip() + "\n" + current["text"].strip()
                i += 1
                continue
            logger.warning("Orphan short chunk kept as-is: %r", current["text"][:80])
        merged.append(current)
        i += 1
    return merged


async def upsert_document_chunks(
    *,
    metadata: BookMetadata,
    source_path: str | None,
    raw_chunks: Iterable[Any],
    batch_size: int = INGEST_BATCH_SIZE,
) -> int:
    if not metadata.book_id:
        raise ValueError("metadata.book_id is required")

    await ensure_collection()
    client = await get_client()
    embedder = get_embedding_service()

    prepared: list[dict[str, Any]] = []
    for raw in raw_chunks:
        text = getattr(raw, "text", "") or ""
        if not text.strip():
            continue
        raw_metadata = getattr(raw, "metadata", None) or {}
        prepared.append(
            {
                "text": text,
                "headings": _extract_headings(raw_metadata),
                "node_type": raw_metadata.get("node_type"),
            }
        )

    prepared = _merge_small_chunks(prepared)

    for idx, p in enumerate(prepared):
        p["chunk_index"] = idx
        p["embedded_text"] = _build_embedded_text(p["headings"], p["text"])

    total = 0
    for start in range(0, len(prepared), batch_size):
        batch = prepared[start : start + batch_size]
        if not batch:
            continue

        texts = [p["embedded_text"] for p in batch]
        dense_vectors, sparse_vectors = await asyncio.gather(
            embedder.embed_passages(texts),
            embedder.embed_passages_sparse(texts),
        )

        points = []
        for p, dense_vec, sparse_vec in zip(batch, dense_vectors, sparse_vectors):
            point_id = _chunk_point_id(metadata.book_id, p["chunk_index"])
            points.append(
                qm.PointStruct(
                    id=point_id,
                    vector={
                        DENSE_VECTOR_NAME: dense_vec,
                        SPARSE_VECTOR_NAME: sparse_vec.as_qdrant(),
                    },
                    payload={
                        "chunk_id": point_id,
                        "book_id": metadata.book_id,
                        "book_title": metadata.title,
                        "book_author": metadata.author,
                        "category": metadata.category,
                        "about": metadata.about,
                        "source_path": source_path,
                        "chunk_index": p["chunk_index"],
                        "text": p["text"],
                        "embedded_text": p["embedded_text"],
                        "headings": p["headings"],
                        "headings_text": " > ".join(p["headings"]),
                        "node_type": p["node_type"],
                        "language": metadata.language,
                        "char_count": len(p["text"]),
                    },
                )
            )

        await client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
        total += len(points)
        logger.info("Upserted %d chunks for book_id=%r", len(points), metadata.book_id)

    return total


async def delete_book(book_id: str) -> None:
    client = await get_client()
    await client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(
                must=[qm.FieldCondition(key="book_id", match=qm.MatchValue(value=book_id))]
            )
        ),
    )


async def collection_stats() -> dict[str, Any]:
    client = await get_client()
    info = await client.get_collection(COLLECTION_NAME)
    return {
        "points_count": info.points_count,
        "vectors_count": info.vectors_count,
        "status": info.status,
    }
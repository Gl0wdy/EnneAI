from __future__ import annotations

import asyncio
import logging
from typing import Any

from qdrant_client import models as qm

try: 
    from .embeddings import get_embedding_service
    from enneai.ai.rag.storage import (
        COLLECTION_NAME,
        DENSE_VECTOR_NAME,
        SPARSE_VECTOR_NAME,
        ScoredChunk,
        get_client,
    )
except ImportError: 
    from enneai.ai.rag.embeddings import get_embedding_service
    from enneai.ai.rag.storage import (
        COLLECTION_NAME,
        DENSE_VECTOR_NAME,
        SPARSE_VECTOR_NAME,
        ScoredChunk,
        get_client,
    )

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 8
DEFAULT_PREFETCH_LIMIT = 25


def _build_filter(
    heading_query: str | None,
    metadata: dict[str, str] | None = None,
) -> qm.Filter | None:
    must: list[qm.Condition] = []

    if metadata:
        for key, value in metadata.items():
            if value is not None:
                must.append(
                    qm.FieldCondition(
                        key=key,
                        match=qm.MatchValue(value=value),
                    )
                )

    if heading_query:
        must.append(
            qm.FieldCondition(
                key="headings_text",
                match=qm.MatchText(text=heading_query),
            )
        )

    if metadata:
        for key, value in metadata.items():
            if value is not None:
                must.append(
                    qm.FieldCondition(
                        key=key,
                        match=qm.MatchValue(value=value),
                    )
                )

    return qm.Filter(must=must) if must else None


def _point_to_chunk(point: qm.ScoredPoint) -> ScoredChunk:
    payload = point.payload or {}
    return ScoredChunk(
        chunk_id=str(point.id),
        book_id=payload.get("book_id", ""),
        book_title=payload.get("book_title", ""),
        text=payload.get("text", ""),
        embedded_text=payload.get("embedded_text", payload.get("text", "")),
        headings=payload.get("headings") or [],
        node_type=payload.get("node_type"),
        chunk_index=payload.get("chunk_index", 0),
        score=point.score,
        source_path=payload.get("source_path"),
        language=payload.get("language"),
    )


async def hybrid_search(
    query: str,
    *,
    metadata: dict[str, str] | None = None,
    heading_query: str | None = None,
    limit: int = DEFAULT_LIMIT,
    dense_prefetch_limit: int = DEFAULT_PREFETCH_LIMIT,
    sparse_prefetch_limit: int = DEFAULT_PREFETCH_LIMIT,
) -> list[ScoredChunk]:

    if not query.strip():
        return []

    embedder = get_embedding_service()

    dense_vec, sparse_vec = await asyncio.gather(
        embedder.embed_query(query),
        embedder.embed_query_sparse(query),
    )

    query_filter = _build_filter(
        heading_query=heading_query,
        metadata=metadata,
    )

    client = await get_client()
    result = await client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            qm.Prefetch(
                query=dense_vec,
                using=DENSE_VECTOR_NAME,
                limit=dense_prefetch_limit,
                filter=query_filter,
            ),
            qm.Prefetch(
                query=sparse_vec.as_qdrant(),
                using=SPARSE_VECTOR_NAME,
                limit=sparse_prefetch_limit,
                filter=query_filter,
            ),
        ],
        query=qm.FusionQuery(fusion=qm.Fusion.RRF),
        limit=limit,
        with_payload=True,
    )

    chunks = [_point_to_chunk(p) for p in result.points]

    logger.debug(
        "hybrid_search(%r) -> %d chunks",
        query,
        len(chunks),
    )

    return chunks


async def dense_search(query: str, *, metadata: dict[str, str] | None = None, limit: int = DEFAULT_LIMIT) -> list[ScoredChunk]:
    embedder = get_embedding_service()
    dense_vec = await embedder.embed_query(query)
    client = await get_client()
    result = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=dense_vec,
        using=DENSE_VECTOR_NAME,
        query_filter=_build_filter(metadata, None),
        limit=limit,
        with_payload=True,
    )
    return [_point_to_chunk(p) for p in result.points]


async def sparse_search(query: str, *, metadata: dict[str, str] | None = None, limit: int = DEFAULT_LIMIT) -> list[ScoredChunk]:
    embedder = get_embedding_service()
    sparse_vec = await embedder.embed_query_sparse(query)
    client = await get_client()
    result = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=sparse_vec.as_qdrant(),
        using=SPARSE_VECTOR_NAME,
        query_filter=_build_filter(metadata, None),
        limit=limit,
        with_payload=True,
    )
    return [_point_to_chunk(p) for p in result.points]
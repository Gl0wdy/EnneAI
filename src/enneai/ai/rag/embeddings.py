from __future__ import annotations

import asyncio
import logging
import os
import threading
from dataclasses import dataclass, field
from functools import lru_cache

from fastembed import SparseTextEmbedding
from qdrant_client import models as qm
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DENSE_MODEL_NAME = os.getenv("RAG_DENSE_MODEL", "intfloat/multilingual-e5-base")
DENSE_VECTOR_SIZE = int(os.getenv("RAG_DENSE_VECTOR_SIZE", "768"))

SPARSE_MODEL_NAME = os.getenv("RAG_SPARSE_MODEL", "Qdrant/bm25")

DEVICE = os.getenv("RAG_EMBED_DEVICE", "cpu")
ENCODE_BATCH_SIZE = int(os.getenv("RAG_ENCODE_BATCH_SIZE", "16"))

_E5_QUERY_PREFIX = "query: "
_E5_PASSAGE_PREFIX = "passage: "

_torch_threads = os.getenv("RAG_TORCH_THREADS")
if _torch_threads:
    try:
        import torch

        torch.set_num_threads(int(_torch_threads))
    except Exception:
        logger.warning("Could not set torch thread count", exc_info=True)

_model_lock = threading.Lock()


@dataclass(slots=True)
class SparseVector:
    indices: list[int] = field(default_factory=list)
    values: list[float] = field(default_factory=list)

    def as_qdrant(self) -> qm.SparseVector:
        return qm.SparseVector(indices=self.indices, values=self.values)


class EmbeddingService:
    _instance: "EmbeddingService | None" = None

    def __init__(self) -> None:
        logger.info("Loading dense encoder %r on %r", DENSE_MODEL_NAME, DEVICE)
        self._dense = SentenceTransformer(DENSE_MODEL_NAME, device=DEVICE)

        logger.info("Loading sparse (BM25) encoder %r", SPARSE_MODEL_NAME)
        self._sparse = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)

    @classmethod
    def get(cls) -> "EmbeddingService":
        if cls._instance is None:
            with _model_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    async def warmup(cls) -> "EmbeddingService":
        """Call once at application startup so the (slow, blocking) model
        loading happens before the first request instead of during it."""
        return await asyncio.to_thread(cls.get)

    def _encode_dense_sync(self, texts: list[str], is_query: bool) -> list[list[float]]:
        prefix = _E5_QUERY_PREFIX if is_query else _E5_PASSAGE_PREFIX
        prefixed = [prefix + t for t in texts]
        vectors = self._dense.encode(
            prefixed,
            batch_size=ENCODE_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    async def embed_query(self, text: str) -> list[float]:
        vectors = await asyncio.to_thread(self._encode_dense_sync, [text], True)
        return vectors[0]

    async def embed_passages(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._encode_dense_sync, texts, False)

    def _encode_sparse_sync(self, texts: list[str]) -> list[SparseVector]:
        embeddings = list(self._sparse.embed(texts))
        return [
            SparseVector(indices=e.indices.tolist(), values=e.values.tolist())
            for e in embeddings
        ]

    async def embed_query_sparse(self, text: str) -> SparseVector:
        result = await asyncio.to_thread(self._encode_sparse_sync, [text])
        return result[0]

    async def embed_passages_sparse(self, texts: list[str]) -> list[SparseVector]:
        if not texts:
            return []
        return await asyncio.to_thread(self._encode_sparse_sync, texts)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService.get()
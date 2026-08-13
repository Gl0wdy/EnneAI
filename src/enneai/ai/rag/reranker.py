from __future__ import annotations

import asyncio
import logging
import os
import threading
from dataclasses import dataclass

from sentence_transformers import CrossEncoder

try: 
    from .storage import ScoredChunk
except ImportError: 
    from enneai.ai.rag.storage import ScoredChunk

logger = logging.getLogger(__name__)

RERANKER_MODEL_NAME = os.getenv("RAG_RERANKER_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
DEVICE = os.getenv("RAG_EMBED_DEVICE", "cpu")
RERANK_BATCH_SIZE = int(os.getenv("RAG_RERANK_BATCH_SIZE", "16"))
RERANK_MAX_LENGTH = int(os.getenv("RAG_RERANK_MAX_LENGTH", "512"))

_model_lock = threading.Lock()


@dataclass(slots=True)
class RankedChunk(ScoredChunk):
    rerank_score: float = 0.0


class Reranker:
    _instance: "Reranker | None" = None

    def __init__(self) -> None:
        logger.info("Loading reranker %r on %r", RERANKER_MODEL_NAME, DEVICE)
        self._model = CrossEncoder(RERANKER_MODEL_NAME, max_length=RERANK_MAX_LENGTH, device=DEVICE)

    @classmethod
    def get(cls) -> "Reranker":
        if cls._instance is None:
            with _model_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    async def warmup(cls) -> "Reranker":
        return await asyncio.to_thread(cls.get)

    def _predict_sync(self, query: str, passages: list[str]) -> list[float]:
        pairs = [(query, p) for p in passages]
        scores = self._model.predict(
            pairs,
            batch_size=RERANK_BATCH_SIZE,
            show_progress_bar=False,
        )
        return scores.tolist()

    async def rerank(
        self,
        query: str,
        chunks: list[ScoredChunk],
        *,
        top_n: int = 6,
    ) -> list[RankedChunk]:
        if not chunks:
            return []

        passages = [c.embedded_text or c.text for c in chunks]
        scores = await asyncio.to_thread(self._predict_sync, query, passages)

        ranked = sorted(zip(chunks, scores), key=lambda pair: pair[1], reverse=True)
        return [
            RankedChunk(
                chunk_id=c.chunk_id,
                book_id=c.book_id,
                book_title=c.book_title,
                text=c.text,
                embedded_text=c.embedded_text,
                headings=c.headings,
                node_type=c.node_type,
                chunk_index=c.chunk_index,
                score=c.score,
                source_path=c.source_path,
                language=c.language,
                rerank_score=float(score),
            )
            for c, score in ranked[:top_n]
        ]
from __future__ import annotations

import asyncio
import logging

try:
    from .context import RagContext, build_context
    from .embeddings import EmbeddingService
    from .reranker import Reranker
    from .retrieval import hybrid_search
    from .storage import ensure_collection
except ImportError:
    from enneai.ai.rag.context import RagContext, build_context
    from enneai.ai.rag.embeddings import EmbeddingService
    from enneai.ai.rag.reranker import Reranker
    from enneai.ai.rag.retrieval import hybrid_search
    from enneai.ai.rag.storage import ensure_collection

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE_LIMIT = 25
DEFAULT_RERANK_TOP_N = 6
DEFAULT_MAX_CONTEXT_CHARS = 6000


async def warmup() -> None:
    await asyncio.gather(
        EmbeddingService.warmup(),
        Reranker.warmup(),
        ensure_collection(),
    )
    logger.info("RAG pipeline warm.")


async def retrieve(
    query: str,
    *,
    metadata: dict[str, str] | None = None,
    heading_query: str | None = None,
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
    rerank_top_n: int = DEFAULT_RERANK_TOP_N,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
) -> RagContext:
    candidates = await hybrid_search(
        query,
        metadata=metadata,
        heading_query=heading_query,
        limit=candidate_limit,
    )
    if not candidates:
        return RagContext(text="", sources=[])

    reranker = Reranker.get()
    ranked = await reranker.rerank(query, candidates, top_n=rerank_top_n)

    return build_context(ranked, max_chars=max_context_chars)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    async def _main() -> None:
        q = " ".join(sys.argv[1:]) or "Невроз сп3"
        await warmup()
        result = await retrieve(q)
        if result.is_empty:
            print("Ничего не найдено.")
            return
        print(result.text)
        print("\n--- sources ---")
        for src in result.sources:
            heading = " > ".join(src.headings) if src.headings else "-"
            print(f"[{src.index}] {src.book_title} | {heading} | score={src.score:.3f}")

    asyncio.run(_main())
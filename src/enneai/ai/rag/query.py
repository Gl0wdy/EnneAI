import asyncio
import logging

from .context import RagContext, build_context
from .embeddings import EmbeddingService
from .reranker import Reranker
from .retrieval import hybrid_search
from .storage import ensure_collection

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE_LIMIT = 40
DEFAULT_RERANK_TOP_N = 15
DEFAULT_MAX_CONTEXT_CHARS = 12000


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
    book_id: str | None = None,
    category: str | None = None,
    heading_query: str | None = None,
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
    rerank_top_n: int = DEFAULT_RERANK_TOP_N,
    score_threshold: float | None = None,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
) -> RagContext:
    candidates = await hybrid_search(
        query,
        book_id=book_id,
        category=category,
        heading_query=heading_query,
        limit=candidate_limit,
    )
    if not candidates:
        return RagContext(text="", sources=[], chunks=[])

    reranker = Reranker.get()
    ranked = await reranker.rerank(query, candidates, top_n=rerank_top_n, score_threshold=score_threshold)

    return build_context(ranked, max_chars=max_context_chars)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    async def _main():
        q = " ".join(sys.argv[1:]) or "Что отличает Enneagram Type 4 от Type 9?"
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
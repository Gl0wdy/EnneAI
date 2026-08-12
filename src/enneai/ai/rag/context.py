from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

try: 
    from .reranker import RankedChunk
except ImportError:  # direct script run
    from enneai.ai.rag.reranker import RankedChunk

DEFAULT_MAX_CONTEXT_CHARS = 6000


@dataclass(slots=True)
class SourceRef:
    index: int
    book_id: str
    book_title: str
    headings: list[str]
    chunk_id: str
    score: float


@dataclass(slots=True)
class RagContext:
    text: str
    sources: list[SourceRef] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.sources


def _dedupe_key(chunk: RankedChunk) -> str:
    normalized = " ".join(chunk.text.split()).lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def build_context(
    chunks: list[RankedChunk],
    *,
    max_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    dedupe: bool = True,
) -> RagContext:
    parts: list[str] = []
    sources: list[SourceRef] = []
    seen: set[str] = set()
    used_chars = 0

    for chunk in chunks:
        if dedupe:
            key = _dedupe_key(chunk)
            if key in seen:
                continue
            seen.add(key)

        heading_path = " > ".join(chunk.headings) if chunk.headings else None
        header_line = f"[{len(sources) + 1}] {chunk.book_title}" + (
            f" -- {heading_path}" if heading_path else ""
        )
        block = f"{header_line}\n{chunk.text.strip()}"

        # Always include at least one chunk, even if it alone exceeds the
        # budget -- an empty context is worse than a slightly oversized one.
        if used_chars + len(block) > max_chars and parts:
            break

        parts.append(block)
        used_chars += len(block)
        sources.append(
            SourceRef(
                index=len(sources) + 1,
                book_id=chunk.book_id,
                book_title=chunk.book_title,
                headings=chunk.headings,
                chunk_id=chunk.chunk_id,
                score=chunk.rerank_score,
            )
        )

    return RagContext(text="\n\n".join(parts), sources=sources)
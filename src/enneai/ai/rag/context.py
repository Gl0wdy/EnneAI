import hashlib
from dataclasses import asdict, dataclass, field

from enneai.ai.rag.reranker import RankedChunk

DEFAULT_MAX_CONTEXT_CHARS = 12000


@dataclass(slots=True)
class SourceRef:
    index: int
    book_id: str
    book_title: str
    headings: list[str]
    chunk_id: str
    score: float
    book_author: str | None = None
    category: str | None = None


@dataclass(slots=True)
class RagContext:
    text: str
    sources: list[SourceRef] = field(default_factory=list)
    chunks: list[dict] = field(default_factory=list)  # raw chunk data, все поля включая rerank_score

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
    parts = []
    sources = []
    raw_chunks = []
    seen = set()
    used_chars = 0

    for chunk in chunks:
        if dedupe:
            key = _dedupe_key(chunk)
            if key in seen:
                continue
            seen.add(key)

        heading_path = " > ".join(chunk.headings) if chunk.headings else None
        by_line = f" (автор: {chunk.book_author})" if chunk.book_author else ""
        header_line = f"[{len(sources) + 1}] {chunk.book_title}{by_line}" + (
            f" -- {heading_path}" if heading_path else ""
        )
        block = f"{header_line}\n{chunk.text.strip()}"

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
                book_author=chunk.book_author,
                category=chunk.category,
            )
        )
        raw_chunks.append(asdict(chunk))

    return RagContext(text="\n\n".join(parts), sources=sources, chunks=raw_chunks)
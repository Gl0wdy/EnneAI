from __future__ import annotations

import asyncio
from html import unescape
import re
from typing import Any

import aiohttp
from ddgs import DDGS
from trafilatura import extract

from enneai.utils.logger import logger


LIMIT = 50
TIMEOUT = 20.0
MAX_CHARS = 128_000
MAX_PAGE_BYTES = 8_000_000

HEADERS = {
    "User-Agent": "EnneAI/0.1, +https://github.com/Gl0wdy/EnneAI"
}

def normalize_text(text: str) -> str:
    text = unescape(text).replace("\xa0", " ")

    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.splitlines()
    ]

    return re.sub(
        r"\n{3,}",
        "\n\n",
        "\n".join(line for line in lines if line),
    )


async def fetch_page(
    session: aiohttp.ClientSession,
    result: dict[str, Any],
    max_page_bytes: int = MAX_PAGE_BYTES,
) -> str | None:
    url = result.get("href") or result.get("url")

    # if not url or not ensure(url):
    #     return None

    try:
        async with session.get(
            url,
            allow_redirects=True,
        ) as response:

            if response.status >= 400:
                return None

            if response.content_type not in {
                "text/html",
                "application/xhtml+xml",
            }:
                return None

            body = await response.content.read(max_page_bytes + 1)

            if len(body) > max_page_bytes:
                body = body[:max_page_bytes]

            html = body.decode(
                response.charset or "utf-8",
                errors="replace",
            )

    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
    ):
        return None

    parsed = extract(
    html,
    favor_precision=True, 
    deduplicate=True,
    include_tables=True,
    include_links=False,
)

    logger.debug(
        f"[extract] url={url} "
        f"html={len(html)} "
        f"parsed={len(parsed) if parsed else None}"
    )

    if parsed and len(parsed) >= 2000:
        return parsed
    return None


async def search(query: str) -> list[dict[str, Any]]:
    return await asyncio.to_thread(
        lambda: list(
            DDGS().text(
                query,
                max_results=LIMIT,
            )
        )
    )


async def scraper(query=None):
    if not query:
        return

    results = await search(query)

    timeout = aiohttp.ClientTimeout(
        total=TIMEOUT
    )

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=HEADERS,
    ) as session:

        pages = await asyncio.gather(
            *(
                fetch_page(
                    session,
                    result,
                    max_page_bytes=MAX_PAGE_BYTES,
                )
                for result in results
            ),
            return_exceptions=True,
        )

    context_parts: list[str] = []
    used_chars = 0

    for page in pages:
        if not isinstance(page, str):
            continue

        block = normalize_text(page)

        if not block:
            continue

        remaining_chars = MAX_CHARS - used_chars

        if remaining_chars <= 0:
            break

        if len(block) > remaining_chars:
            truncated = block[:remaining_chars].rsplit(None, 1)

            if truncated:
                block = truncated[0]
            else:
                block = block[:remaining_chars]

        context_parts.append(block)
        used_chars += len(block)

    return "\n\n".join(context_parts)


if __name__ == "__main__":
    query = input("query: ").strip()
    print(asyncio.run(scraper(query)))
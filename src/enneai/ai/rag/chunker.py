import asyncio
import json
import os
import re
from pathlib import Path

from enneai.ai.modules.chat import ChatClient
from enneai.utils.reader import PROJECT_ROOT, load_file

TYPOLOGIES = {"ennea", "psychosophy", "socio", "jungian"}
CHUNKER_PROMPT_PATH = "data/prompts/chunker.txt"


class ChunkerClient(ChatClient):
    def __init__(self, model=None):
        if model:
            super().__init__(prompt=CHUNKER_PROMPT_PATH, model=model)
        else:
            super().__init__(prompt=CHUNKER_PROMPT_PATH)

    def _build_payload(self, messages, model=None, stream=False, reasoning=True, max_tokens=None):
        payload = super()._build_payload(messages, model=model, stream=stream, reasoning=reasoning, max_tokens=max_tokens)
        payload["response_format"] = {"type": "json_object"}
        return payload

    async def chunk_window(self, window, book_title, typology, api_key=None, max_retries=3):
        messages = [
            {"role": "system", "content": self.prompt},
            {
                "role": "user",
                "content": f"Книга: {book_title}\nТипология по умолчанию: {typology}\n\nТекст:\n\n{window}",
            },
        ]

        last_error = None

        for attempt in range(max_retries):
            try:
                result = await self.get_discrete(messages, api_key=api_key, reasoning=False, max_tokens=6000)
                content = result["choices"][0]["message"]["content"]
                return self._parse_json(content)
            except Exception as exc:
                last_error = exc

                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)

        raise RuntimeError(f"Чанкинг окна не удался после {max_retries} попыток: {last_error}")

    @staticmethod
    def _parse_json(raw):
        raw = raw.strip()
        raw = re.sub(r"^```(json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
        return json.loads(raw)


class BookChunker:
    WINDOW_SIZE = 6000
    MAX_CONCURRENT_REQUESTS = 5

    def __init__(self, typology, filename, model=None, api_key=None, max_concurrent=None):
        if typology not in TYPOLOGIES:
            raise ValueError(f"Неизвестная типология '{typology}', ожидалось одно из {TYPOLOGIES}")

        self.typology = typology
        self.filename = filename
        self.book_title = Path(filename).stem
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.client = ChunkerClient(model=model)
        self.max_concurrent = max_concurrent or self.MAX_CONCURRENT_REQUESTS
        self.chunks = []

    async def run(self, save=True):
        text = load_file(f"data/{self.typology}/books/{self.filename}")
        windows = self._split_into_windows(text)
        semaphore = asyncio.Semaphore(self.max_concurrent)
        total = len(windows)

        results = await asyncio.gather(
            *(self._process_window(window, semaphore, i, total) for i, window in enumerate(windows))
        )

        for i, result in enumerate(results):
            raw_chunks = result.get("chunks", [])

            for raw_chunk in raw_chunks:
                self.chunks.append(self._build_record(raw_chunk, i))

        if save:
            self._save()

        return self.chunks

    async def _process_window(self, window, semaphore, index, total):
        async with semaphore:
            result = await self.client.chunk_window(window, self.book_title, self.typology, api_key=self.api_key)
            raw_chunks = result.get("chunks", [])
            print(f"[{self.book_title}] окно {index + 1}/{total} -> {len(raw_chunks)} чанков")
            return result

    def _build_record(self, raw_chunk, window_index):
        return {
            "id": f"{self.book_title}-{len(self.chunks):04d}",
            "title": raw_chunk.get("title", ""),
            "text": raw_chunk.get("text", ""),
            "typology_system": raw_chunk.get("typology_system", self.typology),
            "types_discussed": raw_chunk.get("types_discussed", []),
            "summary": raw_chunk.get("summary", ""),
            "source_book": self.book_title,
            "source_typology": self.typology,
            "window_index": window_index,
        }

    def _split_into_windows(self, text):
        paragraphs = re.split(r"\n{2,}", text)
        windows = []
        current = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()

            if not para:
                continue

            if len(para) > self.WINDOW_SIZE:
                if current:
                    windows.append("\n\n".join(current))
                    current, current_len = [], 0

                for i in range(0, len(para), self.WINDOW_SIZE):
                    windows.append(para[i : i + self.WINDOW_SIZE])

                continue

            if current and current_len + len(para) > self.WINDOW_SIZE:
                windows.append("\n\n".join(current))
                current, current_len = [], 0

            current.append(para)
            current_len += len(para) + 2

        if current:
            windows.append("\n\n".join(current))

        return windows

    def _save(self):
        out_dir = PROJECT_ROOT / "data" / self.typology / "chunks"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{self.book_title}.json"
        out_path.write_text(json.dumps(self.chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Сохранено: {out_path} ({len(self.chunks)} чанков)")


class TypologyChunker:
    def __init__(self, typology, model=None, api_key=None):
        self.typology = typology
        self.model = model
        self.api_key = api_key

    async def run(self):
        books_dir = PROJECT_ROOT / "data" / self.typology / "books"

        if not books_dir.exists():
            raise FileNotFoundError(f"Не найдена папка: {books_dir}")

        book_paths = [p for p in sorted(books_dir.iterdir()) if p.suffix.lower() in {".pdf", ".docx"}]

        if not book_paths:
            print(f"В {books_dir} нет .pdf/.docx файлов — обрабатывать нечего")
            return {}

        results = {}

        for book_path in book_paths:
            print(f"Начинаю обработку: {book_path.name}")
            chunker = BookChunker(self.typology, book_path.name, model=self.model, api_key=self.api_key)
            results[book_path.name] = await chunker.run()

        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM semantic chunker для книг по типологии")
    parser.add_argument("typology", choices=sorted(TYPOLOGIES))
    parser.add_argument("filename", nargs="?", help="Имя файла в data/<typology>/books/, иначе все книги")
    parser.add_argument("--model")

    args = parser.parse_args()

    if args.filename:
        asyncio.run(BookChunker(args.typology, args.filename, model=args.model).run())
    else:
        asyncio.run(TypologyChunker(args.typology, model=args.model).run())
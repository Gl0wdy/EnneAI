import asyncio
import io
from pathlib import Path
from typing import Union


class BufferTextReader:
    """
    Асинхронный ридер текста из буфера.
    Поддерживает: txt, pdf, fb2, epub, docx
    """

    MAGIC_BYTES = {
        b"%PDF":        ".pdf",
        b"PK\x03\x04": ".docx",
        b"<FictionBook": ".fb2",
    }

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding
        self._extractors = {
            ".txt":  self._read_txt,
            ".md":   self._read_txt,
            ".pdf":  self._read_pdf,
            ".fb2":  self._read_fb2,
            ".epub": self._read_epub,
            ".docx": self._read_docx,
        }

    async def read(self, buffer: Union[bytes, io.BytesIO], filename: str = "") -> str:
        buffer = self._to_bytesio(buffer)
        ext = self._resolve_ext(buffer, filename)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract, buffer, ext)

    async def read_many(self, items: list[tuple[Union[bytes, io.BytesIO], str]]) -> list[str]:
        return await asyncio.gather(*[self.read(buf, name) for buf, name in items])

    @staticmethod
    def _to_bytesio(buffer: Union[bytes, io.BytesIO]) -> io.BytesIO:
        if isinstance(buffer, bytes):
            return io.BytesIO(buffer)
        buffer.seek(0)
        return buffer

    def _resolve_ext(self, buffer: io.BytesIO, filename: str) -> str:
        if filename and (ext := Path(filename).suffix.lower()):
            return ext
        return self._detect_by_magic(buffer)

    def _detect_by_magic(self, buffer: io.BytesIO) -> str:
        header = buffer.read(16)
        buffer.seek(0)
        for sig, ext in self.MAGIC_BYTES.items():
            if header.startswith(sig):
                return ext
        return ".txt"

    def _extract(self, buffer: io.BytesIO, ext: str) -> str:
        extractor = self._extractors.get(ext)
        if extractor is None:
            raise ValueError(f"Unsupported format: '{ext}'. Supported: {', '.join(self._extractors)}")
        return extractor(buffer)


    def _read_txt(self, buffer: io.BytesIO) -> str:
        raw = buffer.read()
        for enc in [self.encoding, "utf-8", "cp1251", "latin-1"]:
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode("latin-1", errors="replace")

    def _read_pdf(self, buffer: io.BytesIO) -> str:
        try:
            import pypdf
        except ImportError:
            raise ImportError("pip install pypdf")
        reader = pypdf.PdfReader(buffer)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _read_fb2(self, buffer: io.BytesIO) -> str:
        try:
            from lxml import etree
            root = etree.parse(buffer).getroot()
            ns = {"fb": "http://www.gribuser.ru/xml/fictionbook/2.0"}
            bodies = root.findall(".//fb:body", ns) or root.findall(".//body")
        except ImportError:
            import xml.etree.ElementTree as etree
            root = etree.parse(buffer).getroot()
            bodies = root.findall(".//body")
        return "\n".join("".join(b.itertext()) for b in bodies) if bodies else "".join(root.itertext())

    def _read_epub(self, buffer: io.BytesIO) -> str:
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("pip install ebooklib beautifulsoup4")
        book = epub.read_epub(buffer)
        return "\n".join(
            BeautifulSoup(item.get_content(), "html.parser").get_text()
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        )

    def _read_docx(self, buffer: io.BytesIO) -> str:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("pip install python-docx")
        return "\n".join(p.text for p in Document(buffer).paragraphs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass
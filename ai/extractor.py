import fitz  # PyMuPDF
import os

class Extractor:
    def __init__(self, chunk_size: int = 2500):
        self.chunk_size = chunk_size

    def extract_text(self, pdf_path: str) -> str:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def split_chunks(self, text: str) -> list[str]:
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def extract_chunks(self, pdf_path: str) -> list[str]:
        full_text = self.extract_text(pdf_path)
        return self.split_chunks(full_text)

    def extract_from_folder(self, folder_path: str) -> dict[str, list[str]]:
        extracted = {}
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf"):
                path = os.path.join(folder_path, filename)
                chunks = self.extract_chunks(path)
                extracted[filename] = chunks
        return extracted

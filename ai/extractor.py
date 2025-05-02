import fitz
import os

class Extractor:
    def __init__(self, chunk_size: int = 2300):
        self.chunk_size = chunk_size

    def extract_pdf_text(self, pdf_path: str) -> str:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    
    def extract_text(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8') as file:
            text = file.read()
            return text

    def split_chunks(self, text: str) -> list[str]:
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def extract_from_folder(self, folder_path: str) -> dict[str, list[str]]:
        extracted = []
        for filename in os.listdir(folder_path):
            print(filename)
            path = os.path.join(folder_path, filename)
            if filename.lower().endswith(".pdf"):
                text = self.extract_pdf_text(path)
            elif filename.lower().endswith(".txt"):
                text = self.extract_text(path)
            else:
                text = ''
            chunks = self.split_chunks(text)
            extracted.extend(chunks)

        return extracted

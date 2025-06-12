import os

class Extractor:
    def __init__(self, chunk_size: int = 2300):
        self.chunk_size = chunk_size

    def extract_text(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8') as file:
            text = file.read()
            return text

    def split_chunks(self, text: str) -> list[str]:
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def extract_from_folder(self, folder_path: str) -> dict[str, list[str]]:
        extracted = []
        for filename in os.listdir(folder_path):
            print('- ', filename)
            path = os.path.join(folder_path, filename)
            text = f'Данные о {filename}:\n {self.extract_text(path)}'
            chunks = self.split_chunks(text)
            extracted.extend(chunks)

        return extracted

import os
from config import BASE_PATH

class Data:
    static = None
    prompt = None

    def __init__(self, collection: str):
        self.path = BASE_PATH / f'data/{collection}/'
        self.write('static')
        self.write('prompt.txt')
    
    def write(self, field: str):
        if getattr(self, field.split('.')[0]) is not None:
            return
        path = self.path / field
        if len(field.split('.')) == 2:
            with open(path, 'r', encoding='utf-8') as file:
                text = file.read()
                setattr(self, field.split('.')[0], [{'role': 'system', 'content': f'{text}'}])
            return
        
        files = os.listdir(path)
        total = []
        for f in files:
            with open(f'{path}/{f}', 'r', encoding='utf-8') as file:
                text = file.read()
                total.append({'role': 'system', 'content': f'{f}:\n{text}'})
        setattr(self, field, total)

with open(BASE_PATH / 'data/group_prompt.txt', 'r', encoding='utf-8') as file:
    GROUP_PROMPT = [{'role': 'system', 'content': file.read()}]
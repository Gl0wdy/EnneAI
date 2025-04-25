import os
import json


def get_enneadata(path: str = 'EnneAI\\data\\ennea'):
    res = []
    for i in os.listdir(path):
        with open(f'{path}\\{i}', 'r', encoding='utf-8') as file:
            data = json.load(file)
            txt_data = f'''
            {i.split('.')[0]} КРАТКИЕ СВЕДЕНИЯ:
            {str(data)}
            '''
            res.append({'role': 'system', 'content': txt_data})

    return res
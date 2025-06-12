import json
import re

def parse_system_info(response: str):
    tag_pattern = r'#(.*?)#'
    button_pattern = r'<(.*?)>'
    
    tags = re.findall(tag_pattern, response)
    buttons = re.findall(button_pattern, response, re.DOTALL)
    
    return {
        'tags': tags[0] if tags else '',
        'buttons': buttons,
        'text': response.split('===')[-1]
    }


def get_classifier_data():
    path = 'root/bots/EnneAI/data/classifier.json'
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def read_session_data():
    with open('root/bots/EnneAI/data/session.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def write_error():
    data = read_session_data()
    data['errors'] += 1
    with open('root/bots/EnneAI/data/session.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
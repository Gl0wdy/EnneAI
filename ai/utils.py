import os
import json
import re



def get_enneadata(path: str = '/root/bots/EnneAI/data/files/ennea_short.json'):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    res = ''

    for item in data:
        enneagram = item.get("enneagram", "N/A")
        focus = item.get("focus", "N/A")
        traits = ", ".join(item.get("traits", []))
        anti_traits = ", ".join(item.get("anti_traits", []))
        socionics = item.get("socionics", "N/A")
        psychosophy = item.get("psychosophy", "N/A")
        neurosis = item.get("neurosis", "N/A")
        childhood = item.get("childhood", "N/A")

        if isinstance(socionics, list):
            socionics = ", ".join(socionics)
        if isinstance(psychosophy, list):
            psychosophy = ", ".join(psychosophy)

        res += f'''Краткие сведения о {enneagram}:
                        1. Триада: {focus};
                        2. Черты: {traits};
                        3. Анти-черты: {anti_traits};
                        4. Типы по соционике: {socionics};
                        5. Типы по психософии: {psychosophy};
                        6. Невроз: {neurosis};
                        '''
    return [{'role': 'system', 'content': f'КРАТКИЕ СВЕДЕНИЯ ОБ ЭННЕАТИПАХ:\n\n{res}'}]


def get_py_data(path: str = '/root/bots/EnneAI/data/files/psychosophy_short.json'):
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        output = []

        for block in data:
            aspect = block['aspect']
            positions = block['position_traits']

            for pos, traits_block in positions.items():
                text = f"Аспект: {aspect} — Позиция {pos}\n"
                text += "Черты:\n"
                for trait in traits_block['traits']:
                    text += f"  - {trait}\n"

                associated = ', '.join(traits_block['associated with'])
                text += f"Связанные типы: {associated}\n"
                text += "-" * 40 + "\n"
                output.append({'role': 'system', 'content': text})
    return output


def get_socio_data(path: str = '/root/bots/EnneAI/data/files/socio_short.json'):
    res = []
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        for type, vals in data.items():
            res.append(f'Краткая информация о {type}:\nфункции: {vals["functions"]}\nквадра:{vals["quadra"]}\nНазвание: {vals['name']}\n\n')
    
    return [{'role': 'system', 'content': i} for i in res]


def get_classifier_data():
    path = '/root/bots/EnneAI/data/classifier.json'
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def parse_buttons(text: str):
    buttons = re.findall(r'<([^>]+)>', text)
    for i in buttons:
        text = text.replace(f'<{i}>', '')
    return text, buttons

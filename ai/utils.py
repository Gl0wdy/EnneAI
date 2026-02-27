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
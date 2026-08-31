import re

# Утилита для Юнга чтоб люди не тупили и писали имена персонажей на инглише
def is_not_english(text: str) -> bool:
    cleaned = re.sub(r'[\s\d\W_]+', '', text)
    if not cleaned:
        return False
    
    return bool(re.search(r'[^a-zA-Z]', cleaned))
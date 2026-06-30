import re
from typing import List, Tuple

def unify_symbols(text: str) -> str:
    mapping = {
        '（': '(', '）': ')', '〔': '(', '〕': ')', '【': '(', '】': ')',
        '｛': '{', '｝': '}', '〈': '<', '〉': '>', '《': '《', '》': '》',
        '，': ',', '。': '.', '；': ';', '：': ':', '！': '!', '？': '?',
        '、': ',', '·': '.', '—': '-', '–': '-', '－': '-',
        '·': '.', '×': 'x', '÷': '/',
        '１': '1', '２': '2', '３': '3', '４': '4', '５': '5',
        '６': '6', '７': '7', '８': '8', '９': '9', '０': '0',
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
        'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
        'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O',
        'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
        'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
        'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e',
        'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
        'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o',
        'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
        'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z',
        '　': ' ',
    }
    
    for old_char, new_char in mapping.items():
        text = text.replace(old_char, new_char)
    
    return text

def extract_standards(text: str) -> List[Tuple[str, str]]:
    text = unify_symbols(text)
    
    standards = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        line = re.sub(r'^\d+[\.\、,]\s*', '', line)
        
        book_pattern = r'《([^》]+)》'
        book_match = re.search(book_pattern, line)
        standard_name = ""
        if book_match:
            standard_name = book_match.group(1).strip()
        
        num_pattern = r'(GB\s?\d+[\-\.]?\d*\-?\d{2,4}|GB/T\s?\d+[\-\.]?\d*\-?\d{2,4}|JGJ\s?\d+[\-\.]?\d*\-?\d{2,4}|JGJ/T\s?\d+[\-\.]?\d*\-?\d{2,4}|GBJ\s?\d+[\-\.]?\d*\-?\d{2,4}|CECS\s?\d+:?\d*\-?\d{2,4}|JC/T\s?\d+[\-\.]?\d*\-?\d{2,4}|JG/T\s?\d+[\-\.]?\d*\-?\d{2,4}|CJJ\s?\d+[\-\.]?\d*\-?\d{2,4}|CJJ/T\s?\d+[\-\.]?\d*\-?\d{2,4}|DB\d+[\-\.]?\d*\-?\d{2,4}|DB/T\s?\d+[\-\.]?\d*\-?\d{2,4}|JTS\s?\d+[\-\.]?\d*\-?\d{2,4}|SL\s?\d+[\-\.]?\d*\-?\d{2,4}|DL/T\s?\d+[\-\.]?\d*\-?\d{2,4}|YB/T\s?\d+[\-\.]?\d*\-?\d{2,4}|NB/T\s?\d+[\-\.]?\d*\-?\d{2,4}|TB\s?\d+[\-\.]?\d*\-?\d{2,4}|EJ\s?\d+[\-\.]?\d*\-?\d{2,4}|SY/T\s?\d+[\-\.]?\d*\-?\d{2,4}|AQ\s?\d+[\-\.]?\d*\-?\d{2,4}|CB\s?\d+[\-\.]?\d*\-?\d{2,4}|HG/T\s?\d+[\-\.]?\d*\-?\d{2,4}|SH/T\s?\d+[\-\.]?\d*\-?\d{2,4}|YS/T\s?\d+[\-\.]?\d*\-?\d{2,4})'
        num_match = re.search(num_pattern, line, re.IGNORECASE)
        
        if num_match:
            standard_number = num_match.group(1).strip().upper()
            standard_number = re.sub(r'\s+', ' ', standard_number)
            standard_number = re.sub(r'\s*-\s*', '-', standard_number)
            
            if standard_name:
                found = False
                for i, (n, name) in enumerate(standards):
                    if n == standard_number:
                        if not name and standard_name:
                            standards[i] = (n, standard_name)
                        found = True
                        break
                if not found:
                    standards.append((standard_number, standard_name))
            else:
                if standard_number not in [s[0] for s in standards]:
                    standards.append((standard_number, ""))
    
    if not standards:
        patterns = [
            r'(GB\s?\d+[\-\.]?\d*\-?\d{2,4})',
            r'(GB/T\s?\d+[\-\.]?\d*\-?\d{2,4})',
            r'(JGJ\s?\d+[\-\.]?\d*\-?\d{2,4})',
            r'(JGJ/T\s?\d+[\-\.]?\d*\-?\d{2,4})',
            r'(GBJ\s?\d+[\-\.]?\d*\-?\d{2,4})',
            r'(CECS\s?\d+:?\d*\-?\d{2,4})',
            r'(DB\d+\s?/\s?T\s?\d+[\-\.]?\d*\-?\d{2,4})',
            r'(DL[\s/T]?\d+[\-\.]?\d*\-?\d{2,4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                standard_number = match.strip().upper()
                standard_number = re.sub(r'\s+', ' ', standard_number)
                standard_number = re.sub(r'\s*-\s*', '-', standard_number)
                if standard_number not in [s[0] for s in standards]:
                    standards.append((standard_number, ""))
    
    return standards
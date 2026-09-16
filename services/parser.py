import re

def parse_deck(file_path):
    """Parses a Moxfield formatted .txt file into a dictionary."""
    deck = {"mainboard": [], "sideboard": []}
    current_section = "mainboard"
    # Regex extracts: Quantity, Name, Set, Collector Num, Optional Tags
    pattern = re.compile(r"^(\d+)\s+(.+?)\s+\(([^)]+)\)\s+(\S+)(?:\s+(.+))?$")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f.read().splitlines():
            if not line: 
                continue
            if line.upper() == "SIDEBOARD:":
                current_section = "sideboard"
                continue
                
            match = pattern.match(line)
            if match:
                qty, name, set_code, col_num, tags = match.groups()
                deck[current_section].append({
                    "qty": int(qty), "name": name, 
                    "set": set_code, "number": col_num
                })
    return deck
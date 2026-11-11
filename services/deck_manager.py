import os
import json
import re
import requests
import base64
import time
from config import DECK_REPO_PATH, SCRYFALL_API_BASE, SCRYFALL_USER_AGENT
from . import parser
from . import scryfall_cache
from . import git_manager

def get_available_decks():
    decks = []
    if os.path.exists(DECK_REPO_PATH):
        for item in os.listdir(DECK_REPO_PATH):
            item_path = os.path.join(DECK_REPO_PATH, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "deck.txt")):
                decks.append(item)
    return sorted(decks)

def get_grouped_deck_data(deck_file_path):
    deck_data = parser.parse_deck(deck_file_path)
    grouped_cards = {}
    mainboard = deck_data.get("mainboard", [])
    
    if mainboard:
        commander_card = mainboard.pop(0)
        info = scryfall_cache.get_card_info(commander_card['name'], commander_card['set'], commander_card['number'])
        grouped_cards["Commander"] = [{
            "qty": commander_card['qty'],
            "name": commander_card['name'],
            "image_uri": info.get('image_uri'),
            "cmc": info.get('cmc', 0),
            "scryfall_uri": info.get('scryfall_uri', '')
        }]
    
    for card in mainboard:
        info = scryfall_cache.get_card_info(card['name'], card['set'], card['number'])
        primary_type = scryfall_cache.get_primary_type(info.get("type_line", "Unknown"))
        if primary_type not in grouped_cards:
            grouped_cards[primary_type] = []
        grouped_cards[primary_type].append({
            "qty": card['qty'],
            "name": card['name'],
            "image_uri": info.get('image_uri'),
            "cmc": info.get('cmc', 0),
            "scryfall_uri": info.get('scryfall_uri', '')
        })
    return grouped_cards

def _write_deck(file_path, deck_data):
    lines = []
    for card in deck_data.get("mainboard", []):
        tags = f" {card['tags']}" if card.get("tags") else ""
        lines.append(f"{card['qty']} {card['name']} ({card['set']}) {card['number']}{tags}")
    if deck_data.get("sideboard"):
        lines.append("SIDEBOARD:")
        for card in deck_data["sideboard"]:
            tags = f" {card['tags']}" if card.get("tags") else ""
            lines.append(f"{card['qty']} {card['name']} ({card['set']}) {card['number']}{tags}")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

def bulk_add_cards(deck_file_path, cards_text):
    """Parses a text block and adds them to the deck. 
    Skips Scryfall entirely if lines are already perfectly formatted."""
    if not cards_text or not cards_text.strip():
        return False, "No cards provided."
    
    deck_data = parser.parse_deck(deck_file_path)
    lines = cards_text.strip().split('\n')
    added = 0
    errors = []
    
    headers = {"User-Agent": SCRYFALL_USER_AGENT}
    
    # Regex to catch perfect format: "1 Sol Ring (C19) 112" or "1 Sol Ring (C19) 112 *F*"
    perfect_format_re = re.compile(r'^(\d+)\s+(.+?)\s+\(([A-Za-z0-9]+)\)\s+([A-Za-z0-9★a-z\-]+)(?:\s+(.+))?$')
    # Fallback regex for lazy format: "1 Sol Ring"
    loose_format_re = re.compile(r'^(\d+)\s+(.+)$')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 1. TRY PERFECT FORMAT (Instant, No API Call)
        perfect_match = perfect_format_re.match(line)
        if perfect_match:
            qty = int(perfect_match.group(1))
            name = perfect_match.group(2)
            set_code = perfect_match.group(3).upper()
            number = perfect_match.group(4)
            tags = perfect_match.group(5)
            
            found = False
            for card in deck_data["mainboard"]:
                if card["name"].lower() == name.lower():
                    card["qty"] += qty
                    found = True
                    break
            
            if not found:
                deck_data["mainboard"].append({
                    "qty": qty, "name": name, 
                    "set": set_code, "number": number, "tags": tags
                })
            added += qty
            
        # 2. FALLBACK TO SCRYFALL API
        else:
            match = loose_format_re.match(line)
            if match:
                qty = int(match.group(1))
                name = match.group(2)
            else:
                qty = 1
                name = line
                
            time.sleep(0.1) # Rate limit delay ONLY applied for incomplete lines
            
            resp = requests.get(f"{SCRYFALL_API_BASE}/cards/named?fuzzy={requests.utils.quote(name)}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                found = False
                for card in deck_data["mainboard"]:
                    if card["name"].lower() == data["name"].lower():
                        card["qty"] += qty
                        found = True
                        break
                if not found:
                    deck_data["mainboard"].append({
                        "qty": qty, "name": data["name"], 
                        "set": data["set"].upper(), "number": data["collector_number"], "tags": None
                    })
                added += qty
            else:
                errors.append(name)
                
    _write_deck(deck_file_path, deck_data)
    
    msg = f"Successfully added {added} cards."
    if errors:
        msg += f" Failed to find: {', '.join(errors)}"
    return True, msg

def remove_card_from_deck(deck_file_path, card_name):
    deck_data = parser.parse_deck(deck_file_path)
    for card in deck_data["mainboard"]:
        if card["name"].lower() == card_name.lower():
            if card["qty"] > 1:
                card["qty"] -= 1
            else:
                deck_data["mainboard"].remove(card)
            _write_deck(deck_file_path, deck_data)
            return True, f"Removed 1x {card_name}."
    return False, f"Card '{card_name}' not in deck."

def remove_all_cards(deck_file_path):
    """Wipes the deck text file clean."""
    _write_deck(deck_file_path, {"mainboard": [], "sideboard": []})
    return True, "All cards removed from deck."

def change_commander(deck_file_path, new_commander_name):
    if not new_commander_name: return False, "Commander name cannot be empty."
    
    deck_data = parser.parse_deck(deck_file_path)
    headers = {"User-Agent": SCRYFALL_USER_AGENT}
    resp = requests.get(f"{SCRYFALL_API_BASE}/cards/named?fuzzy={requests.utils.quote(new_commander_name)}", headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        new_cmd = {
            "qty": 1, "name": data["name"], 
            "set": data["set"].upper(), "number": data["collector_number"], "tags": None
        }
        if deck_data["mainboard"]:
            old_cmd_name = deck_data["mainboard"][0]["name"]
            deck_data["mainboard"][0] = new_cmd
            _write_deck(deck_file_path, deck_data)
            return True, f"Changed commander from {old_cmd_name} to {data['name']}."
        else:
            deck_data["mainboard"].insert(0, new_cmd)
            _write_deck(deck_file_path, deck_data)
            return True, f"Set commander to {data['name']}."
            
    return False, f"Commander '{new_commander_name}' not found on Scryfall."

def _slugify(name):
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug).strip('-')
    return slug

def create_new_deck(deck_name, commander_name):
    if not deck_name or not commander_name:
        return False, "Deck name and commander are required."
    
    deck_slug = _slugify(deck_name)
    if not deck_slug: return False, "Invalid deck name."

    deck_path = os.path.join(DECK_REPO_PATH, deck_slug)
    if os.path.exists(deck_path): return False, f"A deck slug '{deck_slug}' already exists."
        
    os.makedirs(deck_path, exist_ok=True)
    repo = git_manager.init_deck_repo(deck_path)
    if not repo: return False, "Failed to initialize Git repository."
        
    headers = {"User-Agent": SCRYFALL_USER_AGENT}
    resp = requests.get(f"{SCRYFALL_API_BASE}/cards/named?fuzzy={requests.utils.quote(commander_name)}", headers=headers)
    
    if resp.status_code != 200:
        return False, f"Could not find commander '{commander_name}' on Scryfall."
        
    data = resp.json()
    card_line = f"1 {data['name']} ({data['set'].upper()}) {data['collector_number']}\n"
    
    deck_file_path = os.path.join(deck_path, "deck.txt")
    with open(deck_file_path, 'w', encoding='utf-8') as f: f.write(card_line)
        
    meta_file_path = os.path.join(deck_path, "meta.json")
    with open(meta_file_path, 'w', encoding='utf-8') as f: json.dump({"name": deck_name}, f, indent=4)
        
    try:
        repo.git.add(A=True)
        repo.index.commit("Initial commit: Create deck and add commander")
    except Exception: pass
        
    return True, f"Successfully created deck '{deck_name}'!"

def get_card_autocomplete(query):
    if not query or len(query) < 3: return []
    headers = {"User-Agent": SCRYFALL_USER_AGENT}
    try:
        url = f"{SCRYFALL_API_BASE}/cards/autocomplete?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200: return resp.json().get("data", [])
    except Exception: pass
    return []

def import_deck(deck_name, contents):
    if not contents or not deck_name:
        return False, "Deck name and file contents are required."
    
    deck_slug = _slugify(deck_name)
    if not deck_slug: return False, "Invalid deck name format."
        
    deck_path = os.path.join(DECK_REPO_PATH, deck_slug)
    if os.path.exists(deck_path): return False, f"A deck slug '{deck_slug}' already exists."
        
    os.makedirs(deck_path, exist_ok=True)
    repo = git_manager.init_deck_repo(deck_path)
    if not repo: return False, "Failed to initialize Git repository."
        
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string).decode('utf-8')
    except Exception as e:
        return False, f"Failed to decode uploaded file: {str(e)}"
        
    deck_file_path = os.path.join(deck_path, "deck.txt")
    with open(deck_file_path, 'w', encoding='utf-8') as f: f.write(decoded)
        
    meta_file_path = os.path.join(deck_path, "meta.json")
    with open(meta_file_path, 'w', encoding='utf-8') as f: json.dump({"name": deck_name}, f, indent=4)
        
    try:
        repo.git.add(A=True)
        repo.index.commit("Initial commit: Import deck from file")
    except Exception: pass
        
    return True, f"Successfully imported deck '{deck_name}'!"


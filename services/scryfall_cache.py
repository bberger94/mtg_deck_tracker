import os
import json
import time
import requests
from config import SCRYFALL_API_BASE, SCRYFALL_DELAY, SCRYFALL_USER_AGENT

CACHE_FILE = "cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=4)

def get_card_info(card_name, set_code, collector_number):
    """Returns image URI and type line, with a name-based fallback for complex sets."""
    cache = load_cache()
    cache_key = f"{set_code.lower()}_{collector_number.lower()}"
    
    if cache_key in cache:
        card_data = cache[cache_key]
        if "type_line" not in card_data:
            card_data["type_line"] = "Unknown"
        return card_data
    
    headers = {"User-Agent": SCRYFALL_USER_AGENT}
    
    # Clean collector number (strip trailing foil markers like *F* or symbols like ★)
    clean_col = collector_number.split()[0].replace("★", "")
    
    card_data = {"image_uri": None, "type_line": "Unknown", "cmc": 0.0, "scryfall_uri": ""}    

    # 1. Try direct set + collector number lookup
    url = f"{SCRYFALL_API_BASE}/cards/{set_code.lower()}/{clean_col.lower()}"
    response = requests.get(url, headers=headers)
    time.sleep(SCRYFALL_DELAY)
    
    if response.status_code == 200:
        data = response.json()
        card_data["type_line"] = data.get("type_line", "Unknown")
        card_data["cmc"] = float(data.get("cmc", 0.0))
        card_data["scryfall_uri"] = data.get("scryfall_uri", "")
        
        if "image_uris" in data:
            card_data["image_uri"] = data["image_uris"].get("normal")
        elif "card_faces" in data and "image_uris" in data["card_faces"][0]:
            card_data["image_uri"] = data["card_faces"][0]["image_uris"].get("normal")
    else:
        # 2. Fallback: Search by exact card name if direct lookup fails (fixes PLST/MED issues)
        fallback_url = f"{SCRYFALL_API_BASE}/cards/named?exact={requests.utils.quote(card_name)}"
        fallback_response = requests.get(fallback_url, headers=headers)
        time.sleep(SCRYFALL_DELAY)
        
        if fallback_response.status_code == 200:
            data = fallback_response.json()
            card_data["type_line"] = data.get("type_line", "Unknown")
            card_data["cmc"] = float(data.get("cmc", 0.0))
            card_data["scryfall_uri"] = data.get("scryfall_uri", "")
            if "image_uris" in data:
                card_data["image_uri"] = data["image_uris"].get("normal")
            elif "card_faces" in data and "image_uris" in data["card_faces"][0]:
                card_data["image_uri"] = data["card_faces"][0]["image_uris"].get("normal")
                
    cache[cache_key] = card_data
    save_cache(cache)
    return card_data

def get_primary_type(type_line):
    tl = type_line.lower()
    if "land" in tl: return "Lands"
    if "planeswalker" in tl: return "Planeswalkers"
    if "creature" in tl: return "Creatures"
    if "sorcery" in tl: return "Sorceries"
    if "instant" in tl: return "Instants"
    if "artifact" in tl: return "Artifacts"
    if "enchantment" in tl: return "Enchantments"
    return "Other"
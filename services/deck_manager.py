import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DECK_REPO_PATH
from . import parser
from . import scryfall_cache

def get_available_decks():
    """Scans the repo for subdirectories containing a deck.txt file."""
    decks = []
    if os.path.exists(DECK_REPO_PATH):
        for item in os.listdir(DECK_REPO_PATH):
            item_path = os.path.join(DECK_REPO_PATH, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "deck.txt")):
                decks.append(item)
    return sorted(decks)

def get_grouped_deck_data(deck_file_path):
    """Parses a deck file and enriches it with Scryfall data grouped by type."""
    deck_data = parser.parse_deck(deck_file_path)
    grouped_cards = {}
    
    for card in deck_data['mainboard']:
        info = scryfall_cache.get_card_info(card['name'], card['set'], card['number'])
        primary_type = scryfall_cache.get_primary_type(info.get("type_line", "Unknown"))
        
        if primary_type not in grouped_cards:
            grouped_cards[primary_type] = []
            
        grouped_cards[primary_type].append({
            "qty": card['qty'],
            "name": card['name'],
            "image_uri": info['image_uri']
        })
        
    return grouped_cards
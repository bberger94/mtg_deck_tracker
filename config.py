import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Repository Configuration ---
DECK_REPO_PATH = os.getenv("DECK_REPO_PATH")

if not DECK_REPO_PATH or not os.path.exists(DECK_REPO_PATH):
    raise ValueError(
        f"Invalid or missing DECK_REPO_PATH: '{DECK_REPO_PATH}'. "
        "Please check your .env file."
    )

# --- Scryfall API Configuration ---
SCRYFALL_API_BASE = "https://api.scryfall.com"
SCRYFALL_USER_AGENT = os.getenv(
    "SCRYFALL_USER_AGENT", "MTGGitDashApp/1.0"
)
SCRYFALL_DELAY = float(os.getenv("SCRYFALL_REQUEST_DELAY_MS", "100")) / 1000.0

# --- App Settings ---
DEBUG_MODE = True
PORT = 8050
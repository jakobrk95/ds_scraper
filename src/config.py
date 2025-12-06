from pathlib import Path
import os

from dotenv import load_dotenv

# Project root (.. from src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# API base and headers
DANSKE_SPIL_BASE = os.getenv(
    "DANSKE_SPIL_BASE",
    "https://content.sb.danskespil.dk/content-service/api/v1",
)

START_TIME_FROM = os.getenv("START_TIME_FROM")
START_TIME_TO = os.getenv("START_TIME_TO")

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36",
)
REFERER = os.getenv("REFERER", "https://danskespil.dk/")

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": REFERER,
}

# Data directories
DATA_DIR = BASE_DIR / "data"
EVENTS_DIR = DATA_DIR / "events"
GAMES_DIR = DATA_DIR / "games"

EVENTS_DIR.mkdir(parents=True, exist_ok=True)
GAMES_DIR.mkdir(parents=True, exist_ok=True)

# How long before kickoff we scrape odds (in minutes)
LEAD_TIME_MINUTES = int(os.getenv("LEAD_TIME_MINUTES", "10"))

# SQLite database file
DB_PATH = DATA_DIR / "odds.sqlite3"
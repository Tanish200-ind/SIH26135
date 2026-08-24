"""Application configuration.

Settings are read from environment variables (optionally from a ``.env`` file
if python-dotenv is installed). For the 6-day prototype the defaults below are
enough to run the app without any configuration file.

Layout used to resolve paths:

    PROJECT_ROOT /
        data /
            raw /        synthetic source inputs
            processed/   generated demo SQLite database (sih26135.db)
        backend/
        analytics/
        scripts/
"""

import secrets
from pathlib import Path
import os

try:  # optional convenience: python-dotenv is NOT required for the prototype
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Project root = e:/SIH26135 (two levels above this file: backend/app/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Make sure the target directory for the demo database exists.
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default: SQLite file under data/processed/ (git-ignored).
DATABASE_FILE = PROCESSED_DATA_DIR / "sih26135.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATABASE_FILE.as_posix()}",
)

# JWT signing secret for the auth layer (Day 3).
# No real secret is committed or hard-coded here: if SECRET_KEY is not provided
# in the environment, a random one is generated for this process. Tokens issued
# before a restart are then invalidated, which is fine for the demo.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

APP_NAME = os.getenv("APP_NAME", "SIH26135 Skilling Intelligence Platform")
DEBUG = os.getenv("DEBUG", "true").lower() in {"1", "true", "yes"}
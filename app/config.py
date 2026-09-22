"""
Application settings and path configurations.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = BASE_DIR / "public"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
DEFAULT_DRY_RUN = os.getenv("DEFAULT_DRY_RUN", "true").lower() == "true"

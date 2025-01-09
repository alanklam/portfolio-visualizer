import os
from pathlib import Path

# Database settings
DB_DIR = Path("database")
DB_DIR.mkdir(parents=True, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_DIR}/sqlite.db"

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # In production, use env var
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

# CORS settings
CORS_ORIGINS = ["http://localhost:3000"] 
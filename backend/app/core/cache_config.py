from pathlib import Path

CACHE_DIR = "database"
CACHE_DB = "data_cache.db"
CACHE_PATH = Path(CACHE_DIR) / CACHE_DB

def get_cache_path():
    """Get cache database path, creating directory if needed"""
    cache_dir = Path(CACHE_DIR)
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / CACHE_DB

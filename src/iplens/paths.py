from pathlib import Path


def default_cache_db_path() -> str:
    """Return the default SQLite cache path under the user cache directory."""
    cache_dir = Path.home() / ".cache" / "iplens"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir / "iplens_cache.db")

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

from iplens.db_cache import DBCache
from iplens.utils import FIELDNAMES


def _empty_row(ip: str):
    row = {field: "" for field in FIELDNAMES}
    row["ip"] = ip
    row["location_country"] = "Testland"
    return row


def test_cache_round_trip_get_set():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DBCache(db_path=os.path.join(tmpdir, "cache.db"))
        row = _empty_row("8.8.8.8")
        cache.set("8.8.8.8", row)

        loaded = cache.get("8.8.8.8")
        assert loaded is not None
        assert loaded["ip"] == "8.8.8.8"
        assert loaded["location_country"] == "Testland"


def test_get_deletes_expired_row_on_access():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "cache.db")
        cache = DBCache(db_path=db_path)
        cache.set("1.1.1.1", _empty_row("1.1.1.1"))

        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE iplens SET cache_expire_date = ? WHERE ip = ?",
                (past, "1.1.1.1"),
            )

        assert cache.get("1.1.1.1") is None


def test_clear_expired_removes_only_stale_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "cache.db")
        cache = DBCache(db_path=db_path)
        cache.set("1.1.1.1", _empty_row("1.1.1.1"))
        cache.set("8.8.8.8", _empty_row("8.8.8.8"))

        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE iplens SET cache_expire_date = ? WHERE ip = ?",
                (past, "1.1.1.1"),
            )

        removed = cache.clear_expired()
        assert removed == 1
        assert cache.get("1.1.1.1") is None
        assert cache.get("8.8.8.8") is not None


def test_clear_all_removes_everything():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DBCache(db_path=os.path.join(tmpdir, "cache.db"))
        cache.set("8.8.8.8", _empty_row("8.8.8.8"))
        assert cache.clear_all() == 1
        assert cache.get("8.8.8.8") is None

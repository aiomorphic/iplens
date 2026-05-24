import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from iplens.config_loader import load_config
from iplens.logger import logger
from iplens.paths import default_cache_db_path
from iplens.utils import FIELDNAMES


class DBCache:
    def __init__(self, db_path: Optional[str] = None):
        config = load_config()
        self.db_path = db_path or default_cache_db_path()
        self.expire_days = int(config.get("Cache", "expire_days", fallback=30))
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            columns = [
                "ip TEXT PRIMARY KEY",
                "timestamp TEXT",
                "cache_expire_date TEXT",
            ] + [f"{field} TEXT" for field in FIELDNAMES if field != "ip"]
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS iplens (
                    {", ".join(columns)}
                )
            """
            )

    def get(self, ip: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            columns = ", ".join(FIELDNAMES)
            cursor.execute(
                f"SELECT {columns}, cache_expire_date FROM iplens WHERE ip = ?",  # nosec B608
                (ip,),
            )
            result = cursor.fetchone()
            if not result:
                return None

            data = dict(zip(FIELDNAMES + ["cache_expire_date"], result))
            cache_expire_date = datetime.fromisoformat(data["cache_expire_date"])
            if cache_expire_date.tzinfo is None:
                cache_expire_date = cache_expire_date.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) < cache_expire_date:
                return {k: v for k, v in data.items() if k != "cache_expire_date"}

            self.delete(ip)
            return None

    def set(self, ip: str, data: Dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            insert_data = {field: str(data.get(field, "")) for field in FIELDNAMES}
            current_time = datetime.now(timezone.utc)
            insert_data["timestamp"] = current_time.isoformat()
            insert_data["cache_expire_date"] = (
                current_time + timedelta(days=self.expire_days)
            ).isoformat()
            placeholders = ", ".join(["?" for _ in range(len(insert_data))])
            columns = ", ".join(insert_data.keys())
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO iplens ({columns})
                VALUES ({placeholders})
            """,
                tuple(insert_data.values()),
            )

    def delete(self, ip: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM iplens WHERE ip = ?", (ip,))

    def clear_expired(self) -> int:
        """Delete cache rows past their expiry time. Returns rows removed."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM iplens WHERE cache_expire_date < ?",
                (now,),
            )
            deleted_count = cursor.rowcount
            conn.commit()
        logger.info(f"Cleared {deleted_count} expired cache entries.")
        return deleted_count

    def clear_all(self) -> int:
        """Delete every cache row. Returns rows removed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM iplens")
            deleted_count = cursor.rowcount
            conn.commit()
        logger.info(f"Cleared all {deleted_count} cache entries.")
        return deleted_count

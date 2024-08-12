import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional

from iplens.config_loader import load_config
from iplens.logger import logger
from iplens.utils import FIELDNAMES


class DBCache:
    def __init__(self, db_path: str = "iplens_cache.db"):
        """
        Initialize the DBCache class.

        Args:
            db_path (str): Path to the SQLite database file. Defaults to "iplens_cache.db".
        """
        config = load_config()
        self.db_path = db_path
        self.expire_days = int(config.get("Cache", "expire_days", fallback=90))
        self._create_table()

    def _create_table(self):
        """
        Create the cache table if it doesn't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            columns = [
                "ip TEXT PRIMARY KEY",
                "timestamp TEXT",
                "cache_expire_date TEXT",
            ] + [f"{field} TEXT" for field in FIELDNAMES if field != "ip"]

            columns_str = ", ".join(columns)

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS iplens (
                    {columns_str}
                )
            """
            )

    def get(self, ip: str) -> Optional[Dict]:
        """
        Retrieve cached data for a given IP address.

        Args:
            ip (str): The IP address to retrieve data for.

        Returns:
            Optional[Dict]: The cached data for the IP, or None if not found or expired.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT {", ".join(FIELDNAMES)}, cache_expire_date FROM iplens WHERE ip = ?',
                (ip,),
            )
            result = cursor.fetchone()

            if result:
                data = dict(zip(FIELDNAMES + ["cache_expire_date"], result))
                cache_expire_date = datetime.fromisoformat(data["cache_expire_date"])
                if datetime.utcnow() < cache_expire_date:
                    return {k: v for k, v in data.items() if k != "cache_expire_date"}
                else:
                    self.delete(ip)

            return None

    def set(self, ip: str, data: Dict):
        """
        Set cached data for a given IP address.

        Args:
            ip (str): The IP address to cache data for.
            data (Dict): The data to cache.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            insert_data = {field: str(data.get(field, "")) for field in FIELDNAMES}
            current_time = datetime.utcnow()
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
        """
        Delete cached data for a given IP address.

        Args:
            ip (str): The IP address to delete data for.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM iplens WHERE ip = ?", (ip,))

    def clear_expired(self):
        """
        Clear all cache entries from the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM iplens")
            deleted_count = cursor.rowcount
            conn.commit()
        logger.info(f"Cleared {deleted_count} cache entries.")

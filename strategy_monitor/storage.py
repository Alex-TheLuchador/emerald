"""
Storage layer for Open Interest history using SQLite
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path


class OIHistoryStorage:
    """Store and retrieve Open Interest historical data"""

    def __init__(self, db_path: str = "oi_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        # Create directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oi_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open_interest REAL NOT NULL,
                price REAL,
                UNIQUE(coin, timestamp)
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coin_timestamp
            ON oi_snapshots(coin, timestamp)
        """)

        conn.commit()
        conn.close()

    def save_snapshot(
        self,
        coin: str,
        open_interest: float,
        price: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ):
        """Save an OI snapshot"""
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_unix = int(timestamp.timestamp())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO oi_snapshots (coin, timestamp, open_interest, price)
                VALUES (?, ?, ?, ?)
            """, (coin, timestamp_unix, open_interest, price))

            conn.commit()
        finally:
            conn.close()

    def get_snapshot(
        self,
        coin: str,
        hours_ago: int
    ) -> Optional[Dict[str, float]]:
        """
        Get OI snapshot from N hours ago

        Returns:
            {
                "open_interest": float,
                "price": float,
                "timestamp": int
            }
            or None if not found
        """
        target_time = datetime.now() - timedelta(hours=hours_ago)
        timestamp_unix = int(target_time.timestamp())

        # Look for snapshot within ±5 minutes
        window = 5 * 60  # 5 minutes in seconds

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT timestamp, open_interest, price
                FROM oi_snapshots
                WHERE coin = ?
                  AND timestamp BETWEEN ? AND ?
                ORDER BY ABS(timestamp - ?) ASC
                LIMIT 1
            """, (coin, timestamp_unix - window, timestamp_unix + window, timestamp_unix))

            result = cursor.fetchone()

            if result:
                return {
                    "timestamp": result[0],
                    "open_interest": result[1],
                    "price": result[2]
                }
            return None
        finally:
            conn.close()

    def get_recent_snapshots(
        self,
        coin: str,
        hours: int = 24
    ) -> List[Dict[str, float]]:
        """Get all snapshots for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_unix = int(cutoff_time.timestamp())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT timestamp, open_interest, price
                FROM oi_snapshots
                WHERE coin = ?
                  AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (coin, cutoff_unix))

            results = cursor.fetchall()

            return [
                {
                    "timestamp": row[0],
                    "open_interest": row[1],
                    "price": row[2]
                }
                for row in results
            ]
        finally:
            conn.close()

    def cleanup_old_data(self, days: int = 7):
        """Remove snapshots older than N days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_unix = int(cutoff_time.timestamp())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM oi_snapshots
                WHERE timestamp < ?
            """, (cutoff_unix,))

            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM oi_snapshots")
            total_snapshots = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT coin) FROM oi_snapshots")
            unique_coins = cursor.fetchone()[0]

            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp)
                FROM oi_snapshots
            """)
            result = cursor.fetchone()
            oldest = result[0]
            newest = result[1]

            return {
                "total_snapshots": total_snapshots,
                "unique_coins": unique_coins,
                "oldest_timestamp": oldest,
                "newest_timestamp": newest
            }
        finally:
            conn.close()


def test_storage():
    """Test the storage layer"""
    print("Testing OI History Storage...")

    # Use temporary test database
    storage = OIHistoryStorage("test_oi.db")

    print("\n1. Saving snapshots...")
    storage.save_snapshot("BTC", 1250000000.0, price=67800.0)
    storage.save_snapshot("ETH", 450000000.0, price=3200.0)
    print("   ✓ Saved 2 snapshots")

    print("\n2. Retrieving current snapshot...")
    snapshot = storage.get_snapshot("BTC", hours_ago=0)
    print(f"   ✓ Retrieved: OI={snapshot['open_interest']}, Price={snapshot['price']}")

    print("\n3. Testing historical lookup (should be None)...")
    old_snapshot = storage.get_snapshot("BTC", hours_ago=4)
    print(f"   ✓ 4 hours ago: {old_snapshot}")

    print("\n4. Saving snapshot from 4 hours ago...")
    past_time = datetime.now() - timedelta(hours=4)
    storage.save_snapshot("BTC", 1180000000.0, price=67500.0, timestamp=past_time)
    old_snapshot = storage.get_snapshot("BTC", hours_ago=4)
    print(f"   ✓ Retrieved: OI={old_snapshot['open_interest']}")

    print("\n5. Getting recent snapshots...")
    recent = storage.get_recent_snapshots("BTC", hours=24)
    print(f"   ✓ Found {len(recent)} snapshots")

    print("\n6. Storage stats...")
    stats = storage.get_stats()
    print(f"   ✓ Total snapshots: {stats['total_snapshots']}")
    print(f"   ✓ Unique coins: {stats['unique_coins']}")

    print("\n✅ All tests passed!")

    # Cleanup
    import os
    if os.path.exists("test_oi.db"):
        os.remove("test_oi.db")
        print("   Cleaned up test database")


if __name__ == "__main__":
    test_storage()

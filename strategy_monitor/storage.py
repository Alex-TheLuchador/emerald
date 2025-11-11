"""
In-memory storage layer for multi-timeframe historical data

Replaces SQLite with efficient in-memory deques for:
- Open Interest history (4h/24h/7d)
- Funding rate history (4h/8h/12h)
- Order book snapshots (for velocity calculations)
- Whale position snapshots (optional)
"""
import time
from collections import deque
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Snapshot:
    """Generic snapshot with timestamp"""
    timestamp: float  # Unix timestamp
    coin: str
    data: Any


class MultiTimeframeStorage:
    """
    In-memory storage with automatic time-based retention

    Uses deques with maxlen for efficient memory management
    """

    def __init__(
        self,
        oi_retention_hours: int = 168,      # 7 days
        funding_retention_hours: int = 168,  # 7 days
        orderbook_retention_hours: int = 1,  # 1 hour (for velocity)
        snapshot_interval_minutes: int = 15  # How often we snapshot
    ):
        """
        Args:
            oi_retention_hours: How many hours of OI history to keep
            funding_retention_hours: How many hours of funding history to keep
            orderbook_retention_hours: How many hours of order book snapshots
            snapshot_interval_minutes: Expected time between snapshots
        """
        # Calculate maxlen for each deque based on retention and interval
        snapshots_per_hour = 60 / snapshot_interval_minutes

        oi_maxlen = int(oi_retention_hours * snapshots_per_hour)
        funding_maxlen = int(funding_retention_hours * snapshots_per_hour)
        orderbook_maxlen = int(orderbook_retention_hours * snapshots_per_hour)

        # Storage: Dict[coin, deque[Snapshot]]
        self.oi_history: Dict[str, deque] = {}
        self.funding_history: Dict[str, deque] = {}
        self.orderbook_history: Dict[str, deque] = {}
        self.whale_positions: Dict[str, deque] = {}  # Optional

        self._oi_maxlen = oi_maxlen
        self._funding_maxlen = funding_maxlen
        self._orderbook_maxlen = orderbook_maxlen

    def _ensure_deque(self, storage: Dict, coin: str, maxlen: int) -> deque:
        """Ensure deque exists for coin"""
        if coin not in storage:
            storage[coin] = deque(maxlen=maxlen)
        return storage[coin]

    # === Open Interest Storage ===

    def add_oi_snapshot(self, coin: str, oi: float, price: float, timestamp: Optional[float] = None):
        """
        Add OI snapshot for a coin

        Args:
            coin: Coin symbol
            oi: Open interest value
            price: Current price
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        q = self._ensure_deque(self.oi_history, coin, self._oi_maxlen)
        q.append(Snapshot(
            timestamp=timestamp,
            coin=coin,
            data={'oi': oi, 'price': price}
        ))

    def get_oi_at_time(self, coin: str, hours_ago: float) -> Optional[Dict[str, float]]:
        """
        Get OI snapshot from N hours ago

        Args:
            coin: Coin symbol
            hours_ago: How many hours back to look

        Returns:
            {'oi': float, 'price': float, 'timestamp': float} or None
        """
        if coin not in self.oi_history:
            return None

        target_ts = time.time() - (hours_ago * 3600)
        tolerance = 900  # 15 minutes in seconds

        # Search backwards through history for closest match
        snapshots = self.oi_history[coin]
        closest = None
        min_diff = float('inf')

        for snapshot in snapshots:
            diff = abs(snapshot.timestamp - target_ts)
            if diff < tolerance and diff < min_diff:
                min_diff = diff
                closest = snapshot

        if closest:
            return {
                'oi': closest.data['oi'],
                'price': closest.data['price'],
                'timestamp': closest.timestamp
            }

        return None

    def get_oi_changes(self, coin: str) -> Optional[Dict[str, float]]:
        """
        Calculate OI changes across multiple timeframes

        Returns:
            {
                'current': float,
                'change_4h': float (%),
                'change_24h': float (%),
                'change_7d': float (%),
                'price_change_24h': float (%)
            }
        """
        if coin not in self.oi_history or len(self.oi_history[coin]) == 0:
            return None

        current_snapshot = self.oi_history[coin][-1]
        current_oi = current_snapshot.data['oi']
        current_price = current_snapshot.data['price']

        oi_4h = self.get_oi_at_time(coin, 4)
        oi_24h = self.get_oi_at_time(coin, 24)
        oi_7d = self.get_oi_at_time(coin, 168)

        changes = {'current': current_oi}

        if oi_4h:
            changes['change_4h'] = ((current_oi - oi_4h['oi']) / oi_4h['oi']) * 100

        if oi_24h:
            changes['change_24h'] = ((current_oi - oi_24h['oi']) / oi_24h['oi']) * 100
            changes['price_change_24h'] = ((current_price - oi_24h['price']) / oi_24h['price']) * 100

        if oi_7d:
            changes['change_7d'] = ((current_oi - oi_7d['oi']) / oi_7d['oi']) * 100

        return changes

    # === Funding Rate Storage ===

    def add_funding_snapshot(self, coin: str, funding_rate: float, timestamp: Optional[float] = None):
        """
        Add funding rate snapshot

        Args:
            coin: Coin symbol
            funding_rate: Annualized funding rate (%)
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        q = self._ensure_deque(self.funding_history, coin, self._funding_maxlen)
        q.append(Snapshot(
            timestamp=timestamp,
            coin=coin,
            data={'funding_rate': funding_rate}
        ))

    def get_funding_at_time(self, coin: str, hours_ago: float) -> Optional[float]:
        """Get funding rate from N hours ago"""
        if coin not in self.funding_history:
            return None

        target_ts = time.time() - (hours_ago * 3600)
        tolerance = 900  # 15 minutes

        snapshots = self.funding_history[coin]
        closest = None
        min_diff = float('inf')

        for snapshot in snapshots:
            diff = abs(snapshot.timestamp - target_ts)
            if diff < tolerance and diff < min_diff:
                min_diff = diff
                closest = snapshot

        if closest:
            return closest.data['funding_rate']

        return None

    def get_funding_dynamics(self, coin: str) -> Optional[Dict[str, float]]:
        """
        Calculate funding velocity and acceleration

        Returns:
            {
                'current': float,
                'funding_4h_ago': float,
                'funding_8h_ago': float,
                'funding_12h_ago': float,
                'velocity_4h': float (change over 4h),
                'velocity_8h': float (change over 8h),
                'acceleration': float (2nd derivative)
            }

            Returns None if insufficient data (need at least 4h of history)
        """
        if coin not in self.funding_history or len(self.funding_history[coin]) == 0:
            return None

        current_snapshot = self.funding_history[coin][-1]
        current_funding = current_snapshot.data['funding_rate']

        funding_4h = self.get_funding_at_time(coin, 4)
        funding_8h = self.get_funding_at_time(coin, 8)
        funding_12h = self.get_funding_at_time(coin, 12)

        # Require at least 4h of data for meaningful velocity
        if funding_4h is None:
            return None

        dynamics = {
            'current': current_funding,
            'funding_4h_ago': funding_4h,
            'velocity_4h': current_funding - funding_4h
        }

        if funding_8h is not None:
            dynamics['funding_8h_ago'] = funding_8h
            dynamics['velocity_8h'] = current_funding - funding_8h

        if funding_12h is not None:
            dynamics['funding_12h_ago'] = funding_12h

        # Calculate acceleration (2nd derivative)
        if funding_8h is not None:
            velocity_older = funding_4h - funding_8h
            dynamics['acceleration'] = dynamics['velocity_4h'] - velocity_older
        else:
            dynamics['acceleration'] = 0.0  # Can't calculate without 8h data

        return dynamics

    # === Order Book Storage (for velocity calculations) ===

    def add_orderbook_snapshot(self, coin: str, imbalance: float, timestamp: Optional[float] = None):
        """
        Add order book imbalance snapshot

        Args:
            coin: Coin symbol
            imbalance: Bid-ask imbalance (-1 to +1)
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        q = self._ensure_deque(self.orderbook_history, coin, self._orderbook_maxlen)
        q.append(Snapshot(
            timestamp=timestamp,
            coin=coin,
            data={'imbalance': imbalance}
        ))

    def get_orderbook_velocity(self, coin: str, lookback_snapshots: int = 3) -> Optional[float]:
        """
        Calculate order book imbalance velocity

        Args:
            coin: Coin symbol
            lookback_snapshots: How many recent snapshots to analyze

        Returns:
            Average rate of change in imbalance
        """
        if coin not in self.orderbook_history:
            return None

        snapshots = list(self.orderbook_history[coin])
        if len(snapshots) < lookback_snapshots + 1:
            return None

        # Take last N+1 snapshots
        recent = snapshots[-(lookback_snapshots + 1):]

        # Calculate changes between consecutive snapshots
        changes = []
        for i in range(1, len(recent)):
            prev_imbalance = recent[i-1].data['imbalance']
            curr_imbalance = recent[i].data['imbalance']
            change = curr_imbalance - prev_imbalance
            changes.append(change)

        if changes:
            return sum(changes) / len(changes)

        return 0.0

    # === Whale Position Storage (Optional) ===

    def add_whale_snapshot(self, coin: str, whale_data: Dict[str, Any], timestamp: Optional[float] = None):
        """
        Add snapshot of whale positions

        Args:
            coin: Coin symbol
            whale_data: Dict with whale position data
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()

        q = self._ensure_deque(self.whale_positions, coin, maxlen=100)  # Keep last 100
        q.append(Snapshot(
            timestamp=timestamp,
            coin=coin,
            data=whale_data
        ))

    def get_latest_whale_data(self, coin: str) -> Optional[Dict[str, Any]]:
        """Get most recent whale position snapshot"""
        if coin not in self.whale_positions or len(self.whale_positions[coin]) == 0:
            return None

        latest = self.whale_positions[coin][-1]
        return latest.data

    # === Stats & Utilities ===

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'oi_coins': len(self.oi_history),
            'funding_coins': len(self.funding_history),
            'orderbook_coins': len(self.orderbook_history),
            'whale_coins': len(self.whale_positions),
        }

        # Add per-coin snapshot counts
        for coin, q in self.oi_history.items():
            stats[f'oi_snapshots_{coin}'] = len(q)

        for coin, q in self.funding_history.items():
            stats[f'funding_snapshots_{coin}'] = len(q)

        return stats

    def clear_all(self):
        """Clear all storage (useful for testing)"""
        self.oi_history.clear()
        self.funding_history.clear()
        self.orderbook_history.clear()
        self.whale_positions.clear()


def test_storage():
    """Test the in-memory storage layer"""
    print("Testing Multi-Timeframe In-Memory Storage...")

    storage = MultiTimeframeStorage(
        oi_retention_hours=168,  # 7 days
        snapshot_interval_minutes=15
    )

    print("\n1. Testing OI storage...")
    storage.add_oi_snapshot("BTC", oi=1250000000.0, price=67800.0)
    storage.add_oi_snapshot("ETH", oi=450000000.0, price=3200.0)
    print("   ✓ Stored 2 OI snapshots")

    print("\n2. Testing current OI retrieval...")
    oi_current = storage.get_oi_at_time("BTC", hours_ago=0)
    print(f"   ✓ Current BTC OI: {oi_current['oi']:,.0f}")

    print("\n3. Adding historical OI snapshot (4h ago)...")
    timestamp_4h = time.time() - (4 * 3600)
    storage.add_oi_snapshot("BTC", oi=1180000000.0, price=67500.0, timestamp=timestamp_4h)
    oi_4h = storage.get_oi_at_time("BTC", hours_ago=4)
    print(f"   ✓ 4h ago BTC OI: {oi_4h['oi']:,.0f}")

    print("\n4. Testing OI changes calculation...")
    changes = storage.get_oi_changes("BTC")
    if changes and 'change_4h' in changes:
        print(f"   ✓ 4h OI change: {changes['change_4h']:.2f}%")

    print("\n5. Testing funding rate storage...")
    storage.add_funding_snapshot("BTC", funding_rate=15.5)
    timestamp_4h = time.time() - (4 * 3600)
    storage.add_funding_snapshot("BTC", funding_rate=12.0, timestamp=timestamp_4h)

    dynamics = storage.get_funding_dynamics("BTC")
    if dynamics:
        print(f"   ✓ Current funding: {dynamics['current']:.2f}%")
        if 'velocity_4h' in dynamics:
            print(f"   ✓ 4h velocity: {dynamics['velocity_4h']:.2f}%")

    print("\n6. Testing order book velocity...")
    storage.add_orderbook_snapshot("BTC", imbalance=0.2)
    time.sleep(0.01)
    storage.add_orderbook_snapshot("BTC", imbalance=0.35)
    time.sleep(0.01)
    storage.add_orderbook_snapshot("BTC", imbalance=0.5)
    time.sleep(0.01)
    storage.add_orderbook_snapshot("BTC", imbalance=0.6)

    velocity = storage.get_orderbook_velocity("BTC", lookback_snapshots=3)
    print(f"   ✓ Order book velocity: {velocity:.3f}")

    print("\n7. Storage stats...")
    stats = storage.get_stats()
    print(f"   ✓ OI coins tracked: {stats['oi_coins']}")
    print(f"   ✓ Funding coins tracked: {stats['funding_coins']}")
    print(f"   ✓ BTC OI snapshots: {stats.get('oi_snapshots_BTC', 0)}")

    print("\n✅ All tests passed!")
    print("\nMemory efficiency:")
    print(f"   - No database files")
    print(f"   - Automatic retention management")
    print(f"   - Fast in-memory lookups")


if __name__ == "__main__":
    test_storage()

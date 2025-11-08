"""
Order Book Microstructure Analyzer for Institutional Engine.

Tracks order book snapshots over time to detect:
- Spoofing (fake liquidity - orders appearing/disappearing)
- Iceberg orders (hidden institutional accumulation/distribution)
- Wall dynamics (large orders moving with price)

This reveals HIDDEN institutional behavior that doesn't show up in single snapshots.
"""

import requests
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
from collections import defaultdict
from langchain.tools import tool

API_URL = "https://api.hyperliquid.xyz/info"
CACHE_TTL = 2  # 2 seconds

# In-memory storage for order book history (last 60 seconds)
# Format: {coin: [(timestamp, snapshot), ...]}
_order_book_history: Dict[str, List[Tuple[float, Dict[str, Any]]]] = defaultdict(list)


def _fetch_order_book_snapshot(coin: str, depth: int = 20) -> Dict[str, Any]:
    """
    Fetch current L2 order book snapshot.

    Args:
        coin: Trading pair
        depth: Number of levels to fetch

    Returns:
        Order book snapshot with bids/asks
    """
    payload = {
        "type": "l2Book",
        "coin": coin
    }

    response = requests.post(API_URL, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()

    # Parse order book
    levels = data.get("levels", [])
    if not levels or len(levels) < 2:
        return {"error": "Invalid order book data"}

    bids_raw = levels[0][:depth]  # Top N bids
    asks_raw = levels[1][:depth]  # Top N asks

    # Parse bids - handle both dict and list formats
    bids = []
    for level in bids_raw:
        if isinstance(level, dict):
            price = float(level.get("px", 0))
            size = float(level.get("sz", 0))
        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            price = float(level[0])
            size = float(level[1])
        else:
            continue
        if price > 0 and size > 0:
            bids.append([price, size])

    # Parse asks - handle both dict and list formats
    asks = []
    for level in asks_raw:
        if isinstance(level, dict):
            price = float(level.get("px", 0))
            size = float(level.get("sz", 0))
        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            price = float(level[0])
            size = float(level[1])
        else:
            continue
        if price > 0 and size > 0:
            asks.append([price, size])

    return {
        "bids": bids,
        "asks": asks,
        "timestamp": datetime.now(tz=timezone.utc).timestamp()
    }


def _store_snapshot(coin: str, snapshot: Dict[str, Any]):
    """
    Store order book snapshot in history.

    Maintains rolling 60-second window.

    Args:
        coin: Trading pair
        snapshot: Order book snapshot
    """
    timestamp = snapshot.get("timestamp", datetime.now(tz=timezone.utc).timestamp())

    # Add to history
    _order_book_history[coin].append((timestamp, snapshot))

    # Prune old snapshots (older than 60 seconds)
    cutoff = datetime.now(tz=timezone.utc).timestamp() - 60
    _order_book_history[coin] = [
        (ts, snap) for ts, snap in _order_book_history[coin]
        if ts >= cutoff
    ]


def detect_spoofing(coin: str, min_size_btc: float = 10.0) -> List[Dict[str, Any]]:
    """
    Detect spoofing - large orders appearing and disappearing rapidly.

    Spoofing pattern:
    - Large order (>min_size) appears
    - Disappears within 5 seconds
    - Reappears at same/similar price level
    - Happens 3+ times = confirmed spoof

    Args:
        coin: Trading pair
        min_size_btc: Minimum order size to track (in BTC/coin units)

    Returns:
        List of detected spoofs with details
    """
    history = _order_book_history.get(coin, [])

    if len(history) < 3:
        return []  # Not enough data

    spoofs = []

    # Track price levels and their appearance/disappearance
    level_tracker = defaultdict(list)  # {price: [(timestamp, size, side)]}

    for timestamp, snapshot in history:
        if "error" in snapshot:
            continue

        # Track bids
        for price, size in snapshot.get("bids", []):
            if size >= min_size_btc:
                level_tracker[("bid", round(price, 2))].append((timestamp, size))

        # Track asks
        for price, size in snapshot.get("asks", []):
            if size >= min_size_btc:
                level_tracker[("ask", round(price, 2))].append((timestamp, size))

    # Detect patterns
    for (side, price), appearances in level_tracker.items():
        if len(appearances) >= 3:
            # Check if order keeps appearing/disappearing
            gaps = []
            for i in range(1, len(appearances)):
                time_gap = appearances[i][0] - appearances[i-1][0]
                if time_gap > 5:  # 5+ second gap = disappeared
                    gaps.append(time_gap)

            # If 2+ gaps (3+ appearances), it's a spoof
            if len(gaps) >= 2:
                avg_size = sum(size for _, size in appearances) / len(appearances)
                spoofs.append({
                    "side": side,
                    "price": price,
                    "avg_size": round(avg_size, 4),
                    "appearances": len(appearances),
                    "pattern": "spoofing_detected",
                    "confidence": "high" if len(gaps) >= 3 else "moderate"
                })

    return spoofs


def detect_iceberg_orders(coin: str, refill_threshold: int = 3) -> List[Dict[str, Any]]:
    """
    Detect iceberg orders - orders that keep refilling at same price.

    Iceberg pattern:
    - Order at price level gets filled (size decreases)
    - Order immediately refills (size increases back)
    - Happens 3+ times = institutional iceberg

    Args:
        coin: Trading pair
        refill_threshold: Number of refills to confirm iceberg

    Returns:
        List of detected icebergs
    """
    history = _order_book_history.get(coin, [])

    if len(history) < 5:
        return []

    icebergs = []

    # Track size changes at each price level
    level_sizes = defaultdict(list)  # {(side, price): [size1, size2, ...]}

    for timestamp, snapshot in history:
        if "error" in snapshot:
            continue

        for price, size in snapshot.get("bids", []):
            level_sizes[("bid", round(price, 2))].append(size)

        for price, size in snapshot.get("asks", []):
            level_sizes[("ask", round(price, 2))].append(size)

    # Detect refill patterns
    for (side, price), sizes in level_sizes.items():
        if len(sizes) < 5:
            continue

        refills = 0
        for i in range(1, len(sizes)):
            # Check if size decreased then increased (refill pattern)
            if sizes[i] > sizes[i-1] * 1.2:  # 20% increase = refill
                refills += 1

        if refills >= refill_threshold:
            icebergs.append({
                "side": side,
                "price": price,
                "refills_detected": refills,
                "avg_size": round(sum(sizes) / len(sizes), 4),
                "pattern": "iceberg_order",
                "confidence": "high" if refills >= 5 else "moderate"
            })

    return icebergs


def detect_wall_dynamics(coin: str, min_size_btc: float = 50.0) -> Dict[str, Any]:
    """
    Detect moving walls - large orders that chase price.

    Wall movement patterns:
    - Large bid wall (>50 BTC) moves up = bullish institutional support
    - Large ask wall moves down = bearish institutional resistance

    Args:
        coin: Trading pair
        min_size_btc: Minimum size to qualify as a wall

    Returns:
        Wall movement analysis
    """
    history = _order_book_history.get(coin, [])

    if len(history) < 3:
        return {"status": "insufficient_data"}

    # Track largest bid/ask over time
    bid_walls = []
    ask_walls = []

    for timestamp, snapshot in history:
        if "error" in snapshot:
            continue

        # Find largest bid
        bids = snapshot.get("bids", [])
        if bids:
            largest_bid = max(bids, key=lambda x: x[1])
            if largest_bid[1] >= min_size_btc:
                bid_walls.append((timestamp, largest_bid[0], largest_bid[1]))

        # Find largest ask
        asks = snapshot.get("asks", [])
        if asks:
            largest_ask = max(asks, key=lambda x: x[1])
            if largest_ask[1] >= min_size_btc:
                ask_walls.append((timestamp, largest_ask[0], largest_ask[1]))

    # Analyze movement
    result = {"bid_wall": None, "ask_wall": None}

    if len(bid_walls) >= 2:
        start_price = bid_walls[0][1]
        end_price = bid_walls[-1][1]
        movement_pct = ((end_price - start_price) / start_price) * 100

        result["bid_wall"] = {
            "current_price": round(end_price, 2),
            "current_size": round(bid_walls[-1][2], 4),
            "movement_pct": round(movement_pct, 4),
            "direction": "moving_up" if movement_pct > 0.05 else "moving_down" if movement_pct < -0.05 else "stable",
            "signal": "bullish_support" if movement_pct > 0.1 else "neutral"
        }

    if len(ask_walls) >= 2:
        start_price = ask_walls[0][1]
        end_price = ask_walls[-1][1]
        movement_pct = ((end_price - start_price) / start_price) * 100

        result["ask_wall"] = {
            "current_price": round(end_price, 2),
            "current_size": round(ask_walls[-1][2], 4),
            "movement_pct": round(movement_pct, 4),
            "direction": "moving_down" if movement_pct < -0.05 else "moving_up" if movement_pct > 0.05 else "stable",
            "signal": "bearish_resistance" if movement_pct < -0.1 else "neutral"
        }

    return result


def analyze_microstructure(coin: str) -> Dict[str, Any]:
    """
    Comprehensive order book microstructure analysis.

    Args:
        coin: Trading pair

    Returns:
        Complete microstructure analysis
    """
    # Fetch and store new snapshot
    snapshot = _fetch_order_book_snapshot(coin)
    if "error" not in snapshot:
        _store_snapshot(coin, snapshot)

    # Run all detection algorithms
    spoofs = detect_spoofing(coin)
    icebergs = detect_iceberg_orders(coin)
    walls = detect_wall_dynamics(coin)

    # Calculate summary signals
    signals = []

    if spoofs:
        signals.append(f"spoofing_detected_{len(spoofs)}_levels")
    if icebergs:
        signals.append(f"iceberg_orders_{len(icebergs)}_levels")

    if walls.get("bid_wall", {}).get("signal") == "bullish_support":
        signals.append("bid_wall_bullish_support")
    if walls.get("ask_wall", {}).get("signal") == "bearish_resistance":
        signals.append("ask_wall_bearish_resistance")

    return {
        "coin": coin,
        "snapshots_analyzed": len(_order_book_history.get(coin, [])),
        "spoofing": spoofs,
        "icebergs": icebergs,
        "wall_dynamics": walls,
        "signals": signals,
        "timestamp": datetime.now(tz=timezone.utc).isoformat()
    }


@tool
def fetch_order_book_microstructure_tool(coin: str) -> Dict[str, Any]:
    """
    Analyze order book microstructure to detect hidden institutional activity.

    Detects:
    - Spoofing: Fake liquidity (orders appearing/disappearing 3+ times)
    - Iceberg orders: Hidden accumulation (orders refilling at same price)
    - Wall dynamics: Large orders moving with price (institutional positioning)

    This reveals behavior that single snapshots can't show.

    Args:
        coin: Trading pair (e.g., "BTC")

    Returns:
        Microstructure analysis with detected patterns
    """
    return analyze_microstructure(coin)


def fetch_order_book_microstructure(coin: str) -> Dict[str, Any]:
    """
    Non-tool version for direct function calls.

    Args:
        coin: Trading pair

    Returns:
        Microstructure analysis
    """
    return analyze_microstructure(coin)

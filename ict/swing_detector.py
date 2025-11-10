"""
Swing High/Low Detector for ICT Strategy

Detects swing points using 3-candle minimum pattern:
- Swing High: High[i] > High[i-1] AND High[i] > High[i+1]
- Swing Low: Low[i] < Low[i-1] AND Low[i] < Low[i+1]

These swings form the foundation of structure analysis.
"""

from typing import List, Dict, Any
import sys
from pathlib import Path

# Add project root to path for config import
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ICT_CONFIG


def _to_num(x: Any) -> float:
    """Convert value to float, return nan if conversion fails."""
    try:
        return float(x)
    except Exception:
        return float("nan")


def detect_swing_highs(candles: List[Dict[str, Any]], min_candles: int = None) -> List[Dict[str, Any]]:
    """
    Detect swing highs in candle data.

    Args:
        candles: List of candle dictionaries with OHLC data
        min_candles: Minimum number of candles for swing detection (default: from config)

    Returns:
        List of swing high dictionaries with index, timestamp, and price

    Example:
        >>> candles = [
        ...     {"h": 100, "t": 1000},
        ...     {"h": 105, "t": 2000},
        ...     {"h": 102, "t": 3000}
        ... ]
        >>> swings = detect_swing_highs(candles)
        >>> # Returns: [{"index": 1, "price": 105.0, "timestamp": 2000}]
    """
    if min_candles is None:
        min_candles = ICT_CONFIG.min_swing_candles

    if len(candles) < min_candles:
        return []

    swing_highs = []

    # Use 3-candle pattern: check if middle candle high is highest
    for i in range(1, len(candles) - 1):
        h_prev = _to_num(candles[i - 1]["h"])
        h = _to_num(candles[i]["h"])
        h_next = _to_num(candles[i + 1]["h"])

        # Swing high: middle candle higher than both neighbors
        if h > h_prev and h > h_next:
            swing_highs.append({
                "index": i,
                "timestamp": candles[i]["t"],
                "price": _to_num(candles[i]["h"]),
            })

    return swing_highs


def detect_swing_lows(candles: List[Dict[str, Any]], min_candles: int = None) -> List[Dict[str, Any]]:
    """
    Detect swing lows in candle data.

    Args:
        candles: List of candle dictionaries with OHLC data
        min_candles: Minimum number of candles for swing detection (default: from config)

    Returns:
        List of swing low dictionaries with index, timestamp, and price

    Example:
        >>> candles = [
        ...     {"l": 100, "t": 1000},
        ...     {"l": 95, "t": 2000},
        ...     {"l": 98, "t": 3000}
        ... ]
        >>> swings = detect_swing_lows(candles)
        >>> # Returns: [{"index": 1, "price": 95.0, "timestamp": 2000}]
    """
    if min_candles is None:
        min_candles = ICT_CONFIG.min_swing_candles

    if len(candles) < min_candles:
        return []

    swing_lows = []

    # Use 3-candle pattern: check if middle candle low is lowest
    for i in range(1, len(candles) - 1):
        l_prev = _to_num(candles[i - 1]["l"])
        l = _to_num(candles[i]["l"])
        l_next = _to_num(candles[i + 1]["l"])

        # Swing low: middle candle lower than both neighbors
        if l < l_prev and l < l_next:
            swing_lows.append({
                "index": i,
                "timestamp": candles[i]["t"],
                "price": _to_num(candles[i]["l"]),
            })

    return swing_lows


def filter_significant_swings(
    swings: List[Dict[str, Any]],
    swing_type: str,
) -> List[Dict[str, Any]]:
    """
    Filter swings to only significant ones (swings of swings).

    A significant swing high is a swing high that is higher than the surrounding swing highs.
    A significant swing low is a swing low that is lower than the surrounding swing lows.

    This helps identify major structural points rather than every minor swing.

    Args:
        swings: List of swing dictionaries
        swing_type: "high" or "low"

    Returns:
        List of significant swings only

    Example:
        >>> swing_highs = [
        ...     {"price": 100}, {"price": 105}, {"price": 102}, {"price": 110}, {"price": 108}
        ... ]
        >>> significant = filter_significant_swings(swing_highs, "high")
        >>> # Returns only the swings that are higher than neighbors: [105, 110]
    """
    if len(swings) < 3:
        return swings  # Not enough swings to filter

    significant = []

    # Check each swing against its neighbors
    for i in range(1, len(swings) - 1):
        left = swings[i - 1]
        mid = swings[i]
        right = swings[i + 1]

        lp = _to_num(left["price"])
        mp = _to_num(mid["price"])
        rp = _to_num(right["price"])

        if swing_type == "high":
            # Significant swing high: higher than both neighboring swing highs
            if mp > lp and mp > rp:
                significant.append(mid)
        else:
            # Significant swing low: lower than both neighboring swing lows
            if mp < lp and mp < rp:
                significant.append(mid)

    return significant


def detect_all_swings(candles: List[Dict[str, Any]], significant_only: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect both swing highs and swing lows in one call.

    Convenience function that calls both detect_swing_highs and detect_swing_lows.

    Args:
        candles: List of candle dictionaries
        significant_only: If True, filter to significant swings only

    Returns:
        Dictionary with "swing_highs" and "swing_lows" keys
        {
            "swing_highs": [...],
            "swing_lows": [...]
        }
    """
    swing_highs = detect_swing_highs(candles)
    swing_lows = detect_swing_lows(candles)

    if significant_only:
        swing_highs = filter_significant_swings(swing_highs, "high")
        swing_lows = filter_significant_swings(swing_lows, "low")

    return {
        "swing_highs": swing_highs,
        "swing_lows": swing_lows,
    }

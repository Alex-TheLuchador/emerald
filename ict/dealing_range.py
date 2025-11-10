"""
Dealing Range Calculator for ICT Strategy

The dealing range defines entry zones:
- Range Low: Recent swing low that grabbed liquidity
- Range High: Recent swing high that grabbed liquidity
- Discount Zone: Below 50% of range (long entries)
- Premium Zone: Above 50% of range (short entries)
"""

from typing import List, Dict, Any, Optional
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


def identify_liquidity_grab(
    swing: Dict[str, Any],
    previous_swings: List[Dict[str, Any]],
    swing_type: str,
    threshold_pct: float = None,
) -> bool:
    """
    Determine if a swing point grabbed liquidity.

    A swing "grabs liquidity" when it sweeps a previous swing high/low,
    triggering stop losses and limit orders clustered at that level.

    Args:
        swing: Current swing point dictionary
        previous_swings: List of previous swing points to check against
        swing_type: "high" or "low"
        threshold_pct: Minimum % move beyond previous swing to count as grab

    Returns:
        True if liquidity was grabbed, False otherwise
    """
    if threshold_pct is None:
        threshold_pct = ICT_CONFIG.liquidity_grab_threshold_pct

    if not previous_swings:
        return False

    current_price = _to_num(swing["price"])

    # Check if this swing exceeded any previous swing by threshold
    for prev_swing in previous_swings:
        prev_price = _to_num(prev_swing["price"])

        if swing_type == "high":
            # Liquidity grab on high: current high > previous high by threshold
            pct_move = ((current_price - prev_price) / prev_price) * 100
            if pct_move >= threshold_pct:
                return True
        else:
            # Liquidity grab on low: current low < previous low by threshold
            pct_move = ((prev_price - current_price) / prev_price) * 100
            if pct_move >= threshold_pct:
                return True

    return False


def calculate_dealing_range(
    candles: List[Dict[str, Any]],
    swing_highs: List[Dict[str, Any]],
    swing_lows: List[Dict[str, Any]],
    current_price: float,
) -> Dict[str, Any]:
    """
    Calculate the dealing range from recent swings.

    Args:
        candles: Candle data
        swing_highs: Detected swing highs
        swing_lows: Detected swing lows
        current_price: Current market price

    Returns:
        Dictionary containing:
        - range_low: Price at range low
        - range_high: Price at range high
        - range_size: High - Low
        - midpoint: 50% level
        - current_percent: Where current price sits in range (0.0-1.0)
        - zone: "discount", "premium", or "mid-range"
        - valid: True if range is clear, False if unclear

    Example:
        >>> result = calculate_dealing_range(candles, highs, lows, 66200)
        >>> # Returns:
        >>> # {
        >>> #   "range_low": 66000,
        >>> #   "range_high": 68000,
        >>> #   "range_size": 2000,
        >>> #   "midpoint": 67000,
        >>> #   "current_percent": 0.10,  # 10% of range
        >>> #   "zone": "discount",
        >>> #   "valid": True
        >>> # }
    """
    # Need at least one swing high and one swing low
    if not swing_highs or not swing_lows:
        return {
            "range_low": None,
            "range_high": None,
            "range_size": None,
            "midpoint": None,
            "current_percent": None,
            "zone": "unknown",
            "valid": False,
            "reason": "Insufficient swings (need at least 1 high and 1 low)"
        }

    # Find most recent swing low that potentially grabbed liquidity
    range_low = None
    range_low_swing = None
    for i in range(len(swing_lows) - 1, -1, -1):
        swing = swing_lows[i]
        # Check if this swing grabbed liquidity from previous lows
        previous_lows = swing_lows[:i] if i > 0 else []
        if identify_liquidity_grab(swing, previous_lows, "low"):
            range_low = _to_num(swing["price"])
            range_low_swing = swing
            break

    # If no liquidity grab found, use most recent swing low
    if range_low is None:
        range_low = _to_num(swing_lows[-1]["price"])
        range_low_swing = swing_lows[-1]

    # Find most recent swing high that potentially grabbed liquidity
    range_high = None
    range_high_swing = None
    for i in range(len(swing_highs) - 1, -1, -1):
        swing = swing_highs[i]
        # Check if this swing grabbed liquidity from previous highs
        previous_highs = swing_highs[:i] if i > 0 else []
        if identify_liquidity_grab(swing, previous_highs, "high"):
            range_high = _to_num(swing["price"])
            range_high_swing = swing
            break

    # If no liquidity grab found, use most recent swing high
    if range_high is None:
        range_high = _to_num(swing_highs[-1]["price"])
        range_high_swing = swing_highs[-1]

    # Calculate range metrics
    range_size = range_high - range_low
    midpoint = (range_high + range_low) / 2.0

    # Calculate where current price sits in the range
    if range_size > 0:
        current_percent = (current_price - range_low) / range_size
    else:
        current_percent = 0.5  # If range is flat, assume mid-range

    # Determine zone (with mid-range buffer)
    discount_threshold = ICT_CONFIG.discount_threshold - ICT_CONFIG.mid_range_buffer
    premium_threshold = ICT_CONFIG.premium_threshold + ICT_CONFIG.mid_range_buffer

    if current_percent <= discount_threshold:
        zone = "discount"
    elif current_percent >= premium_threshold:
        zone = "premium"
    else:
        zone = "mid-range"

    return {
        "range_low": round(range_low, 2),
        "range_high": round(range_high, 2),
        "range_size": round(range_size, 2),
        "midpoint": round(midpoint, 2),
        "current_percent": round(current_percent, 3),
        "zone": zone,
        "valid": True,
        "range_low_swing": range_low_swing,
        "range_high_swing": range_high_swing,
    }


def is_price_in_discount(dealing_range: Dict[str, Any]) -> bool:
    """
    Check if current price is in discount zone (below 50% of dealing range).

    Args:
        dealing_range: Dealing range dictionary from calculate_dealing_range()

    Returns:
        True if in discount (good for longs), False otherwise
    """
    return dealing_range.get("valid", False) and dealing_range.get("zone") == "discount"


def is_price_in_premium(dealing_range: Dict[str, Any]) -> bool:
    """
    Check if current price is in premium zone (above 50% of dealing range).

    Args:
        dealing_range: Dealing range dictionary from calculate_dealing_range()

    Returns:
        True if in premium (good for shorts), False otherwise
    """
    return dealing_range.get("valid", False) and dealing_range.get("zone") == "premium"


def is_price_in_mid_range(dealing_range: Dict[str, Any]) -> bool:
    """
    Check if current price is in mid-range (around 50%).

    Mid-range is typically avoided for entries as it offers poor risk/reward.

    Args:
        dealing_range: Dealing range dictionary from calculate_dealing_range()

    Returns:
        True if in mid-range, False otherwise
    """
    return dealing_range.get("valid", False) and dealing_range.get("zone") == "mid-range"

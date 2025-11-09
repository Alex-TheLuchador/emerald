"""
Dealing Range Calculator for ICT Strategy

The dealing range defines entry zones:
- Range Low: Recent swing low that grabbed liquidity
- Range High: Recent swing high that grabbed liquidity
- Discount Zone: Below 50% of range (long entries)
- Premium Zone: Above 50% of range (short entries)
"""

from typing import List, Dict, Any, Optional


def identify_liquidity_grab(
    swing: Dict[str, Any],
    candles: List[Dict[str, Any]],
    threshold_pct: float = 0.1,
) -> bool:
    """
    Determine if a swing point grabbed liquidity.

    A swing "grabs liquidity" when it sweeps a previous swing high/low,
    triggering stop losses and limit orders clustered at that level.

    Args:
        swing: Swing point dictionary
        candles: Candle data
        threshold_pct: Minimum % move beyond previous swing to count as grab

    Returns:
        True if liquidity was grabbed, False otherwise
    """
    # TODO: Implement in Phase 2
    # Logic: Check if this swing exceeded a previous swing of the same type
    # by at least threshold_pct
    raise NotImplementedError("To be implemented in Phase 2")


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
    # TODO: Implement in Phase 2
    # Logic:
    # 1. Find most recent swing low that grabbed liquidity → range_low
    # 2. Find most recent swing high that grabbed liquidity → range_high
    # 3. Calculate midpoint = (high + low) / 2
    # 4. Calculate current_percent = (current_price - low) / (high - low)
    # 5. Determine zone: <45% = discount, >55% = premium, else mid-range
    raise NotImplementedError("To be implemented in Phase 2")


def is_price_in_discount(dealing_range: Dict[str, Any]) -> bool:
    """
    Check if current price is in discount zone (below 50% of dealing range).

    Args:
        dealing_range: Dealing range dictionary from calculate_dealing_range()

    Returns:
        True if in discount (good for longs), False otherwise
    """
    return dealing_range.get("zone") == "discount"


def is_price_in_premium(dealing_range: Dict[str, Any]) -> bool:
    """
    Check if current price is in premium zone (above 50% of dealing range).

    Args:
        dealing_range: Dealing range dictionary from calculate_dealing_range()

    Returns:
        True if in premium (good for shorts), False otherwise
    """
    return dealing_range.get("zone") == "premium"

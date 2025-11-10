"""
Liquidity Pool Tracker for ICT Strategy

Liquidity pools are price levels where stops and orders cluster.
Price is drawn to these levels like a magnet.

Primary pools (in order of significance):
1. Previous Day High (PDH) / Previous Day Low (PDL)
2. Session Highs/Lows (Asian, London, New York)
3. Equal Highs/Equal Lows
4. Round Numbers
"""

from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add project root to path
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


def calculate_pdh_pdl(candles: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate Previous Day High (PDH) and Previous Day Low (PDL).

    PDH/PDL are the most significant intraday liquidity levels.

    Args:
        candles: Last 48+ hours of candle data (any timeframe, preferably 1h or 4h)

    Returns:
        Dictionary with PDH and PDL prices
        {"pdh": 68000.0, "pdl": 66000.0}
    """
    if not candles:
        return {"pdh": None, "pdl": None}

    # Get current time
    now = datetime.now(tz=timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    # Filter candles from yesterday (00:00-23:59 UTC)
    yesterday_candles = []
    for candle in candles:
        candle_time = datetime.fromtimestamp(candle["t"] / 1000, tz=timezone.utc)
        if yesterday_start <= candle_time < today_start:
            yesterday_candles.append(candle)

    if not yesterday_candles:
        # If no yesterday candles, use older data
        if len(candles) >= 24:
            # Take the 24 candles before the most recent
            yesterday_candles = candles[-48:-24] if len(candles) >= 48 else candles[-24:]
        else:
            yesterday_candles = candles

    # Find max high and min low from yesterday
    pdh = max(_to_num(c["h"]) for c in yesterday_candles)
    pdl = min(_to_num(c["l"]) for c in yesterday_candles)

    return {
        "pdh": round(pdh, 2) if pdh != float("nan") else None,
        "pdl": round(pdl, 2) if pdl != float("nan") else None,
    }


def detect_equal_highs_lows(
    swing_highs: List[Dict[str, Any]],
    swing_lows: List[Dict[str, Any]],
    tolerance_pct: float = None,
) -> Dict[str, List[float]]:
    """
    Detect equal highs and equal lows.

    Equal highs/lows = 2+ swing points at approximately the same price level.
    These are obvious levels where retail traders cluster stop losses.

    Args:
        swing_highs: List of swing high points
        swing_lows: List of swing low points
        tolerance_pct: Price tolerance for "equal" (default: from config)

    Returns:
        Dictionary:
        {
            "equal_highs": [68000.0, 67500.0],  # Prices with 2+ swing highs
            "equal_lows": [66000.0, 65500.0]    # Prices with 2+ swing lows
        }
    """
    if tolerance_pct is None:
        tolerance_pct = ICT_CONFIG.equal_levels_tolerance_pct

    def find_equal_levels(swings: List[Dict[str, Any]]) -> List[float]:
        """Helper to find clustered price levels."""
        if len(swings) < 2:
            return []

        # Group swings by price (within tolerance)
        price_groups = {}
        for swing in swings:
            price = _to_num(swing["price"])
            if price == float("nan"):
                continue

            # Check if price is within tolerance of any existing group
            found_group = False
            for group_price in price_groups.keys():
                pct_diff = abs((price - group_price) / group_price) * 100
                if pct_diff <= tolerance_pct:
                    price_groups[group_price].append(price)
                    found_group = True
                    break

            if not found_group:
                price_groups[price] = [price]

        # Return groups with 2+ swings
        equal_levels = []
        for group_price, prices in price_groups.items():
            if len(prices) >= 2:
                # Use average of the group
                avg_price = sum(prices) / len(prices)
                equal_levels.append(round(avg_price, 2))

        return sorted(equal_levels)

    equal_highs = find_equal_levels(swing_highs)
    equal_lows = find_equal_levels(swing_lows)

    return {
        "equal_highs": equal_highs,
        "equal_lows": equal_lows,
    }


def identify_round_numbers(
    current_price: float,
    range_pct: float = 5.0,
) -> List[float]:
    """
    Identify psychologically significant round numbers near current price.

    Round numbers (e.g., $60,000, $65,000, $70,000 for BTC) attract retail orders.

    Args:
        current_price: Current market price
        range_pct: How far above/below to look (default: 5%)

    Returns:
        List of round number levels within range
        Example: [65000.0, 66000.0, 67000.0, 68000.0, 69000.0, 70000.0]
    """
    if current_price <= 0:
        return []

    # Determine appropriate rounding level based on price magnitude
    if current_price >= 10000:
        # For BTC-sized prices, use $1000 intervals
        round_level = 1000
    elif current_price >= 1000:
        # For ETH-sized prices, use $100 intervals
        round_level = 100
    elif current_price >= 100:
        # For SOL-sized prices, use $10 intervals
        round_level = 10
    else:
        # For smaller prices, use $1 intervals
        round_level = 1

    # Calculate range
    range_amount = current_price * (range_pct / 100)
    min_price = current_price - range_amount
    max_price = current_price + range_amount

    # Generate round numbers within range
    start = int(min_price / round_level) * round_level
    end = int(max_price / round_level) * round_level + round_level

    round_numbers = []
    price = start
    while price <= end:
        if price > 0:  # Don't include zero or negative
            round_numbers.append(float(price))
        price += round_level

    return round_numbers


def get_all_liquidity_pools(
    candles: List[Dict[str, Any]],
    swing_highs: List[Dict[str, Any]],
    swing_lows: List[Dict[str, Any]],
    current_price: float,
) -> Dict[str, Any]:
    """
    Aggregate all liquidity pools for current market conditions.

    Master function that combines PDH/PDL, equal highs/lows, and round numbers.

    Args:
        candles: Recent candle data (48+ hours recommended)
        swing_highs: Detected swing highs
        swing_lows: Detected swing lows
        current_price: Current market price

    Returns:
        Complete liquidity pool map:
        {
            "pdh": 68000.0,
            "pdl": 66000.0,
            "equal_highs": [68000.0, 67500.0],
            "equal_lows": [66000.0, 65500.0],
            "round_numbers": [66000.0, 67000.0, 68000.0],
            "nearest_above": 68000.0,  # Closest liquidity above current price
            "nearest_below": 66000.0,  # Closest liquidity below current price
        }
    """
    # Calculate PDH/PDL
    pdh_pdl = calculate_pdh_pdl(candles)

    # Detect equal highs/lows
    equal_levels = detect_equal_highs_lows(swing_highs, swing_lows)

    # Identify round numbers
    round_numbers = identify_round_numbers(current_price)

    # Aggregate all liquidity levels
    all_levels_above = []
    all_levels_below = []

    # Add PDH/PDL
    if pdh_pdl["pdh"] and pdh_pdl["pdh"] > current_price:
        all_levels_above.append(pdh_pdl["pdh"])
    if pdh_pdl["pdl"] and pdh_pdl["pdl"] < current_price:
        all_levels_below.append(pdh_pdl["pdl"])

    # Add equal highs/lows
    for level in equal_levels["equal_highs"]:
        if level > current_price:
            all_levels_above.append(level)
        elif level < current_price:
            all_levels_below.append(level)

    for level in equal_levels["equal_lows"]:
        if level < current_price:
            all_levels_below.append(level)
        elif level > current_price:
            all_levels_above.append(level)

    # Add round numbers
    for level in round_numbers:
        if level > current_price:
            all_levels_above.append(level)
        elif level < current_price:
            all_levels_below.append(level)

    # Find nearest levels
    nearest_above = min(all_levels_above) if all_levels_above else None
    nearest_below = max(all_levels_below) if all_levels_below else None

    return {
        "pdh": pdh_pdl["pdh"],
        "pdl": pdh_pdl["pdl"],
        "equal_highs": equal_levels["equal_highs"],
        "equal_lows": equal_levels["equal_lows"],
        "round_numbers": round_numbers,
        "nearest_above": nearest_above,
        "nearest_below": nearest_below,
        "all_above": sorted(set(all_levels_above)),
        "all_below": sorted(set(all_levels_below), reverse=True),
    }

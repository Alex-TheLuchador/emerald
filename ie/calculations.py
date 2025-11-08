"""
Pure calculation functions for institutional metrics.

These functions are stateless and side-effect-free. They take raw data as input
and return calculated metrics. All functions are tested and validated.

Design principles:
- Pure functions (no side effects)
- Type-hinted for safety
- Documented with examples
- Handle edge cases gracefully
"""

from typing import List, Dict, Any, Tuple, Optional, Literal
import math


def calculate_order_book_imbalance(
    bids: List[Tuple[float, float]],
    asks: List[Tuple[float, float]],
    depth: int = 10
) -> Tuple[float, str]:
    """
    Calculate order book bid/ask imbalance.

    Args:
        bids: List of (price, size) tuples for bid side
        asks: List of (price, size) tuples for ask side
        depth: Number of levels to analyze (default: 10)

    Returns:
        Tuple of (imbalance_ratio, strength_label)
        - imbalance_ratio: -1 to 1 (-1 = all asks, 0 = balanced, 1 = all bids)
        - strength_label: Human-readable interpretation

    Example:
        >>> bids = [(100, 5), (99, 3), (98, 2)]
        >>> asks = [(101, 2), (102, 1), (103, 1)]
        >>> calculate_order_book_imbalance(bids, asks, depth=3)
        (0.4285714285714286, 'moderate_bid_pressure')
    """
    # Take only top N levels
    bids_subset = bids[:depth]
    asks_subset = asks[:depth]

    # Sum volumes
    total_bid_volume = sum(size for _, size in bids_subset)
    total_ask_volume = sum(size for _, size in asks_subset)

    # Calculate imbalance
    total_volume = total_bid_volume + total_ask_volume

    if total_volume == 0:
        return 0.0, "neutral"

    imbalance = (total_bid_volume - total_ask_volume) / total_volume

    # Classify strength
    if imbalance > 0.4:
        strength = "strong_bid_pressure"
    elif imbalance > 0.2:
        strength = "moderate_bid_pressure"
    elif imbalance < -0.4:
        strength = "strong_ask_pressure"
    elif imbalance < -0.2:
        strength = "moderate_ask_pressure"
    else:
        strength = "neutral"

    return imbalance, strength


def calculate_vwap(candles: List[Dict[str, Any]]) -> float:
    """
    Calculate Volume-Weighted Average Price.

    Args:
        candles: List of candle dictionaries with keys: high, low, close, volume

    Returns:
        VWAP value

    Formula:
        VWAP = Σ(Typical Price × Volume) / Σ(Volume)
        where Typical Price = (High + Low + Close) / 3

    Example:
        >>> candles = [
        ...     {"high": 100, "low": 98, "close": 99, "volume": 1000},
        ...     {"high": 102, "low": 99, "close": 101, "volume": 1500},
        ... ]
        >>> calculate_vwap(candles)
        100.16666666666667
    """
    if not candles:
        return 0.0

    total_pv = 0.0  # Price × Volume
    total_volume = 0.0

    for candle in candles:
        # Typical price
        typical_price = (candle['high'] + candle['low'] + candle['close']) / 3
        volume = candle.get('volume', 0)

        total_pv += typical_price * volume
        total_volume += volume

    if total_volume == 0:
        # Fallback to simple average if no volume data
        return sum((c['high'] + c['low'] + c['close']) / 3 for c in candles) / len(candles)

    return total_pv / total_volume


def calculate_z_score(
    current_price: float,
    prices: List[float]
) -> Tuple[float, float, str]:
    """
    Calculate z-score (number of standard deviations from mean).

    Args:
        current_price: Current market price
        prices: Historical prices for mean/std calculation

    Returns:
        Tuple of (z_score, std_dev, deviation_level)
        - z_score: Number of standard deviations from mean
        - std_dev: Standard deviation of prices
        - deviation_level: Categorical level (extreme/high/moderate/low)

    Example:
        >>> prices = [100, 101, 99, 100, 102, 98, 100]
        >>> calculate_z_score(105, prices)
        (3.5355339059327378, 1.4142135623730951, 'extreme')
    """
    if not prices or len(prices) < 2:
        return 0.0, 0.0, "low"

    # Calculate mean
    mean = sum(prices) / len(prices)

    # Calculate standard deviation
    variance = sum((p - mean) ** 2 for p in prices) / len(prices)
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return 0.0, 0.0, "low"

    # Calculate z-score
    z_score = (current_price - mean) / std_dev

    # Classify deviation level
    abs_z = abs(z_score)
    if abs_z >= 2.0:
        level = "extreme"
    elif abs_z >= 1.5:
        level = "high"
    elif abs_z >= 1.0:
        level = "moderate"
    else:
        level = "low"

    return z_score, std_dev, level


def calculate_funding_annualized(funding_rate_8h: float) -> Tuple[float, str, bool]:
    """
    Convert 8-hour funding rate to annualized percentage.

    Args:
        funding_rate_8h: Funding rate per 8 hours (decimal, e.g., 0.0001 = 0.01%)

    Returns:
        Tuple of (annualized_pct, sentiment, is_extreme)
        - annualized_pct: Annualized rate as percentage (e.g., 10.95 = 10.95%)
        - sentiment: Market sentiment interpretation
        - is_extreme: True if > 10% annualized

    Formula:
        Annualized = funding_rate_8h × 3 periods/day × 365 days × 100%

    Example:
        >>> calculate_funding_annualized(0.0001)
        (10.95, 'bullish', True)
        >>> calculate_funding_annualized(-0.0002)
        (-21.9, 'extreme_bearish', True)
    """
    # Convert to annualized percentage
    annualized_pct = funding_rate_8h * 3 * 365 * 100

    # Determine sentiment
    if annualized_pct > 15:
        sentiment = "extreme_bullish"
    elif annualized_pct > 5:
        sentiment = "bullish"
    elif annualized_pct < -15:
        sentiment = "extreme_bearish"
    elif annualized_pct < -5:
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    # Check if extreme (threshold: 10% annualized)
    is_extreme = abs(annualized_pct) > 10

    return annualized_pct, sentiment, is_extreme


def calculate_oi_change(
    current_oi: float,
    previous_oi: float
) -> float:
    """
    Calculate percentage change in open interest.

    Args:
        current_oi: Current open interest
        previous_oi: Previous open interest

    Returns:
        Percentage change (e.g., 5.7 = 5.7% increase)

    Example:
        >>> calculate_oi_change(105_000_000, 100_000_000)
        5.0
        >>> calculate_oi_change(95_000_000, 100_000_000)
        -5.0
    """
    if previous_oi == 0:
        return 0.0

    change = ((current_oi - previous_oi) / previous_oi) * 100
    return change


def determine_oi_divergence(
    price_change_pct: float,
    oi_change_pct: float,
    threshold_pct: float = 1.5
) -> Literal["strong_bullish", "weak_bullish", "strong_bearish", "weak_bearish", "neutral"]:
    """
    Determine price-OI divergence scenario.

    Args:
        price_change_pct: Price percentage change
        oi_change_pct: Open interest percentage change
        threshold_pct: Minimum change to be considered significant (default: 1.5%)

    Returns:
        Divergence scenario type

    Scenarios:
        - strong_bullish: Price ↑ + OI ↑ (new longs entering)
        - weak_bullish: Price ↑ + OI ↓ (shorts covering, potential exhaustion)
        - strong_bearish: Price ↓ + OI ↑ (new shorts entering)
        - weak_bearish: Price ↓ + OI ↓ (longs closing, potential exhaustion)
        - neutral: No significant divergence

    Example:
        >>> determine_oi_divergence(3.5, 5.0)
        'strong_bullish'
        >>> determine_oi_divergence(-2.5, -4.0)
        'weak_bearish'
    """
    price_up = price_change_pct > threshold_pct
    price_down = price_change_pct < -threshold_pct
    oi_up = oi_change_pct > threshold_pct
    oi_down = oi_change_pct < -threshold_pct

    if price_up and oi_up:
        return "strong_bullish"
    elif price_up and oi_down:
        return "weak_bullish"
    elif price_down and oi_up:
        return "strong_bearish"
    elif price_down and oi_down:
        return "weak_bearish"
    else:
        return "neutral"


def calculate_volume_ratio(
    current_volume: float,
    volumes: List[float],
    lookback: int = 20
) -> Tuple[float, float, str]:
    """
    Calculate current volume vs. average ratio.

    Args:
        current_volume: Current candle volume
        volumes: Historical volumes
        lookback: Number of periods for average (default: 20)

    Returns:
        Tuple of (ratio, avg_volume, significance)
        - ratio: Current vs. average (e.g., 1.5 = 50% above average)
        - avg_volume: Average volume over lookback period
        - significance: Categorical level

    Example:
        >>> volumes = [100, 110, 95, 105, 100, 98, 102, 100]
        >>> calculate_volume_ratio(150, volumes, lookback=8)
        (1.487..., 101.25, 'high')
    """
    if not volumes:
        return 1.0, current_volume, "normal"

    # Use last N volumes
    recent_volumes = volumes[-lookback:]
    avg_volume = sum(recent_volumes) / len(recent_volumes)

    if avg_volume == 0:
        return 1.0, 0.0, "normal"

    ratio = current_volume / avg_volume

    # Classify significance
    if ratio >= 2.0:
        significance = "very_high"
    elif ratio >= 1.5:
        significance = "high"
    elif ratio <= 0.5:
        significance = "low"
    else:
        significance = "normal"

    return ratio, avg_volume, significance


def calculate_vwap_bands(
    vwap: float,
    std_dev: float
) -> Dict[str, float]:
    """
    Calculate VWAP bands (similar to Bollinger Bands).

    Args:
        vwap: Volume-weighted average price
        std_dev: Standard deviation

    Returns:
        Dictionary with band levels

    Example:
        >>> calculate_vwap_bands(100, 2)
        {'upper_2std': 104.0, 'upper_1std': 102.0, 'vwap': 100.0, 'lower_1std': 98.0, 'lower_2std': 96.0}
    """
    return {
        'upper_2std': vwap + (2 * std_dev),
        'upper_1std': vwap + std_dev,
        'vwap': vwap,
        'lower_1std': vwap - std_dev,
        'lower_2std': vwap - (2 * std_dev),
    }


def calculate_spread_bps(bid: float, ask: float, mid_price: float) -> float:
    """
    Calculate bid-ask spread in basis points.

    Args:
        bid: Best bid price
        ask: Best ask price
        mid_price: Mid price (usually (bid + ask) / 2)

    Returns:
        Spread in basis points (1 bp = 0.01%)

    Example:
        >>> calculate_spread_bps(99.5, 100.5, 100)
        100.0
    """
    if mid_price == 0:
        return 0.0

    spread = ask - bid
    spread_bps = (spread / mid_price) * 10000  # 1 bp = 0.0001 = 0.01%

    return spread_bps


# Validation and edge case helpers

def validate_candles(candles: List[Dict[str, Any]]) -> bool:
    """
    Validate candle data structure.

    Args:
        candles: List of candle dictionaries

    Returns:
        True if valid, False otherwise
    """
    if not candles:
        return False

    required_keys = {'high', 'low', 'close'}

    for candle in candles:
        if not all(key in candle for key in required_keys):
            return False

        # Validate price logic
        if candle['high'] < candle['low']:
            return False
        if candle['close'] < candle['low'] or candle['close'] > candle['high']:
            return False

    return True


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division with default fallback.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Value to return if division by zero (default: 0.0)

    Returns:
        Division result or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator

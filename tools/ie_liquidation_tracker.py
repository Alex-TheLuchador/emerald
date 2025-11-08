"""
Liquidation Cascade Detector for Institutional Engine.

Tracks liquidation events from Hyperliquid to identify:
- Long squeezes (cascading long liquidations = bearish)
- Short squeezes (cascading short liquidations = bullish)
- Stop hunt zones (price levels with high liquidation density)
- Liquidation cascades (mass liquidations in <5 min = momentum signal)

Liquidations are a leading indicator of violent price moves.
"""

import requests
from typing import Dict, Any, List
from datetime import datetime, timezone
from collections import defaultdict
from langchain.tools import tool

API_URL = "https://api.hyperliquid.xyz/info"
CACHE_TTL = 5  # 5 seconds


def _fetch_recent_liquidations(coin: str, lookback_minutes: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch recent liquidations from Hyperliquid.

    Note: Hyperliquid's liquidation API may have specific requirements.
    This is a placeholder implementation - adjust based on actual API.

    Args:
        coin: Trading pair
        lookback_minutes: How far back to look

    Returns:
        List of liquidation events
    """
    # Note: Hyperliquid API structure may vary
    # This implementation assumes a liquidations endpoint exists
    # Adjust based on actual API documentation

    try:
        # Try to fetch user funding data which may include liquidations
        # This is a placeholder - actual implementation depends on API
        payload = {
            "type": "userFunding",
            "user": "0x0000000000000000000000000000000000000000"  # Placeholder
        }

        response = requests.post(API_URL, json=payload, timeout=15)

        # For now, return empty list as liquidation API needs verification
        # TODO: Verify Hyperliquid liquidation API endpoint
        return []

    except Exception:
        return []


def calculate_liquidation_metrics(
    liquidations: List[Dict[str, Any]],
    lookback_minutes: int = 30
) -> Dict[str, Any]:
    """
    Calculate liquidation cascade metrics.

    Args:
        liquidations: List of liquidation events
        lookback_minutes: Time window analyzed

    Returns:
        Liquidation analysis metrics
    """
    if not liquidations:
        return {
            "total_liquidations": 0,
            "long_liquidations_usd": 0.0,
            "short_liquidations_usd": 0.0,
            "liquidation_ratio": 0.0,
            "cascade_detected": False,
            "stop_hunt_zones": [],
            "signal": "neutral"
        }

    long_liq_volume = 0.0
    short_liq_volume = 0.0
    liquidation_times = []
    price_levels = defaultdict(float)  # {price: total_volume_liquidated}

    for liq in liquidations:
        side = liq.get("side", "").lower()
        size_usd = float(liq.get("size_usd", 0))
        price = float(liq.get("price", 0))
        timestamp = liq.get("timestamp", 0)

        if side == "long":
            long_liq_volume += size_usd
        elif side == "short":
            short_liq_volume += size_usd

        liquidation_times.append(timestamp)
        price_levels[round(price, 2)] += size_usd

    total_liquidations = len(liquidations)
    total_volume = long_liq_volume + short_liq_volume

    # Calculate liquidation ratio (long vs short)
    if total_volume > 0:
        liq_ratio = (short_liq_volume - long_liq_volume) / total_volume
    else:
        liq_ratio = 0.0

    # Detect cascade (5+ liquidations within 5 minutes)
    cascade_detected = False
    if len(liquidation_times) >= 5:
        # Check if 5+ liquidations happened within 300 seconds
        sorted_times = sorted(liquidation_times)
        for i in range(len(sorted_times) - 4):
            time_span = sorted_times[i + 4] - sorted_times[i]
            if time_span <= 300:  # 5 minutes
                cascade_detected = True
                break

    # Identify stop hunt zones (prices with >$100k liquidations)
    stop_hunt_zones = [
        {"price": price, "volume_usd": round(volume, 2)}
        for price, volume in price_levels.items()
        if volume >= 100000
    ]
    stop_hunt_zones.sort(key=lambda x: x["volume_usd"], reverse=True)

    # Generate signal
    if cascade_detected and liq_ratio > 0.5:
        signal = "short_squeeze_bullish"
    elif cascade_detected and liq_ratio < -0.5:
        signal = "long_squeeze_bearish"
    elif liq_ratio > 0.6:
        signal = "moderate_short_squeeze"
    elif liq_ratio < -0.6:
        signal = "moderate_long_squeeze"
    else:
        signal = "neutral"

    return {
        "total_liquidations": total_liquidations,
        "long_liquidations_usd": round(long_liq_volume, 2),
        "short_liquidations_usd": round(short_liq_volume, 2),
        "liquidation_ratio": round(liq_ratio, 4),
        "cascade_detected": cascade_detected,
        "stop_hunt_zones": stop_hunt_zones[:5],  # Top 5
        "signal": signal,
        "lookback_minutes": lookback_minutes
    }


def analyze_liquidations(coin: str, lookback_minutes: int = 30) -> Dict[str, Any]:
    """
    Comprehensive liquidation cascade analysis.

    Args:
        coin: Trading pair
        lookback_minutes: Time window to analyze

    Returns:
        Liquidation analysis with cascade detection
    """
    liquidations = _fetch_recent_liquidations(coin, lookback_minutes)
    metrics = calculate_liquidation_metrics(liquidations, lookback_minutes)

    metrics["coin"] = coin
    metrics["timestamp"] = datetime.now(tz=timezone.utc).isoformat()

    # Add interpretation
    if metrics["cascade_detected"]:
        if metrics["signal"] == "short_squeeze_bullish":
            metrics["interpretation"] = "Mass short liquidations detected. Strong bullish momentum likely."
        elif metrics["signal"] == "long_squeeze_bearish":
            metrics["interpretation"] = "Mass long liquidations detected. Strong bearish momentum likely."
        else:
            metrics["interpretation"] = "Liquidation cascade detected but mixed direction."
    else:
        if metrics["total_liquidations"] == 0:
            metrics["interpretation"] = "No recent liquidation data available from Hyperliquid API."
        else:
            metrics["interpretation"] = "Normal liquidation activity. No cascade pattern."

    return metrics


@tool
def fetch_liquidation_tracker_tool(
    coin: str,
    lookback_minutes: int = 30
) -> Dict[str, Any]:
    """
    Track liquidation cascades and stop hunt zones.

    Liquidations are a leading indicator of violent price moves:
    - Short squeeze (shorts liquidated) = bullish
    - Long squeeze (longs liquidated) = bearish
    - Cascade (5+ liquidations in 5 min) = high volatility signal

    Args:
        coin: Trading pair (e.g., "BTC")
        lookback_minutes: Time window in minutes (default: 30)

    Returns:
        Liquidation analysis with cascade detection
    """
    return analyze_liquidations(coin, lookback_minutes)


def fetch_liquidation_tracker(coin: str, lookback_minutes: int = 30) -> Dict[str, Any]:
    """
    Non-tool version for direct function calls.

    Args:
        coin: Trading pair
        lookback_minutes: Time window

    Returns:
        Liquidation analysis
    """
    return analyze_liquidations(coin, lookback_minutes)

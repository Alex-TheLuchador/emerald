"""
Multi-Timeframe Convergence Analyzer for Institutional Engine.

This is the core institutional edge: waiting for signal alignment
across multiple timeframes before taking any position.

Renaissance, Two Sigma, Citadel - they all use variants of this.
Only trade when convergence score > 70.
"""

import requests
from typing import Dict, Any, List
from langchain.tools import tool
from datetime import datetime, timezone

# Import existing IE tools
from tools.ie_fetch_order_book import fetch_order_book_metrics
from tools.ie_fetch_funding import fetch_funding_metrics
from tools.ie_fetch_open_interest import fetch_open_interest_metrics
from tools.ie_fetch_perpetuals_basis import fetch_perpetuals_basis
from tools.ie_fetch_trade_flow import fetch_trade_flow_metrics

API_URL = "https://api.hyperliquid.xyz/info"


def fetch_vwap_for_timeframe(coin: str, timeframe: str) -> Dict[str, Any]:
    """
    Fetch VWAP metrics for a specific timeframe.

    Timeframes: "1m", "5m", "15m", "1h"

    Args:
        coin: Trading pair
        timeframe: Candle timeframe

    Returns:
        VWAP metrics dictionary
    """
    # Map timeframe to candle count and hours
    timeframe_map = {
        "1m": {"interval": "1m", "hours": 1},      # 1 hour of 1m candles
        "5m": {"interval": "5m", "hours": 5},      # 5 hours of 5m candles
        "15m": {"interval": "15m", "hours": 15},   # 15 hours of 15m candles
        "1h": {"interval": "1h", "hours": 24},     # 24 hours of 1h candles
    }

    if timeframe not in timeframe_map:
        raise ValueError(f"Invalid timeframe: {timeframe}")

    config = timeframe_map[timeframe]

    # Calculate start time
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    start_ms = now_ms - (config["hours"] * 3600 * 1000)

    # Fetch candles from Hyperliquid
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": config["interval"],
            "startTime": start_ms,
        }
    }

    response = requests.post(API_URL, json=payload, timeout=15)
    response.raise_for_status()
    candles = response.json()

    # Calculate VWAP
    from ie.calculations import calculate_vwap, calculate_z_score

    if not candles or len(candles) < 2:
        return {"error": "Insufficient candle data"}

    # Parse candles (handle both dict and list formats)
    parsed_candles = []
    for candle in candles:
        if isinstance(candle, dict):
            parsed_candles.append({
                "high": float(candle.get("h", 0)),
                "low": float(candle.get("l", 0)),
                "close": float(candle.get("c", 0)),
                "volume": float(candle.get("v", 0)),
            })
        elif isinstance(candle, list) and len(candle) >= 6:
            # [timestamp, open, high, low, close, volume]
            parsed_candles.append({
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
            })

    if not parsed_candles:
        return {"error": "Failed to parse candles"}

    vwap = calculate_vwap(parsed_candles)
    current_price = parsed_candles[-1]["close"]

    # Get historical prices for z-score
    prices = [c["close"] for c in parsed_candles]
    z_score, std_dev, deviation_level = calculate_z_score(current_price, prices)

    deviation_pct = ((current_price - vwap) / vwap) * 100

    return {
        "timeframe": timeframe,
        "vwap": round(vwap, 2),
        "current_price": round(current_price, 2),
        "deviation_pct": round(deviation_pct, 4),
        "z_score": round(z_score, 4),
        "deviation_level": deviation_level,
    }


def analyze_timeframe_convergence(
    coin: str,
    timeframes: List[str] = None
) -> Dict[str, Any]:
    """
    Analyze signal convergence across multiple timeframes.

    This is the institutional edge: only trade when ALL timeframes
    show the same signal.

    Args:
        coin: Trading pair
        timeframes: List of timeframes to analyze

    Returns:
        Convergence analysis with conviction score
    """
    if timeframes is None:
        timeframes = ["1m", "5m", "15m"]

    # Fetch order book (single snapshot, not timeframe-dependent)
    try:
        ob = fetch_order_book_metrics(coin, depth=10, use_cache=True)
    except Exception as e:
        ob = {"error": str(e)}

    # Fetch trade flow (last 60 seconds)
    try:
        trade_flow = fetch_trade_flow_metrics(coin, lookback_seconds=60)
    except Exception as e:
        trade_flow = {"error": str(e)}

    # Fetch funding and basis (not timeframe-dependent)
    try:
        funding = fetch_funding_metrics(coin, use_cache=True)
    except Exception as e:
        funding = {"error": str(e)}

    try:
        basis = fetch_perpetuals_basis(coin, use_cache=True)
    except Exception as e:
        basis = {"error": str(e)}

    # Fetch VWAP for each timeframe
    vwap_data = {}
    for tf in timeframes:
        try:
            vwap_data[tf] = fetch_vwap_for_timeframe(coin, tf)
        except Exception as e:
            vwap_data[tf] = {"error": str(e)}

    # Calculate convergence score (0-100)
    score = 0
    signals = []

    # 1. Order Book Alignment (25 points)
    if "error" not in ob:
        ob_imbalance = ob.get("imbalance", 0)
        if abs(ob_imbalance) > 0.4:
            score += 25
            direction = "bullish" if ob_imbalance > 0 else "bearish"
            signals.append(f"order_book_{direction}")

    # 2. Trade Flow Alignment (25 points)
    if "error" not in trade_flow:
        tf_imbalance = trade_flow.get("imbalance", 0)
        if abs(tf_imbalance) > 0.4:
            score += 25
            direction = "bullish" if tf_imbalance > 0 else "bearish"
            signals.append(f"trade_flow_{direction}")

    # 3. VWAP Multi-Timeframe Alignment (30 points)
    # All timeframes must show same VWAP deviation direction
    vwap_deviations = []
    for tf, data in vwap_data.items():
        if "error" not in data:
            vwap_deviations.append(data.get("deviation_pct", 0))

    if len(vwap_deviations) >= 2:
        # Check if all deviations have same sign (all positive or all negative)
        all_positive = all(d > 1.0 for d in vwap_deviations)  # >1% above VWAP
        all_negative = all(d < -1.0 for d in vwap_deviations)  # >1% below VWAP

        if all_positive:
            score += 30
            signals.append("vwap_all_timeframes_above")
        elif all_negative:
            score += 30
            signals.append("vwap_all_timeframes_below")

    # 4. Funding-Basis Convergence (20 points)
    if "error" not in funding and "error" not in basis:
        funding_pct = funding.get("annualized_pct", 0)
        basis_pct = basis.get("basis_pct", 0)

        # Both bullish
        if funding_pct > 10 and basis_pct > 0.2:
            score += 20
            signals.append("funding_basis_bullish_convergence")
        # Both bearish
        elif funding_pct < -10 and basis_pct < -0.2:
            score += 20
            signals.append("funding_basis_bearish_convergence")
        # Divergence (penalty)
        elif (funding_pct > 10 and basis_pct < -0.1) or \
             (funding_pct < -10 and basis_pct > 0.1):
            score -= 15
            signals.append("funding_basis_divergence_avoid")

    # Ensure score doesn't go negative
    score = max(0, score)

    # Determine conviction level
    if score >= 85:
        conviction = "very_high"
        recommendation = "max_size_trade"
    elif score >= 70:
        conviction = "high"
        recommendation = "standard_size_trade"
    elif score >= 50:
        conviction = "moderate"
        recommendation = "reduced_size_trade"
    else:
        conviction = "low"
        recommendation = "no_trade"

    return {
        "coin": coin,
        "convergence_score": score,
        "conviction": conviction,
        "recommendation": recommendation,
        "signals": signals,
        "timeframes_analyzed": timeframes,
        "order_book": ob,
        "trade_flow": trade_flow,
        "funding": funding,
        "basis": basis,
        "vwap_by_timeframe": vwap_data,
    }


@tool
def fetch_multi_timeframe_convergence_tool(
    coin: str,
    timeframes: str = "1m,5m,15m"
) -> Dict[str, Any]:
    """
    Analyze multi-timeframe signal convergence (institutional edge).

    This tool checks if order book, trade flow, VWAP (across timeframes),
    funding, and basis all align. Only trade when convergence score > 70.

    Args:
        coin: Trading pair (e.g., "BTC")
        timeframes: Comma-separated timeframes (e.g., "1m,5m,15m")

    Returns:
        Convergence analysis with conviction score
    """
    # Parse timeframes string
    tf_list = [tf.strip() for tf in timeframes.split(",")]

    return analyze_timeframe_convergence(coin, tf_list)


def fetch_multi_timeframe_convergence(
    coin: str,
    timeframes: List[str] = None
) -> Dict[str, Any]:
    """
    Non-tool version for direct function calls.

    Args:
        coin: Trading pair
        timeframes: List of timeframes

    Returns:
        Convergence analysis
    """
    return analyze_timeframe_convergence(coin, timeframes)

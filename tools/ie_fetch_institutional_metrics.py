"""
Unified Institutional Metrics Tool for Institutional Engine.

This is the main agent-facing tool that combines all IE capabilities into a
single, comprehensive metrics package. The agent calls this one tool to get
complete institutional analysis.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from langchain.tools import tool
from datetime import datetime, timezone

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.ie_fetch_order_book import fetch_order_book_metrics
from tools.ie_fetch_funding import fetch_funding_metrics
from tools.ie_fetch_open_interest import fetch_open_interest_metrics
from ie.data_models import InstitutionalMetrics


def fetch_institutional_metrics(
    coin: str,
    include_order_book: bool = True,
    include_funding: bool = True,
    include_oi: bool = True,
    use_cache: bool = True,
    order_book_depth: int = 10,
    funding_lookback_hours: int = 24,
) -> Dict[str, Any]:
    """Fetch comprehensive institutional metrics for a trading pair.

    This is the main IE function that combines all data sources into a
    single, unified metrics package for agent analysis.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH", "SOL")
        include_order_book: Include order book imbalance metrics (default: True)
        include_funding: Include funding rate metrics (default: True)
        include_oi: Include open interest metrics (default: True)
        use_cache: Whether to use cached data (default: True)
        order_book_depth: Order book depth to analyze (default: 10)
        funding_lookback_hours: Hours of funding history (default: 24)

    Returns:
        Dictionary with comprehensive institutional metrics:
        {
            "coin": "BTC",
            "timestamp": "2025-11-08T12:00:00Z",
            "price": 67890.50,

            "order_book": {
                "imbalance": 0.45,
                "imbalance_strength": "strong_bid_pressure",
                "spread": 1.0,
                "spread_bps": 1.47,
                ...
            },

            "funding": {
                "rate_8h": 0.0001,
                "annualized_pct": 10.95,
                "sentiment": "bullish",
                "is_extreme": True,
                ...
            },

            "open_interest": {
                "current_usd": 125000000.0,
                "change_4h_pct": 5.7,
                "divergence_type": "strong_bullish",
                ...
            },

            "summary": {
                "signals": ["strong_bid_pressure", "extreme_funding", "strong_bullish_oi"],
                "convergence_score": 85,
                "recommendation": "high_conviction_long"
            }
        }

    Example:
        >>> metrics = fetch_institutional_metrics("BTC")
        >>> print(f"Convergence: {metrics['summary']['convergence_score']}")
        >>> print(f"Signals: {metrics['summary']['signals']}")
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    result = {
        "coin": coin,
        "timestamp": timestamp,
        "price": None,  # Will be populated from one of the fetchers
    }

    errors = []

    # Fetch order book metrics
    if include_order_book:
        ob_metrics = fetch_order_book_metrics(coin, order_book_depth, use_cache)
        if "error" in ob_metrics:
            errors.append(f"Order book: {ob_metrics['error']}")
            result["order_book"] = None
        else:
            result["order_book"] = ob_metrics
            if result["price"] is None and "top_bid" in ob_metrics and "top_ask" in ob_metrics:
                result["price"] = (ob_metrics["top_bid"] + ob_metrics["top_ask"]) / 2

    # Fetch funding metrics
    if include_funding:
        funding_metrics = fetch_funding_metrics(coin, funding_lookback_hours, use_cache)
        if "error" in funding_metrics:
            errors.append(f"Funding: {funding_metrics['error']}")
            result["funding"] = None
        else:
            result["funding"] = funding_metrics

    # Fetch OI metrics
    if include_oi:
        oi_metrics = fetch_open_interest_metrics(coin, use_cache)
        if "error" in oi_metrics:
            errors.append(f"Open interest: {oi_metrics['error']}")
            result["open_interest"] = None
        else:
            result["open_interest"] = oi_metrics
            if result["price"] is None and "current_price" in oi_metrics:
                result["price"] = oi_metrics["current_price"]

    # Add errors if any
    if errors:
        result["errors"] = errors

    # Generate summary and convergence analysis
    result["summary"] = _generate_summary(result)

    return result


def _generate_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary and convergence analysis from metrics.

    Args:
        metrics: Complete metrics dictionary

    Returns:
        Summary dict with signals, convergence score, and recommendation
    """
    signals = []
    convergence_score = 0
    bullish_signals = 0
    bearish_signals = 0

    # Analyze order book
    ob = metrics.get("order_book")
    if ob and ob is not None:
        if ob.get("imbalance", 0) > 0.3:
            signals.append("strong_bid_pressure")
            bullish_signals += 1
            convergence_score += 25
        elif ob.get("imbalance", 0) < -0.3:
            signals.append("strong_ask_pressure")
            bearish_signals += 1
            convergence_score += 25

    # Analyze funding
    funding = metrics.get("funding")
    if funding and funding is not None:
        if funding.get("is_extreme"):
            signals.append(f"extreme_funding_{funding.get('sentiment', 'unknown')}")
            # Extreme positive funding = fade signal (contrarian bearish)
            if funding.get("annualized_pct", 0) > 10:
                bearish_signals += 1
            elif funding.get("annualized_pct", 0) < -10:
                bullish_signals += 1
            convergence_score += 20

    # Analyze OI
    oi = metrics.get("open_interest")
    if oi and oi is not None:
        divergence = oi.get("divergence_type", "neutral")
        if divergence in ["strong_bullish", "strong_bearish"]:
            signals.append(f"{divergence}_oi")
            if divergence == "strong_bullish":
                bullish_signals += 1
            else:
                bearish_signals += 1
            convergence_score += 30

    # Determine recommendation
    if convergence_score >= 70 and bullish_signals > bearish_signals:
        recommendation = "high_conviction_long"
    elif convergence_score >= 70 and bearish_signals > bullish_signals:
        recommendation = "high_conviction_short"
    elif convergence_score >= 50:
        if bullish_signals > bearish_signals:
            recommendation = "moderate_long"
        elif bearish_signals > bullish_signals:
            recommendation = "moderate_short"
        else:
            recommendation = "neutral_mixed_signals"
    else:
        recommendation = "no_trade_low_conviction"

    return {
        "signals": signals,
        "convergence_score": convergence_score,
        "bullish_signals": bullish_signals,
        "bearish_signals": bearish_signals,
        "recommendation": recommendation,
    }


# LangChain tool wrapper
@tool
def fetch_institutional_metrics_tool(
    coin: str,
    include_order_book: bool = True,
    include_funding: bool = True,
    include_oi: bool = True,
) -> Dict[str, Any]:
    """Fetch comprehensive institutional-grade market metrics.

    This tool provides quantitative analysis using:
    - Order book imbalance (bid/ask pressure)
    - Funding rate extremes (sentiment)
    - Open interest divergence (smart money tracking)

    Use this to validate ICT setups with quantitative metrics.

    Args:
        coin: Trading pair (e.g., "BTC", "ETH")
        include_order_book: Include order book metrics
        include_funding: Include funding metrics
        include_oi: Include open interest metrics

    Returns:
        Complete institutional metrics package with summary
    """
    return fetch_institutional_metrics(
        coin=coin,
        include_order_book=include_order_book,
        include_funding=include_funding,
        include_oi=include_oi,
    )


# Standalone testing
if __name__ == "__main__":
    import json

    print("=" * 70)
    print("  UNIFIED INSTITUTIONAL METRICS - Demo")
    print("=" * 70)

    # Test with BTC
    print("\n🔍 Fetching complete institutional analysis for BTC...")
    metrics = fetch_institutional_metrics("BTC")

    if "errors" in metrics and metrics["errors"]:
        print(f"\n⚠️  Some data unavailable:")
        for error in metrics["errors"]:
            print(f"  - {error}")

    print("\n" + json.dumps(metrics, indent=2))

    # Show summary
    summary = metrics.get("summary", {})
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"Signals detected: {', '.join(summary.get('signals', []))}")
    print(f"Convergence score: {summary.get('convergence_score', 0)}/100")
    print(f"Bullish signals: {summary.get('bullish_signals', 0)}")
    print(f"Bearish signals: {summary.get('bearish_signals', 0)}")
    print(f"Recommendation: {summary.get('recommendation', 'unknown')}")

"""
Funding rate data fetcher for Institutional Engine.

Fetches funding rate data from Hyperliquid API and calculates
annualized rates and sentiment analysis using IE calculation functions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime, timezone
from langchain.tools import tool

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ie.calculations import calculate_funding_annualized
from ie.data_models import FundingMetrics
from ie.cache import get_cache


# API Configuration
API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}
REQUEST_TIMEOUT = 15
CACHE_TTL = 300  # Cache for 5 minutes (funding changes every 8h)


def _fetch_raw_funding(coin: str, lookback_hours: int = 24) -> Dict[str, Any]:
    """Fetch raw funding rate data from Hyperliquid API.

    Args:
        coin: Trading pair symbol (e.g., "BTC")
        lookback_hours: Hours of historical data (default: 24)

    Returns:
        Raw API response with funding data

    Raises:
        requests.exceptions.RequestException: On network errors
        ValueError: On invalid API response
    """
    # Calculate start time (milliseconds)
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    start_ms = now_ms - (lookback_hours * 3_600_000)

    # First, get current funding rate from meta
    meta_payload = {
        "type": "metaAndAssetCtxs"
    }

    try:
        response = requests.post(
            API_URL,
            json=meta_payload,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        meta_data = response.json()

        # Extract funding rate for the specified coin
        current_funding = None
        if isinstance(meta_data, list) and len(meta_data) > 1:
            # meta_data[1] contains asset contexts
            asset_ctxs = meta_data[1]
            for ctx in asset_ctxs:
                if isinstance(ctx, dict) and ctx.get("coin") == coin:
                    current_funding = float(ctx.get("funding", 0))
                    break

        # Now get funding history
        history_payload = {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": start_ms,
        }

        response = requests.post(
            API_URL,
            json=history_payload,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        history_data = response.json()

        return {
            "current_funding": current_funding,
            "history": history_data if isinstance(history_data, list) else [],
        }

    except requests.exceptions.Timeout:
        raise requests.exceptions.RequestException(f"API request timeout for {coin} funding")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"API request failed: {str(e)}")


def _parse_funding_history(history_data: List[Any]) -> List[Dict[str, Any]]:
    """Parse raw funding history data.

    Args:
        history_data: Raw history array from API

    Returns:
        List of parsed funding rate entries
    """
    parsed = []

    for entry in history_data:
        if isinstance(entry, dict):
            parsed.append({
                "time": entry.get("time", 0),
                "rate": float(entry.get("fundingRate", entry.get("funding", 0))),
            })
        elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
            parsed.append({
                "time": entry[0],
                "rate": float(entry[1]),
            })

    return parsed


def _calculate_funding_trend(history: List[Dict[str, Any]]) -> Optional[str]:
    """Determine if funding rate is increasing, decreasing, or stable.

    Args:
        history: List of funding rate entries (chronological)

    Returns:
        "increasing", "decreasing", "stable", or None if insufficient data
    """
    if len(history) < 3:
        return None

    # Get last 3 rates
    recent_3 = [h["rate"] for h in history[-3:]]

    # Check if monotonically increasing
    if all(recent_3[i] < recent_3[i+1] for i in range(len(recent_3)-1)):
        return "increasing"
    # Check if monotonically decreasing
    elif all(recent_3[i] > recent_3[i+1] for i in range(len(recent_3)-1)):
        return "decreasing"
    else:
        return "stable"


def fetch_funding_metrics(
    coin: str,
    lookback_hours: int = 24,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Fetch and analyze funding rate data from Hyperliquid.

    This tool fetches current and historical funding rates, calculates
    annualized rates, and determines market sentiment.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        lookback_hours: Hours of history to fetch (default: 24)
        use_cache: Whether to use cached data (default: True)

    Returns:
        Dictionary with funding rate metrics:
        {
            "coin": "BTC",
            "rate_8h": 0.0001,
            "annualized_pct": 10.95,
            "sentiment": "bullish",
            "is_extreme": True,
            "historical_avg_24h": 0.00012,
            "trend": "increasing",
            "history_count": 3,
            "cached": False
        }

    Example:
        >>> metrics = fetch_funding_metrics("BTC")
        >>> print(f"Funding: {metrics['annualized_pct']:.2f}%")
        >>> print(f"Sentiment: {metrics['sentiment']}")
    """
    # Validate inputs
    if lookback_hours < 1 or lookback_hours > 168:  # Max 1 week
        return {
            "error": "Lookback hours must be between 1 and 168",
            "coin": coin,
        }

    # Check cache
    cache = get_cache()
    cache_key = f"funding:{coin}:{lookback_hours}"

    if use_cache:
        cached_data = cache.get(cache_key, ttl=CACHE_TTL)
        if cached_data:
            cached_data["cached"] = True
            return cached_data

    try:
        # Fetch raw funding data
        raw_data = _fetch_raw_funding(coin, lookback_hours)
        current_rate = raw_data["current_funding"]

        if current_rate is None:
            return {
                "error": f"Could not find funding rate for {coin}",
                "coin": coin,
            }

        # Parse history
        history = _parse_funding_history(raw_data["history"])

        # Calculate annualized rate and sentiment
        annualized_pct, sentiment, is_extreme = calculate_funding_annualized(current_rate)

        # Calculate 24h average if we have history
        historical_avg = None
        if history:
            historical_avg = sum(h["rate"] for h in history) / len(history)

        # Determine trend
        trend = _calculate_funding_trend(history)

        # Build result
        result = {
            "coin": coin,
            "rate_8h": round(current_rate, 6),
            "annualized_pct": round(annualized_pct, 2),
            "sentiment": sentiment,
            "is_extreme": is_extreme,
            "historical_avg_24h": round(historical_avg, 6) if historical_avg else None,
            "trend": trend,
            "history_count": len(history),
            "cached": False,
        }

        # Cache the result
        if use_cache:
            cache.set(cache_key, result)

        return result

    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "coin": coin,
        }
    except ValueError as e:
        return {
            "error": f"Data parsing error: {str(e)}",
            "coin": coin,
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "coin": coin,
        }


# LangChain tool wrapper
@tool
def fetch_funding_metrics_tool(
    coin: str,
    lookback_hours: int = 24,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Fetch and analyze funding rate data from Hyperliquid.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        lookback_hours: Hours of history to fetch (default: 24)
        use_cache: Whether to use cached data (default: True)

    Returns:
        Dictionary with funding rate metrics
    """
    return fetch_funding_metrics(coin, lookback_hours, use_cache)


def fetch_funding_metrics_typed(
    coin: str,
    lookback_hours: int = 24,
    use_cache: bool = True
) -> Optional[FundingMetrics]:
    """Typed version that returns FundingMetrics dataclass.

    Args:
        coin: Trading pair symbol
        lookback_hours: Hours of history to fetch
        use_cache: Whether to use cached data

    Returns:
        FundingMetrics instance or None on error
    """
    result = fetch_funding_metrics(coin, lookback_hours, use_cache)

    if "error" in result:
        return None

    return FundingMetrics(
        rate_8h=result["rate_8h"],
        annualized_pct=result["annualized_pct"],
        sentiment=result["sentiment"],
        is_extreme=result["is_extreme"],
        historical_avg_24h=result.get("historical_avg_24h"),
        trend=result.get("trend"),
    )


# Standalone testing
if __name__ == "__main__":
    import json

    print("Testing Funding Rate Fetcher...")
    print("=" * 60)

    # Test with BTC
    print("\nFetching BTC funding rate...")
    result = fetch_funding_metrics("BTC", lookback_hours=24)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✓ Success!")
        print(json.dumps(result, indent=2))

        # Show interpretation
        print(f"\nInterpretation:")
        print(f"  Current (8h): {result['rate_8h']:.6f}")
        print(f"  Annualized: {result['annualized_pct']:.2f}%")
        print(f"  Sentiment: {result['sentiment']}")
        print(f"  Extreme: {'Yes' if result['is_extreme'] else 'No'}")
        if result['trend']:
            print(f"  Trend: {result['trend']}")

    # Test multiple coins
    print("\n" + "=" * 60)
    print("Testing multiple coins...")
    for coin in ["ETH", "SOL"]:
        print(f"\n{coin}:")
        result = fetch_funding_metrics(coin, lookback_hours=24)
        if "error" not in result:
            print(f"  Annualized: {result['annualized_pct']:+.2f}% ({result['sentiment']})")
        else:
            print(f"  Error: {result['error']}")

    # Show cache stats
    cache = get_cache()
    stats = cache.get_stats()
    print(f"\nCache stats:")
    print(f"  Hit rate: {stats['hit_rate_pct']:.1f}%")
    print(f"  Entries: {stats['entries']}")

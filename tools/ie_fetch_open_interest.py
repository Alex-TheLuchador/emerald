"""
Open Interest data fetcher for Institutional Engine.

Fetches open interest data from Hyperliquid API and calculates OI changes
and price-OI divergence scenarios using IE calculation functions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timezone
from langchain.tools import tool
import json

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ie.calculations import calculate_oi_change, determine_oi_divergence
from ie.data_models import OpenInterestMetrics
from ie.cache import get_cache


# API Configuration
API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}
REQUEST_TIMEOUT = 15
CACHE_TTL = 300  # Cache for 5 minutes


# Historical OI tracking (in-memory storage)
# In production, this should use a database
OI_HISTORY_FILE = BASE_DIR / "ie" / "oi_history.json"


def _load_oi_history() -> Dict[str, list]:
    """Load OI history from file.

    Returns:
        Dictionary mapping coin -> list of (timestamp, oi, price) tuples
    """
    try:
        if OI_HISTORY_FILE.exists():
            with open(OI_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_oi_history(history: Dict[str, list]) -> None:
    """Save OI history to file.

    Args:
        history: Dictionary mapping coin -> list of entries
    """
    try:
        OI_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OI_HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except Exception:
        pass  # Fail silently - history is nice-to-have


def _update_oi_history(coin: str, oi: float, price: float) -> None:
    """Update OI history with new data point.

    Args:
        coin: Trading pair
        oi: Open interest value
        price: Current price
    """
    history = _load_oi_history()

    if coin not in history:
        history[coin] = []

    timestamp = int(datetime.now(tz=timezone.utc).timestamp())

    # Add new entry
    history[coin].append({
        "timestamp": timestamp,
        "oi": oi,
        "price": price,
    })

    # Keep only last 24 hours of data
    cutoff = timestamp - (24 * 3600)
    history[coin] = [
        entry for entry in history[coin]
        if entry["timestamp"] > cutoff
    ]

    _save_oi_history(history)


def _get_oi_at_time(coin: str, hours_ago: int) -> Optional[tuple]:
    """Get OI and price from N hours ago.

    Args:
        coin: Trading pair
        hours_ago: Hours to look back

    Returns:
        Tuple of (oi, price) or None if not found
    """
    history = _load_oi_history()

    if coin not in history or not history[coin]:
        return None

    target_time = int(datetime.now(tz=timezone.utc).timestamp()) - (hours_ago * 3600)

    # Find closest entry to target time
    closest_entry = min(
        history[coin],
        key=lambda x: abs(x["timestamp"] - target_time),
        default=None
    )

    if closest_entry:
        # Only use if within reasonable range (±30 minutes)
        time_diff = abs(closest_entry["timestamp"] - target_time)
        if time_diff < 1800:  # 30 minutes
            return closest_entry["oi"], closest_entry["price"]

    return None


def _fetch_raw_oi(coin: str) -> Dict[str, Any]:
    """Fetch raw open interest data from Hyperliquid API.

    Args:
        coin: Trading pair symbol (e.g., "BTC")

    Returns:
        Raw API response with OI and price data

    Raises:
        requests.exceptions.RequestException: On network errors
        ValueError: On invalid API response
    """
    payload = {
        "type": "metaAndAssetCtxs"
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        # data is usually [meta, asset_ctxs]
        if not isinstance(data, list) or len(data) < 2:
            raise ValueError("Unexpected API response format")

        asset_ctxs = data[1]

        # Find the specific coin
        for ctx in asset_ctxs:
            if isinstance(ctx, dict):
                # Try multiple possible field names for coin identification
                coin_name = (ctx.get("coin") or ctx.get("symbol") or
                            ctx.get("name") or ctx.get("asset") or "")

                # Match coin (case-insensitive, handle different formats)
                if coin_name.upper() == coin.upper() or coin_name.upper() == f"{coin.upper()}-USD":
                    # Try multiple possible field names for OI
                    oi = (ctx.get("openInterest") or ctx.get("open_interest") or
                         ctx.get("oi") or ctx.get("openInt") or 0)

                    # Try multiple possible field names for price
                    price = (ctx.get("markPx") or ctx.get("midPx") or
                            ctx.get("mark_price") or ctx.get("price") or 0)

                    return {
                        "coin": coin,
                        "oi": float(oi),
                        "price": float(price),
                    }

        raise ValueError(f"Coin {coin} not found in API response")

    except requests.exceptions.Timeout:
        raise requests.exceptions.RequestException(f"API request timeout for {coin} OI")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"API request failed: {str(e)}")


def fetch_open_interest_metrics(
    coin: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Fetch and analyze open interest data from Hyperliquid.

    This tool fetches current open interest, tracks changes over time,
    and determines price-OI divergence scenarios.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        use_cache: Whether to use cached data (default: True)

    Returns:
        Dictionary with open interest metrics:
        {
            "coin": "BTC",
            "current_usd": 125000000.0,
            "current_price": 67890.0,
            "change_1h_pct": 2.3,
            "change_4h_pct": 5.7,
            "change_24h_pct": -3.2,
            "divergence_type": "strong_bullish",
            "price_change_4h_pct": 3.5,
            "cached": False
        }

    Example:
        >>> metrics = fetch_open_interest_metrics("BTC")
        >>> print(f"OI Change (4h): {metrics['change_4h_pct']:+.2f}%")
        >>> print(f"Divergence: {metrics['divergence_type']}")
    """
    # Check cache
    cache = get_cache()
    cache_key = f"oi:{coin}"

    if use_cache:
        cached_data = cache.get(cache_key, ttl=CACHE_TTL)
        if cached_data:
            cached_data["cached"] = True
            return cached_data

    try:
        # Fetch current OI and price
        raw_data = _fetch_raw_oi(coin)
        current_oi = raw_data["oi"]
        current_price = raw_data["price"]

        # Update history
        _update_oi_history(coin, current_oi, current_price)

        # Calculate OI changes
        oi_1h_ago = _get_oi_at_time(coin, 1)
        oi_4h_ago = _get_oi_at_time(coin, 4)
        oi_24h_ago = _get_oi_at_time(coin, 24)

        change_1h_pct = None
        change_4h_pct = None
        change_24h_pct = None
        price_change_4h_pct = None

        if oi_1h_ago:
            change_1h_pct = calculate_oi_change(current_oi, oi_1h_ago[0])

        if oi_4h_ago:
            change_4h_pct = calculate_oi_change(current_oi, oi_4h_ago[0])
            price_change_4h_pct = ((current_price - oi_4h_ago[1]) / oi_4h_ago[1]) * 100

        if oi_24h_ago:
            change_24h_pct = calculate_oi_change(current_oi, oi_24h_ago[0])

        # Determine divergence (use 4h window)
        divergence_type = "neutral"
        if change_4h_pct is not None and price_change_4h_pct is not None:
            divergence_type = determine_oi_divergence(price_change_4h_pct, change_4h_pct)

        # Build result
        result = {
            "coin": coin,
            "current_usd": round(current_oi, 2),
            "current_price": round(current_price, 2),
            "change_1h_pct": round(change_1h_pct, 2) if change_1h_pct is not None else None,
            "change_4h_pct": round(change_4h_pct, 2) if change_4h_pct is not None else None,
            "change_24h_pct": round(change_24h_pct, 2) if change_24h_pct is not None else None,
            "divergence_type": divergence_type,
            "price_change_4h_pct": round(price_change_4h_pct, 2) if price_change_4h_pct is not None else None,
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
def fetch_open_interest_metrics_tool(
    coin: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Fetch and analyze open interest data from Hyperliquid.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        use_cache: Whether to use cached data (default: True)

    Returns:
        Dictionary with open interest metrics
    """
    return fetch_open_interest_metrics(coin, use_cache)


def fetch_open_interest_metrics_typed(
    coin: str,
    use_cache: bool = True
) -> Optional[OpenInterestMetrics]:
    """Typed version that returns OpenInterestMetrics dataclass.

    Args:
        coin: Trading pair symbol
        use_cache: Whether to use cached data

    Returns:
        OpenInterestMetrics instance or None on error
    """
    result = fetch_open_interest_metrics(coin, use_cache)

    if "error" in result:
        return None

    return OpenInterestMetrics(
        current_usd=result["current_usd"],
        change_1h_pct=result.get("change_1h_pct") or 0.0,
        change_4h_pct=result.get("change_4h_pct") or 0.0,
        change_24h_pct=result.get("change_24h_pct") or 0.0,
        divergence_type=result["divergence_type"],
        price_change_4h_pct=result.get("price_change_4h_pct"),
    )


# Standalone testing
if __name__ == "__main__":
    import json
    import time

    print("Testing Open Interest Fetcher...")
    print("=" * 60)

    # Test with BTC
    print("\nFetching BTC open interest...")
    result = fetch_open_interest_metrics("BTC")

    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✓ Success!")
        print(json.dumps(result, indent=2))

        # Show interpretation
        print(f"\nInterpretation:")
        print(f"  Current OI: ${result['current_usd']:,.0f}")
        print(f"  Current Price: ${result['current_price']:,.2f}")
        if result['change_4h_pct'] is not None:
            print(f"  OI Change (4h): {result['change_4h_pct']:+.2f}%")
            print(f"  Price Change (4h): {result['price_change_4h_pct']:+.2f}%")
            print(f"  Divergence: {result['divergence_type']}")
        else:
            print(f"  (Not enough historical data for divergence analysis)")

    print("\n" + "=" * 60)
    print("Collecting OI data over time...")
    print("(Run this script multiple times over hours to see changes)")

    # Show what's in history
    history = _load_oi_history()
    if "BTC" in history:
        print(f"\nBTC OI History: {len(history['BTC'])} data points")
        if history['BTC']:
            oldest = history['BTC'][0]
            newest = history['BTC'][-1]
            age_hours = (newest['timestamp'] - oldest['timestamp']) / 3600
            print(f"  Oldest: {age_hours:.1f} hours ago")

    # Show cache stats
    cache = get_cache()
    stats = cache.get_stats()
    print(f"\nCache stats:")
    print(f"  Hit rate: {stats['hit_rate_pct']:.1f}%")
    print(f"  Entries: {stats['entries']}")

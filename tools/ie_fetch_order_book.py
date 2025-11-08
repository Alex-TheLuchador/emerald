"""
Order book data fetcher for Institutional Engine.

Fetches Level 2 order book data from Hyperliquid API and calculates
bid/ask imbalance metrics using IE calculation functions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import requests
from langchain.tools import tool

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ie.calculations import (
    calculate_order_book_imbalance,
    calculate_spread_bps,
)
from ie.data_models import OrderBookMetrics
from ie.cache import get_cache


# API Configuration
API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}
REQUEST_TIMEOUT = 15
CACHE_TTL = 2  # Cache for 2 seconds (order book changes rapidly)


def _fetch_raw_order_book(coin: str, depth: int = 20) -> Dict[str, Any]:
    """Fetch raw order book data from Hyperliquid API.

    Args:
        coin: Trading pair symbol (e.g., "BTC")
        depth: Number of price levels to fetch (default: 20)

    Returns:
        Raw API response

    Raises:
        requests.exceptions.RequestException: On network errors
        ValueError: On invalid API response
    """
    payload = {
        "type": "l2Book",
        "coin": coin,
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

        # Hyperliquid l2Book returns different formats, normalize it
        if isinstance(data, dict):
            # Already a dict, good
            return data
        elif isinstance(data, list):
            # List format - wrap it
            return {"raw_list": data}
        else:
            raise ValueError(f"Unexpected response type: {type(data)}")

    except requests.exceptions.Timeout:
        raise requests.exceptions.RequestException(f"API request timeout for {coin} order book")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"API request failed: {str(e)}")


def _parse_order_book_levels(
    data: Dict[str, Any],
    depth: int
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """Parse raw order book data into bid/ask lists.

    Args:
        data: Raw API response (can be dict or wrapped list)
        depth: Number of levels to parse

    Returns:
        Tuple of (bids, asks) where each is a list of (price, size) tuples

    Raises:
        ValueError: If data structure is invalid
    """
    # Try different possible response formats
    bids_raw = []
    asks_raw = []

    # Format 1: Direct dict with bids/asks
    if isinstance(data, dict) and "bids" in data and "asks" in data:
        bids_raw = data["bids"]
        asks_raw = data["asks"]
    # Format 2: Nested in levels array
    elif isinstance(data, dict) and "levels" in data and isinstance(data["levels"], list) and data["levels"]:
        first_level = data["levels"][0]
        if isinstance(first_level, dict):
            bids_raw = first_level.get("bids", [])
            asks_raw = first_level.get("asks", [])
    # Format 3: Wrapped list (from our normalization)
    elif isinstance(data, dict) and "raw_list" in data:
        # List format - might be [bids, asks] or something else
        raw_list = data["raw_list"]
        if isinstance(raw_list, list) and len(raw_list) >= 2:
            if isinstance(raw_list[0], list):
                bids_raw = raw_list[0]  # Assume first is bids
                asks_raw = raw_list[1]  # Assume second is asks
    # Format 4: Direct list [bids, asks]
    elif isinstance(data, list) and len(data) >= 2:
        if isinstance(data[0], list) and isinstance(data[1], list):
            bids_raw = data[0]  # First list is bids
            asks_raw = data[1]  # Second list is asks

    if not bids_raw or not asks_raw:
        raise ValueError("Order book data missing bids or asks")

    # Parse bid levels
    bids = []
    for level in bids_raw[:depth]:
        if isinstance(level, dict):
            price = float(level.get("px", level.get("price", 0)))
            size = float(level.get("sz", level.get("size", 0)))
        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            price = float(level[0])
            size = float(level[1])
        else:
            continue

        if price > 0 and size > 0:
            bids.append((price, size))

    # Parse ask levels
    asks = []
    for level in asks_raw[:depth]:
        if isinstance(level, dict):
            price = float(level.get("px", level.get("price", 0)))
            size = float(level.get("sz", level.get("size", 0)))
        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            price = float(level[0])
            size = float(level[1])
        else:
            continue

        if price > 0 and size > 0:
            asks.append((price, size))

    if not bids or not asks:
        raise ValueError("Failed to parse any valid bid/ask levels")

    return bids, asks


def fetch_order_book_metrics(
    coin: str,
    depth: int = 10,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Fetch and analyze order book data from Hyperliquid.

    This tool fetches the Level 2 order book, calculates bid/ask imbalance,
    and returns institutional-grade metrics.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        depth: Number of price levels to analyze (default: 10, max: 20)
        use_cache: Whether to use cached data (default: True)

    Returns:
        Dictionary with order book metrics:
        {
            "coin": "BTC",
            "imbalance": 0.45,
            "imbalance_strength": "strong_bid_pressure",
            "top_bid": 67890.0,
            "top_ask": 67891.0,
            "spread": 1.0,
            "spread_bps": 1.47,
            "total_bid_volume": 23.5,
            "total_ask_volume": 12.1,
            "depth_analyzed": 10,
            "cached": False
        }

    Example:
        >>> metrics = fetch_order_book_metrics("BTC", depth=10)
        >>> print(f"Imbalance: {metrics['imbalance']:.2f}")
        >>> print(f"Strength: {metrics['imbalance_strength']}")
    """
    # Validate inputs
    if depth < 1 or depth > 20:
        return {
            "error": "Depth must be between 1 and 20",
            "coin": coin,
        }

    # Check cache first
    cache = get_cache()
    cache_key = f"order_book:{coin}:{depth}"
    cached_data = None

    if use_cache:
        cached_data = cache.get(cache_key, ttl=CACHE_TTL)
        if cached_data:
            cached_data["cached"] = True
            return cached_data

    try:
        # Fetch raw order book
        raw_data = _fetch_raw_order_book(coin, depth)

        # Parse into bid/ask lists
        bids, asks = _parse_order_book_levels(raw_data, depth)

        # Calculate imbalance using IE calculation function
        imbalance, strength = calculate_order_book_imbalance(bids, asks, depth)

        # Get top of book
        top_bid = bids[0][0] if bids else 0.0
        top_ask = asks[0][0] if asks else 0.0
        spread = top_ask - top_bid
        mid_price = (top_bid + top_ask) / 2

        # Calculate spread in basis points
        spread_bps = calculate_spread_bps(top_bid, top_ask, mid_price)

        # Calculate total volumes
        total_bid_volume = sum(size for _, size in bids[:depth])
        total_ask_volume = sum(size for _, size in asks[:depth])

        # Build result
        result = {
            "coin": coin,
            "imbalance": round(imbalance, 4),
            "imbalance_strength": strength,
            "top_bid": top_bid,
            "top_ask": top_ask,
            "spread": round(spread, 2),
            "spread_bps": round(spread_bps, 2),
            "total_bid_volume": round(total_bid_volume, 2),
            "total_ask_volume": round(total_ask_volume, 2),
            "depth_analyzed": len(bids),
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
def fetch_order_book_metrics_tool(
    coin: str,
    depth: int = 10,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Fetch and analyze order book data from Hyperliquid.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        depth: Number of price levels to analyze (default: 10, max: 20)
        use_cache: Whether to use cached data (default: True)

    Returns:
        Dictionary with order book metrics
    """
    return fetch_order_book_metrics(coin, depth, use_cache)


def fetch_order_book_metrics_typed(
    coin: str,
    depth: int = 10,
    use_cache: bool = True
) -> Optional[OrderBookMetrics]:
    """Typed version that returns OrderBookMetrics dataclass.

    Args:
        coin: Trading pair symbol
        depth: Number of price levels to analyze
        use_cache: Whether to use cached data

    Returns:
        OrderBookMetrics instance or None on error
    """
    result = fetch_order_book_metrics(coin, depth, use_cache)

    if "error" in result:
        return None

    return OrderBookMetrics(
        imbalance=result["imbalance"],
        imbalance_strength=result["imbalance_strength"],
        top_bid=result["top_bid"],
        top_ask=result["top_ask"],
        spread=result["spread"],
        spread_bps=result["spread_bps"],
        total_bid_volume=result["total_bid_volume"],
        total_ask_volume=result["total_ask_volume"],
        depth_analyzed=result["depth_analyzed"],
    )


# Standalone testing
if __name__ == "__main__":
    import json

    print("Testing Order Book Fetcher...")
    print("=" * 60)

    # Test with BTC
    print("\nFetching BTC order book...")
    result = fetch_order_book_metrics("BTC", depth=10)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✓ Success!")
        print(json.dumps(result, indent=2))

        # Show interpretation
        print(f"\nInterpretation:")
        print(f"  Imbalance: {result['imbalance']:.4f} ({result['imbalance_strength']})")
        print(f"  Spread: ${result['spread']:.2f} ({result['spread_bps']:.2f} bps)")
        print(f"  Bid volume: {result['total_bid_volume']:.2f}")
        print(f"  Ask volume: {result['total_ask_volume']:.2f}")

    # Test caching
    print("\n" + "=" * 60)
    print("Testing cache...")
    import time
    start = time.time()
    result1 = fetch_order_book_metrics("BTC", depth=10, use_cache=True)
    time1 = time.time() - start

    start = time.time()
    result2 = fetch_order_book_metrics("BTC", depth=10, use_cache=True)
    time2 = time.time() - start

    print(f"First call: {time1*1000:.2f}ms (cached: {result1.get('cached', False)})")
    print(f"Second call: {time2*1000:.2f}ms (cached: {result2.get('cached', False)})")

    if result2.get('cached'):
        print(f"✓ Cache working! Speedup: {time1/time2:.1f}x faster")

    # Show cache stats
    cache = get_cache()
    stats = cache.get_stats()
    print(f"\nCache stats:")
    print(f"  Hit rate: {stats['hit_rate_pct']:.1f}%")
    print(f"  Entries: {stats['entries']}")

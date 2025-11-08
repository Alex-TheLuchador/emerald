"""
Perpetuals Basis Calculator for Institutional Engine.

Fetches spot reference price and perp price from Hyperliquid,
calculates basis spread, and determines arbitrage opportunities.

This is a critical institutional metric. When basis and funding
align, it confirms real institutional positioning vs noise.
"""

import requests
from typing import Dict, Any
from langchain.tools import tool

API_URL = "https://api.hyperliquid.xyz/info"
CACHE_TTL = 5  # 5 seconds - basis changes rapidly


def _fetch_spot_reference(coin: str) -> float:
    """
    Fetch spot reference price from Hyperliquid.

    Hyperliquid uses an index price (average of major exchanges)
    as the spot reference for perpetuals.

    Args:
        coin: Trading pair (e.g., "BTC")

    Returns:
        Spot index price
    """
    payload = {
        "type": "metaAndAssetCtxs"
    }

    response = requests.post(API_URL, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()

    # Find coin in universe
    meta = data[0]
    asset_ctxs = data[1]

    for i, coin_info in enumerate(meta["universe"]):
        if coin_info.get("name", "").upper() == coin.upper():
            ctx = asset_ctxs[i]
            # Index price is the spot reference (oraclePx)
            return float(ctx.get("oraclePx", ctx.get("markPx", 0)))

    raise ValueError(f"Coin {coin} not found")


def _fetch_perp_price(coin: str) -> float:
    """
    Fetch current perpetual mark price.

    Args:
        coin: Trading pair

    Returns:
        Perp mark price
    """
    payload = {
        "type": "metaAndAssetCtxs"
    }

    response = requests.post(API_URL, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()

    meta = data[0]
    asset_ctxs = data[1]

    for i, coin_info in enumerate(meta["universe"]):
        if coin_info.get("name", "").upper() == coin.upper():
            ctx = asset_ctxs[i]
            return float(ctx.get("markPx", 0))

    raise ValueError(f"Coin {coin} not found")


def calculate_basis_spread(spot_price: float, perp_price: float) -> Dict[str, Any]:
    """
    Calculate perpetuals basis spread and annualized rate.

    Basis = (Perp Price - Spot Price) / Spot Price

    Positive basis = perp trading at premium (bullish)
    Negative basis = perp trading at discount (bearish)

    Args:
        spot_price: Spot/index price
        perp_price: Perpetual contract price

    Returns:
        Basis metrics dictionary
    """
    if spot_price == 0:
        return {"error": "Invalid spot price"}

    # Calculate basis spread
    basis_pct = ((perp_price - spot_price) / spot_price) * 100

    # Classify basis strength
    if basis_pct > 0.5:
        strength = "extreme_premium"
    elif basis_pct > 0.2:
        strength = "moderate_premium"
    elif basis_pct < -0.5:
        strength = "extreme_discount"
    elif basis_pct < -0.2:
        strength = "moderate_discount"
    else:
        strength = "neutral"

    # Arbitrage opportunity flag
    # Institutions arb when basis > 0.3% (covers fees + slippage)
    arb_opportunity = abs(basis_pct) > 0.3

    return {
        "spot_price": round(spot_price, 2),
        "perp_price": round(perp_price, 2),
        "basis_pct": round(basis_pct, 4),
        "basis_strength": strength,
        "arb_opportunity": arb_opportunity,
    }


@tool
def fetch_perpetuals_basis_tool(coin: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Fetch perpetuals basis spread (spot-perp deviation).

    This is a critical institutional metric. When basis and funding
    align, it confirms real institutional positioning vs noise.

    Args:
        coin: Trading pair (e.g., "BTC", "ETH")
        use_cache: Use cached data

    Returns:
        Basis spread metrics
    """
    from ie.cache import get_cache

    cache = get_cache()
    cache_key = f"basis:{coin}"

    if use_cache:
        cached = cache.get(cache_key, ttl=CACHE_TTL)
        if cached:
            cached["cached"] = True
            return cached

    try:
        spot = _fetch_spot_reference(coin)
        perp = _fetch_perp_price(coin)

        result = calculate_basis_spread(spot, perp)
        result["coin"] = coin
        result["cached"] = False

        if use_cache:
            cache.set(cache_key, result)

        return result

    except Exception as e:
        return {
            "error": f"Failed to fetch basis: {str(e)}",
            "coin": coin
        }


def fetch_perpetuals_basis(coin: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Non-tool version for direct function calls.

    Args:
        coin: Trading pair
        use_cache: Use cached data

    Returns:
        Basis metrics
    """
    return fetch_perpetuals_basis_tool(coin, use_cache)

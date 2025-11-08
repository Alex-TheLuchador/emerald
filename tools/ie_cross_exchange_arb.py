"""
Cross-Exchange Arbitrage Monitor for Institutional Engine.

Compares Hyperliquid prices to major exchanges (Binance, OKX) to detect:
- Arbitrage opportunities (price discrepancies >0.1%)
- Institutional flow signals (HL cheaper = arb bots buying = bullish pressure incoming)
- Exchange-specific premium/discount patterns

When Hyperliquid is cheaper, arb bots buy on HL and sell elsewhere = bullish.
When Hyperliquid is more expensive, arb bots sell on HL = bearish.
"""

import requests
from typing import Dict, Any
from langchain.tools import tool

HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"
BINANCE_API = "https://api.binance.com/api/v3/ticker/price"
CACHE_TTL = 3  # 3 seconds


def _fetch_hyperliquid_price(coin: str) -> float:
    """
    Fetch current mark price from Hyperliquid.

    Args:
        coin: Trading pair (e.g., "BTC")

    Returns:
        Mark price
    """
    payload = {
        "type": "metaAndAssetCtxs"
    }

    response = requests.post(HYPERLIQUID_API, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()

    meta = data[0]
    asset_ctxs = data[1]

    for i, coin_info in enumerate(meta["universe"]):
        if coin_info.get("name", "").upper() == coin.upper():
            ctx = asset_ctxs[i]
            return float(ctx.get("markPx", 0))

    raise ValueError(f"Coin {coin} not found on Hyperliquid")


def _fetch_binance_price(coin: str) -> float:
    """
    Fetch current price from Binance perpetuals.

    Args:
        coin: Trading pair (e.g., "BTC")

    Returns:
        Price from Binance
    """
    # Map coin to Binance symbol
    symbol_map = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT",
        "AVAX": "AVAXUSDT",
        "MATIC": "MATICUSDT",
        "ARB": "ARBUSDT",
        "OP": "OPUSDT",
    }

    symbol = symbol_map.get(coin.upper())
    if not symbol:
        raise ValueError(f"Coin {coin} not supported for Binance comparison")

    response = requests.get(
        BINANCE_API,
        params={"symbol": symbol},
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    return float(data.get("price", 0))


def calculate_arbitrage_metrics(
    hl_price: float,
    binance_price: float,
    threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Calculate arbitrage metrics between exchanges.

    Args:
        hl_price: Hyperliquid price
        binance_price: Binance price
        threshold: Arbitrage opportunity threshold (%)

    Returns:
        Arbitrage analysis
    """
    if binance_price == 0:
        return {"error": "Invalid Binance price"}

    # Calculate deviation
    deviation_pct = ((hl_price - binance_price) / binance_price) * 100

    # Classify deviation
    if deviation_pct > threshold:
        status = "hl_premium"
        signal = "bearish"  # HL more expensive = arb bots sell on HL
        arb_opportunity = True
    elif deviation_pct < -threshold:
        status = "hl_discount"
        signal = "bullish"  # HL cheaper = arb bots buy on HL
        arb_opportunity = True
    else:
        status = "neutral"
        signal = "neutral"
        arb_opportunity = False

    # Calculate potential profit (minus fees)
    # Assume 0.05% fees on each side = 0.1% total
    gross_profit_pct = abs(deviation_pct)
    net_profit_pct = max(0, gross_profit_pct - 0.1)

    return {
        "hl_price": round(hl_price, 2),
        "binance_price": round(binance_price, 2),
        "deviation_pct": round(deviation_pct, 4),
        "status": status,
        "signal": signal,
        "arb_opportunity": arb_opportunity,
        "net_profit_pct": round(net_profit_pct, 4),
    }


def analyze_cross_exchange_arb(coin: str) -> Dict[str, Any]:
    """
    Comprehensive cross-exchange arbitrage analysis.

    Args:
        coin: Trading pair

    Returns:
        Arbitrage analysis with flow signals
    """
    try:
        hl_price = _fetch_hyperliquid_price(coin)
    except Exception as e:
        return {
            "error": f"Failed to fetch Hyperliquid price: {str(e)}",
            "coin": coin
        }

    try:
        binance_price = _fetch_binance_price(coin)
    except Exception as e:
        return {
            "error": f"Failed to fetch Binance price: {str(e)}",
            "coin": coin
        }

    metrics = calculate_arbitrage_metrics(hl_price, binance_price)
    metrics["coin"] = coin
    metrics["exchange_comparison"] = "Hyperliquid vs Binance"

    # Add interpretation
    if metrics["arb_opportunity"]:
        if metrics["signal"] == "bullish":
            metrics["interpretation"] = (
                f"HL is {abs(metrics['deviation_pct']):.2f}% cheaper than Binance. "
                "Arb bots likely buying on HL = bullish pressure incoming."
            )
        else:
            metrics["interpretation"] = (
                f"HL is {abs(metrics['deviation_pct']):.2f}% more expensive than Binance. "
                "Arb bots likely selling on HL = bearish pressure incoming."
            )
    else:
        metrics["interpretation"] = "Prices aligned across exchanges. No arbitrage signal."

    return metrics


@tool
def fetch_cross_exchange_arb_tool(coin: str) -> Dict[str, Any]:
    """
    Monitor cross-exchange arbitrage opportunities.

    Compares Hyperliquid vs Binance prices to detect:
    - Arbitrage opportunities (>0.1% deviation)
    - Flow signals:
      * HL cheaper = arb bots buy on HL = bullish
      * HL expensive = arb bots sell on HL = bearish

    Args:
        coin: Trading pair (e.g., "BTC", "ETH", "SOL")

    Returns:
        Arbitrage analysis with flow signals
    """
    return analyze_cross_exchange_arb(coin)


def fetch_cross_exchange_arb(coin: str) -> Dict[str, Any]:
    """
    Non-tool version for direct function calls.

    Args:
        coin: Trading pair

    Returns:
        Arbitrage analysis
    """
    return analyze_cross_exchange_arb(coin)

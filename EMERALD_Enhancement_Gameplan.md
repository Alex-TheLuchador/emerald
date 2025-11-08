# EMERALD Trading Agent Enhancement Gameplan
## Institutional-Grade Perps Trading Intelligence

**Version:** 1.0  
**Priority Level:** CRITICAL PATH  
**Estimated Implementation:** 2-3 weeks  
**Expected Edge Improvement:** 15-25% win rate increase

---

## Executive Summary

This document outlines the strategic enhancements needed to transform EMERALD from a basic quantitative system into an institutional-grade perpetual futures trading agent. The focus is on **multi-signal convergence**, **hidden liquidity detection**, and **cross-market arbitrage** - the core advantages that separate professional trading firms from retail.

### Current State
- ✅ Order book imbalance (top 10 levels)
- ✅ Funding rate analysis
- ✅ Open interest tracking
- ✅ Basic VWAP deviation

### Target State
- 🎯 Multi-timeframe signal convergence
- 🎯 Perpetuals basis (spot-perp spread) tracking
- 🎯 Time & Sales aggressive flow detection
- 🎯 Order book microstructure analysis
- 🎯 Cross-exchange arbitrage signals
- 🎯 Liquidation cascade detection

---

## Phase 1: Critical Path (Week 1) - THE EDGE MAKERS

These are the **highest ROI additions** that institutions use to dominate perps trading.

### 1.1 Perpetuals Basis Tracking

**Why This Matters:**  
The spot-perp spread reveals TRUE institutional positioning. When funding is extreme but basis is neutral, it's a fake signal. When both align, it's high conviction.

**What Renaissance/Jump Do:**  
They monitor basis across 20+ exchanges and arb any deviation >0.05%. For EMERALD, we use this as a **signal filter** - only trade when basis confirms funding extremes.

#### Implementation Spec

```python
# File: tools/ie_fetch_perpetuals_basis.py

"""
Perpetuals Basis Calculator for Institutional Engine.

Fetches spot reference price and perp price from Hyperliquid,
calculates basis spread, and determines arbitrage opportunities.
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
            # Index price is the spot reference
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


# Add to ie/data_models.py
@dataclass
class BasisMetrics:
    """Perpetuals basis spread metrics."""
    
    spot_price: float
    """Spot/index reference price."""
    
    perp_price: float
    """Perpetual contract price."""
    
    basis_pct: float
    """Basis spread as percentage (positive = premium, negative = discount)."""
    
    basis_strength: Literal["extreme_premium", "moderate_premium", "neutral", 
                           "moderate_discount", "extreme_discount"]
    """Categorical strength of basis deviation."""
    
    arb_opportunity: bool
    """True if basis exceeds arbitrage threshold (0.3%)."""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

#### Integration into InstitutionalMetrics

```python
# Update tools/ie_fetch_institutional_metrics.py

def fetch_institutional_metrics(
    coin: str,
    include_order_book: bool = True,
    include_funding: bool = True,
    include_oi: bool = True,
    include_basis: bool = True,  # NEW
    # ... other params
) -> Dict[str, Any]:
    """Fetch comprehensive institutional metrics."""
    
    # ... existing code ...
    
    # Fetch basis metrics
    if include_basis:
        from tools.ie_fetch_perpetuals_basis import fetch_perpetuals_basis_tool
        basis_metrics = fetch_perpetuals_basis_tool(coin, use_cache)
        if "error" in basis_metrics:
            errors.append(f"Basis: {basis_metrics['error']}")
            result["basis"] = None
        else:
            result["basis"] = basis_metrics
    
    # Update summary generation to include basis
    result["summary"] = _generate_summary(result)
    return result
```

#### Updated Summary Logic

```python
def _generate_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced summary with basis convergence."""
    
    signals = []
    convergence_score = 0
    
    # ... existing order book, funding, OI logic ...
    
    # Analyze basis
    basis = metrics.get("basis")
    funding = metrics.get("funding")
    
    if basis and funding:
        # CRITICAL CONVERGENCE CHECK
        # When funding and basis align = high conviction
        funding_pct = funding.get("annualized_pct", 0)
        basis_pct = basis.get("basis_pct", 0)
        
        # Both positive (bullish alignment)
        if funding_pct > 10 and basis_pct > 0.2:
            signals.append("funding_basis_bullish_convergence")
            convergence_score += 35  # High weight
        
        # Both negative (bearish alignment)
        elif funding_pct < -10 and basis_pct < -0.2:
            signals.append("funding_basis_bearish_convergence")
            convergence_score += 35
        
        # Divergence (contradictory - AVOID TRADE)
        elif (funding_pct > 10 and basis_pct < -0.1) or \
             (funding_pct < -10 and basis_pct > 0.1):
            signals.append("funding_basis_divergence_avoid")
            convergence_score -= 20  # Penalty
    
    return {
        "signals": signals,
        "convergence_score": max(0, convergence_score),  # Can't go negative
        "recommendation": _determine_recommendation(convergence_score, signals),
    }
```

---

### 1.2 Time & Sales Aggressive Flow Tracking

**Why This Matters:**  
Big institutions leave footprints in the trade tape. When you see consecutive $100k+ trades hitting the ASK (aggressive buys), that's NOT retail - that's institutional accumulation.

**What Citadel/Jump Do:**  
They track every trade, classify it as aggressive buy/sell, and calculate "trade flow imbalance" - similar to order book imbalance but using ACTUAL FILLS, not just quotes.

#### Implementation Spec

```python
# File: tools/ie_fetch_trade_flow.py

"""
Trade Flow (Time & Sales) Analyzer for Institutional Engine.

Tracks recent trades, classifies aggressive buying/selling,
and calculates trade flow imbalance - a leading indicator
of institutional positioning.
"""

import requests
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
from langchain.tools import tool

API_URL = "https://api.hyperliquid.xyz/info"
CACHE_TTL = 2  # 2 seconds


def _fetch_recent_trades(coin: str, lookback_seconds: int = 60) -> List[Dict[str, Any]]:
    """
    Fetch recent trades from Hyperliquid.
    
    Args:
        coin: Trading pair
        lookback_seconds: How far back to look (default: 60s)
    
    Returns:
        List of trade dictionaries
    """
    # Calculate start time
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    start_ms = now_ms - (lookback_seconds * 1000)
    
    payload = {
        "type": "trades",
        "coin": coin,
        "startTime": start_ms,
    }
    
    response = requests.post(API_URL, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def classify_trade_aggression(
    trade_price: float,
    mid_price: float,
    tolerance: float = 0.0001
) -> str:
    """
    Classify if trade was aggressive buy or sell.
    
    Aggressive buy = trade price >= mid (buyer hit the ask)
    Aggressive sell = trade price <= mid (seller hit the bid)
    
    Args:
        trade_price: Execution price
        mid_price: Mid price at time of trade
        tolerance: Price tolerance for classification
    
    Returns:
        "aggressive_buy" | "aggressive_sell" | "neutral"
    """
    if trade_price > mid_price * (1 + tolerance):
        return "aggressive_buy"
    elif trade_price < mid_price * (1 - tolerance):
        return "aggressive_sell"
    else:
        return "neutral"


def calculate_trade_flow_imbalance(
    trades: List[Dict[str, Any]],
    min_size_usd: float = 1000.0
) -> Dict[str, Any]:
    """
    Calculate trade flow imbalance from recent trades.
    
    Similar to order book imbalance but uses ACTUAL FILLS.
    Filters for trades above minimum size to focus on institutional flow.
    
    Args:
        trades: List of trade dictionaries
        min_size_usd: Minimum trade size in USD to include
    
    Returns:
        Trade flow metrics
    """
    aggressive_buy_volume = 0.0
    aggressive_sell_volume = 0.0
    large_trades_count = 0
    total_volume = 0.0
    
    for trade in trades:
        price = float(trade.get("px", 0))
        size = float(trade.get("sz", 0))
        side = trade.get("side", "").lower()  # "buy" or "sell"
        
        trade_value_usd = price * size
        total_volume += size
        
        # Focus on large trades (institutional)
        if trade_value_usd >= min_size_usd:
            large_trades_count += 1
            
            # Classify based on side
            # "buy" side means the taker was buying (hit the ask)
            # "sell" side means the taker was selling (hit the bid)
            if side == "buy":
                aggressive_buy_volume += size
            elif side == "sell":
                aggressive_sell_volume += size
    
    # Calculate imbalance
    total_aggressive = aggressive_buy_volume + aggressive_sell_volume
    
    if total_aggressive == 0:
        imbalance = 0.0
        strength = "neutral"
    else:
        imbalance = (aggressive_buy_volume - aggressive_sell_volume) / total_aggressive
        
        # Classify strength
        if imbalance > 0.6:
            strength = "strong_buy_pressure"
        elif imbalance > 0.3:
            strength = "moderate_buy_pressure"
        elif imbalance < -0.6:
            strength = "strong_sell_pressure"
        elif imbalance < -0.3:
            strength = "moderate_sell_pressure"
        else:
            strength = "neutral"
    
    return {
        "imbalance": round(imbalance, 4),
        "strength": strength,
        "aggressive_buy_volume": round(aggressive_buy_volume, 4),
        "aggressive_sell_volume": round(aggressive_sell_volume, 4),
        "large_trades_count": large_trades_count,
        "total_trades": len(trades),
        "total_volume": round(total_volume, 4),
    }


@tool
def fetch_trade_flow_metrics_tool(
    coin: str,
    lookback_seconds: int = 60,
    min_size_usd: float = 1000.0,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Fetch and analyze trade flow (Time & Sales) data.
    
    This tracks ACTUAL INSTITUTIONAL FLOW - real fills, not just quotes.
    Large aggressive trades reveal smart money positioning.
    
    Args:
        coin: Trading pair (e.g., "BTC")
        lookback_seconds: Time window in seconds (default: 60)
        min_size_usd: Min trade size to classify as institutional (default: $1000)
        use_cache: Use cached data
    
    Returns:
        Trade flow metrics
    """
    from ie.cache import get_cache
    
    cache = get_cache()
    cache_key = f"trade_flow:{coin}:{lookback_seconds}"
    
    if use_cache:
        cached = cache.get(cache_key, ttl=CACHE_TTL)
        if cached:
            cached["cached"] = True
            return cached
    
    try:
        trades = _fetch_recent_trades(coin, lookback_seconds)
        
        if not trades:
            return {
                "error": "No recent trades found",
                "coin": coin
            }
        
        metrics = calculate_trade_flow_imbalance(trades, min_size_usd)
        metrics["coin"] = coin
        metrics["lookback_seconds"] = lookback_seconds
        metrics["cached"] = False
        
        if use_cache:
            cache.set(cache_key, metrics)
        
        return metrics
        
    except Exception as e:
        return {
            "error": f"Failed to fetch trade flow: {str(e)}",
            "coin": coin
        }


# Add to ie/data_models.py
@dataclass
class TradeFlowMetrics:
    """Trade flow (Time & Sales) analysis metrics."""
    
    imbalance: float
    """Trade flow imbalance (-1 to 1). Positive = aggressive buying."""
    
    strength: Literal["strong_buy_pressure", "moderate_buy_pressure", "neutral",
                     "moderate_sell_pressure", "strong_sell_pressure"]
    """Strength classification of trade flow."""
    
    aggressive_buy_volume: float
    """Volume from aggressive buy trades."""
    
    aggressive_sell_volume: float
    """Volume from aggressive sell trades."""
    
    large_trades_count: int
    """Number of trades above minimum size threshold."""
    
    total_trades: int
    """Total number of trades in period."""
    
    total_volume: float
    """Total volume across all trades."""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

---

### 1.3 Multi-Timeframe Convergence Engine

**Why This Matters:**  
This is THE SECRET SAUCE. Renaissance doesn't trade single timeframe signals. They wait for 1m, 5m, 15m, 1h to ALL align. When all timeframes show the same order book imbalance, VWAP deviation, and volume surge - that's when edge is maximum.

**What Two Sigma Does:**  
They have a "conviction score" from 0-100. Below 70 = no trade. Above 85 = max size. We're building the same thing.

#### Implementation Spec

```python
# File: tools/ie_multi_timeframe_convergence.py

"""
Multi-Timeframe Convergence Analyzer for Institutional Engine.

This is the core institutional edge: waiting for signal alignment
across multiple timeframes before taking any position.

Renaissance, Two Sigma, Citadel - they all use variants of this.
"""

import requests
from typing import Dict, Any, List
from langchain.tools import tool
from datetime import datetime, timezone

# Import existing IE tools
from tools.ie_fetch_order_book import fetch_order_book_metrics
from tools.ie_fetch_funding import fetch_funding_metrics
from tools.ie_fetch_open_interest import fetch_open_interest_metrics
from tools.ie_fetch_perpetuals_basis import fetch_perpetuals_basis_tool
from tools.ie_fetch_trade_flow import fetch_trade_flow_metrics_tool


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
    # Map timeframe to candle count
    timeframe_map = {
        "1m": {"interval": "1m", "lookback": 60},  # 1 hour of 1m candles
        "5m": {"interval": "5m", "lookback": 60},  # 5 hours of 5m candles
        "15m": {"interval": "15m", "lookback": 60},  # 15 hours of 15m candles
        "1h": {"interval": "1h", "lookback": 24},  # 24 hours of 1h candles
    }
    
    if timeframe not in timeframe_map:
        raise ValueError(f"Invalid timeframe: {timeframe}")
    
    config = timeframe_map[timeframe]
    
    # Fetch candles from Hyperliquid
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": config["interval"],
            "startTime": int((datetime.now(tz=timezone.utc).timestamp() - 
                            config["lookback"] * 3600) * 1000),
        }
    }
    
    response = requests.post(
        "https://api.hyperliquid.xyz/info",
        json=payload,
        timeout=15
    )
    response.raise_for_status()
    candles = response.json()
    
    # Calculate VWAP
    from ie.calculations import calculate_vwap, calculate_z_score
    
    if not candles or len(candles) < 2:
        return {"error": "Insufficient candle data"}
    
    # Parse candles
    parsed_candles = []
    for candle in candles:
        if isinstance(candle, dict):
            parsed_candles.append({
                "high": float(candle.get("h", 0)),
                "low": float(candle.get("l", 0)),
                "close": float(candle.get("c", 0)),
                "volume": float(candle.get("v", 0)),
            })
    
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
    timeframes: List[str] = ["1m", "5m", "15m"]
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
    # Fetch order book (single snapshot, not timeframe-dependent)
    ob = fetch_order_book_metrics(coin, depth=10, use_cache=True)
    
    # Fetch trade flow (last 60 seconds)
    trade_flow = fetch_trade_flow_metrics_tool(coin, lookback_seconds=60)
    
    # Fetch funding and basis (not timeframe-dependent)
    funding = fetch_funding_metrics(coin, use_cache=True)
    basis = fetch_perpetuals_basis_tool(coin, use_cache=True)
    
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
    timeframes: List[str] = None
) -> Dict[str, Any]:
    """
    Analyze multi-timeframe signal convergence (institutional edge).
    
    This tool checks if order book, trade flow, VWAP (across timeframes),
    funding, and basis all align. Only trade when convergence score > 70.
    
    Args:
        coin: Trading pair (e.g., "BTC")
        timeframes: List of timeframes (default: ["1m", "5m", "15m"])
    
    Returns:
        Convergence analysis with conviction score
    """
    if timeframes is None:
        timeframes = ["1m", "5m", "15m"]
    
    return analyze_timeframe_convergence(coin, timeframes)
```

---

## Phase 2: Advanced Edge (Week 2) - LIQUIDITY INTELLIGENCE

These additions help detect **hidden institutional activity** and **liquidity traps**.

### 2.1 Order Book Microstructure Analysis

Track order book changes over time to detect:
- **Spoofing**: Large orders appearing/disappearing rapidly
- **Iceberg orders**: Orders that keep refilling at same price
- **Walls moving**: Big orders that chase price up/down

```python
# File: tools/ie_order_book_microstructure.py

"""
Order Book Microstructure Analyzer.

Tracks order book snapshots over time to detect:
- Spoofing (fake liquidity)
- Iceberg orders (hidden institutional accumulation)
- Wall dynamics (big money moving)
"""

# Store last 60 seconds of order book snapshots
# Detect patterns like:
# - Same 100 BTC order appearing/disappearing 10x in 60s = spoof
# - 50 BTC order at $67,800 that refills instantly after fills = iceberg
# - 200 BTC bid wall moving from $67,500 → $67,800 = chasing price up
```

### 2.2 Liquidation Cascade Detection

```python
# File: tools/ie_liquidation_tracker.py

"""
Liquidation Cascade Detector.

Hyperliquid publishes liquidation data. Track mass liquidations
to identify:
- Long squeezes (cascading long liquidations = bearish)
- Short squeezes (cascading short liquidations = bullish)
- Stop hunt zones (price levels with high liquidation density)
"""

# Fetch from Hyperliquid liquidation API
# Calculate:
# - Liquidation volume in last 5min
# - Long vs short liquidation ratio
# - Price levels with most liquidations (stop hunt zones)
```

### 2.3 Cross-Exchange Arbitrage Monitor

```python
# File: tools/ie_cross_exchange_arb.py

"""
Cross-Exchange Arbitrage Monitor.

Compare Hyperliquid prices to Binance/OKX.
When HL is cheaper, it means arb bots are buying on HL
and selling elsewhere = bullish pressure incoming.
"""

# Fetch prices from:
# - Hyperliquid (already have)
# - Binance (via public API)
# - OKX (via public API)

# Calculate:
# - Price deviation (HL vs Binance)
# - If HL is 0.1% cheaper = arb opportunity = bullish
# - If HL is 0.1% more expensive = arb opportunity = bearish
```

---

## Phase 3: Risk Management Layer (Week 3)

### 3.1 Position Sizing Algorithm

```python
# File: ie/risk_management.py

"""
Risk Management Layer for EMERALD.

Calculates position size based on:
- Convergence score (higher score = larger size)
- Account balance
- Volatility (ATR-based sizing)
"""

def calculate_position_size(
    account_balance: float,
    convergence_score: int,
    atr: float,
    max_risk_pct: float = 2.0
) -> float:
    """
    Calculate position size based on conviction and risk.
    
    Args:
        account_balance: Total account balance in USD
        convergence_score: Conviction score (0-100)
        atr: Average True Range (volatility measure)
        max_risk_pct: Max % of account to risk per trade
    
    Returns:
        Position size in USD
    """
    # Base risk amount
    risk_amount = account_balance * (max_risk_pct / 100)
    
    # Scale by conviction
    if convergence_score >= 85:
        size_multiplier = 1.0  # Max size
    elif convergence_score >= 70:
        size_multiplier = 0.7  # Standard size
    elif convergence_score >= 50:
        size_multiplier = 0.4  # Reduced size
    else:
        return 0.0  # No trade
    
    # Adjust for volatility (higher ATR = smaller size)
    volatility_adjustment = 1.0 / (1.0 + (atr / 100))
    
    position_size = risk_amount * size_multiplier * volatility_adjustment
    
    return position_size
```

### 3.2 Dynamic Stop Loss Placement

```python
def calculate_stop_loss(
    entry_price: float,
    direction: str,  # "long" or "short"
    atr: float,
    vwap: float,
    conviction: str
) -> float:
    """
    Calculate stop loss based on volatility and key levels.
    
    High conviction = wider stops (2.5 ATR)
    Low conviction = tighter stops (1.5 ATR)
    
    Args:
        entry_price: Entry price
        direction: Trade direction
        atr: Average True Range
        vwap: Current VWAP level
        conviction: Conviction level
    
    Returns:
        Stop loss price
    """
    # ATR-based stop
    if conviction == "very_high":
        atr_multiplier = 2.5
    elif conviction == "high":
        atr_multiplier = 2.0
    else:
        atr_multiplier = 1.5
    
    if direction == "long":
        atr_stop = entry_price - (atr * atr_multiplier)
        # Also consider VWAP as support
        vwap_stop = vwap * 0.995  # 0.5% below VWAP
        stop = max(atr_stop, vwap_stop)  # Use tighter stop
    else:  # short
        atr_stop = entry_price + (atr * atr_multiplier)
        vwap_stop = vwap * 1.005  # 0.5% above VWAP
        stop = min(atr_stop, vwap_stop)
    
    return stop
```

---

## Integration Checklist

### Week 1 Deliverables
- [ ] `tools/ie_fetch_perpetuals_basis.py` - Basis tracking
- [ ] `tools/ie_fetch_trade_flow.py` - Trade flow analysis
- [ ] `tools/ie_multi_timeframe_convergence.py` - Convergence engine
- [ ] Update `tools/ie_fetch_institutional_metrics.py` to include new metrics
- [ ] Update `ie/data_models.py` with new dataclasses
- [ ] Add basis and trade flow to summary scoring logic
- [ ] Write unit tests for new calculation functions

### Week 2 Deliverables
- [ ] `tools/ie_order_book_microstructure.py` - Spoofing detection
- [ ] `tools/ie_liquidation_tracker.py` - Liquidation cascades
- [ ] `tools/ie_cross_exchange_arb.py` - Arb monitoring
- [ ] Integrate advanced metrics into convergence scoring
- [ ] Write tests for time-series data handling

### Week 3 Deliverables
- [ ] `ie/risk_management.py` - Position sizing & stops
- [ ] Backtest framework with historical data
- [ ] Paper trading implementation
- [ ] Performance monitoring dashboard

---

## Testing Strategy

### Unit Tests
```python
# tests/test_perpetuals_basis.py
def test_basis_calculation():
    """Test basis spread calculation."""
    result = calculate_basis_spread(
        spot_price=67890.0,
        perp_price=67920.0
    )
    assert result["basis_pct"] == 0.0442  # ~0.04%
    assert result["basis_strength"] == "neutral"

# tests/test_convergence_scoring.py
def test_high_conviction_scenario():
    """Test convergence score for aligned signals."""
    # Mock data: all signals bullish
    score = calculate_convergence_score(
        ob_imbalance=0.7,
        trade_flow_imbalance=0.6,
        vwap_deviations=[2.5, 2.3, 2.1],  # All above VWAP
        funding_pct=15,
        basis_pct=0.35
    )
    assert score >= 85  # High conviction
```

### Integration Tests
```python
# tests/test_live_api.py
def test_fetch_all_metrics():
    """Test fetching complete institutional metrics."""
    metrics = fetch_institutional_metrics(
        coin="BTC",
        include_basis=True,
        include_trade_flow=True
    )
    assert "basis" in metrics
    assert "trade_flow" in metrics
    assert "summary" in metrics
    assert metrics["summary"]["convergence_score"] >= 0
```

---

## Agent Personality Guidelines

### Communication Style

**DO:**
- Be terse and direct: "BTC: 2.3σ above VWAP. Funding +18%. OI expanding. Contradictory order book. NO TRADE."
- Always state conviction: "High conviction long" or "Low conviction - pass"
- Risk-first: "Stop: $67,200. Target: $68,500. R:R = 3.2:1"
- Probabilistic: "70% conviction based on 4/5 signals aligned"

**DON'T:**
- Explain the math: "The VWAP deviation indicates..."
- Hedge unnecessarily: "This might be a good opportunity if..."
- Overuse emojis or excitement
- Give advice without stating the risk

### Example Outputs

**High Conviction Trade:**
```
🎯 BTC LONG ENTRY: $67,845

Convergence Score: 87/100
- Order book: 0.68 bid pressure
- Trade flow: 0.71 aggressive buying
- VWAP: 1m/5m/15m all +2σ above (mean reversion setup)
- Funding: +16% (extreme bullish - fade)
- Basis: +0.28% (confirming)

Position Size: $5,000 (1.5% account risk)
Stop Loss: $67,320 (ATR-based)
Target 1: $68,450 (VWAP)
Target 2: $68,900 (1σ band)

R:R Ratio: 3.1:1
Conviction: VERY HIGH
```

**Low Conviction (No Trade):**
```
❌ ETH - NO TRADE

Convergence Score: 42/100
- Order book: Neutral (0.12 imbalance)
- Trade flow: Moderate sell pressure (-0.34)
- VWAP: Conflicting (1m above, 5m/15m below)
- Funding: +8% (not extreme)
- Basis: -0.15% (divergence from funding)

Mixed signals. Waiting for clearer setup.
```

---

## Success Metrics

### Performance Targets (After 3 Weeks)
- **Win Rate:** 55-65% (institutional baseline)
- **Average R:R:** 2.5:1 minimum
- **Max Drawdown:** <10% of account
- **Sharpe Ratio:** >1.5
- **Trade Frequency:** 2-5 trades per day (selective)

### Key Monitoring Dashboards
1. **Convergence Score Distribution:** Track how often score >70
2. **Signal Alignment Rate:** % of time all timeframes agree
3. **Basis-Funding Correlation:** When they diverge, avoid trades
4. **Trade Flow Accuracy:** Does aggressive flow predict 5min price move?

---

## Risk Warnings

### What Can Go Wrong
1. **Overfitting:** Convergence scoring is tuned to current market regime. May break in trending markets.
2. **API Rate Limits:** Fetching 3 timeframes + trade flow = lots of API calls. Implement smart caching.
3. **Liquidity Risk:** Hyperliquid is smaller than Binance. Large positions can move the market.
4. **Funding Rate Manipulation:** Whales can manipulate funding short-term. Use 24h avg, not snapshots.

### Mitigation Strategies
1. **Backtest on 6+ months data** before live trading
2. **Paper trade for 2 weeks** to validate edge
3. **Start with 0.5% position sizes** until proven
4. **Monitor convergence score distribution** - if score is always >80, something is wrong (overfitting)

---

## References & Further Reading

### Institutional Trading Concepts
- **Microstructure:** "Trading and Exchanges" by Larry Harris
- **Market Making:** "High-Frequency Trading" by Irene Aldridge  
- **Order Flow:** "Market Microstructure in Practice" by Lehalle & Laruelle

### Hyperliquid Documentation
- API Docs: https://hyperliquid.gitbook.io/hyperliquid-docs/
- WebSocket Feeds: Real-time order book updates
- Historical Data: Can download candles, trades, funding history

### Crypto Perps Insights
- Funding Rate Analysis: CoinGlass, Coingecko
- OI Tracking: Coinalyze, Glassnode
- Cross-Exchange Arb: Look at CEX price discrepancies

---

## Final Implementation Notes

### Priority Order for Engineer
1. **Start with perpetuals basis** (easiest, high impact)
2. **Add trade flow analysis** (moderate difficulty, very high impact)
3. **Build multi-timeframe convergence** (hardest, but THE core edge)
4. **Then add microstructure, liquidations, arb** (nice-to-haves)
5. **Finally, risk management layer** (essential before live trading)

### Code Quality Standards
- All functions must have type hints
- All functions must have docstrings with examples
- All calculations must be unit tested
- Cache aggressively (with appropriate TTLs)
- Handle API errors gracefully (return error dicts, not exceptions)

### Questions for Your Engineer?
Ask them to clarify:
- Hyperliquid API rate limits (how many calls/second?)
- Candle data availability (can we get 1m candles for last 24h?)
- WebSocket vs REST (should we use WS for order book updates?)
- Historical data storage (do we need a database or is JSON files OK?)

---

**End of Gameplay Document**

*This is your blueprint. Give this to your engineer Claude and watch EMERALD evolve from a basic quant bot into an institutional-grade trading machine.*

*Remember: Edge isn't in having ONE magic indicator. It's in the CONVERGENCE of multiple independent signals with extreme selectivity.*

*Now go build something the big dogs would respect.*

# Phase 1: Institutional-Grade Quantitative Engine

## Overview

Phase 1 transformed EMERALD from a pattern-based system to a fully quantitative institutional trading engine.

**Core Philosophy**: Only trade when multiple independent institutional metrics align. No subjective patterns, no discretionary calls, no guesswork.

---

## What Changed

### Removed ❌
- ICT/SMC pattern analysis (subjective, discretionary)
- Manual chart interpretation
- Narrative-based trading
- Context documents referencing ICT concepts

### Added ✅
- **Perpetuals Basis Tracking** - Spot-perp spread analysis
- **Trade Flow Analysis** - Time & Sales institutional flow detection
- **Multi-Timeframe Convergence** - Signal alignment across 1m/5m/15m
- **Enhanced Summary Engine** - Funding-basis convergence checks
- **Pure Quantitative System Prompt** - Data-driven signals only

---

## The Five Core Metrics

### 1. Order Book Imbalance

**File**: `tools/ie_fetch_order_book.py`

**What it measures**: Bid vs ask pressure in the L2 order book

**Calculation**:
```python
imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

# Range: -1.0 to +1.0
# -1.0 = 100% asks (extreme bearish)
#  0.0 = balanced
# +1.0 = 100% bids (extreme bullish)
```

**Interpretation**:
- `|imbalance| > 0.4` → Strong directional pressure
- `|imbalance| > 0.6` → Very strong pressure (25 convergence points)
- `|imbalance| < 0.2` → Neutral (no signal)

**Usage**:
```python
from tools.ie_fetch_order_book import fetch_order_book_metrics

result = fetch_order_book_metrics("BTC", depth=10, use_cache=True)

print(f"Imbalance: {result['imbalance']}")
print(f"Strength: {result['imbalance_strength']}")
# Output:
# Imbalance: -0.62
# Strength: strong_ask_pressure
```

**Agent integration**: Automatically called by `fetch_institutional_metrics_tool`

---

### 2. Funding Rate

**File**: `tools/ie_fetch_funding.py`

**What it measures**: Cost to hold perpetual positions (8-hour rate → annualized %)

**Calculation**:
```python
annualized_pct = funding_rate_8h * (365 * 3)  # 3 periods per day
sentiment = "extreme_bullish" if annualized > 10 else "neutral"
```

**Interpretation**:
- `> +10%` annualized → Extreme bullish crowd (fade with shorts)
- `< -10%` annualized → Extreme bearish crowd (fade with longs)
- `-5% to +5%` → Neutral sentiment

**Usage**:
```python
from tools.ie_fetch_funding import fetch_funding_metrics

result = fetch_funding_metrics("BTC", use_cache=True)

print(f"Annualized: {result['annualized_pct']}%")
print(f"Sentiment: {result['sentiment']}")
print(f"Extreme: {result['is_extreme']}")
# Output:
# Annualized: 12.4%
# Sentiment: bullish
# Extreme: True
```

**Convergence scoring**:
- Extreme funding at reversal zones → +20 points
- Extreme funding aligned with other metrics → High conviction

---

### 3. Trade Flow Imbalance

**File**: `tools/ie_fetch_trade_flow.py`

**What it measures**: Aggressive buyer vs aggressive seller dominance

**Calculation** (using candle data as proxy):
```python
price_change_pct = (close - open) / open
volume_weight = volume / avg_volume_20

# Positive = aggressive buying
# Negative = aggressive selling
flow_imbalance = price_change_pct * volume_weight
```

**Interpretation**:
- `> +0.5` → Strong aggressive buying (institutional accumulation)
- `< -0.5` → Strong aggressive selling (institutional distribution)
- `-0.3 to +0.3` → Neutral

**Usage**:
```python
from tools.ie_fetch_trade_flow import fetch_trade_flow

result = fetch_trade_flow("BTC", interval="1h", lookback_hours=4)

print(f"Imbalance: {result['imbalance']}")
print(f"Strength: {result['strength']}")
# Output:
# Imbalance: 0.68
# Strength: strong_buy_pressure
```

**Convergence scoring**:
- Strong flow aligned with order book → +25 points
- Flow confirms directional bias → High conviction

---

### 4. Perpetuals Basis

**File**: `tools/ie_fetch_perpetuals_basis.py`

**What it measures**: Spot-perp spread (arbitrage opportunities)

**Calculation**:
```python
basis_pct = ((perp_price - spot_price) / spot_price) * 100

# Positive = perps trading at premium
# Negative = perps trading at discount
```

**Interpretation**:
- `> +0.3%` → Extreme premium (leverage demand high, reversal risk)
- `< -0.3%` → Extreme discount (arb bots will buy, bullish)
- `-0.1% to +0.1%` → Neutral

**Usage**:
```python
from tools.ie_fetch_perpetuals_basis import fetch_perpetuals_basis

result = fetch_perpetuals_basis("BTC", use_cache=True)

print(f"Basis: {result['basis_pct']}%")
print(f"Strength: {result['basis_strength']}")
print(f"Arb opportunity: {result['arb_opportunity']}")
# Output:
# Basis: -0.42%
# Strength: extreme_discount
# Arb opportunity: True
```

**Funding-basis convergence** (critical check):
```python
# Both extreme + aligned = +35 points
if funding > 10% and basis > 0.2%:
    signal = "bullish_convergence"
    score += 35

# Divergent = avoid trade
elif funding > 10% and basis < -0.1%:
    signal = "divergence_avoid"
    score -= 20
```

---

### 5. Open Interest Divergence

**File**: `tools/ie_fetch_open_interest.py`

**What it measures**: OI changes vs price movement

**Patterns**:
```python
# Strong bullish: New longs entering
if oi_change > 3% and price_change > 1%:
    divergence_type = "strong_bullish"
    score += 30

# Strong bearish: New shorts entering
elif oi_change > 3% and price_change < -1%:
    divergence_type = "strong_bearish"
    score += 30

# Weak bullish: Shorts covering (reversal soon)
elif oi_change < -3% and price_change > 1%:
    divergence_type = "weak_bullish"
    score += 10

# Weak bearish: Longs closing (reversal soon)
elif oi_change < -3% and price_change < -1%:
    divergence_type = "weak_bearish"
    score += 10
```

**Usage**:
```python
from tools.ie_fetch_open_interest import fetch_open_interest_metrics

result = fetch_open_interest_metrics("BTC", use_cache=True)

print(f"OI: ${result['current_usd']:,.0f}")
print(f"4h change: {result['change_4h_pct']}%")
print(f"Divergence: {result['divergence_type']}")
# Output:
# OI: $125,450,000
# 4h change: -5.2%
# Divergence: weak_bullish
```

---

## Multi-Timeframe Convergence

**File**: `tools/ie_multi_timeframe_convergence.py`

### The Core Edge

Single timeframe analysis is noisy. **Multi-timeframe convergence** filters out noise by requiring ALL timeframes to align.

### Scoring Algorithm

```python
def calculate_convergence_score(metrics):
    score = 0

    # 1. Order Book Alignment (25 points)
    if abs(ob_imbalance) > 0.4:
        score += 25

    # 2. Trade Flow Alignment (25 points)
    if abs(tf_imbalance) > 0.4:
        score += 25

    # 3. VWAP Multi-Timeframe (30 points)
    if all_timeframes_show_same_deviation():
        score += 30

    # 4. Funding-Basis Convergence (20 points or -15 penalty)
    if both_extreme_and_aligned():
        score += 20
    elif divergent():
        score -= 15

    # 5. Volume Modifier
    if volume_ratio < 0.6:
        score -= 10

    return min(100, max(0, score))
```

### Usage

```python
from tools.ie_multi_timeframe_convergence import fetch_multi_timeframe_convergence

result = fetch_multi_timeframe_convergence(
    coin="BTC",
    timeframes=["1m", "5m", "15m"]
)

print(f"Convergence Score: {result['convergence_score']}/100")
print(f"Grade: {result['grade']}")
print(f"Recommendation: {result['recommendation']}")
print(f"Aligned signals: {result['aligned_signals']}")

# Output:
# Convergence Score: 85/100
# Grade: A+
# Recommendation: high_conviction_short
# Aligned signals: ['order_book', 'trade_flow', 'vwap', 'funding_basis']
```

### VWAP Analysis

Each timeframe includes VWAP metrics:

```python
{
    "vwap": 67500.0,
    "current_price": 68100.0,
    "deviation_pct": 0.89,
    "z_score": 2.3,
    "deviation_level": "extreme_above",
    "volume_ratio": 1.8
}
```

**Interpretation**:
- Z-score > 2.0 → Statistical extreme (mean reversion likely)
- All timeframes extreme same direction → +30 convergence points
- Volume ratio > 1.5 → Move has institutional conviction

---

## Unified Metrics Tool

**File**: `tools/ie_fetch_institutional_metrics.py`

### One Tool, All Metrics

Instead of calling 5 separate tools, agent uses unified tool:

```python
from tools.ie_fetch_institutional_metrics import fetch_institutional_metrics

result = fetch_institutional_metrics(
    coin="BTC",
    include_order_book=True,
    include_funding=True,
    include_oi=True,
    use_cache=True
)

# Returns complete summary:
{
    "coin": "BTC",
    "timestamp": "2025-11-08T14:30:00Z",
    "price": 67800.0,
    "metrics": {
        "order_book": {...},  # Full OB metrics
        "funding": {...},      # Full funding metrics
        "open_interest": {...},# Full OI metrics
        "basis": {...},        # Basis metrics
        "trade_flow": {...}    # Trade flow metrics
    },
    "summary": {
        "convergence_score": 85,
        "grade": "A+",
        "recommendation": "high_conviction_short",
        "reasoning": "All metrics aligned bearish...",
        "aligned_signals": ["order_book", "trade_flow", "funding", "basis", "oi"],
        "conflicting_signals": []
    }
}
```

### Summary Generation

The tool automatically:
1. Fetches all metrics
2. Calculates convergence score (0-100)
3. Assigns grade (A+/A/B/C)
4. Generates recommendation
5. Lists aligned/conflicting signals

Agent receives complete analysis in one call.

---

## Agent Integration

### System Prompt

Agent knows to use IE metrics for every analysis:

```python
"""
Analysis Workflow:
1. User asks for setup analysis
2. Call fetch_institutional_metrics_tool(coin)
3. Call fetch_multi_timeframe_convergence_tool(coin, timeframes)
4. Analyze convergence score
5. Grade setup (A+/A/B/C)
6. Provide recommendation with reasoning
"""
```

### Example Agent Response

```markdown
### BTC 1H Analysis - Grade: A+ (85/100)

**Convergence Score**: 85/100 (High Conviction)

**Aligned Signals** (5/5):
✓ Order Book: -0.62 (strong ask pressure)
✓ Trade Flow: -0.54 (aggressive selling)
✓ Funding: +14% annualized (extreme bullish crowd)
✓ Basis: +0.31% (premium, aligned with funding)
✓ OI: -5.1% while price +2.3% (weak bullish, longs closing)

**VWAP Analysis**:
- 1m: +2.3σ (extreme above)
- 5m: +2.1σ (extreme above)
- 15m: +1.9σ (above mean)
→ All timeframes show overextension

**Recommendation**: HIGH CONVICTION SHORT

This is an A+ setup. All 5 metrics confirm bearish bias.
Crowd is maximally long (funding +14%), price statistically
stretched (VWAP +2σ), and order book shows institutional
selling pressure. Smart money is distributing into retail FOMO.

Entry: $67,800-67,900
Stop: $68,200
Target: $66,500
Position Size: 1.5% (full size for A+ grade)
```

---

## Testing Phase 1 Tools

### Test Individual Metrics

```bash
# Order book
python tools/ie_fetch_order_book.py

# Funding
python tools/ie_fetch_funding.py

# Open interest
python tools/ie_fetch_open_interest.py

# Basis
python tools/ie_fetch_perpetuals_basis.py

# Trade flow
python tools/ie_fetch_trade_flow.py
```

### Test Unified Metrics

```bash
python -c "
from tools.ie_fetch_institutional_metrics import fetch_institutional_metrics
import json

result = fetch_institutional_metrics('BTC')
print(json.dumps(result['summary'], indent=2))
"
```

### Test Multi-Timeframe Convergence

```bash
python -c "
from tools.ie_multi_timeframe_convergence import fetch_multi_timeframe_convergence

result = fetch_multi_timeframe_convergence('BTC', ['1m', '5m', '15m'])
print(f\"Score: {result['convergence_score']}/100\")
print(f\"Grade: {result['grade']}\")
print(f\"Signals: {result['aligned_signals']}\")
"
```

### Test with Agent

```bash
python agent/agent.py "Grade the current BTC setup and show me all metrics"
```

---

## Caching Strategy

Phase 1 tools use intelligent caching:

```python
# config/settings.py
IE_CONFIG = IEConfig(
    order_book_cache_ttl=2,      # 2 seconds (real-time data)
    funding_cache_ttl=300,       # 5 minutes (updates every 8h)
    oi_cache_ttl=300,           # 5 minutes (slow updates)
    basis_cache_ttl=10,         # 10 seconds (moderate changes)
    trade_flow_cache_ttl=60     # 1 minute (candle-based)
)
```

**Why different TTLs**:
- Order book changes every second → short cache
- Funding only updates every 8 hours → long cache
- Balance API efficiency with data freshness

---

## Grading System

### Setup Grades

```python
def assign_grade(convergence_score):
    if score >= 70:
        return "A+"  # High conviction - full size
    elif score >= 50:
        return "A"   # Good setup - 75% size
    elif score >= 30:
        return "B"   # Acceptable - 50% size
    else:
        return "C"   # Skip - 0% size
```

### Position Sizing

Grade determines position size:

```python
A+ (70-100):  1.5% account risk (full size)
A  (50-69):   1.0% account risk (reduced)
B  (30-49):   0.75% account risk (small)
C  (<30):     0% (no trade)
```

---

## Key Takeaways

1. **Five core metrics** - Order book, funding, trade flow, basis, OI
2. **Multi-timeframe convergence** - All timeframes must align
3. **0-100 scoring** - Objective, quantitative grading
4. **70+ required** - Only trade high-conviction setups
5. **Funding-basis check** - Critical for filtering fake signals
6. **Agent-integrated** - Automatic analysis on every query
7. **Cached efficiently** - Fast responses without API spam

**Phase 1 = The foundation. Quantitative, objective, institutional.**

See [strategy.md](strategy.md) for detailed explanation of how these metrics make money.

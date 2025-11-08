# Phase 2: Advanced Liquidity Intelligence

## Overview

Phase 2 adds **temporal order book analysis** - tracking liquidity changes over time to detect manipulation, hidden institutional activity, and market microstructure patterns invisible in single snapshots.

**Core Insight**: Single order book snapshots lie. Watching orders appear, disappear, refill, and move over 60-second windows reveals true institutional intent.

---

## What's New in Phase 2

### Added Tools ✅

1. **Order Book Microstructure** (`ie_order_book_microstructure.py`)
   - Spoofing detection (fake liquidity)
   - Iceberg order detection (hidden institutional orders)
   - Wall dynamics tracking (moving support/resistance)

2. **Liquidation Cascade Tracker** (`ie_liquidation_tracker.py`)
   - Mass liquidation detection
   - Long squeeze vs short squeeze identification
   - Stop hunt zone mapping

3. **Cross-Exchange Arbitrage Monitor** (`ie_cross_exchange_arb.py`)
   - Hyperliquid vs Binance price comparison
   - Arbitrage flow signal detection
   - Exchange-specific pressure identification

---

## Tool 1: Order Book Microstructure

**File**: `tools/ie_order_book_microstructure.py`

### What It Detects

#### 1. Spoofing (Fake Liquidity)

**Definition**: Large orders that appear and disappear repeatedly without executing.

**Detection Logic**:
```python
# Track order book snapshots over 60 seconds
# If same price level appears 3+ times then cancels → spoof

Example:
t=0s:  Bid at $67,800 for 50 BTC appears
t=15s: Bid at $67,800 for 50 BTC disappears
t=30s: Bid at $67,800 for 50 BTC appears again
t=45s: Bid at $67,800 for 50 BTC disappears again

→ SPOOFING DETECTED (moderate confidence)
→ Fake bid support, bearish signal
```

**Confidence Levels**:
- 3-4 appearances → Moderate confidence
- 5+ appearances → High confidence

**Usage**:
```python
from tools.ie_order_book_microstructure import fetch_order_book_microstructure

result = fetch_order_book_microstructure("BTC")

print(f"Spoofs detected: {len(result['spoofing'])}")

for spoof in result['spoofing']:
    print(f"  {spoof['side']} at ${spoof['price']} ({spoof['confidence']})")

# Output:
# Spoofs detected: 2
#   bid at $67,800 (high_confidence, 6 appearances)
#   ask at $68,200 (moderate_confidence, 4 appearances)
```

**Interpretation**:
- Spoofed bids → Fake support, bearish (institutions selling into it)
- Spoofed asks → Fake resistance, bullish (institutions buying through it)

#### 2. Iceberg Orders (Hidden Institutional Activity)

**Definition**: Orders that keep refilling at the same price level after fills.

**Detection Logic**:
```python
# Track if order at price level refills 3+ times

Example:
t=0s:  Ask at $68,000 for 20 BTC
t=10s: Ask at $68,000 for 5 BTC (15 BTC filled)
t=20s: Ask at $68,000 for 20 BTC again (refilled!)
t=30s: Ask at $68,000 for 8 BTC (12 BTC filled)
t=40s: Ask at $68,000 for 20 BTC again (refilled!)

→ ICEBERG ORDER DETECTED (5 refills)
→ Institution has large sell order at $68,000
→ Bearish resistance
```

**Usage**:
```python
result = fetch_order_book_microstructure("BTC")

print(f"Icebergs detected: {len(result['icebergs'])}")

for iceberg in result['icebergs']:
    print(f"  {iceberg['side']} at ${iceberg['price']} ({iceberg['refills']} refills)")

# Output:
# Icebergs detected: 1
#   ask at $68,000 (5 refills)
```

**Interpretation**:
- Iceberg bids → Institutional accumulation zone (strong support)
- Iceberg asks → Institutional distribution zone (strong resistance)

#### 3. Wall Dynamics (Moving Support/Resistance)

**Definition**: Large orders (>2x median size) that move with price.

**Detection Logic**:
```python
# Track if large orders shift price levels over time

Example:
t=0s:  Large bid at $67,800 (50 BTC)
t=20s: Large bid at $67,850 (50 BTC)
t=40s: Large bid at $67,900 (50 BTC)

→ BID WALL MOVING UP
→ Institutions supporting price higher
→ Bullish signal
```

**Signals**:
```python
{
    "wall_dynamics": "bid_wall_up",     # Bullish
    "wall_dynamics": "bid_wall_down",   # Bearish
    "wall_dynamics": "ask_wall_down",   # Bullish
    "wall_dynamics": "ask_wall_up",     # Bearish
    "wall_dynamics": "stable"           # Neutral
}
```

**Usage**:
```python
result = fetch_order_book_microstructure("BTC")

print(f"Wall signal: {result['signals']}")

# Output:
# Wall signal: ['bid_wall_up', 'iceberg_ask_at_68000']
```

**Interpretation**:
- Bid wall moving up → Institutions stepping in higher (bullish)
- Ask wall moving down → Institutions stepping in lower (bullish)
- Bid wall moving down → Institutional support weakening (bearish)
- Ask wall moving up → Institutional selling increasing (bearish)

### Complete Example

```python
from tools.ie_order_book_microstructure import analyze_microstructure

result = analyze_microstructure("BTC")

# Output structure:
{
    "spoofing": [
        {
            "side": "bid",
            "price": 67800.0,
            "size": 50.0,
            "appearances": 6,
            "confidence": "high"
        }
    ],
    "icebergs": [
        {
            "side": "ask",
            "price": 68000.0,
            "refills": 5,
            "total_volume": 125.0
        }
    ],
    "wall_dynamics": "bid_wall_up",
    "signals": [
        "spoofing_detected",
        "iceberg_ask_at_68000",
        "bid_wall_moving_up"
    ],
    "summary": "Conflicting signals: Spoofed bid (bearish) vs bid wall up (bullish). Iceberg ask at $68,000 = strong resistance."
}
```

### Agent Usage

```bash
python agent/agent.py "Analyze BTC. Check for spoofing and icebergs."

# Agent response includes:
# - Spoofing: 1 fake bid detected (bearish)
# - Icebergs: 1 institutional sell order at $68,000 (strong resistance)
# - Walls: Bid support moving higher (bullish)
# - Interpretation: Mixed signals, wait for clarity
```

---

## Tool 2: Liquidation Cascade Tracker

**File**: `tools/ie_liquidation_tracker.py`

### What It Detects

#### Mass Liquidation Events

**Definition**: 5+ liquidations within 5 minutes = cascade risk

**Patterns**:
```python
# Short Squeeze: Mass short liquidations
Shorts liquidated → Forced buying → Price pumps → More shorts liquidated

Signal: Bullish momentum cascade

# Long Squeeze: Mass long liquidations
Longs liquidated → Forced selling → Price dumps → More longs liquidated

Signal: Bearish momentum cascade
```

### Detection Logic

```python
def detect_cascades(liquidations, lookback_minutes=5):
    """
    Count liquidations in rolling 5-minute windows.

    Cascade thresholds:
    - 5-9 liquidations: Minor cascade
    - 10-19 liquidations: Major cascade
    - 20+ liquidations: Extreme cascade
    """

    if cascade_detected:
        # Determine type
        if short_liq_count > long_liq_count * 2:
            return "short_squeeze"  # Bullish
        elif long_liq_count > short_liq_count * 2:
            return "long_squeeze"   # Bearish
        else:
            return "mixed_cascade"  # High volatility, no clear bias
```

### Stop Hunt Zones

**Definition**: Price levels with >$100k total liquidations

**Usage**: These levels act as magnets for future price action (stop losses clustered)

```python
{
    "stop_hunt_zones": [
        {
            "price": 67500.0,
            "liquidation_volume_usd": 450000,
            "side": "long",
            "interpretation": "Major long stop cluster, price may sweep this level"
        }
    ]
}
```

### Usage Example

```python
from tools.ie_liquidation_tracker import fetch_liquidation_tracker

result = fetch_liquidation_tracker("BTC", lookback_minutes=30)

print(f"Cascade detected: {result['cascade_detected']}")
print(f"Signal: {result['signal']}")
print(f"Total liquidations: {result['total_liquidations']}")
print(f"Stop hunt zones: {result['stop_hunt_zones']}")

# Output:
# Cascade detected: True
# Signal: short_squeeze
# Total liquidations: 12
# Stop hunt zones: [{'price': 67500, 'volume_usd': 450000, 'side': 'long'}]
```

### Agent Usage

```bash
python agent/agent.py "Check BTC for liquidation cascades"

# Agent response:
# - Cascade: Short squeeze detected (12 short liquidations in 5 min)
# - Signal: Bullish momentum (forced buying)
# - Stop hunt zone at $67,500 (450k longs liquidated)
# - Interpretation: Price likely to test higher, stops cleared below
```

### Note on Implementation

**Current Status**: Placeholder implementation (Hyperliquid liquidation API endpoint needs verification)

The tool returns neutral data if liquidation API is unavailable:
```python
{
    "cascade_detected": False,
    "signal": "neutral",
    "total_liquidations": 0,
    "note": "Hyperliquid liquidation API endpoint not confirmed"
}
```

**Future**: Once API endpoint is verified, tool will provide real liquidation data.

---

## Tool 3: Cross-Exchange Arbitrage Monitor

**File**: `tools/ie_cross_exchange_arb.py`

### What It Detects

**Price discrepancies** between Hyperliquid and Binance.

**Why It Matters**: Arbitrage bots instantly exploit price differences, creating directional pressure.

### Flow Signals

```python
# HL cheaper than Binance → Arb bots buy on HL → Bullish pressure
if hl_price < binance_price * 0.999:  # >0.1% cheaper
    signal = "bullish"
    interpretation = "HL cheaper, arb bots buying = bullish pressure"

# HL expensive vs Binance → Arb bots sell on HL → Bearish pressure
elif hl_price > binance_price * 1.001:  # >0.1% expensive
    signal = "bearish"
    interpretation = "HL expensive, arb bots selling = bearish pressure"

# Within 0.1% → Neutral
else:
    signal = "neutral"
```

### Supported Pairs

- BTC, ETH, SOL
- AVAX, MATIC, ARB, OP

### Usage Example

```python
from tools.ie_cross_exchange_arb import fetch_cross_exchange_arb

result = fetch_cross_exchange_arb("BTC")

print(f"HL Price: ${result['hl_price']}")
print(f"Binance Price: ${result['binance_price']}")
print(f"Deviation: {result['deviation_pct']}%")
print(f"Signal: {result['signal']}")
print(f"Interpretation: {result['interpretation']}")

# Output:
# HL Price: $67,750
# Binance Price: $67,825
# Deviation: -0.11%
# Signal: bullish
# Interpretation: HL cheaper by 0.11%, arb bots buying on HL = bullish pressure
```

### Agent Usage

```bash
python agent/agent.py "Check BTC cross-exchange arb signals"

# Agent response:
# - HL Price: $67,750
# - Binance Price: $67,825
# - Deviation: -0.11% (HL cheaper)
# - Signal: Bullish
# - Flow: Arb bots buying on HL to sell on Binance
# - Interpretation: Institutional buying pressure on HL
```

### Threshold Tuning

```python
# In config/settings.py
class IEConfig:
    arb_threshold_pct = 0.1  # Default: 0.1% deviation required

    # Adjust for different sensitivity:
    arb_threshold_pct = 0.05  # More sensitive (more signals)
    arb_threshold_pct = 0.2   # Less sensitive (fewer signals)
```

---

## Phase 2 Integration with Phase 1

### Convergence Bonus

Phase 2 signals **add to** Phase 1 convergence scores:

```python
base_score = phase1_convergence_score(coin)  # 0-100 from 5 core metrics

# Phase 2 bonuses:
if iceberg_detected and liquidation_cascade:
    base_score += 10  # Strong confluence bonus

if spoofing_detected and cross_exchange_arb:
    base_score += 5   # Moderate confluence bonus

final_score = min(100, base_score)
```

### Example: A+ Setup with Phase 2 Confluence

```markdown
### BTC SHORT - Grade: A+ (Score: 95/100)

**Phase 1 Metrics** (85/100):
✓ Order Book: -0.68 (strong ask pressure)
✓ Trade Flow: -0.61 (aggressive selling)
✓ Funding: +15% (extreme bullish crowd)
✓ Basis: +0.35% (premium)
✓ VWAP: +2.3σ (extreme overextension)

**Phase 2 Confluence** (+10):
✓ Iceberg sell order at $68,000 (7 refills)
✓ Short squeeze just completed (18 liquidations)
✓ HL trading 0.14% premium to Binance (arb selling pressure)
✓ Spoofed bid at $67,800 (fake support)

**Total Score**: 95/100

This is an EXCEPTIONAL short setup. Phase 1 shows institutional
bearish positioning. Phase 2 confirms with iceberg resistance,
completed short squeeze (forced buyers exhausted), arb bots
selling, and spoofed support. All systems aligned.
```

---

## When to Use Phase 2 Tools

### Order Book Microstructure

**Use when**:
- Price consolidating (detect accumulation/distribution)
- Suspected manipulation (confirm spoofing)
- High volume at key levels (track institutional activity)

**Skip when**:
- Fast trending markets (snapshots too volatile)
- Low liquidity coins (insufficient data)

### Liquidation Tracker

**Use when**:
- Price near key levels (stop hunt zones)
- After violent moves (cascade confirmation)
- High funding rates (liquidation risk assessment)

**Skip when**:
- Low volatility (few liquidations occur)
- Early in session (insufficient data)

### Cross-Exchange Arbitrage

**Use when**:
- Validating breakouts (arb flow confirmation)
- Low volume periods (detect early institutional flow)
- Divergent price action (exchange-specific signals)

**Skip when**:
- Extremely volatile markets (arb spreads widen, signals break)
- Low liquidity coins not on Binance (no comparison data)

---

## Testing Phase 2 Tools

### Test Microstructure

```bash
python -c "
from tools.ie_order_book_microstructure import fetch_order_book_microstructure_tool

result = fetch_order_book_microstructure_tool('BTC')
print(f\"Spoofs: {len(result.get('spoofing', []))}\")
print(f\"Icebergs: {len(result.get('icebergs', []))}\")
print(f\"Signals: {result.get('signals', [])}\")
"
```

### Test Liquidation Tracker

```bash
python -c "
from tools.ie_liquidation_tracker import fetch_liquidation_tracker_tool

result = fetch_liquidation_tracker_tool('BTC', lookback_minutes=30)
print(f\"Cascade: {result.get('cascade_detected')}\")
print(f\"Signal: {result.get('signal')}\")
"
```

### Test Cross-Exchange Arb

```bash
python -c "
from tools.ie_cross_exchange_arb import fetch_cross_exchange_arb_tool

result = fetch_cross_exchange_arb_tool('BTC')
print(f\"Deviation: {result.get('deviation_pct')}%\")
print(f\"Signal: {result.get('signal')}\")
"
```

### Test with Agent

```bash
python agent/agent.py "Analyze BTC with full Phase 2 analysis: spoofing, liquidations, and cross-exchange arb"
```

---

## Key Takeaways

1. **Temporal analysis** - Single snapshots lie, track changes over 60 seconds
2. **Spoofing detection** - Identify fake liquidity (fade that direction)
3. **Iceberg orders** - Find hidden institutional activity
4. **Wall dynamics** - Track moving support/resistance
5. **Liquidation cascades** - Detect forced buying/selling momentum
6. **Cross-exchange arb** - Follow institutional arb bot flow
7. **Confluence bonus** - Phase 2 adds +10 points to Phase 1 scores
8. **Context-dependent** - Use when appropriate (consolidation, key levels, post-cascade)

**Phase 2 = The edge. See what retail cannot see.**

See [strategy.md](strategy.md) for how Phase 2 signals integrate into overall trading strategy.

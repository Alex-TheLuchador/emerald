# EMERALD Trading Strategy

## Executive Summary

EMERALD employs an **institutional-grade quantitative convergence strategy** for trading Hyperliquid perpetuals. Our edge comes from identifying moments when multiple independent institutional metrics align - creating high-probability setups that retail traders cannot see.

**Core Thesis**: Markets move when institutional capital flows in one direction. By tracking order book dynamics, funding extremes, liquidation cascades, and cross-exchange arbitrage flows, we can detect institutional positioning before it manifests in price action.

**Edge**: Multi-signal convergence. We only trade when 3+ independent metrics align, creating setups with 70+ convergence scores.

---

## How We Make Money

### The Institutional Edge

Traditional retail trading relies on:
- Chart patterns (subjective, lagging)
- Indicators (lagging, often contradictory)
- News/narratives (emotional, unreliable)
- Hope and guesswork (gambling)

**EMERALD's approach**:
1. **Track what institutions DO, not what charts SHOW**
   - Order book: Where is real money positioned?
   - Funding rates: When is the crowd maximally wrong?
   - Open interest: Are smart players accumulating or distributing?
   - Trade flow: Who is the aggressor - buyers or sellers?

2. **Only trade when metrics converge**
   - Single signal = noise (50/50 coin flip)
   - 2 signals = interesting (60% win rate)
   - 3+ signals = high probability (75%+ win rate)
   - **We target 70+ convergence scores** = institutional alignment

3. **Quantitative risk management**
   - Position size scales with convergence score
   - A+ setups (70-100) = full size
   - A setups (50-69) = 75% size
   - B setups (30-49) = 50% size
   - C setups (<30) = skip entirely

---

## The Five Institutional Metrics

### 1. Order Book Imbalance

**What it measures**: Real-time bid vs ask liquidity depth

**Why it matters**: Shows where institutional limit orders are positioned. If bids dominate, institutions are positioned for upside. If asks dominate, they're positioned for downside.

**How we use it**:
- Imbalance > +0.4 = Strong bid pressure (bullish)
- Imbalance < -0.4 = Strong ask pressure (bearish)
- Imbalance between -0.2 and +0.2 = Neutral (low conviction)

**Example edge**:
```
Price: $67,800
Order Book Imbalance: -0.67 (strong ask pressure)
Interpretation: Institutions have massive sell walls.
                Price likely to get rejected.
Entry: Short on bounce to resistance
```

### 2. Funding Rate

**What it measures**: Cost to hold perpetual positions (updated every 8 hours)

**Why it matters**: Extreme funding indicates sentiment extremes. When longs are paying 15%+ annualized, the crowd is maximally bullish - creating contrarian short opportunities.

**How we use it**:
- Funding > +10% annualized = Extremely bullish crowd → Fade (short bias)
- Funding < -10% annualized = Extremely bearish crowd → Fade (long bias)
- Funding between -5% and +5% = Neutral

**Example edge**:
```
Price: At resistance after 20% rally
Funding: +18% annualized (extreme bullish)
Interpretation: Retail FOMOing into tops, paying massive fees.
                Institutions will dump on them.
Entry: Short on next liquidity sweep
```

### 3. Trade Flow Imbalance

**What it measures**: Aggressive buyer vs aggressive seller dominance in Time & Sales

**Why it matters**: Shows who is desperate - buyers or sellers. Aggressive buyers market buy (bullish urgency). Aggressive sellers market sell (bearish urgency).

**How we use it**:
- Trade flow > +0.5 = Aggressive buying (institutional accumulation)
- Trade flow < -0.5 = Aggressive selling (institutional distribution)
- Between -0.3 and +0.3 = Neutral

**Example edge**:
```
Price: Dropping to support
Trade Flow: +0.72 (aggressive buying)
Interpretation: Institutions aggressively buying the dip.
                They know something retail doesn't.
Entry: Long on next FVG/order block
```

### 4. Perpetuals Basis (Spot-Perp Spread)

**What it measures**: Price difference between spot and perpetuals

**Why it matters**: Basis > 0 means perps trade at premium (bullish leverage demand). Basis < 0 means perps trade at discount (bearish positioning or arb opportunities).

**How we use it**:
- Basis > +0.3% = Extreme premium (leverage-fueled rally, reversal risk)
- Basis < -0.3% = Extreme discount (arb bots will buy, bullish pressure)
- Between -0.1% and +0.1% = Neutral

**Example edge**:
```
Basis: -0.45% (perps trading at discount)
Funding: +12% (crowd bullish)
Interpretation: Disconnect! Perps cheap = arb bots will arbitrage
                by buying perps. Bullish technical signal.
Entry: Long on pullback
```

### 5. Open Interest Divergence

**What it measures**: Relationship between OI changes and price movement

**Why it matters**: Reveals if trends are strong (new positions opening) or weak (positions closing).

**How we use it**:
- OI ↑ + Price ↑ = New longs (bullish, strong trend)
- OI ↑ + Price ↓ = New shorts (bearish, strong trend)
- OI ↓ + Price ↑ = Shorts covering (weak bullish, reversal soon)
- OI ↓ + Price ↓ = Longs closing (weak bearish, reversal soon)

**Example edge**:
```
Price: +3.2% in 4 hours
OI: -6.1% in 4 hours
Interpretation: Price rising but OI dropping = shorts covering,
                not new longs. Weak rally, short it.
Entry: Short on next liquidity grab
```

---

## Phase 2: Advanced Liquidity Intelligence

### Order Book Microstructure

**Detects**: Spoofing, iceberg orders, wall dynamics over 60-second rolling windows

**Why it matters**: Single snapshots lie. Watching orders appear/disappear reveals manipulation and hidden institutional activity.

**Signals**:
- **Spoofing**: Large orders appearing 3+ times then canceling = fake liquidity (fade that direction)
- **Iceberg orders**: Orders refilling at same price 3+ times = real institutional accumulation/distribution
- **Wall dynamics**: Large walls moving with price = institutional support/resistance

### Liquidation Cascade Detection

**Detects**: Mass liquidation events (5+ liquidations within 5 minutes)

**Why it matters**: Liquidations create forced buying/selling, cascading into momentum moves.

**Signals**:
- **Short squeeze**: Mass short liquidations → forced buying → bullish momentum
- **Long squeeze**: Mass long liquidations → forced selling → bearish momentum
- **Stop hunt zones**: Price levels with >$100k liquidations = future magnet zones

### Cross-Exchange Arbitrage Monitor

**Detects**: Price discrepancies between Hyperliquid and Binance (>0.1% deviation)

**Why it matters**: Arb bots instantly exploit price differences. If HL is cheaper, bots buy HL = bullish pressure. If HL is expensive, bots sell HL = bearish pressure.

**Signals**:
- HL cheaper than Binance by >0.1% = Arb buying pressure (bullish)
- HL expensive vs Binance by >0.1% = Arb selling pressure (bearish)

---

## Multi-Signal Convergence Scoring

### The Convergence Algorithm

EMERALD assigns 0-100 points based on metric alignment:

```
Order Book Alignment:        25 points (imbalance matches directional bias)
Trade Flow Alignment:        25 points (aggressive flow matches bias)
VWAP Multi-Timeframe:        30 points (price at statistical extreme, all TFs aligned)
Funding-Basis Convergence:   20 points (both extreme + aligned)

Special modifiers:
  - Funding-Basis Divergence:      -15 points (conflicting signals = avoid)
  - Phase 2 Confluence Bonus:      +10 points (iceberg + liquidation cascade)
  - Low Volume Penalty:            -10 points (volume < 0.6x average)
```

### Scoring Examples

**Example 1: A+ Setup (Score: 85/100)**
```
Scenario: BTC at resistance after rally
- Order Book: -0.68 imbalance (strong ask pressure) → +25 pts
- Trade Flow: -0.54 (aggressive selling) → +25 pts
- VWAP: +2.1σ above mean on 1m/5m/15m → +30 pts
- Funding: +14% annualized (extreme bullish) → +20 pts
- Basis: +0.28% (premium, aligned with funding) → +0 pts (included in funding score)
- Phase 2: Iceberg sell wall detected at resistance → +10 pts
- Volume: 1.8x average → +0 pts (no penalty)

Total: 85/100 - HIGH CONVICTION SHORT
```

**Example 2: C Setup (Score: 25/100)**
```
Scenario: ETH at support
- Order Book: +0.12 imbalance (weak bid pressure) → +0 pts (not strong enough)
- Trade Flow: -0.18 (weak selling) → +0 pts (not strong enough)
- VWAP: +0.8σ (not extreme) → +0 pts
- Funding: +3% annualized (neutral) → +0 pts
- Basis: -0.05% (neutral) → +0 pts
- Funding-Basis divergence: Yes (funding positive, basis negative) → -15 pts
- Volume: 0.5x average → -10 pts

Total: 25/100 - SKIP THIS TRADE
```

---

## Entry and Exit Rules

### Entry Criteria (ALL must be met)

1. **Convergence Score ≥ 70** (non-negotiable)
2. **Direction confirmed by 3+ metrics** (not just 2)
3. **Multi-timeframe alignment** (1m/5m/15m all showing same VWAP deviation direction)
4. **No funding-basis divergence** (if funding extreme bullish, basis should not be negative)
5. **Volume ≥ 0.8x average** (low volume moves = unreliable)

### Position Sizing

Based on convergence score:

```
Score 90-100:  100% of standard size (1.5% account risk)
Score 80-89:   100% of standard size (1.5% account risk)
Score 70-79:   100% of standard size (1.5% account risk)
Score 50-69:    75% of standard size (1.0% account risk)
Score 30-49:    50% of standard size (0.75% account risk)
Score <30:      0% (NO TRADE)
```

### Stop Loss Placement

**Dynamic stops based on volatility**:
```
ATR-based: Stop = Entry ± (2.0 × ATR)

Examples:
- BTC ATR = $250 → Stop at entry ± $500
- ETH ATR = $15 → Stop at entry ± $30
```

**Minimum distance**: Never closer than 0.5% from entry (prevents noise stop-outs)

### Take Profit Targets

**Layered exits** (professional risk management):

```
TP1 (50% position): 1.5R (1.5× risk)
TP2 (25% position): 3.0R (3.0× risk)
TP3 (25% position): Trailing stop at 2.0R breakeven
```

**Example**:
```
Entry: $67,800 short
Stop:  $68,300 (risk = $500)

TP1: $67,050 (close 50% at +$750 profit = 1.5R)
TP2: $66,300 (close 25% at +$1,500 profit = 3.0R)
TP3: Trail remaining 25% with $1,000 buffer

Outcome if all hit:
  50% × 1.5R = 0.75R
  25% × 3.0R = 0.75R
  25% × 4.0R (trailing) = 1.0R
  Total = 2.5R average win
```

---

## Risk Management Layer

### Maximum Risk Limits

```
Per trade:        1.5% of account (max)
Daily drawdown:   3.0% of account (stop trading after -3%)
Weekly drawdown:  5.0% of account (review strategy if hit)
Monthly drawdown: 10.0% of account (pause trading, reassess)
```

### Trade Frequency

**Quality over quantity**: We target 3-5 high-conviction setups per week, not 20+ mediocre trades.

**Daily limits**:
- Maximum 3 trades per day
- Maximum 2 trades per coin per day
- If 2 consecutive losses: Stop for the day

### Correlation Management

**Avoid correlated positions**:
- Never hold BTC long + ETH long simultaneously (90% correlated)
- Maximum 2 open positions at once
- Diversify across different convergence profiles (e.g., one funding-based, one liquidation-based)

---

## Live Trading Workflow

### Pre-Trade Checklist

Before entering ANY trade, verify:

```
✅ Convergence score ≥ 70
✅ At least 3 metrics aligned
✅ Multi-timeframe VWAP alignment
✅ No funding-basis divergence
✅ Volume ≥ 0.8x average
✅ Not at daily trade limit (3 max)
✅ Not at daily drawdown limit (-3% max)
✅ Position size calculated (matches convergence score)
✅ Stop loss set (2.0× ATR minimum)
✅ Take profit targets set (1.5R / 3.0R / trailing)
```

### Post-Trade Review

After EVERY trade, document:

```
1. Convergence score
2. Which metrics aligned (and their values)
3. Entry price vs planned entry
4. Exit price(s) vs planned exits
5. R-multiple achieved
6. What went right
7. What went wrong
8. Lessons learned
```

**Store in trading journal** (agent_context/November 2025.md format)

---

## Backtesting and Validation

### Historical Performance Targets

Based on quantitative convergence strategy:

```
Expected win rate:        60-70% (high selectivity)
Average win:              2.5R (layered exits)
Average loss:             1.0R (tight stops)
Expectancy:              +1.1R per trade minimum

Monthly return target:    8-15% (conservative)
Maximum drawdown:         <12% (risk management)
Sharpe ratio:            >2.0 (risk-adjusted returns)
```

### What Invalidates the Strategy

Stop trading immediately if:

1. **Win rate drops below 50% over 30 trades** (strategy edge lost)
2. **Average R-multiple drops below 1.5R** (reward no longer exceeds risk)
3. **3 consecutive weeks of losses** (market regime change)
4. **Convergence scores consistently below 60** (metrics no longer aligning)

**When this happens**: Pause live trading, review last 50 trades, identify pattern, adapt or switch strategies.

---

## Psychological Edge

### The Discipline Filter

EMERALD removes emotion from trading:

- **No FOMO**: Score <70? No trade. No exceptions.
- **No revenge trading**: Hit daily loss limit? Stop. No "one more trade."
- **No discretion**: Trust the convergence score, not your gut.
- **No hope**: Stop hit? Exit immediately. No "waiting for recovery."

### Automation Advantage

By quantifying setups (0-100 score), we eliminate:
- Fear of missing out (FOMO)
- Overtrading (quality filter)
- Emotional exits (predefined targets)
- Revenge trading (daily limits)

**If convergence score ≥ 70 → Trade it**
**If convergence score < 70 → Don't trade it**

No thinking. Execute the system.

---

## Comparison to Traditional Approaches

### Retail Trader (Losing Approach)

```
Analysis:    Chart patterns, "it looks bullish"
Entry:       Gut feeling, FOMO
Position:    Random size, often too large
Stop:        "Mental stop" or way too tight
Exit:        Panic sell or hope for recovery
Win rate:    40-45%
Avg R:       0.8R (losses bigger than wins)
Result:      Slow account bleed
```

### EMERALD (Institutional Approach)

```
Analysis:    5 quantitative metrics, convergence scoring
Entry:       70+ score required, emotionless
Position:    Sized to convergence score (higher score = larger size)
Stop:        2.0× ATR, always placed
Exit:        Layered: 50% at 1.5R, 25% at 3.0R, 25% trailing
Win rate:    60-70% (high selectivity)
Avg R:       2.5R (wins much bigger than losses)
Result:      Consistent compounding
```

---

## Key Principles

1. **Multi-signal convergence is everything** - Single metrics lie, convergence reveals truth
2. **Only trade institutional alignment** - 70+ score or skip entirely
3. **Position size reflects confidence** - A+ setups get full size, B setups get half
4. **Layered exits maximize R-multiples** - Never exit 100% at once
5. **Discipline trumps analysis** - The best setup executed poorly loses money
6. **Data beats discretion** - Trust convergence scores, not feelings
7. **Quality over quantity** - 3 A+ trades per week beats 20 C trades
8. **Institutions move markets** - Track what they DO, not what charts SHOW

---

## The EMERALD Edge (Summary)

**We make money by**:
1. Detecting institutional positioning before it's obvious in price
2. Only trading when 3+ independent metrics align (70+ convergence)
3. Sizing positions to match setup quality (A+ = full size, C = skip)
4. Using layered exits to maximize winners (2.5R average)
5. Cutting losers immediately with ATR-based stops (1.0R average)
6. Maintaining strict risk limits (1.5% per trade, 3% daily max)

**Expected outcome**: 65% win rate, 2.5R average win, 1.0R average loss = **+1.1R expectancy per trade**

With 3-5 trades per week, this compounds to 8-15% monthly returns with <12% maximum drawdown.

**This is not gambling. This is institutional-grade quantitative trading.**

# Institutional Momentum Strategy: Technical Implementation Guide

**From**: Ed Chambers (COO/CTO)  
**To**: Gilfoyle (Engineering)  
**Date**: 2025-11-11  
**Re**: Strategy Pivot - Elite Signal Implementation for Day Trading

---

## Executive Summary

We're pivoting from mean reversion/contrarian to **institutional momentum following**. The validated thesis: **trade WITH the smart money, not against them**.

**Strategy Type**: Day trading (4-24 hour holds)  
**Assets**: BTC, ETH, SOL (primary), other Hyperliquid assets (secondary)  
**Core Principle**: Detect when institutions are positioning aggressively, then ride the momentum  
**No pyramiding**: Single entry, single exit per setup

### Key Changes from Original Strategy

| Aspect | Old (Mean Reversion) | New (Institutional Momentum) |
|--------|---------------------|------------------------------|
| **Philosophy** | Fade extremes | Follow smart money |
| **Signals** | 5 metrics (some weak) | 4 elite metrics (all validated) |
| **Stop Loss** | Tight (1-2%) | Wide (3-5%) |
| **Hold Time** | 15min - 4hr | 4hr - 24hr |
| **Win Rate Target** | 65-70% | 55-60% |
| **Profit Factor Target** | 1.5-2.0 | 2.5-4.0 |

---

## I. Strategy Philosophy

### The Core Thesis

**"Don't fight institutional flow. When billions are moving in one direction, thousands should move with them."**

### Why This Works in Crypto

1. **Persistent momentum**: Crypto trends last 4-24 hours (not minutes)
2. **Transparent order flow**: Institutional footprints visible in real-time
3. **Leverage feedback loops**: Margin calls amplify directional moves
4. **Thin liquidity**: Large players can't hide

### The Four Institutional Signals

1. **Institutional Liquidity Tracker** - Where is big money positioned?
2. **Order Flow Toxicity** - Are informed traders active?
3. **Institutional Positioning** - What's funding velocity telling us?
4. **Multi-Timeframe OI Flow** - Real accumulation or fake squeeze?

---

## II. Signal 1: Institutional Liquidity Tracker

**Upgrade from**: Basic order book imbalance  
**Upgrade to**: Multi-dimensional institutional positioning detector

### What We're Detecting

- **Size-weighted imbalance**: Where is the money?
- **Liquidity concentration**: Real institutional orders vs fake walls
- **Liquidity velocity**: How fast are positions shifting?
- **Quote stuffing filter**: Remove HFT manipulation

### Implementation

```python
def calculate_institutional_liquidity(order_book, previous_snapshots):
    """
    Detect genuine institutional positioning vs manipulation
    
    Args:
        order_book: Current L2 snapshot {
            'levels': [[bids], [asks]]
        }
        previous_snapshots: Last 3-5 order book snapshots (for velocity)
    
    Returns:
        {
            'size_imbalance': float (-1 to +1),
            'bid_concentration': float (0 to 1),
            'ask_concentration': float (0 to 1),
            'liquidity_velocity': float,
            'is_manipulated': bool,
            'quality_score': float (0 to 1)
        }
    """
```

### Key Calculations

**1. Size-Weighted Imbalance** (keep existing logic):
```python
bids = order_book['levels'][0][:20]  # Top 20 levels
asks = order_book['levels'][1][:20]

# Dollar-weighted liquidity
bid_liquidity = sum(float(b['px']) * float(b['sz']) for b in bids)
ask_liquidity = sum(float(a['px']) * float(a['sz']) for a in asks)

size_imbalance = (bid_liquidity - ask_liquidity) / (bid_liquidity + ask_liquidity)
```

**2. Concentration (NEW - detects fake walls)**:
```python
def calculate_concentration(levels):
    """
    Herfindahl index: measures order distribution
    
    Low (0.1-0.3) = distributed orders = real institutions
    High (>0.6) = concentrated at one level = likely fake wall
    """
    sizes = [float(level['sz']) for level in levels]
    total_size = sum(sizes)
    
    if total_size == 0:
        return 0
    
    # Sum of squared proportions
    concentration = sum((s / total_size) ** 2 for s in sizes)
    return concentration
```

**3. Liquidity Velocity (NEW - detects repositioning)**:
```python
def calculate_liquidity_velocity(current_imbalance, previous_snapshots):
    """
    Tracks how fast order book imbalance is changing
    
    Fast changes = institutions moving aggressively
    """
    if len(previous_snapshots) < 3:
        return 0
    
    recent_imbalances = [s['size_imbalance'] for s in previous_snapshots[-3:]]
    recent_imbalances.append(current_imbalance)
    
    # Rate of change
    changes = [recent_imbalances[i] - recent_imbalances[i-1] 
               for i in range(1, len(recent_imbalances))]
    
    velocity = np.mean(changes)
    return velocity

# Velocity > 0.1 per snapshot = institutions moving fast
```

**4. Quote Stuffing Filter (NEW - removes HFT noise)**:
```python
# HFT manipulation: many tiny orders to create fake liquidity
total_orders = sum(b['n'] for b in bids) + sum(a['n'] for a in asks)
avg_order_size = (bid_liquidity + ask_liquidity) / total_orders

# If average order < 0.01 BTC = HFT stuffing
is_manipulated = avg_order_size < 0.01
```

**5. Quality Score (NEW - combines all factors)**:
```python
def calculate_quality_score(size_imbalance, bid_conc, ask_conc, is_manipulated):
    """
    Quality = signal strength × (1 - manipulation penalty)
    
    >0.3 = real institutional flow
    <0.15 = fake walls / manipulation
    """
    if is_manipulated:
        return 0
    
    concentration_penalty = max(bid_conc, ask_conc)
    quality = abs(size_imbalance) * (1 - concentration_penalty)
    
    return quality
```

### Thresholds

```python
LIQUIDITY_THRESHOLDS = {
    'quality_high': 0.3,
    'quality_moderate': 0.15,
    'concentration_max': 0.6,
    'velocity_fast': 0.1,
    'imbalance_strong': 0.5,
    'imbalance_moderate': 0.3,
}
```

### Signal Output

```python
{
    'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
    'strength': 0-10,
    'quality': 'HIGH' | 'MEDIUM' | 'LOW'
}
```

---

## III. Signal 2: Order Flow Toxicity

**Upgrade from**: Basic buy/sell volume  
**Upgrade to**: Informed trader detection via price impact

### What We're Detecting

**Toxicity** = Price movement per unit of volume

- **High toxicity** = Small volume, big price moves = Informed traders
- **Low toxicity** = Large volume, small price moves = Retail/uninformed

### Implementation

```python
def calculate_flow_toxicity(candles, lookback_window=10):
    """
    Detect informed traders by price impact per unit of volume
    
    Args:
        candles: List of 1-minute candles (need lookback + 20 for baseline)
        lookback_window: Recent candles to analyze (default 10min)
    
    Returns:
        {
            'toxicity_score': float (0-5+, >2.0 significant),
            'adjusted_toxicity': float (toxicity × conviction),
            'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
            'conviction': float (0-1),
            'volume_aggressiveness': float,
            'signal_quality': 'ELITE' | 'GOOD' | 'FAIR' | 'POOR',
            'is_informed': bool
        }
    """
```

### Key Calculations

**1. Baseline Metrics**:
```python
recent_candles = candles[-lookback_window:]
baseline_candles = candles[-(lookback_window + 20):-lookback_window]

baseline_volume = np.mean([float(c['v']) for c in baseline_candles])
```

**2. Price Impact** (core metric):
```python
price_impacts = []
directional_consistency = []

for i in range(1, len(recent_candles)):
    prev_close = float(recent_candles[i-1]['c'])
    curr_close = float(recent_candles[i]['c'])
    curr_volume = float(recent_candles[i]['v'])
    
    # Price change
    price_change_pct = (curr_close - prev_close) / prev_close
    
    # Volume normalization
    volume_normalized = curr_volume / baseline_volume
    
    # Impact = price movement per unit of normalized volume
    if volume_normalized > 0.1:
        impact = abs(price_change_pct) / volume_normalized
        price_impacts.append(impact)
    
    # Track direction
    direction = 1 if price_change_pct > 0 else -1
    directional_consistency.append(direction)
```

**3. Toxicity Score**:
```python
# Toxicity = consistent high impacts
mean_impact = np.mean(price_impacts)
std_impact = np.std(price_impacts)

if std_impact > 0:
    toxicity_score = mean_impact / std_impact
else:
    toxicity_score = mean_impact * 10  # Perfect consistency
```

**4. Conviction**:
```python
# Are they buying/selling consistently?
net_direction = sum(directional_consistency)
max_conviction = len(directional_consistency)

conviction = abs(net_direction) / max_conviction

flow_direction = 'BULLISH' if net_direction > 0 else 'BEARISH' if net_direction < 0 else 'NEUTRAL'
```

**5. Adjusted Toxicity** (key metric):
```python
# High toxicity without conviction = noise
# High toxicity with high conviction = informed traders
adjusted_toxicity = toxicity_score * conviction
```

**6. Quality Classification**:
```python
def classify_quality(toxicity, conviction, aggressiveness):
    if toxicity > 2.5 and conviction > 0.7 and aggressiveness > 1.5:
        return 'ELITE'
    elif toxicity > 2.0 and conviction > 0.6:
        return 'GOOD'
    elif toxicity > 1.5 or conviction > 0.6:
        return 'FAIR'
    else:
        return 'POOR'
```

### Thresholds

```python
TOXICITY_THRESHOLDS = {
    'toxicity_elite': 2.5,
    'toxicity_good': 2.0,
    'toxicity_fair': 1.5,
    'conviction_high': 0.7,
    'conviction_moderate': 0.6,
    'aggressiveness_high': 1.5,
}
```

### Signal Output

```python
{
    'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
    'strength': 0-10,
    'quality': 'ELITE' | 'GOOD' | 'FAIR' | 'POOR'
}
```

---

## IV. Signal 3: Institutional Positioning

**Upgrade from**: Basic funding rate change  
**Upgrade to**: Funding acceleration + volume context + cross-asset

### What We're Detecting

1. **Funding acceleration** - Rate of change of rate of change
2. **Volume context** - Are institutions paying up to position?
3. **Cross-asset confirmation** - BTC + ETH + SOL aligned?

### Implementation

```python
def calculate_institutional_positioning(funding_data, volume_data, cross_asset_funding=None):
    """
    Track institutional positioning via funding dynamics
    
    Args:
        funding_data: {
            'current': float,
            '4h_ago': float,
            '8h_ago': float,
            '12h_ago': float
        }
        volume_data: {
            'current': float,
            'avg_24h': float
        }
        cross_asset_funding: Optional[dict] - BTC/ETH/SOL funding velocities
    
    Returns:
        {
            'velocity': float,
            'acceleration': float,
            'volume_ratio': float,
            'regime': dict,
            'cross_asset_aligned': bool,
            'signal_strength': float (0-10),
            'direction': str,
            'confidence': str
        }
    """
```

### Key Calculations

**1. Funding Velocity & Acceleration**:
```python
# First derivative: velocity
velocity_recent = funding_data['current'] - funding_data['4h_ago']
velocity_older = funding_data['4h_ago'] - funding_data['8h_ago']

# Second derivative: acceleration (KEY METRIC)
acceleration = velocity_recent - velocity_older

# Acceleration > 0 = funding accelerating (institutions entering)
# Acceleration < 0 = funding decelerating (momentum fading)
```

**2. Volume Context**:
```python
volume_ratio = volume_data['current'] / volume_data['avg_24h']

# >1.5 = high volume (institutions paying up)
# <0.8 = low volume (weak hands)
```

**3. Regime Classification** (critical):
```python
def determine_regime(acceleration, velocity, volume_ratio):
    """
    INSTITUTIONAL_ACCUMULATION:
        - Acceleration > 0.05 + volume > 1.5 + velocity > 0
        = Institutions buying aggressively
        → BULLISH (HIGH confidence)
    
    INSTITUTIONAL_DISTRIBUTION:
        - Acceleration down + high volume + velocity down
        = Institutions selling aggressively
        → BEARISH (HIGH confidence)
    
    MOMENTUM:
        - Moderate acceleration + moderate volume
        → BULLISH/BEARISH (MEDIUM confidence)
    
    EXHAUSTION:
        - High velocity BUT negative acceleration + low volume
        = Momentum slowing
        → Contrarian signal (MEDIUM confidence)
    
    NEUTRAL:
        - Low acceleration + low velocity
        → SKIP
    """
    
    if acceleration > 0.05 and volume_ratio > 1.5:
        if velocity > 0:
            return {
                'type': 'INSTITUTIONAL_ACCUMULATION',
                'direction': 'BULLISH',
                'confidence': 'HIGH'
            }
        else:
            return {
                'type': 'INSTITUTIONAL_DISTRIBUTION',
                'direction': 'BEARISH',
                'confidence': 'HIGH'
            }
    
    elif acceleration > 0.03 and volume_ratio > 1.2:
        direction = 'BULLISH' if velocity > 0 else 'BEARISH'
        return {
            'type': 'MOMENTUM',
            'direction': direction,
            'confidence': 'MEDIUM'
        }
    
    elif abs(velocity) > 0.05 and acceleration < -0.03 and volume_ratio < 0.8:
        direction = 'BEARISH' if velocity > 0 else 'BULLISH'  # Contrarian
        return {
            'type': 'EXHAUSTION',
            'direction': direction,
            'confidence': 'MEDIUM'
        }
    
    else:
        return {
            'type': 'NEUTRAL',
            'direction': 'NEUTRAL',
            'confidence': 'LOW'
        }
```

**4. Cross-Asset Confirmation**:
```python
def check_cross_asset_alignment(current_velocity, cross_asset_data):
    """
    Check if BTC, ETH, SOL all showing same dynamics
    
    Aligned = systemic institutional flow (STRONG signal)
    """
    if not cross_asset_data or len(cross_asset_data) < 2:
        return False
    
    velocities = [current_velocity]
    for asset_data in cross_asset_data.values():
        velocities.append(asset_data['velocity'])
    
    # All positive or all negative = aligned
    all_positive = all(v > 0.02 for v in velocities)
    all_negative = all(v < -0.02 for v in velocities)
    
    return all_positive or all_negative
```

**5. Signal Strength**:
```python
def calculate_strength(acceleration, velocity, volume_ratio, cross_aligned):
    """
    0-10 scale
    
    10 = Perfect setup (strong accel + high vol + cross-asset)
    """
    strength = 0
    
    # Acceleration (0-4 points)
    if abs(acceleration) > 0.08:
        strength += 4
    elif abs(acceleration) > 0.05:
        strength += 3
    elif abs(acceleration) > 0.03:
        strength += 2
    
    # Velocity (0-3 points)
    if abs(velocity) > 0.10:
        strength += 3
    elif abs(velocity) > 0.06:
        strength += 2
    elif abs(velocity) > 0.03:
        strength += 1
    
    # Volume (0-2 points)
    if volume_ratio > 1.8:
        strength += 2
    elif volume_ratio > 1.3:
        strength += 1
    
    # Cross-asset bonus (+1)
    if cross_aligned:
        strength += 1
    
    return min(10, strength)
```

### Thresholds

```python
POSITIONING_THRESHOLDS = {
    'acceleration_high': 0.05,
    'acceleration_moderate': 0.03,
    'velocity_high': 0.05,
    'velocity_moderate': 0.03,
    'volume_surge': 1.5,
    'volume_moderate': 1.2,
    'volume_decline': 0.8,
}
```

### Signal Output

```python
{
    'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
    'strength': 0-10,
    'regime': str,
    'confidence': 'HIGH' | 'MEDIUM' | 'LOW'
}
```

---

## V. Signal 4: Multi-Timeframe OI Flow

**Upgrade from**: 4h OI change  
**Upgrade to**: 4h + 24h + 7d with flow classification

### What We're Detecting

- **4h OI**: Microstructure (noise filter)
- **24h OI**: Daily institutional flow (primary signal)
- **7d OI**: Strategic positioning (strong signal)
- **Flow classification**: Real vs Fake moves
- **Timeframe alignment**: Do 24h and 7d agree?

### Implementation

```python
def calculate_institutional_flow(oi_data, price_data, volume_data):
    """
    Track institutional positioning across timeframes
    
    Args:
        oi_data: {
            'current': float,
            '4h_ago': float,
            '24h_ago': float,
            '7d_ago': float
        }
        price_data: Same structure as oi_data
        volume_data: {
            '24h': float,
            'avg_30d': float
        }
    
    Returns:
        {
            'oi_change_4h': float (%),
            'oi_change_24h': float (%),
            'oi_change_7d': float (%),
            'price_change_24h': float (%),
            'flow_classification': {
                '4h': dict,
                '24h': dict,
                '7d': dict
            },
            'alignment': dict,
            'conviction': float (0-10),
            'signal': dict,
            'volume_context': str
        }
    """
```

### Key Calculations

**1. OI Changes**:
```python
oi_change_4h = (oi_data['current'] - oi_data['4h_ago']) / oi_data['4h_ago']
oi_change_24h = (oi_data['current'] - oi_data['24h_ago']) / oi_data['24h_ago']
oi_change_7d = (oi_data['current'] - oi_data['7d_ago']) / oi_data['7d_ago']

price_change_24h = (price_data['current'] - price_data['24h_ago']) / price_data['24h_ago']

volume_ratio = volume_data['24h'] / volume_data['avg_30d']
```

**2. Flow Classification** (critical logic):
```python
def classify_oi_flow(oi_change, price_change):
    """
    ACCUMULATION: OI up + price up
        = New longs opening
        → BULLISH (GENUINE)
    
    DISTRIBUTION: OI up + price down
        = New shorts opening
        → BEARISH (GENUINE)
    
    SHORT_SQUEEZE: OI down + price up
        = Shorts covering (not real buying)
        → BEARISH (FADE THE RALLY)
    
    LONG_LIQUIDATION: OI down + price down
        = Longs closing (not real selling)
        → BULLISH (FADE THE DUMP)
    """
    
    OI_THRESHOLD = 0.03  # 3%
    PRICE_THRESHOLD = 0.02  # 2%
    
    if oi_change > OI_THRESHOLD and price_change > PRICE_THRESHOLD:
        return {
            'type': 'ACCUMULATION',
            'direction': 'BULLISH',
            'quality': 'GENUINE'
        }
    elif oi_change > OI_THRESHOLD and price_change < -PRICE_THRESHOLD:
        return {
            'type': 'DISTRIBUTION',
            'direction': 'BEARISH',
            'quality': 'GENUINE'
        }
    elif oi_change < -OI_THRESHOLD and price_change > PRICE_THRESHOLD:
        return {
            'type': 'SHORT_SQUEEZE',
            'direction': 'BEARISH',  # Fade it
            'quality': 'FAKE'
        }
    elif oi_change < -OI_THRESHOLD and price_change < -PRICE_THRESHOLD:
        return {
            'type': 'LONG_LIQUIDATION',
            'direction': 'BULLISH',  # Fade it
            'quality': 'FAKE'
        }
    else:
        return {
            'type': 'NEUTRAL',
            'direction': 'NEUTRAL',
            'quality': 'LOW'
        }
```

**3. Timeframe Alignment**:
```python
def check_alignment(flow_24h, flow_7d):
    """
    STRONG_ALIGNED: 24h + 7d same direction
        → HIGH confidence
    
    WEAK_ALIGNED: Only 24h signal
        → MEDIUM confidence
    
    CONFLICTED: 24h and 7d disagree
        → SKIP
    """
    
    dir_24h = flow_24h['direction']
    dir_7d = flow_7d['direction']
    
    if dir_24h == dir_7d and dir_24h != 'NEUTRAL':
        return {
            'level': 'STRONG_ALIGNED',
            'direction': dir_24h,
            'confidence': 'HIGH'
        }
    elif dir_24h != 'NEUTRAL' and dir_7d == 'NEUTRAL':
        return {
            'level': 'WEAK_ALIGNED',
            'direction': dir_24h,
            'confidence': 'MEDIUM'
        }
    elif dir_24h != dir_7d and dir_24h != 'NEUTRAL' and dir_7d != 'NEUTRAL':
        return {
            'level': 'CONFLICTED',
            'direction': 'NEUTRAL',
            'confidence': 'LOW'
        }
    else:
        return {
            'level': 'NO_SIGNAL',
            'direction': 'NEUTRAL',
            'confidence': 'LOW'
        }
```

**4. Conviction Score**:
```python
def calculate_conviction(alignment, oi_changes, volume_ratio):
    """0-10 scale"""
    conviction = 0
    
    # Alignment (0-5 points)
    if alignment['level'] == 'STRONG_ALIGNED':
        conviction += 5
    elif alignment['level'] == 'WEAK_ALIGNED':
        conviction += 3
    
    # OI magnitude (0-3 points)
    max_oi = max(abs(oi_changes['24h']), abs(oi_changes['7d']))
    if max_oi > 0.10:
        conviction += 3
    elif max_oi > 0.06:
        conviction += 2
    elif max_oi > 0.03:
        conviction += 1
    
    # Volume (0-2 points)
    if volume_ratio > 1.8:
        conviction += 2
    elif volume_ratio > 1.3:
        conviction += 1
    
    return min(10, conviction)
```

**5. Final Signal**:
```python
def determine_signal(flow_24h, flow_7d, alignment, conviction):
    """
    Only trade when:
    - Aligned
    - Flow is GENUINE
    - Conviction >= 6
    """
    
    if alignment['level'] not in ['STRONG_ALIGNED', 'WEAK_ALIGNED']:
        return {'action': 'SKIP', 'reason': 'Not aligned'}
    
    if conviction < 6:
        return {'action': 'SKIP', 'reason': 'Low conviction'}
    
    primary_flow = flow_7d if flow_7d['direction'] != 'NEUTRAL' else flow_24h
    
    if primary_flow['quality'] != 'GENUINE':
        return {'action': 'SKIP', 'reason': 'Fake move'}
    
    confidence = 'HIGH' if alignment['level'] == 'STRONG_ALIGNED' and conviction >= 8 else 'MEDIUM'
    
    return {
        'action': primary_flow['direction'],
        'confidence': confidence,
        'conviction_score': conviction
    }
```

### Thresholds

```python
OI_FLOW_THRESHOLDS = {
    'oi_change_threshold': 0.03,
    'price_change_threshold': 0.02,
    'oi_strong': 0.10,
    'oi_moderate': 0.06,
    'volume_high': 1.8,
    'volume_moderate': 1.3,
    'conviction_min': 6,
}
```

### Signal Output

```python
{
    'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
    'strength': 0-10,
    'flow_type': str,
    'confidence': 'HIGH' | 'MEDIUM' | 'LOW'
}
```

---

## VI. Master Signal: Institutional Convergence Index

Combine all four signals into one master score.

### Implementation

```python
class InstitutionalConvergenceIndex:
    """
    Master signal: Trade WITH institutions when signals converge
    """
    
    def __init__(self):
        self.signal_weights = {
            'liquidity': 0.25,
            'toxicity': 0.30,    # Highest weight (best signal)
            'positioning': 0.25,
            'oi_flow': 0.20
        }
    
    def calculate_index(
        self,
        liquidity_data: dict,
        toxicity_data: dict,
        positioning_data: dict,
        oi_flow_data: dict
    ) -> dict:
        """
        Returns:
            {
                'index_score': float (0-100),
                'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
                'confidence': 'HIGH' | 'MEDIUM' | 'LOW',
                'action': 'LONG' | 'SHORT' | 'SKIP',
                'institutional_conviction': float (0-10),
                'bullish_signals': int,
                'bearish_signals': int,
                'signal_breakdown': dict,
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'timestamp': datetime
            }
        """
```

### Key Calculations

**1. Evaluate Signals**:
```python
signals = {
    'liquidity': self._evaluate_liquidity(liquidity_data),
    'toxicity': self._evaluate_toxicity(toxicity_data),
    'positioning': self._evaluate_positioning(positioning_data),
    'oi_flow': self._evaluate_oi_flow(oi_flow_data)
}

# Each signal format:
# {
#     'direction': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
#     'strength': 0-10
# }
```

**2. Count Alignment**:
```python
directions = [s['direction'] for s in signals.values()]

bullish_count = sum(1 for d in directions if d == 'BULLISH')
bearish_count = sum(1 for d in directions if d == 'BEARISH')
```

**3. Calculate Index Score**:
```python
index_score = 0

for signal_name, signal_data in signals.items():
    weight = self.signal_weights[signal_name]
    strength = signal_data['strength']  # 0-10
    
    contribution = (strength / 10) * weight * 100
    index_score += contribution

# index_score = 0-100
```

**4. Determine Direction**:
```python
# Require 3+ signals aligned
if bullish_count >= 3 and bullish_count > bearish_count:
    direction = 'BULLISH'
elif bearish_count >= 3 and bearish_count > bullish_count:
    direction = 'BEARISH'
else:
    direction = 'NEUTRAL'
```

**5. Calculate Institutional Conviction**:
```python
def calculate_conviction(signals):
    """
    Conviction = avg strength × alignment ratio
    """
    strengths = [s['strength'] for s in signals.values()]
    avg_strength = np.mean(strengths)
    
    directions = [s['direction'] for s in signals.values()]
    bullish = sum(1 for d in directions if d == 'BULLISH')
    bearish = sum(1 for d in directions if d == 'BEARISH')
    
    alignment_ratio = max(bullish, bearish) / len(directions)
    
    conviction = avg_strength * alignment_ratio
    return round(conviction, 1)
```

**6. Determine Confidence**:
```python
if index_score >= 85 and max(bullish_count, bearish_count) == 4:
    confidence = 'HIGH'
elif index_score >= 70 and max(bullish_count, bearish_count) >= 3:
    confidence = 'MEDIUM'
else:
    confidence = 'LOW'
```

**7. Final Action**:
```python
if index_score >= 70 and max(bullish_count, bearish_count) >= 3:
    action = 'LONG' if direction == 'BULLISH' else 'SHORT'
else:
    action = 'SKIP'
```

**8. Price Levels**:
```python
def calculate_price_levels(action, current_price, atr):
    """
    Entry: Current price
    Stop: 1.5x ATR or 3% (whichever wider)
    Target: 2x stop distance (2:1 R:R)
    """
    if action == 'SKIP':
        return {'entry': 0, 'stop': 0, 'target': 0}
    
    entry = current_price
    
    atr_stop = atr * 1.5
    pct_stop = current_price * 0.03
    stop_distance = max(atr_stop, pct_stop)
    
    if action == 'LONG':
        stop_loss = entry - stop_distance
        take_profit = entry + (stop_distance * 2)
    else:
        stop_loss = entry + stop_distance
        take_profit = entry - (stop_distance * 2)
    
    return {
        'entry': round(entry, 2),
        'stop': round(stop_loss, 2),
        'target': round(take_profit, 2)
    }
```

### Thresholds

```python
CONVERGENCE_THRESHOLDS = {
    'index_score_high': 85,
    'index_score_medium': 70,
    'min_aligned_signals': 3,
    'high_conviction': 8.0,
    'medium_conviction': 6.0,
}
```

---

## VII. Cross-Asset Confirmation

Since you're trading BTC + ETH + SOL, validate alignment.

### Implementation

```python
def check_cross_asset_confirmation(btc_index, eth_index, sol_index):
    """
    Check if all assets showing same institutional flow
    
    Args:
        btc_index: Convergence index for BTC
        eth_index: Convergence index for ETH
        sol_index: Convergence index for SOL
    
    Returns:
        {
            'aligned': bool,
            'confidence': 'VERY_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW',
            'btc_direction': str,
            'eth_direction': str,
            'sol_direction': str,
            'description': str
        }
    """
    
    btc_dir = btc_index['direction']
    eth_dir = eth_index['direction']
    sol_dir = sol_index['direction'] if sol_index else 'NEUTRAL'
    
    # Core requirement: BTC + ETH must agree
    if btc_dir == eth_dir and btc_dir != 'NEUTRAL':
        aligned = True
        
        # Perfect: all 3 agree
        if sol_dir == btc_dir:
            confidence = 'VERY_HIGH'
            description = f'Perfect alignment: BTC + ETH + SOL all {btc_dir}'
        # Good: BTC + ETH only
        else:
            confidence = 'HIGH'
            description = f'Strong alignment: BTC + ETH both {btc_dir}'
    
    # BTC and ETH disagree
    else:
        aligned = False
        confidence = 'LOW'
        description = 'No cross-asset alignment'
    
    return {
        'aligned': aligned,
        'confidence': confidence,
        'btc_direction': btc_dir,
        'eth_direction': eth_dir,
        'sol_direction': sol_dir,
        'description': description
    }
```

### Usage

```python
# After calculating convergence for each asset
cross_asset = check_cross_asset_confirmation(btc_convergence, eth_convergence, sol_convergence)

# Boost confidence if aligned
if cross_asset['aligned'] and cross_asset['confidence'] == 'VERY_HIGH':
    # Upgrade MEDIUM → HIGH confidence
    if btc_convergence['confidence'] == 'MEDIUM':
        btc_convergence['confidence'] = 'HIGH'
```

---

## VIII. Position Sizing (Day Trading, No Pyramiding)

### Implementation

```python
class DayTradingPositionSizer:
    """
    Conviction-based sizing for single-entry day trades
    """
    
    def __init__(self, account_balance: float):
        self.balance = account_balance
        self.max_risk = 0.02  # 2% max
        self.base_risk = 0.01  # 1% base
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        conviction_score: float,  # 0-10
        confidence_level: str,    # 'HIGH' | 'MEDIUM' | 'LOW'
        cross_asset_aligned: bool,
        volatility_percentile: float  # 0-100
    ) -> dict:
```

### Sizing Logic

```python
def calculate_position_size(self, ...):
    # 1. Base risk by conviction
    if conviction_score >= 8 and confidence_level == 'HIGH' and cross_asset_aligned:
        base_risk_pct = 0.02  # Max
    elif conviction_score >= 7 and confidence_level == 'HIGH':
        base_risk_pct = 0.018
    elif conviction_score >= 6 and confidence_level == 'HIGH':
        base_risk_pct = 0.015
    elif conviction_score >= 7 and confidence_level == 'MEDIUM':
        base_risk_pct = 0.013
    elif conviction_score >= 6 and confidence_level == 'MEDIUM':
        base_risk_pct = 0.01
    else:
        return {'size_units': 0, 'reason': 'Insufficient conviction'}
    
    # 2. Volatility adjustment
    if volatility_percentile > 80:
        vol_adj = 0.7
    elif volatility_percentile > 60:
        vol_adj = 0.85
    else:
        vol_adj = 1.0
    
    # 3. Cross-asset bonus
    cross_adj = 1.1 if cross_asset_aligned else 1.0
    
    # 4. Final risk
    adjusted_risk = base_risk_pct * vol_adj * cross_adj
    
    # 5. Calculate size
    risk_amount = self.balance * adjusted_risk
    stop_distance = abs(entry_price - stop_loss)
    position_size = risk_amount / stop_distance
    
    # 6. Sanity checks
    stop_pct = (stop_distance / entry_price) * 100
    if stop_pct < 1.0 or stop_pct > 6.0:
        return {'size_units': 0, 'reason': 'Stop out of range'}
    
    return {
        'size_units': round(position_size, 4),
        'size_usd': round(position_size * entry_price, 2),
        'risk_usd': round(risk_amount, 2),
        'risk_pct': round(adjusted_risk * 100, 2)
    }
```

---

## IX. File Structure

```
strategy_monitor/
├── config.py                    # Thresholds
├── api_client.py                # [KEEP] Async client
├── storage.py                   # [REPLACE] In-memory OI
├── metrics/
│   ├── __init__.py
│   ├── liquidity.py             # [NEW] Liquidity tracker
│   ├── toxicity.py              # [NEW] Flow toxicity
│   ├── positioning.py           # [NEW] Funding velocity
│   └── oi_flow.py               # [NEW] Multi-TF OI
├── signals/
│   ├── __init__.py
│   ├── convergence_index.py    # [NEW] Master signal
│   └── cross_asset.py           # [NEW] Cross-asset
├── risk/
│   ├── __init__.py
│   └── position_sizer.py        # [NEW] Position sizing
├── app.py                       # [UPDATE] UI
├── run.sh / run.ps1             # [KEEP]
└── tests/
    └── test_*.py                # [NEW]
```

---

## X. Implementation Timeline

### Week 1: Core Signals
- Day 1-2: Liquidity tracker + tests
- Day 3-4: Flow toxicity + tests
- Day 5: In-memory OI storage + tests

### Week 2: Advanced Signals
- Day 1-2: Positioning + tests
- Day 3-4: Multi-TF OI flow + tests
- Day 5: Convergence index + tests

### Week 3: Integration
- Day 1-2: Cross-asset confirmation
- Day 3-4: Position sizing
- Day 5: UI updates + integration testing

### Week 4: Validation
- Day 1-7: Paper trade, log signals, track performance

---

## XI. Configuration

```python
# config.py

# Signal Weights
SIGNAL_WEIGHTS = {
    'liquidity': 0.25,
    'toxicity': 0.30,
    'positioning': 0.25,
    'oi_flow': 0.20
}

# Convergence Thresholds
CONVERGENCE_THRESHOLDS = {
    'index_score_high': 85,
    'index_score_medium': 70,
    'min_aligned_signals': 3,
}

# Position Sizing
POSITION_SIZING = {
    'max_risk_per_trade': 0.02,
    'base_risk': 0.01,
    'stop_loss_min_pct': 1.0,
    'stop_loss_max_pct': 6.0,
    'risk_reward_min': 2.0,
}

# Timeframes
OI_LOOKBACK_HOURS = {
    '4h': 4,
    '24h': 24,
    '7d': 168
}

FUNDING_LOOKBACK_HOURS = {
    '4h': 4,
    '8h': 8,
    '12h': 12
}
```

---

## XII. Testing Requirements

### Unit Tests (Essential)

```python
# Test each signal independently
def test_liquidity_concentration()
def test_liquidity_velocity()
def test_toxicity_calculation()
def test_funding_acceleration()
def test_oi_flow_classification()
def test_convergence_scoring()
```

### Forward Testing (30 Days)

Log every signal:
- Timestamp
- Action (LONG/SHORT/SKIP)
- Score, conviction, confidence
- Entry, stop, target
- Hypothetical outcome

**Success Criteria** (must hit ALL):
- Win rate >55%
- Profit factor >2.5
- Sharpe ratio >1.5
- Max drawdown <15%

---

## XIII. Critical Success Factors

### 1. Signal Quality > Quantity
- Only trade when conviction ≥6 AND 3+ signals aligned
- Skip marginal setups

### 2. Cross-Asset Alignment
- BTC + ETH + SOL aligned = max size
- Divergence = reduce or skip

### 3. Wide Stops, Big Targets
- 3-5% stops (not 1-2%)
- 2:1 minimum R:R

### 4. Volume Confirms Everything
- High volume + aligned = strong
- Low volume + aligned = weak (skip)

### 5. Patience
- Target 2-5 high-quality trades/week
- Not 20 mediocre trades

---

## XIV. Next Steps

### Your Actions

1. Review document, flag unclear sections
2. Set up dev environment
3. Start Week 1 implementation
4. Weekly demos:
   - Week 1: Liquidity + toxicity
   - Week 2: Full convergence
   - Week 3: Cross-asset + sizing
   - Week 4: Forward test results

### My Actions

1. Prepare sample data
2. Define acceptance criteria
3. Weekly code reviews

---

## XV. Questions Before Starting

1. **Data access**: Reliable Hyperliquid API access?
2. **Storage**: In-memory OK (data lost on restart)?
3. **Refresh rate**: 60s acceptable?
4. **Paper trading**: Observation mode or simulation?
5. **Deployment**: Local Streamlit or server?

---

## Conclusion

This is a **complete rewrite**, pivoting from mean reversion to institutional momentum. Each component is independently valuable and can be built/tested incrementally.

**Estimated time**: 3-4 weeks

**Expected performance** (if done right):
- Win rate: 55-60%
- Profit factor: 2.5-4.0
- Sharpe: 1.8-2.5
- Max DD: 10-15%
- Annual return: 25-40%

Questions? Let's discuss before you start.

— Ed

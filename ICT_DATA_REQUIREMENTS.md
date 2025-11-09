# ICT/SMC Data Requirements Specification

**Purpose**: Define exactly what candle data is needed from Hyperliquid for ICT/SMC strategy implementation.

---

## Overview

The ICT/SMC strategy requires multi-timeframe analysis across 5-6 timeframes simultaneously. Unlike the old quantitative approach (which primarily used single-timeframe metrics), ICT requires **hierarchical structure alignment** across weekly → daily → 4H → 1H → 5M.

---

## Timeframe Hierarchy

### Primary Timeframes (REQUIRED)

| Timeframe | Purpose | Candles Needed | Max Lookback |
|-----------|---------|----------------|--------------|
| **1d (Daily)** | HTF bias confirmation | 20-30 | 30 days |
| **4h (4-Hour)** | HTF bias confirmation | 30-50 | 14 days |
| **1h (1-Hour)** | Dealing range identification | 50-100 | 4-7 days |
| **5m (5-Minute)** | Entry execution (FVG detection) | 100-150 | 12 hours |

### Optional Timeframes

| Timeframe | Purpose | Candles Needed | Max Lookback |
|-----------|---------|----------------|--------------|
| **1w (Weekly)** | Overall market bias | 10-20 | 6 months |

---

## Data Fields Required

### Per Candle (OHLCV)

```json
{
  "t": 1699488000000,     // Timestamp (milliseconds) - REQUIRED
  "o": "65432.10",        // Open price - REQUIRED
  "h": "65892.50",        // High price - REQUIRED
  "l": "65123.00",        // Low price - REQUIRED
  "c": "65678.90",        // Close price - REQUIRED
  "v": "1234567.89"       // Volume - OPTIONAL (used for confluence only)
}
```

**Note**: Volume is optional for ICT/SMC core logic (structure doesn't require volume), but useful for IE confluence tools.

---

## Use Cases by Analysis Type

### 1. HTF Alignment Check

**Objective**: Determine if Weekly/Daily/4H/1H all show the same structure (bullish or bearish).

**Process**:
1. Fetch last 30 candles for Daily
2. Fetch last 50 candles for 4H
3. Fetch last 100 candles for 1H
4. For each timeframe, detect swing highs/lows
5. Determine structure: HH/HL (bullish) vs LL/LH (bearish)
6. Compare across timeframes → aligned or conflicting?

**Data Needed**:
- Daily: 30 candles (~30 days of history)
- 4H: 50 candles (~8 days of history)
- 1H: 100 candles (~4 days of history)
- **Total**: 180 candles across 3 timeframes

---

### 2. Dealing Range Identification

**Objective**: Identify the current price range defined by:
- **Range Low**: Most recent swing low that grabbed liquidity (swept PDL, session low, or swing low)
- **Range High**: Most recent swing high that grabbed liquidity (swept PDH, session high, or swing high)

**Process**:
1. Fetch last 100 candles on 1H (or 4H for swing trades)
2. Detect swing highs and swing lows
3. Identify which swings grabbed liquidity (exceeded previous highs/lows)
4. Calculate range: High - Low
5. Calculate 50% midpoint
6. Determine if current price is in discount (<50%) or premium (>50%)

**Data Needed**:
- 1H: 100 candles (~4 days of history)
- 4H: 50 candles (~8 days, if using 4H for dealing range)
- **Total**: 100 candles (single timeframe)

---

### 3. Liquidity Pool Tracking

**Objective**: Identify key liquidity levels price is likely to target:
- Previous Day High (PDH) / Previous Day Low (PDL)
- Session Highs/Lows (Asian, London, NY)
- Equal Highs/Equal Lows
- Round numbers

**Process**:
1. Fetch last 48 hours of 1H candles (48 candles)
2. Identify previous day's high and low
3. Identify session boundaries based on UTC time
4. Track session highs/lows
5. Detect equal highs/lows (2+ swing highs/lows at same price level)

**Data Needed**:
- 1H: 48 candles (2 days of history for PDH/PDL)
- **Total**: 48 candles

---

### 4. Entry Execution (FVG Detection)

**Objective**: Identify Fair Value Gaps on 5M chart for precise entry within discount/premium zones.

**Process**:
1. Fetch last 150 candles on 5M (~12 hours)
2. Detect FVGs (3-candle pattern where wicks don't overlap)
3. Identify bullish FVGs (for long entries) or bearish FVGs (for short entries)
4. Check if current price is within an FVG zone
5. Use FVG boundaries as entry limits

**Data Needed**:
- 5M: 150 candles (~12 hours of history)
- **Total**: 150 candles

---

### 5. BOS/CHoCH Detection (Invalidation Signals)

**Objective**: Detect Break of Structure (trend continuation) or Change of Character (trend reversal).

**Process**:
1. Use same 1H candles from HTF alignment (already fetched)
2. Identify most recent swing high (for bearish structure) or swing low (for bullish structure)
3. Monitor for price breaking that level
4. **BOS**: Break in direction of trend (bullish breaks swing high, bearish breaks swing low)
5. **CHoCH**: Break against trend (bullish breaks swing low, bearish breaks swing high)

**Data Needed**:
- 1H: 100 candles (reuse from HTF alignment)
- **Total**: 0 additional candles (reuse existing data)

---

## Batch Fetching Strategy

### Problem
Making 4-5 separate API calls for each analysis is inefficient and slow.

### Solution: Multi-Timeframe Batch Fetch

**Function**: `fetch_multi_timeframe_candles(coin, timeframes_config)`

**Example**:
```python
config = {
    "1d": {"hours": 720, "limit": 30},    # 30 days
    "4h": {"hours": 192, "limit": 50},    # 8 days
    "1h": {"hours": 100, "limit": 100},   # 4 days
    "5m": {"hours": 12, "limit": 150},    # 12 hours
}

result = fetch_multi_timeframe_candles("BTC", config)
# Returns: {
#   "1d": [candle1, candle2, ...],
#   "4h": [candle1, candle2, ...],
#   "1h": [candle1, candle2, ...],
#   "5m": [candle1, candle2, ...],
# }
```

**Benefits**:
- Single function call instead of 4-5 separate calls
- Parallel or sequential fetching (configurable)
- Cached results for repeated use in same analysis session

---

## Data Processing Pipeline

### Step 1: Fetch Raw Candles
```
fetch_multi_timeframe_candles("BTC", config)
  ↓
{
  "1d": [raw candles],
  "4h": [raw candles],
  "1h": [raw candles],
  "5m": [raw candles]
}
```

### Step 2: Parse & Standardize
```
parse_raw_keep_ohlc(candles)
  ↓
[
  {"t": 1699488000000, "o": "65432.10", "h": "65892.50", "l": "65123.00", "c": "65678.90", "v": "123.45"},
  ...
]
```

### Step 3: Detect Swings (per timeframe)
```
detect_swing_highs_lows(candles)
  ↓
{
  "swing_highs": [{index: 5, price: 65892.50, timestamp: 1699488000000}, ...],
  "swing_lows": [{index: 12, price: 65123.00, timestamp: 1699491600000}, ...]
}
```

### Step 4: Determine Structure (per timeframe)
```
determine_structure_bias(swing_highs, swing_lows)
  ↓
{
  "bias": "BULLISH",  // or "BEARISH" or "NEUTRAL"
  "pattern": "HH/HL",
  "last_bos": {"type": "bullish", "price": 65892.50, "timestamp": 1699488000000}
}
```

### Step 5: Calculate Dealing Range (1H or 4H)
```
calculate_dealing_range(candles, swings)
  ↓
{
  "range_low": 66000.00,
  "range_high": 68000.00,
  "midpoint": 67000.00,
  "current_price": 66200.00,
  "percent_in_range": 0.10,  // 10% of range (deep discount)
  "zone": "discount"  // or "premium" or "mid-range"
}
```

### Step 6: Detect FVGs (5M)
```
detect_fvgs(candles_5m)
  ↓
[
  {"type": "bullish", "top": 66250.00, "bottom": 66150.00, "size": 100.00, "index": 42},
  ...
]
```

### Step 7: Check IE Confluence
```
get_ie_confluence(coin, entry_zone, direction)
  ↓
{
  "liquidation_grab": true,      // +25 points
  "order_book_aligned": true,    // +20 points
  "trade_flow_aligned": true,    // +20 points
  "oi_divergence": false,        // +0 points
  "funding_extreme": false,      // +0 points
  "total_score": 65,
  "grade": "A"
}
```

### Step 8: Final Setup Validation
```
validate_ict_setup(htf_data, dealing_range, fvgs, ie_confluence)
  ↓
{
  "valid": true,
  "direction": "LONG",
  "entry_zone": {"min": 66150.00, "max": 66250.00},
  "stop_loss": 64400.00,
  "target_1": 68000.00,
  "risk_reward": "1:1",
  "grade": "A",
  "confluence_score": 65,
  "position_size_pct": 1.0
}
```

---

## Performance Considerations

### Candle Fetching

**Best Case** (all timeframes cached):
- Fetch time: ~0ms (instant from cache)
- Processing time: ~50-100ms (swing detection + structure analysis)
- **Total**: ~50-100ms

**Worst Case** (cold start, all API calls):
- Fetch time: ~3-5 seconds (4-5 sequential API calls @ ~1 sec each)
- Processing time: ~50-100ms
- **Total**: ~3-5 seconds

**Optimized** (batch fetch with parallel requests):
- Fetch time: ~1-2 seconds (parallel API calls)
- Processing time: ~50-100ms
- **Total**: ~1-2 seconds

### Caching Strategy

**Cache TTL by Timeframe**:
- 1w (Weekly): 1 hour cache (data rarely changes)
- 1d (Daily): 15 minutes cache
- 4h (4-Hour): 5 minutes cache
- 1h (1-Hour): 2 minutes cache
- 5m (5-Minute): 30 seconds cache

**Benefit**: Repeated analysis within cache window = instant results

---

## Edge Cases & Handling

### 1. Insufficient Candle History
**Problem**: New coin listing, less than 100 candles available.
**Solution**: Skip trade (cannot determine structure with <50 candles).

### 2. API Rate Limiting
**Problem**: Hyperliquid rate limits excessive requests.
**Solution**: Implement exponential backoff, respect cache TTLs.

### 3. Malformed Candle Data
**Problem**: API returns incomplete candles (missing OHLC).
**Solution**: Filter out malformed candles, log warning, continue with valid data.

### 4. Timeframe Misalignment During High Volatility
**Problem**: Weekly bullish, Daily bearish (conflict).
**Solution**: Skip trade (HTF alignment required, no exceptions).

---

## Summary: Data Footprint

**Per Full Analysis** (HTF alignment + dealing range + entry):
- Weekly: 10 candles (optional)
- Daily: 30 candles
- 4H: 50 candles
- 1H: 100 candles
- 5M: 150 candles
- **Total**: ~340 candles across 5 timeframes

**Estimated API Calls**: 4-5 calls per full analysis (without caching)

**Estimated Response Time**: 1-5 seconds (depending on caching and parallelization)

---

## Implementation Checklist

- [ ] Implement `fetch_multi_timeframe_candles()` in `tool_fetch_hl_raw.py`
- [ ] Add caching per timeframe with appropriate TTLs
- [ ] Test batch fetching with BTC, ETH, SOL
- [ ] Verify all intervals return expected candle counts
- [ ] Measure actual response times (cold vs cached)
- [ ] Document any API quirks or limitations discovered

---

**Status**: Ready for implementation in Phase 2.

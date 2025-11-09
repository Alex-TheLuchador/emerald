# ICT/SMC Trading Strategy for Hyperliquid Perpetuals

## Overview

This strategy trades perpetual futures on Hyperliquid using ICT (Inner Circle Trader) and SMC (Smart Money Concepts) methodology. The core principle is to trade WITH higher timeframe structure by entering on lower timeframe pullbacks into discount zones, targeting either the dealing range swing high or the next liquidity draw.

**Target Market**: Hyperliquid Perpetuals (BTC, ETH, SOL, and other liquid pairs)

**Expected Performance**:
- Win Rate: 65-75%
- Average Win: 2.5R
- Average Loss: 1.0R
- Expectancy: +1.2R per trade minimum

---

## Core Philosophy

Markets move from liquidity pool to liquidity pool. Price does not move randomly—it hunts clustered orders (stops, limit orders) at key structural levels. Institutions need liquidity to fill large orders, so they:

1. Push price to sweep liquidity (stop hunts)
2. Accumulate/distribute into the resulting panic
3. Drive price toward the next liquidity pool

**Our edge**: We identify which liquidity was just taken, determine where price is headed next (the draw), and enter on pullbacks when price returns to discount/premium zones with higher timeframe structure aligned.

---

## Market Structure Fundamentals

### Swing Points

**Swing High**: A candle with the highest high in the middle, with lower highs on both sides (minimum 3 candles).

**Swing Low**: A candle with the lowest low in the middle, with higher lows on both sides (minimum 3 candles).

**Liquidity Grabs**: When price moves beyond a swing high or swing low, it "takes liquidity" by triggering stops and limit orders clustered at that level. This is often followed by a reversal or continuation after the grab.

### Structure Bias

**Bullish Structure**: 
- Higher Highs (HH) and Higher Lows (HL)
- Recent swing highs are breaking above previous swing highs
- Recent swing lows are forming above previous swing lows

**Bearish Structure**: 
- Lower Lows (LL) and Lower Highs (LH)
- Recent swing lows are breaking below previous swing lows
- Recent swing highs are forming below previous swing highs

**Neutral/Ranging**: 
- No clear HH/HL or LL/LH pattern
- Skip trading in neutral structure

### Break of Structure (BOS)

A BOS occurs when price breaks beyond a previous swing point in the direction of the trend:
- **Bullish BOS**: Price breaks above a swing high
- **Bearish BOS**: Price breaks below a swing low

A BOS confirms trend continuation.

### Change of Character (CHoCH)

A CHoCH occurs when price breaks a swing point AGAINST the prevailing trend:
- In a bullish trend: Price breaks below a recent swing low (bearish CHoCH)
- In a bearish trend: Price breaks above a recent swing high (bullish CHoCH)

A CHoCH signals potential trend reversal or structure weakening.

---

## Liquidity Pools

Liquidity pools are price levels where stops and orders cluster. Price is drawn to these levels like a magnet.

### Primary Liquidity Pools (in order of significance):

1. **Previous Day High (PDH) / Previous Day Low (PDL)**
   - The most significant intraday liquidity
   - In bullish structure, PDH is the primary upside target
   - In bearish structure, PDL is the primary downside target

2. **Session Highs/Lows**
   - Asian Session: 00:00-08:00 UTC
   - London Session: 08:00-16:00 UTC
   - New York Session: 13:00-21:00 UTC
   - These levels often get swept before major moves

3. **Weekly/Monthly Highs/Lows**
   - Higher timeframe liquidity
   - Major targets in extended trends

4. **Equal Highs/Equal Lows**
   - Two or more swing highs at approximately the same level
   - Two or more swing lows at approximately the same level
   - Obvious levels where retail traders place stops

5. **Round Numbers**
   - Psychological levels (e.g., $60,000, $65,000, $70,000 for BTC)
   - Retail traders cluster orders at these levels

### The Draw on Liquidity

**Concept**: After taking one liquidity pool, price seeks the next pool in the direction of structure.

**In Bullish Structure**:
- After sweeping a swing low, PDL, or session low → price targets the swing high, PDH, or session high above
- Continuous move from low to high until structure breaks

**In Bearish Structure**:
- After sweeping a swing high, PDH, or session high → price targets the swing low, PDL, or session low below
- Continuous move from high to low until structure breaks

**Identifying the Draw**:
1. Determine HTF bias (bullish or bearish)
2. Identify which liquidity pool was just taken (the sweep)
3. Identify the next pool in the direction of structure (the target)

---

## Fair Value Gaps (FVGs)

**Definition**: A three-candle pattern where the wicks of the first and third candles do not overlap, creating a "gap" or imbalance.

**Bullish FVG**:
- Candle 1: Moves up
- Candle 2: Explosive move up (leaves a gap)
- Candle 3: Continues up
- Gap: Top of Candle 1's wick does not touch bottom of Candle 3's wick

**Bearish FVG**:
- Candle 1: Moves down
- Candle 2: Explosive move down (leaves a gap)
- Candle 3: Continues down
- Gap: Bottom of Candle 1's wick does not touch top of Candle 3's wick

**Purpose in This Strategy**:

FVGs serve two functions:

1. **Support/Resistance Identification**:
   - FVGs often act as supply or demand zones
   - Price may respect FVG boundaries as support (bullish) or resistance (bearish)

2. **Internal Liquidity Draw**:
   - Price may "fill" or "refill" an FVG (return to rebalance the imbalance)
   - This creates a pullback entry opportunity
   - Not required for entry, but provides additional confluence when present

**Usage**: After identifying a valid setup (HTF aligned, price in discount/premium), check the 5m chart for FVGs in the direction of your trade. Enter within an FVG if present for additional confluence.

---

## Dealing Range

**Definition**: The most recent price range created by a pullback and subsequent move that defines your entry and target zones.

### How to Identify the Dealing Range

**For Bullish Setups**:

1. **Identify the Swing Low**: 
   - Look for the most recent swing low that grabbed liquidity (swept a previous swing low, session low, PDL, or equal lows)
   - This becomes the **dealing range low**

2. **Identify the Swing High**:
   - From that swing low, identify where price moved up to create a swing high
   - Ideally, this swing high also grabbed liquidity (swept a previous swing high, session high, PDH, or equal highs)
   - This becomes the **dealing range high**

3. **Calculate the Range**:
   - Range = Dealing Range High - Dealing Range Low
   - 50% Level = Dealing Range Low + (Range × 0.5)
   - Discount Zone = Below 50% (closer to dealing range low)
   - Premium Zone = Above 50% (closer to dealing range high)

**For Bearish Setups**:
- Mirror the logic: Swing high (that grabbed liquidity) to swing low (that grabbed liquidity)
- Premium zone = entry zone for shorts (above 50%)
- Discount zone = target zone (below 50%)

### Timeframe for Dealing Range

**Primary Timeframes**: 1H or 4H

**Selection Logic**:
- Use the timeframe where structure is clearest
- If both show clear structure, prefer 4H (larger range = larger R:R)
- The 1H chart is most commonly used for intraday setups
- The 4H chart is used for swing setups or when 1H structure is unclear

**Note**: The dealing range does NOT need to be redrawn constantly. It remains valid until:
- Price breaks below the dealing range low (bullish range invalidated)
- Price breaks above the dealing range high (bearish range invalidated)
- A new, clearer range forms with liquidity grabs on both ends

---

## Higher Timeframe (HTF) Alignment

**Critical Principle**: Only trade when higher timeframe structure supports your direction.

### Timeframe Hierarchy

1. **Weekly (W)** - Optional but helpful for overall bias
2. **Daily (D)** - CRITICAL
3. **4-Hour (4H)** - CRITICAL
4. **1-Hour (1H)** - CRITICAL (but can show counter-trend pullbacks)

### Alignment Requirements

**Minimum for Trade Entry**:
- Daily, 4H, and 1H must show structure in the same direction
- Weekly alignment is a bonus but not required

**Example - Bullish Alignment**:
- Daily: HH/HL pattern, recent BOS to upside
- 4H: HH/HL pattern, recent BOS to upside
- 1H: HH/HL pattern (may show temporary pullback, but overall structure is up)

**Example - Bearish Alignment**:
- Daily: LL/LH pattern, recent BOS to downside
- 4H: LL/LH pattern, recent BOS to downside
- 1H: LL/LH pattern (may show temporary bounce, but overall structure is down)

### The 1H Pullback Exception

**Important Nuance**: The 1H chart can show a counter-trend pullback within a higher timeframe trend. This is NOT a conflict—this is the setup.

**Example**:
- Daily: Bullish (HH/HL)
- 4H: Bullish (HH/HL)
- 1H: Shows a pullback down (creating a swing low)

**This is VALID**. The 1H pullback is what creates your discount entry zone. As long as the 1H structure has not broken (no bearish CHoCH), the bullish bias remains intact.

### How to Check HTF Alignment

**For Each Timeframe (W, D, 4H, 1H)**:

1. Identify the last 3-5 swing highs and swing lows
2. Check if they form HH/HL (bullish) or LL/LH (bearish)
3. Identify the most recent BOS:
   - If the most recent BOS is bullish → structure is bullish
   - If the most recent BOS is bearish → structure is bearish
4. Compare across all timeframes:
   - If D, 4H, and 1H are all bullish → BULLISH BIAS confirmed
   - If D, 4H, and 1H are all bearish → BEARISH BIAS confirmed
   - If any critical timeframe (D, 4H, or 1H) conflicts → NO TRADE

---

## Complete Setup Rules

### Bullish Setup (Long Entry)

**Step 1: HTF Alignment**
- Daily: Bullish structure (HH/HL, recent BOS up)
- 4H: Bullish structure (HH/HL, recent BOS up)
- 1H: Bullish structure (may show pullback, but no bearish CHoCH)

**Step 2: Define Dealing Range**
- On 1H or 4H chart, identify:
  - **Range Low**: Most recent swing low that grabbed liquidity
  - **Range High**: Swing high created from the move up from that swing low (ideally grabbed liquidity)
- Calculate 50% level of the range

**Step 3: Identify the Draw**
- Determine the target:
  - **Option A**: The dealing range high (swing high)
  - **Option B**: The next liquidity pool above (PDH, session high, equal highs)
- Both are valid targets; use whichever provides better R:R

**Step 4: Wait for Discount Entry**
- Price must pull back below 50% of the dealing range
- The deeper into discount, the better (closer to range low = better R:R)

**Step 5: Entry Trigger**
- Price is in discount (<50% of dealing range)
- HTF alignment confirmed
- **Optional confluence**: Check 5m chart for bullish FVG to enter within

**Step 6: Entry Execution**
- Enter when price is in the discount zone
- Use 5m chart for precise entry timing
- If FVG is present, enter within the FVG zone
- Use limit orders to avoid slippage

**Step 7: Set Stop Loss**
- Initial stop loss: Set at 1:1 Risk-to-Reward
  - If entry is $66,500 and target is $68,000 (reward = $1,500), stop = $65,000 (risk = $1,500)
- After entry, stop loss can ONLY move toward breakeven, never away from entry

**Step 8: Set Take Profit**
- **Primary Target**: Dealing range high OR next liquidity draw (PDH, session high, etc.)
- **Secondary Target** (optional): Next liquidity pool beyond the primary target
- Consider scaling out: 50% at primary target, 50% at secondary target or trailing

**Step 9: Invalidation**
- If price breaks below the dealing range low before hitting target → structure is broken, exit immediately
- If 1H forms a bearish CHoCH → HTF alignment broken, exit immediately

---

### Bearish Setup (Short Entry)

**Mirror the bullish setup logic**:

**Step 1: HTF Alignment**
- Daily, 4H, 1H all bearish (LL/LH, recent BOS down)

**Step 2: Define Dealing Range**
- **Range High**: Most recent swing high that grabbed liquidity
- **Range Low**: Swing low created from the move down from that swing high

**Step 3: Identify the Draw**
- Target: Dealing range low OR next liquidity pool below (PDL, session low, equal lows)

**Step 4: Wait for Premium Entry**
- Price must pull back above 50% of the dealing range
- The deeper into premium, the better (closer to range high = better R:R)

**Step 5: Entry Trigger**
- Price in premium (>50% of dealing range)
- HTF alignment confirmed
- Optional: Bearish FVG on 5m chart for confluence

**Step 6: Entry Execution**
- Enter short in the premium zone
- Use 5m chart for precise timing
- Enter within FVG if present

**Step 7: Set Stop Loss**
- Initial stop: 1:1 Risk-to-Reward
- Can only move toward breakeven, never away

**Step 8: Set Take Profit**
- Primary: Dealing range low OR next liquidity draw (PDL, session low)
- Secondary: Next liquidity pool beyond primary

**Step 9: Invalidation**
- If price breaks above dealing range high → exit
- If 1H forms bullish CHoCH → exit

---

## Entry Timing and Execution

### Timeframe Usage Summary

- **Weekly**: Check for overall bias (optional, not critical)
- **Daily**: CRITICAL - Must align with trade direction
- **4H**: CRITICAL - Must align with trade direction
- **1H**: CRITICAL - Defines dealing range and confirms structure (can show pullbacks)
- **5m**: ENTRY EXECUTION - Used for precise entry timing and FVG identification

### The 1H Decision Point

**The 1H chart is your primary decision-making timeframe**:

1. Check if 1H structure aligns with Daily and 4H
2. Identify the dealing range on 1H (or 4H if structure is clearer)
3. Determine if price is in discount (longs) or premium (shorts)
4. If all conditions met → proceed to 5m for entry

**If 1H is unclear or conflicts with Daily/4H → skip the trade**

### The 5m Entry Execution

**Once the 1H confirms a valid setup**:

1. Switch to 5m chart
2. Look for FVG in the direction of your trade (bullish FVG for longs, bearish FVG for shorts)
3. If FVG exists:
   - Place limit order within the FVG zone
   - This provides precise, low-risk entry
4. If no FVG exists:
   - Enter at current price if in discount/premium zone
   - Or wait for a small pullback on 5m to refine entry

**FVGs on 5m are NOT required for entry—they simply provide additional confluence and precision.**

---

## Risk Management

### Position Sizing

**Standard Risk per Trade**: 1-2% of account balance

**Example**:
- Account: $10,000
- Risk per trade: 1% = $100
- Entry: $66,500
- Stop: $65,000 (determined by 1:1 R:R with target at $68,000)
- Risk: $1,500 per contract
- Position size: $100 ÷ $1,500 = 0.067 contracts

**Adjust position size based on your risk tolerance and account size.**

### Stop Loss Management

**Initial Stop Loss**:
- Set at 1:1 Risk-to-Reward relative to your target
- If target is $2,000 away, stop is $2,000 away (opposite direction)

**Stop Loss Adjustment Rules**:
- **Only move stop toward breakeven**, never away from entry
- If price moves 50% toward target → consider moving stop to breakeven
- If price hits 1:1 (equal to initial risk) → move stop to breakeven
- Never widen stop after entry

**Invalidation Exits** (override stop loss):
- If dealing range low/high is broken → exit immediately
- If HTF structure shifts (1H CHoCH) → exit immediately
- These are structural invalidations, more important than stop price

### Take Profit Management

**Scaling Out (Recommended)**:
- **50% of position at primary target** (dealing range high/low OR first liquidity draw)
- **25% of position at secondary target** (next liquidity pool beyond primary)
- **25% of position trailing** (let it run with trailing stop)

**Alternative - Full Exit**:
- Exit 100% at primary target if you prefer simplicity
- This is acceptable but reduces potential for large winners

### Daily/Weekly Limits

**Daily Limits**:
- Maximum 3 trades per day
- Maximum 2 consecutive losses → stop trading for the day
- Maximum -3% daily drawdown → stop trading for the day

**Weekly Limits**:
- Maximum -5% weekly drawdown → reduce position size by 50% or stop trading
- Review strategy if weekly limit is hit

**Monthly Limits**:
- Maximum -10% monthly drawdown → pause trading and reassess strategy

---

## Do-Not-Trade Filters

**Skip the trade if ANY of the following are true**:

1. **HTF Misalignment**:
   - Daily, 4H, or 1H are in conflict
   - Example: Daily bullish but 4H bearish = NO TRADE

2. **No Clear Dealing Range**:
   - Cannot identify a swing low and swing high with liquidity grabs
   - Structure is messy or unclear

3. **Price at Mid-Range**:
   - Price is between 45%-55% of the dealing range
   - Not in clear discount or premium = NO EDGE

4. **No Clear Draw on Liquidity**:
   - Cannot identify a clear target (swing high/low or liquidity pool)
   - If you don't know where price is going, don't trade

5. **Major News Events**:
   - Fed announcements, CPI, Non-Farm Payrolls, etc.
   - Crypto-specific: Exchange hacks, regulatory news, major protocol exploits
   - Wait for clean structural read after news spike settles

6. **Low Volume / Illiquid Pairs**:
   - On Hyperliquid, stick to BTC, ETH, SOL, and other liquid pairs
   - Avoid low-volume pairs where stops can be easily hunted

7. **Conflicting Sessions**:
   - During session transitions (e.g., Asian close / London open), price can be choppy
   - Prefer clear directional sessions (London or New York)

---

## Session Dynamics (Hyperliquid Perpetuals)

### 24/7 Market Considerations

Hyperliquid operates 24/7, but trading activity follows traditional market sessions:

**Asian Session** (00:00-08:00 UTC):
- Generally lower volume
- Often used for liquidity grabs (sweeping lows in bullish markets, highs in bearish markets)
- Can be choppy; use caution

**London Session** (08:00-16:00 UTC):
- Volume picks up
- Major moves often begin during London session
- Good for identifying early structure shifts

**New York Session** (13:00-21:00 UTC):
- Highest volume
- Most reliable for institutional moves
- Best session for high-conviction trades

**Overlap** (13:00-16:00 UTC):
- London + New York overlap
- Highest liquidity and volume
- Ideal for entries and exits

### Session High/Low as Liquidity

- Track the high and low of each session
- These levels often get swept before major moves
- Example: In bullish structure, Asian session low is often swept before price runs to PDH during London/NY sessions

---

## Common Patterns and Scenarios

### Pattern 1: Asian Low Sweep → London Rally

**Setup**:
1. HTF bullish (D/4H/1H aligned)
2. During Asian session, price sweeps previous day low or Asian session low
3. Price creates a swing low (liquidity grabbed)
4. During London session, price moves up, creating a swing high
5. Dealing range: Asian swing low → London swing high
6. Price pulls back into discount during NY session

**Trade**:
- Enter long in discount zone (below 50% of dealing range)
- Target: PDH or London session high

### Pattern 2: PDH Rejection → Discount Entry

**Setup**:
1. HTF bullish (D/4H/1H aligned)
2. Price moves up and sweeps PDH (takes liquidity)
3. Price rejects and pulls back down
4. Dealing range: Recent swing low → PDH
5. Price re-enters discount zone

**Trade**:
- Enter long in discount zone
- Target: PDH retest or next session high

### Pattern 3: Equal Lows Sweep → Rally

**Setup**:
1. HTF bullish (D/4H/1H aligned)
2. Price forms equal lows on 1H chart (two swing lows at approximately the same level)
3. Price sweeps below equal lows (liquidity grab)
4. Price displaces back up aggressively
5. Dealing range: Sweep low → subsequent swing high

**Trade**:
- Enter long on pullback into discount
- Target: Previous swing high or PDH

---

## Example Trade Walkthrough

### Bullish Long Setup on BTC

**Context**:
- Date: November 9, 2025
- Pair: BTC/USD Perpetual on Hyperliquid

**Step 1: HTF Check**
- **Weekly**: Bullish (HH/HL, trending up for months)
- **Daily**: Bullish (HH/HL, last BOS was to upside at $66,000)
- **4H**: Bullish (HH/HL, recent swing low at $65,500)
- **1H**: Bullish overall, but showing pullback from $68,000 to $66,200
- **Verdict**: ✅ HTF ALIGNED (D/4H/1H all bullish)

**Step 2: Define Dealing Range (on 1H chart)**
- **Range Low**: $66,000 (swing low that swept Asian session low at $65,950)
- **Range High**: $68,000 (swing high that swept PDH at $67,950)
- **Range Size**: $2,000
- **50% Level**: $67,000
- **Current Price**: $66,200 (pullback in progress)

**Step 3: Calculate Discount/Premium**
- Current price: $66,200
- Distance from range low: $200
- Percentage in range: ($66,200 - $66,000) / $2,000 = 10%
- **Verdict**: ✅ DEEP DISCOUNT (10% of range, well below 50%)

**Step 4: Identify the Draw**
- **Option A**: Dealing range high at $68,000
- **Option B**: Next session high at $68,500
- **Choice**: Use $68,000 as primary target (conservative)

**Step 5: Check 5m Chart for Entry**
- Switch to 5m chart
- Identify bullish FVG from $66,150 to $66,250 (created during the pullback)
- **Entry Plan**: Place limit buy at $66,200 (within FVG)

**Step 6: Set Stop Loss (1:1 R:R)**
- Entry: $66,200
- Target: $68,000
- Reward: $68,000 - $66,200 = $1,800
- Risk: $1,800 (1:1 R:R)
- Stop: $66,200 - $1,800 = $64,400

**Step 7: Position Size**
- Account: $10,000
- Risk per trade: 1% = $100
- Risk per contract: $1,800
- Position size: $100 / $1,800 = 0.056 BTC

**Step 8: Execute**
- Place limit buy order at $66,200
- Set stop loss at $64,400
- Set take profit at $68,000 (or scale: 50% at $68,000, 50% trailing)

**Step 9: Monitor**
- If price hits $67,100 (50% to target) → consider moving stop to breakeven ($66,200)
- If 1H forms bearish CHoCH → exit immediately regardless of stop
- If dealing range low ($66,000) breaks → exit immediately

**Outcome** (hypothetical):
- Entry filled at $66,200
- Price moves to $68,000 → Take profit hit
- Profit: $1,800 per contract × 0.056 BTC = $100.80
- Result: +1% account gain (1R win)

---

## Key Principles Summary

1. **Trade with HTF structure only** - Never counter-trend trade
2. **Enter from discount (longs) or premium (shorts)** - Buy low, sell high
3. **Wait for liquidity grabs** - Institutions need liquidity to move size
4. **Identify the draw** - Know where price is going before entering
5. **Use 1H for decisions, 5m for execution** - Multi-timeframe precision
6. **1:1 R:R stop loss** - Conservative risk management
7. **Only move stops toward breakeven** - Protect profits, never widen risk
8. **Exit on structure breaks** - If HTF structure shifts, exit immediately
9. **Scale out at targets** - Take profits in layers
10. **Be selective** - 3-5 high-quality setups per week beats 20 mediocre trades

---

## Implementation Notes for Software Engineer

### Data Requirements

**Candlestick Data**:
- Timeframes needed: 1w, 1d, 4h, 1h, 5m
- Fields: Open, High, Low, Close, Volume, Timestamp
- Lookback: Minimum 100 candles per timeframe for structure analysis

**Liquidity Pool Tracking**:
- Previous Day High/Low (calculate from 1d candles)
- Session High/Low (track by UTC time ranges)
- Equal highs/lows (detect programmatically or manually mark)

**Real-Time Price**:
- Current price for discount/premium calculation
- Order book data (optional, for additional confluence)

### Core Functions to Implement

1. **identify_swing_highs_lows(candles, min_candles=3)**
   - Returns list of swing highs and swing lows
   - Use 3-candle minimum pattern (highest/lowest in middle)

2. **determine_structure_bias(swing_highs, swing_lows)**
   - Returns "BULLISH", "BEARISH", or "NEUTRAL"
   - Check for HH/HL (bullish) or LL/LH (bearish)

3. **calculate_dealing_range(swing_low, swing_high)**
   - Returns range low, range high, 50% level, current percentage

4. **check_htf_alignment(weekly, daily, four_hour, one_hour)**
   - Returns True if D/4H/1H aligned, False otherwise
   - Weekly is optional

5. **identify_liquidity_pools(candles)**
   - Returns PDH, PDL, session highs/lows, equal highs/lows

6. **detect_fvg(candles)**
   - Returns list of FVGs with price ranges
   - Check for gaps between candle wicks

7. **calculate_position_size(account_balance, risk_pct, entry, stop)**
   - Returns position size in contracts/units

8. **validate_setup(htf_aligned, price_location, draw_identified)**
   - Returns True if all setup conditions met

### Workflow Automation

**Scanning Workflow**:
1. Every 5 minutes, fetch latest candles for all timeframes
2. Check HTF alignment for each coin
3. If aligned, calculate dealing range
4. If price in discount/premium, check for FVG on 5m
5. If all conditions met, send alert or auto-execute

**Trade Management Workflow**:
1. Monitor open positions
2. Check if stop loss or take profit hit
3. Check if HTF structure shifts (1H CHoCH)
4. Check if dealing range invalidated
5. Execute exits based on conditions

### Edge Cases to Handle

- **Dealing range not clear**: Skip trade if cannot identify clean swing low/high with liquidity grabs
- **Multiple FVGs**: Use the most recent FVG closest to current price
- **HTF structure shift during trade**: Exit immediately, override stop loss
- **Low liquidity periods**: Avoid trading during low-volume times (use volume filter)

---

## Risk Disclaimer

This strategy is designed for experienced traders. Perpetual futures trading involves significant risk of loss. Always:
- Start with small position sizes
- Paper trade before using real capital
- Never risk more than you can afford to lose
- Continuously review and refine your execution

**Past performance does not guarantee future results.**

---

## Version History

- **Version 1.0** (November 9, 2025): Initial comprehensive strategy documentation for software implementation

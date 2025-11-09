# EMERALD Trading Agent

**E**ffective **M**arket **E**valuation and **R**igorous **A**nalysis for **L**ogical **D**ecisions

---

## What is EMERALD?

An **ICT/SMC trading analyst** for Hyperliquid perpetuals. EMERALD analyzes market structure across multiple timeframes and identifies high-probability setups based on liquidity hunts and structural alignment.

**Core Philosophy**: Markets move from liquidity to liquidity. We trade WITH higher timeframe structure by entering on pullbacks into discount (longs) or premium (shorts) zones.

### Quick Stats

- **ICT/SMC Methodology**: Structure-based trading system
- **Multi-Timeframe Analysis**: Daily/4H/1H alignment required
- **Discount/Premium Zones**: Entry only in optimal price areas
- **Liquidity Tracking**: PDH/PDL, equal highs/lows, round numbers
- **IE Confluence Layer**: Quantitative validation (order book, funding, trade flow, OI)
- **Conversation Memory**: Persistent sessions for analysis continuity

---

## Core Concepts (ICT/SMC Explained Like You're 18)

### What is ICT/SMC?

ICT (Inner Circle Trader) / SMC (Smart Money Concepts) is a trading methodology based on understanding how institutional traders (banks, hedge funds) move markets.

**The Big Idea**:
- Markets don't move randomly - they hunt liquidity clusters
- Liquidity = stop losses + pending orders clustered at key levels
- Price sweeps these levels (liquidity grab), then reverses
- We enter AFTER the grab, in the direction price was really going

### Market Structure

Markets move in one of two patterns:

**Bullish Structure** (HH/HL):
- Higher Highs: Each peak is higher than the last
- Higher Lows: Each dip is higher than the last
- Meaning: Buyers are in control → Look for LONG setups

**Bearish Structure** (LL/LH):
- Lower Lows: Each dip is lower than the last
- Lower Highs: Each peak is lower than the last
- Meaning: Sellers are in control → Look for SHORT setups

### The Dealing Range

After price grabs liquidity, it establishes a range:
- **Range High**: Swing high where liquidity was grabbed
- **Range Low**: Swing low where liquidity was grabbed
- **Midpoint**: The 50% level that divides the range

**Entry Zones**:
- **Discount Zone**: Below 50% (0-45%) → LONG entries
- **Premium Zone**: Above 50% (55-100%) → SHORT entries
- **Mid-Range**: 45-55% → SKIP (poor risk/reward)

### Higher Timeframe (HTF) Alignment

**Rule**: Daily, 4H, AND 1H must ALL show the same structure.

- All bullish? → Look for longs in discount
- All bearish? → Look for shorts in premium
- Mixed? → NO TRADE (wait for clarity)

This prevents trading against the larger trend.

### Liquidity Pools

Price levels where stops cluster:
- **PDH/PDL**: Previous Day High/Low (strongest levels)
- **Equal Highs/Lows**: 2+ swing points at same price
- **Round Numbers**: $60k, $65k, $70k (psychological levels)

These are our targets - price is magnetically drawn to them.

---

## How EMERALD Works

### 1. Structure Analysis
```
EMERALD fetches Daily/4H/1H/5M candles
  ↓
Detects swing highs and swing lows
  ↓
Determines structure: HH/HL (bullish) or LL/LH (bearish)?
  ↓
Checks if all timeframes agree (HTF alignment)
```

### 2. Entry Validation
```
IF HTF aligned:
  ↓
Calculate dealing range (swing low to swing high)
  ↓
Check current price position:
  - Bullish structure + discount zone? → VALID LONG
  - Bearish structure + premium zone? → VALID SHORT
  - Anything else? → NO SETUP
```

### 3. IE Confluence (Optional)
```
Valid ICT setup found
  ↓
Check quantitative metrics:
  - Order book pressure aligned? (+20 pts)
  - Trade flow aligned? (+20 pts)
  - Funding extreme (contrarian)? (+15 pts)
  - OI divergence? (+20 pts)
  ↓
Score 60-75: Grade A+ (full size)
Score 40-59: Grade A (75% size)
Score 20-39: Grade B (50% size)
Score 0-19: Grade C (proceed with caution)
```

---

## Quick Start

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd emerald

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Basic Usage

```bash
# Analyze a coin for ICT setup
python agent/agent.py "Analyze BTC"

# Check specific coin with account balance
python agent/agent.py "Analyze ETH with $50000 account"

# Ask about market structure
python agent/agent.py "What's the structure on SOL?"

# Check IE confluence for a direction
python agent/agent.py "Check IE confluence for BTC long"
```

### Session Management

```bash
# Continue today's session (default)
python agent/agent.py "BTC analysis"

# Use a specific session
python agent/agent.py --session "swing_trades" "Analyze BTC"

# Start fresh session
python agent/agent.py --new "BTC analysis"

# List all sessions
python agent/agent.py --list-sessions

# View session history
python agent/agent.py --show-session "2025-11-09_session"

# Delete old session
python agent/agent.py --delete-session "old_session"
```

---

## Example Analysis

**User**: `python agent/agent.py "Analyze BTC"`

**EMERALD (if valid setup)**:
```
🟢 BTC - LONG SETUP (ICT Valid)

HTF Alignment: BULLISH
  - Daily: HH/HL (confidence: 0.85)
  - 4H: HH/HL (confidence: 0.90)
  - 1H: HH/HL (confidence: 0.80)

Dealing Range (1H):
  - High: $68,000
  - Low: $66,000
  - Midpoint: $67,000
  - Current: $66,200 (10% of range - DEEP DISCOUNT)

Entry Setup:
  - Direction: LONG
  - Entry: $66,200
  - Stop Loss: $64,400 (1:1 R:R)
  - Target 1: $68,000 (range high)
  - Target 2: $68,500 (PDH)
  - R:R: 1.0:1

Position Sizing:
  - Risk: $100 (1% of $10k account)
  - Size: 0.0015 BTC

Liquidity Pools:
  - PDH: $68,500
  - PDL: $65,800
  - Nearest above: $67,000
```

**EMERALD (if invalid)**:
```
❌ BTC - NO ICT SETUP

Reason: HTF not aligned

Structure Analysis:
  - Daily: BULLISH (HH/HL)
  - 4H: BEARISH (LL/LH) ← CONFLICT
  - 1H: NEUTRAL

Recommendation: Wait for Daily and 4H to align.
```

---

## Project Structure

```
emerald/
├── agent/
│   └── agent.py              # Main agent with ICT/SMC system prompt
├── config/
│   └── settings.py           # Configuration (ICT thresholds, IE weights)
├── ict/                      # ICT core modules
│   ├── swing_detector.py     # Swing high/low detection
│   ├── structure_analyzer.py # HH/HL vs LL/LH determination
│   ├── dealing_range.py      # Discount/premium calculator
│   ├── htf_alignment.py      # Multi-timeframe alignment
│   ├── liquidity_pools.py    # PDH/PDL, equal highs/lows
│   └── setup_validator.py    # Master setup validation
├── tools/                    # Agent tools
│   ├── ict_analyze_setup.py         # Master ICT analysis tool
│   ├── ie_confluence_for_ict.py     # IE confluence scoring
│   ├── ie_fetch_order_book.py       # Order book pressure
│   ├── ie_fetch_funding.py          # Funding rate
│   ├── ie_fetch_trade_flow.py       # Trade flow
│   ├── ie_fetch_open_interest.py    # Open interest
│   ├── ie_liquidation_tracker.py    # Liquidation events
│   ├── ie_order_book_microstructure.py  # Spoofing/icebergs
│   └── tool_fetch_hl_raw.py         # Raw candle data
├── ie/                       # Institutional Engine (supporting modules)
│   ├── cache.py              # Caching for IE tools
│   ├── calculations.py       # IE metric calculations
│   └── data_models.py        # IE data structures
├── memory/                   # Conversation memory
│   └── session_manager.py    # Session persistence
├── ICT_SMC_Strategy.md       # Full ICT/SMC methodology reference
└── README.md                 # This file
```

---

## Strategy Reference

For complete ICT/SMC methodology, see [ICT_SMC_Strategy.md](ICT_SMC_Strategy.md).

**Key Sections**:
- Swing High/Low Detection (3-candle pattern)
- Market Structure Determination (HH/HL vs LL/LH)
- Dealing Range Calculation
- Discount/Premium Zones
- Liquidity Pool Identification
- HTF Alignment Requirements
- Entry/Exit Rules

---

## Configuration

Key settings in `config/settings.py`:

**ICT Parameters**:
- `min_swing_candles`: 3 (swing detection pattern)
- `discount_threshold`: 0.50 (price below 50% = discount)
- `premium_threshold`: 0.50 (price above 50% = premium)
- `htf_required_timeframes`: ["1d", "4h", "1h"]
- `min_structure_confidence`: 0.7 (70% confidence minimum)

**IE Confluence Weights**:
- `order_book_points`: 20
- `trade_flow_points`: 20
- `funding_extreme_points`: 15
- `oi_divergence_points`: 20

**Position Sizing**:
- `base_position_risk_pct`: 1.0 (1% risk per trade)
- `grade_a_plus_position_mult`: 1.0 (full size for A+ setups)
- `grade_a_position_mult`: 0.75 (75% for A setups)
- `grade_b_position_mult`: 0.5 (50% for B setups)

---

## FAQ

**Q: What if HTF timeframes conflict?**
A: NO TRADE. Wait for alignment. Never trade against higher timeframe structure.

**Q: Can I trade from mid-range?**
A: No. Mid-range (45-55%) offers poor risk/reward. Wait for discount or premium.

**Q: What if there's a valid ICT setup but weak IE confluence?**
A: Proceed with caution. ICT setup is valid, but reduce position size based on grade.

**Q: How often do valid setups appear?**
A: Rarely. ICT is selective - HTF alignment + correct zone = maybe 2-3 setups per week per coin.

**Q: Can I use this for scalping?**
A: No. ICT/SMC is a swing/position trading methodology. Entries on 1H-4H, hold for days/weeks.

---

## License & Disclaimer

This is a trading ANALYSIS tool, not a trading bot. It provides setup identification and analysis - YOU make all trading decisions.

Trading perpetuals involves substantial risk. Never risk more than you can afford to lose.

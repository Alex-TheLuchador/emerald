# EMERALD Institutional Strategy Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Phase 1: Data Infrastructure](#phase-1-data-infrastructure)
4. [Phase 2: Strategy Layers](#phase-2-strategy-layers)
5. [Phase 3: Scoring System](#phase-3-scoring-system)
6. [Phase 4: Integration & Testing](#phase-4-integration--testing)
7. [Phase 5: Production Deployment](#phase-5-production-deployment)
8. [Appendix: Key Formulas](#appendix-key-formulas)

---

## Overview

### Objective
Rebuild EMERALD's trading strategy from ICT/SMC concepts to institutional-grade quantitative methods based on:
- Order book microstructure
- Statistical mean reversion
- Market maker behavior
- Volume/OI analysis
- Funding rate arbitrage

### Success Criteria
- Agent can analyze 5 independent data layers
- Produces quantitative scores (0-100) for trade setups
- Generates actionable trade recommendations with clear entry/exit/risk parameters
- Backtestable and measurable (track win rate, Sharpe ratio, etc.)

### Timeline
12 weeks from data infrastructure to live trading

---

## Architecture Design

### High-Level System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     EMERALD Agent Core                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              InstitutionalStrategyEvaluator                  │
│  (Orchestrates all strategy layers, produces final score)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Layer 1     │  │  Layer 2     │  │  Layer 3     │
│  OrderBook   │  │  VWAP        │  │  Funding     │
│  Imbalance   │  │  Deviation   │  │  Rate Arb    │
└──────────────┘  └──────────────┘  └──────────────┘
        ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐
│  Layer 4     │  │  Layer 5     │
│  OI/Volume   │  │  Mean        │
│  Divergence  │  │  Reversion   │
└──────────────┘  └──────────────┘
        │
        ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Fetching Layer                         │
│  (Hyperliquid API calls - order book, funding, OI, candles) │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Language**: Python 3.9+
- **Data**: Pandas, NumPy for calculations
- **API**: Requests library for Hyperliquid API
- **Agent Framework**: LangChain (existing)
- **Storage**: JSON files for caching, SQLite for historical data (optional)
- **Testing**: Pytest for unit tests, custom backtesting framework

### File Structure
```
emerald/
├── config/
│   ├── settings.py                  # Configuration (existing)
│   └── strategy_config.py           # New: Strategy-specific config
├── tools/
│   ├── fetch_order_book.py          # New: Order book data
│   ├── fetch_funding.py             # New: Funding rates
│   ├── fetch_open_interest.py       # New: OI data
│   ├── fetch_candles.py             # Enhanced: Add volume, VWAP
│   └── data_cache.py                # New: Caching layer
├── strategies/
│   ├── base_strategy.py             # New: Abstract base class
│   ├── order_book_imbalance.py      # New: Layer 1
│   ├── vwap_deviation.py            # New: Layer 2
│   ├── funding_arbitrage.py         # New: Layer 3
│   ├── oi_volume_divergence.py      # New: Layer 4
│   └── mean_reversion.py            # New: Layer 5
├── evaluation/
│   ├── strategy_evaluator.py        # New: Main scoring system
│   └── trade_generator.py           # New: Converts scores to trades
├── backtest/
│   ├── backtester.py                # New: Historical testing
│   └── performance_metrics.py       # New: Win rate, Sharpe, etc.
├── agent/
│   └── agent.py                     # Enhanced: New prompts
└── tests/
    ├── test_strategies.py           # New: Strategy unit tests
    └── test_evaluation.py           # New: Scoring tests
```

---

## Phase 1: Data Infrastructure

**Timeline**: Week 1-2  
**Goal**: Build robust data fetching layer for all required market data

### Step 1.1: Extend Hyperliquid API Integration

**File**: `tools/fetch_order_book.py`

**Requirements**:
- Fetch L2 order book data (bid/ask levels with sizes)
- Return top 20 levels on each side minimum
- Include timestamp for each snapshot
- Handle API rate limits (implement exponential backoff)
- Cache responses for 1-2 seconds to avoid redundant calls

**API Endpoint**: 
```python
POST https://api.hyperliquid.xyz/info
Body: {"type": "l2Book", "coin": "BTC"}
```

**Expected Output Format**:
```python
{
    "coin": "BTC",
    "timestamp": 1699564800000,
    "bids": [
        {"price": "67890.5", "size": "2.45"},
        {"price": "67890.0", "size": "1.23"},
        # ... 18 more levels
    ],
    "asks": [
        {"price": "67891.0", "size": "3.12"},
        {"price": "67891.5", "size": "0.85"},
        # ... 18 more levels
    ]
}
```

**Implementation Details**:
```python
from langchain.tools import tool
from typing import Dict, Any, List
import requests

@tool
def fetch_order_book(
    coin: str,
    depth: int = 20
) -> Dict[str, Any]:
    """Fetch order book data from Hyperliquid.
    
    Args:
        coin: Symbol (e.g., "BTC", "ETH")
        depth: Number of levels to return (default 20)
    
    Returns:
        Dictionary with bids, asks, and metadata
    """
    # Implementation here
    pass
```

**Testing Checklist**:
- [ ] Successfully fetches data for BTC, ETH, SOL
- [ ] Handles API errors gracefully (timeout, rate limit)
- [ ] Cache reduces API calls by 80%+
- [ ] Data format matches expected structure

---

### Step 1.2: Funding Rate Data

**File**: `tools/fetch_funding.py`

**Requirements**:
- Fetch current funding rate
- Fetch historical funding rates (24h minimum)
- Calculate annualized funding rate
- Handle multiple coins simultaneously

**API Endpoint**:
```python
POST https://api.hyperliquid.xyz/info
Body: {"type": "fundingHistory", "coin": "BTC", "startTime": <ms>}
```

**Expected Output Format**:
```python
{
    "coin": "BTC",
    "current_funding": 0.0001,  # Per 8 hours
    "annualized_funding": 0.0365,  # 3.65%
    "history_24h": [
        {"time": 1699564800000, "rate": 0.0001},
        {"time": 1699536000000, "rate": 0.00015},
        # ... more data points
    ],
    "premium_index": 67890.5  # Spot vs perp premium
}
```

**Implementation Details**:
```python
@tool
def fetch_funding_rate(
    coin: str,
    lookback_hours: int = 24
) -> Dict[str, Any]:
    """Fetch funding rate data.
    
    Args:
        coin: Symbol
        lookback_hours: How far back to fetch history
    
    Returns:
        Current rate, annualized rate, and historical data
    """
    # Implementation here
    pass
```

---

### Step 1.3: Open Interest Data

**File**: `tools/fetch_open_interest.py`

**Requirements**:
- Fetch current open interest
- Track OI changes over time (1h, 4h, 24h periods)
- Calculate OI percentage change
- Correlate with price changes

**API Endpoint**:
```python
POST https://api.hyperliquid.xyz/info
Body: {"type": "metaAndAssetCtxs"}
```

**Expected Output Format**:
```python
{
    "coin": "BTC",
    "timestamp": 1699564800000,
    "open_interest": 125000000.0,  # USD value
    "oi_change_1h": 2.3,  # Percentage
    "oi_change_4h": 5.7,
    "oi_change_24h": -3.2,
    "price_change_1h": 1.5,  # For correlation
    "price_change_4h": 3.2,
    "price_change_24h": -2.1
}
```

**Implementation Details**:
```python
@tool
def fetch_open_interest(
    coin: str
) -> Dict[str, Any]:
    """Fetch open interest data and calculate changes.
    
    Args:
        coin: Symbol
    
    Returns:
        Current OI, changes over multiple timeframes
    """
    # Implementation here
    pass
```

---

### Step 1.4: Enhanced Candle Data

**File**: `tools/fetch_candles.py` (enhance existing `fetch_hl_raw.py`)

**Requirements**:
- Keep existing functionality
- Add volume analysis (vs. average volume)
- Add timestamp alignment for VWAP calculations
- Return data in format suitable for NumPy operations

**Enhancements**:
```python
@tool
def fetch_candles_with_volume_analysis(
    coin: str,
    interval: str,
    hours: int,
    limit: int
) -> Dict[str, Any]:
    """Enhanced candle fetching with volume metrics.
    
    Returns existing data plus:
        - average_volume (20-period)
        - volume_ratio (current vs average)
        - cumulative_volume
    """
    # Build on existing fetch_hl_raw
    pass
```

---

### Step 1.5: Data Caching Layer

**File**: `tools/data_cache.py`

**Purpose**: Reduce API calls, improve performance

**Requirements**:
- Cache order book data for 2 seconds
- Cache funding rates for 5 minutes
- Cache OI data for 5 minutes
- Cache candles based on interval (1m = 30s, 1h = 5min, etc.)
- Implement LRU eviction for memory management

**Implementation**:
```python
from functools import lru_cache
from datetime import datetime, timedelta
import time

class DataCache:
    """Time-based cache for market data."""
    
    def __init__(self):
        self.cache = {}
        self.ttl = {
            'order_book': 2,      # seconds
            'funding': 300,       # 5 minutes
            'oi': 300,
            'candles_1m': 30,
            'candles_5m': 60,
            'candles_15m': 180,
            'candles_1h': 300,
        }
    
    def get(self, key: str) -> Any:
        """Retrieve cached data if still valid."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            cache_type = self._get_cache_type(key)
            if time.time() - timestamp < self.ttl[cache_type]:
                return data
        return None
    
    def set(self, key: str, data: Any) -> None:
        """Store data with current timestamp."""
        self.cache[key] = (data, time.time())
    
    def _get_cache_type(self, key: str) -> str:
        """Determine TTL based on key pattern."""
        # Logic to extract cache type from key
        pass

# Global cache instance
data_cache = DataCache()
```

---

### Step 1.6: Configuration

**File**: `config/strategy_config.py`

**Purpose**: Centralize all strategy-specific parameters

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class StrategyWeights:
    """Weights for each strategy layer in final score."""
    order_book_imbalance: float = 0.25
    vwap_deviation: float = 0.20
    funding_rate: float = 0.20
    oi_volume: float = 0.20
    mean_reversion: float = 0.15

@dataclass
class OrderBookConfig:
    """Configuration for order book imbalance strategy."""
    depth_levels: int = 10  # How many levels to analyze
    imbalance_threshold: float = 0.4  # Minimum for signal
    min_consecutive_snapshots: int = 3  # Stability check

@dataclass
class VWAPConfig:
    """Configuration for VWAP deviation strategy."""
    lookback_candles: int = 24  # For VWAP calculation
    std_dev_threshold_1: float = 1.0
    std_dev_threshold_2: float = 2.0

@dataclass
class FundingConfig:
    """Configuration for funding rate strategy."""
    annualized_threshold: float = 0.10  # 10% annualized
    extreme_threshold: float = 0.15     # 15% = very extreme

@dataclass
class OIVolumeConfig:
    """Configuration for OI/Volume divergence."""
    oi_change_threshold: float = 5.0    # Percentage
    volume_multiplier: float = 1.5      # vs. average
    price_change_threshold: float = 1.5

@dataclass
class MeanReversionConfig:
    """Configuration for statistical mean reversion."""
    lookback_period: int = 20
    z_score_threshold: float = 2.0
    z_score_extreme: float = 3.0

# Global config instances
STRATEGY_WEIGHTS = StrategyWeights()
ORDERBOOK_CONFIG = OrderBookConfig()
VWAP_CONFIG = VWAPConfig()
FUNDING_CONFIG = FundingConfig()
OI_VOLUME_CONFIG = OIVolumeConfig()
MEAN_REVERSION_CONFIG = MeanReversionConfig()
```

---

## Phase 2: Strategy Layers

**Timeline**: Week 3-5  
**Goal**: Implement each of the 5 strategy layers independently

### Step 2.1: Base Strategy Class

**File**: `strategies/base_strategy.py`

**Purpose**: Abstract base class that all strategies inherit from

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    def __init__(self, config: Any):
        """Initialize strategy with configuration.
        
        Args:
            config: Strategy-specific configuration object
        """
        self.config = config
    
    @abstractmethod
    def analyze(self, coin: str, market_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Analyze market data and produce a score.
        
        Args:
            coin: Trading pair symbol
            market_data: Dictionary containing all relevant market data
        
        Returns:
            Tuple of (score: 0-100, details: dict with reasoning)
        """
        pass
    
    @abstractmethod
    def get_signal(self, score: float, details: Dict[str, Any]) -> str:
        """Convert score to actionable signal.
        
        Args:
            score: Analysis score (0-100)
            details: Additional context from analysis
        
        Returns:
            Signal: "LONG", "SHORT", or "NEUTRAL"
        """
        pass
    
    def validate_data(self, market_data: Dict[str, Any], required_keys: list) -> bool:
        """Validate that required data is present.
        
        Args:
            market_data: Data dictionary to validate
            required_keys: List of required keys
        
        Returns:
            True if all required keys present
        """
        return all(key in market_data for key in required_keys)
```

---

### Step 2.2: Layer 1 - Order Book Imbalance

**File**: `strategies/order_book_imbalance.py`

**Algorithm**:
1. Sum bid volumes for top N levels
2. Sum ask volumes for top N levels
3. Calculate imbalance ratio: `(bids - asks) / (bids + asks)`
4. Check if imbalance persists across multiple snapshots
5. Combine with recent price action

**Implementation**:
```python
from strategies.base_strategy import BaseStrategy
from config.strategy_config import ORDERBOOK_CONFIG
from typing import Dict, Any, Tuple
import numpy as np

class OrderBookImbalanceStrategy(BaseStrategy):
    """Strategy based on order book bid/ask imbalance."""
    
    def __init__(self):
        super().__init__(ORDERBOOK_CONFIG)
    
    def analyze(self, coin: str, market_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Analyze order book imbalance.
        
        Required market_data keys:
            - order_book: Current order book snapshot
            - price_change_5m: Recent price movement
            - historical_imbalances: Last 3-5 snapshots (for stability)
        """
        # Validate data
        required = ['order_book', 'price_change_5m']
        if not self.validate_data(market_data, required):
            return 0.0, {"error": "Missing required data"}
        
        # Calculate imbalance
        order_book = market_data['order_book']
        imbalance = self._calculate_imbalance(order_book)
        
        # Check stability (has imbalance persisted?)
        is_stable = self._check_stability(market_data.get('historical_imbalances', []))
        
        # Get price action context
        price_change = market_data.get('price_change_5m', 0)
        
        # Score calculation
        score = self._calculate_score(imbalance, is_stable, price_change)
        
        details = {
            "imbalance": imbalance,
            "is_stable": is_stable,
            "price_change": price_change,
            "signal_type": self._get_signal_type(imbalance, price_change)
        }
        
        return score, details
    
    def _calculate_imbalance(self, order_book: Dict[str, Any]) -> float:
        """Calculate bid/ask imbalance ratio."""
        bids = order_book['bids'][:self.config.depth_levels]
        asks = order_book['asks'][:self.config.depth_levels]
        
        total_bid_volume = sum(float(bid['size']) for bid in bids)
        total_ask_volume = sum(float(ask['size']) for ask in asks)
        
        total = total_bid_volume + total_ask_volume
        if total == 0:
            return 0.0
        
        imbalance = (total_bid_volume - total_ask_volume) / total
        return imbalance
    
    def _check_stability(self, historical_imbalances: list) -> bool:
        """Check if imbalance has persisted across snapshots."""
        if len(historical_imbalances) < self.config.min_consecutive_snapshots:
            return False
        
        recent = historical_imbalances[-self.config.min_consecutive_snapshots:]
        
        # Check if all have same sign and above threshold
        if all(abs(imb) > self.config.imbalance_threshold for imb in recent):
            if all(imb > 0 for imb in recent) or all(imb < 0 for imb in recent):
                return True
        
        return False
    
    def _calculate_score(self, imbalance: float, is_stable: bool, price_change: float) -> float:
        """Convert imbalance metrics to 0-100 score."""
        # Base score from imbalance strength
        base_score = min(100, abs(imbalance) * 150)
        
        # Bonus for stability
        if is_stable:
            base_score *= 1.2
        
        # Bonus for absorption/distribution setup
        if (imbalance > 0.4 and price_change < -0.5) or \
           (imbalance < -0.4 and price_change > 0.5):
            base_score *= 1.3  # Price moving against imbalance = setup
        
        return min(100, base_score)
    
    def _get_signal_type(self, imbalance: float, price_change: float) -> str:
        """Identify the type of signal."""
        if imbalance > 0.4 and price_change < -0.5:
            return "ABSORPTION"  # Bids absorbing selling
        elif imbalance < -0.4 and price_change > 0.5:
            return "DISTRIBUTION"  # Asks distributing into buying
        else:
            return "NEUTRAL"
    
    def get_signal(self, score: float, details: Dict[str, Any]) -> str:
        """Convert score to trading signal."""
        if score < 40:
            return "NEUTRAL"
        
        signal_type = details.get('signal_type', 'NEUTRAL')
        
        if signal_type == "ABSORPTION":
            return "LONG"
        elif signal_type == "DISTRIBUTION":
            return "SHORT"
        else:
            return "NEUTRAL"
```

**Testing Requirements**:
- [ ] Test with synthetic order book data (known imbalances)
- [ ] Test stability detection logic
- [ ] Test scoring edge cases (zero volume, extreme imbalance)
- [ ] Validate against real market data

---

### Step 2.3: Layer 2 - VWAP Deviation

**File**: `strategies/vwap_deviation.py`

**Algorithm**:
1. Calculate VWAP from recent candles: `VWAP = Σ(Price × Volume) / Σ(Volume)`
2. Calculate standard deviation of prices
3. Determine how many std devs current price is from VWAP
4. Score based on deviation (higher deviation = higher mean reversion probability)

**Implementation**:
```python
from strategies.base_strategy import BaseStrategy
from config.strategy_config import VWAP_CONFIG
from typing import Dict, Any, Tuple, List
import numpy as np

class VWAPDeviationStrategy(BaseStrategy):
    """Strategy based on VWAP deviation (mean reversion)."""
    
    def __init__(self):
        super().__init__(VWAP_CONFIG)
    
    def analyze(self, coin: str, market_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Analyze VWAP deviation.
        
        Required market_data keys:
            - candles: Recent OHLCV data
            - current_price: Latest price
        """
        required = ['candles', 'current_price']
        if not self.validate_data(market_data, required):
            return 0.0, {"error": "Missing required data"}
        
        candles = market_data['candles'][-self.config.lookback_candles:]
        current_price = market_data['current_price']
        
        # Calculate VWAP
        vwap = self._calculate_vwap(candles)
        
        # Calculate standard deviation bands
        std_dev = self._calculate_std_dev(candles, vwap)
        bands = self._calculate_bands(vwap, std_dev)
        
        # Calculate z-score (how many std devs away)
        z_score = (current_price - vwap) / std_dev if std_dev > 0 else 0
        
        # Calculate score
        score = self._calculate_score(z_score, current_price, bands)
        
        details = {
            "vwap": vwap,
            "current_price": current_price,
            "std_dev": std_dev,
            "z_score": z_score,
            "bands": bands,
            "deviation_level": self._get_deviation_level(z_score)
        }
        
        return score, details
    
    def _calculate_vwap(self, candles: List[Dict[str, Any]]) -> float:
        """Calculate Volume Weighted Average Price."""
        total_pv = 0.0
        total_volume = 0.0
        
        for candle in candles:
            typical_price = (candle['high'] + candle['low'] + candle['close']) / 3
            volume = candle['volume']
            total_pv += typical_price * volume
            total_volume += volume
        
        return total_pv / total_volume if total_volume > 0 else 0
    
    def _calculate_std_dev(self, candles: List[Dict[str, Any]], vwap: float) -> float:
        """Calculate standard deviation of prices around VWAP."""
        prices = [(c['high'] + c['low'] + c['close']) / 3 for c in candles]
        return np.std(prices)
    
    def _calculate_bands(self, vwap: float, std_dev: float) -> Dict[str, float]:
        """Calculate VWAP bands (similar to Bollinger Bands)."""
        return {
            'upper_2': vwap + (2 * std_dev),
            'upper_1': vwap + std_dev,
            'vwap': vwap,
            'lower_1': vwap - std_dev,
            'lower_2': vwap - (2 * std_dev)
        }
    
    def _calculate_score(self, z_score: float, price: float, bands: Dict[str, float]) -> float:
        """Score based on deviation from VWAP."""
        # Higher score = further from VWAP = higher mean reversion probability
        abs_z = abs(z_score)
        
        if abs_z >= 2.0:
            return 100  # 2+ std devs = maximum score
        elif abs_z >= 1.5:
            return 80
        elif abs_z >= 1.0:
            return 60
        elif abs_z >= 0.5:
            return 40
        else:
            return 20  # Near VWAP = low score
    
    def _get_deviation_level(self, z_score: float) -> str:
        """Categorize deviation level."""
        abs_z = abs(z_score)
        if abs_z >= 2.0:
            return "EXTREME"
        elif abs_z >= 1.5:
            return "HIGH"
        elif abs_z >= 1.0:
            return "MODERATE"
        else:
            return "LOW"
    
    def get_signal(self, score: float, details: Dict[str, Any]) -> str:
        """Convert score to trading signal."""
        if score < 60:
            return "NEUTRAL"
        
        z_score = details['z_score']
        
        if z_score > 1.5:
            return "SHORT"  # Above VWAP, expect reversion down
        elif z_score < -1.5:
            return "LONG"   # Below VWAP, expect reversion up
        else:
            return "NEUTRAL"
```

**Testing Requirements**:
- [ ] Test VWAP calculation accuracy
- [ ] Test with extreme price movements
- [ ] Validate scoring thresholds
- [ ] Compare against TradingView VWAP indicator

---

### Step 2.4: Layer 3 - Funding Rate Arbitrage

**File**: `strategies/funding_arbitrage.py`

**Algorithm**:
1. Fetch current funding rate
2. Annualize funding rate (multiply by 3 periods/day × 365 days)
3. Check if funding exceeds threshold (10%+ annualized)
4. Determine if opportunity is delta-neutral or directional

**Implementation**:
```python
from strategies.base_strategy import BaseStrategy
from config.strategy_config import FUNDING_CONFIG
from typing import Dict, Any, Tuple

class FundingArbitrageStrategy(BaseStrategy):
    """Strategy based on funding rate extremes."""
    
    def __init__(self):
        super().__init__(FUNDING_CONFIG)
    
    def analyze(self, coin: str, market_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Analyze funding rate for arbitrage opportunities.
        
        Required market_data keys:
            - funding_rate: Current 8-hour funding rate
            - funding_history: Historical rates for trend analysis
        """
        required = ['funding_rate']
        if not self.validate_data(market_data, required):
            return 0.0, {"error": "Missing required data"}
        
        funding_rate = market_data['funding_rate']
        
        # Convert to annualized rate
        annualized = self._annualize_funding(funding_rate)
        
        # Check funding trend
        history = market_data.get('funding_history', [])
        trend = self._analyze_funding_trend(history)
        
        # Calculate score
        score = self._calculate_score(annualized, trend)
        
        details = {
            "funding_rate_8h": funding_rate,
            "annualized_rate": annualized,
            "trend": trend,
            "opportunity_type": self._get_opportunity_type(annualized)
        }
        
        return score, details
    
    def _annualize_funding(self, rate_8h: float) -> float:
        """Convert 8-hour funding to annualized rate."""
        return rate_8h * 3 * 365  # 3 periods per day, 365 days
    
    def _analyze_funding_trend(self, history: List[float]) -> str:
        """Determine if funding is increasing, decreasing, or stable."""
        if len(history) < 3:
            return "UNKNOWN"
        
        recent_3 = history[-3:]
        
        if all(recent_3[i] < recent_3[i+1] for i in range(len(recent_3)-1)):
            return "INCREASING"
        elif all(recent_3[i] > recent_3[i+1] for i in range(len(recent_3)-1)):
            return "DECREASING"
        else:
            return "STABLE"
    
    def _calculate_score(self, annualized: float, trend: str) -> float:
        """Score based on funding rate extremes."""
        abs_rate = abs(annualized)
        
        # Base score from rate magnitude
        if abs_rate >= self.config.extreme_threshold:
            base_score = 100
        elif abs_rate >= self.config.annualized_threshold:
            base_score = 70
        else:
            base_score = abs_rate / self.config.annualized_threshold * 50
        
        # Adjust for trend (increasing extreme = even better opportunity)
        if trend == "INCREASING" and abs_rate > self.config.annualized_threshold:
            base_score *= 1.2
        
        return min(100, base_score)
    
    def _get_opportunity_type(self, annualized: float) -> str:
        """Categorize the funding opportunity."""
        if annualized > self.config.annualized_threshold:
            return "SHORT_PERP_LONG_SPOT"  # Collect positive funding
        elif annualized < -self.config.annualized_threshold:
            return "LONG_PERP_SHORT_SPOT"  # Collect negative funding
        else:
            return "NO_OPPORTUNITY"
    
    def get_signal(self, score: float, details: Dict[str, Any]) -> str:
        """Convert score to trading signal."""
        if score < 70:
            return "NEUTRAL"
        
        opportunity = details['opportunity_type']
        
        if opportunity == "SHORT_PERP_LONG_SPOT":
            return "SHORT"  # Can also be directional short if other layers agree
        elif opportunity == "LONG_PERP_SHORT_SPOT":
            return "LONG"   # Can also be directional long if other layers agree
        else:
            return "NEUTRAL"
```

---

### Step 2.5: Layer 4 - OI/Volume Divergence

**File**: `strategies/oi_volume_divergence.py`

**Algorithm**:
1. Track price change, OI change, and volume over same period
2. Identify 4 key scenarios:
   - Price ↑ + OI ↑ + Vol ↑ = Strong bullish (new longs)
   - Price ↑ + OI ↓ + Vol ↑ = Weak bullish (short covering)
   - Price ↓ + OI ↑ + Vol ↑ = Strong bearish (new shorts)
   - Price ↓ + OI ↓ + Vol ↑ = Weak bearish (long liquidations)
3. Score based on scenario and magnitude

**Implementation**:
```python
from strategies.base_strategy import BaseStrategy
from config.strategy_config import OI_VOLUME_CONFIG
from typing import Dict, Any, Tuple

class OIVolumeDivergenceStrategy(BaseStrategy):
    """Strategy based on OI/Volume/Price relationship."""
    
    def __init__(self):
        super().__init__(OI_VOLUME_CONFIG)
    
    def analyze(self, coin: str, market_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Analyze OI and volume divergence.
        
        Required market_data keys:
            - price_change_4h: Price % change
            - oi_change_4h: Open interest % change
            - volume_vs_average: Current volume vs 20-period average
        """
        required = ['price_change_4h', 'oi_change_4h', 'volume_vs_average']
        if not self.validate_data(market_data, required):
            return 0.0, {"error": "Missing required data"}
        
        price_change = market_data['price_change_4h']
        oi_change = market_data['oi_change_4h']
        volume_ratio = market_data['volume_vs_average']
        
        # Identify scenario
        scenario, confidence = self._identify_scenario(price_change, oi_change, volume_ratio)
        
        # Calculate score
        score = self._calculate_score(scenario, confidence, abs(price_change), abs(oi_change))
        
        details = {
            "price_change": price_change,
            "oi_change": oi_change,
            "volume_ratio": volume_ratio,
            "scenario": scenario,
            "confidence": confidence
        }
        
        return score, details
    
    def _identify_scenario(self, price_change: float, oi_change: float, volume_ratio: float) -> Tuple[str, float]:
        """Identify which OI/Volume scenario is occurring."""
        price_threshold = self.config.price_change_threshold
        oi_threshold = self.config.oi_change_threshold
        vol_threshold = self.config.volume_multiplier
        
        # Check if volume is significant
        high_volume = volume_ratio > vol_threshold
        
        if not high_volume:
            return "LOW_VOLUME", 0.2
        
        # Four key scenarios
        if price_change > price_threshold and oi_change > oi_threshold:
            return "STRONG_BULLISH", 0.85  # New longs entering
        elif price_change > price_threshold and oi_change < -oi_threshold:
            return "WEAK_BULLISH", 0.45    # Shorts covering (exhaustion)
        elif price_change < -price_threshold and oi_change > oi_threshold:
            return "STRONG_BEARISH", 0.85  # New shorts entering
        elif price_change < -price_threshold and oi_change < -oi_threshold:
            return "WEAK_BEARISH", 0.45    # Longs closing (exhaustion)
        else:
            return "NEUTRAL", 0.25
    
    def _calculate_score(self, scenario: str, confidence: float, price_magnitude: float, oi_magnitude: float) -> float:
        """Calculate score based on scenario strength."""
        base_score = confidence * 100
        
        # Boost score if moves are large
        if price_magnitude > 3.0 and oi_magnitude > 10.0:
            base_score *= 1.2
        
        return min(100, base_score)
    
    def get_signal(self, score: float, details: Dict[str, Any]) -> str:
        """Convert score to trading signal."""
        if score < 60:
            return "NEUTRAL"
        
        scenario = details['scenario']
        
        if scenario == "STRONG_BULLISH":
            return "LONG"   # Ride the new money
        elif scenario == "STRONG_BEARISH":
            return "SHORT"  # Ride the new money
        elif scenario in ["WEAK_BULLISH", "WEAK_BEARISH"]:
            # Exhaustion signals - could fade the move
            return "REVERSAL_WATCH"
        else:
            return "NEUTRAL"
```

---

### Step 2.6: Layer 5 - Mean Reversion

**File**: `strategies/mean_reversion.py`

**Algorithm**:
1. Calculate rolling mean and std dev of prices
2. Calculate z-score: `(current_price - mean) / std_dev`
3. If z-score > 2 or < -2, price is at statistical extreme
4. Enter trades toward the mean

**Implementation**:
```python
from strategies.base_strategy import BaseStrategy
from config.strategy_config import MEAN_REVERSION_CONFIG
from typing import Dict, Any, Tuple, List
import numpy as np

class MeanReversionStrategy(BaseStrategy):
    """Strategy based on statistical mean reversion."""
    
    def __init__(self):
        super().__init__(MEAN_REVERSION_CONFIG)
    
    def analyze(self, coin: str, market_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Analyze statistical deviation from mean.
        
        Required market_data keys:
            - candles: Recent price history
            - current_price: Latest price
        """
        required = ['candles', 'current_price']
        if not self.validate_data(market_data, required):
            return 0.0, {"error": "Missing required data"}
        
        candles = market_data['candles'][-self.config.lookback_period:]
        current_price = market_data['current_price']
        
        # Calculate statistics
        prices = [c['close'] for c in candles]
        mean = np.mean(prices)
        std_dev = np.std(prices)
        
        # Calculate z-score
        z_score = (current_price - mean) / std_dev if std_dev > 0 else 0
        
        # Calculate Bollinger Bands
        bands = self._calculate_bollinger_bands(mean, std_dev)
        
        # Calculate score
        score = self._calculate_score(z_score)
        
        # Calculate expected return
        expected_move = self._calculate_expected_return(z_score, std_dev)
        
        details = {
            "mean": mean,
            "std_dev": std_dev,
            "z_score": z_score,
            "bollinger_bands": bands,
            "expected_move": expected_move,
            "deviation_level": self._get_deviation_level(z_score)
        }
        
        return score, details
    
    def _calculate_bollinger_bands(self, mean: float, std_dev: float) -> Dict[str, float]:
        """Calculate 2-std-dev Bollinger Bands."""
        return {
            'upper': mean + (2 * std_dev),
            'middle': mean,
            'lower': mean - (2 * std_dev)
        }
    
    def _calculate_score(self, z_score: float) -> float:
        """Score based on statistical deviation."""
        abs_z = abs(z_score)
        
        if abs_z >= self.config.z_score_extreme:
            return 100  # 3+ std devs = extreme
        elif abs_z >= self.config.z_score_threshold:
            return 80   # 2+ std devs = high probability
        elif abs_z >= 1.5:
            return 60
        elif abs_z >= 1.0:
            return 40
        else:
            return 20
    
    def _calculate_expected_return(self, z_score: float, std_dev: float) -> float:
        """Calculate expected price move back to mean."""
        return z_score * std_dev
    
    def _get_deviation_level(self, z_score: float) -> str:
        """Categorize deviation."""
        abs_z = abs(z_score)
        if abs_z >= 3.0:
            return "EXTREME"
        elif abs_z >= 2.0:
            return "HIGH"
        elif abs_z >= 1.0:
            return "MODERATE"
        else:
            return "LOW"
    
    def get_signal(self, score: float, details: Dict[str, Any]) -> str:
        """Convert score to trading signal."""
        if score < 60:
            return "NEUTRAL"
        
        z_score = details['z_score']
        
        if z_score > 2.0:
            return "SHORT"  # Overextended up, expect mean reversion
        elif z_score < -2.0:
            return "LONG"   # Overextended down, expect mean reversion
        else:
            return "NEUTRAL"
```

---

## Phase 3: Scoring System

**Timeline**: Week 6-7  
**Goal**: Integrate all strategy layers into unified evaluation system

### Step 3.1: Strategy Evaluator

**File**: `evaluation/strategy_evaluator.py`

**Purpose**: Orchestrate all 5 strategies and produce final score

**Implementation**:
```python
from typing import Dict, Any, List, Tuple
from strategies.order_book_imbalance import OrderBookImbalanceStrategy
from strategies.vwap_deviation import VWAPDeviationStrategy
from strategies.funding_arbitrage import FundingArbitrageStrategy
from strategies.oi_volume_divergence import OIVolumeDivergenceStrategy
from strategies.mean_reversion import MeanReversionStrategy
from config.strategy_config import STRATEGY_WEIGHTS

class InstitutionalStrategyEvaluator:
    """Main evaluation system that combines all strategy layers."""
    
    def __init__(self):
        """Initialize all strategy components."""
        self.strategies = {
            'order_book': OrderBookImbalanceStrategy(),
            'vwap': VWAPDeviationStrategy(),
            'funding': FundingArbitrageStrategy(),
            'oi_volume': OIVolumeDivergenceStrategy(),
            'mean_reversion': MeanReversionStrategy()
        }
        self.weights = STRATEGY_WEIGHTS
    
    def evaluate_trade(self, coin: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete evaluation of a trading opportunity.
        
        Args:
            coin: Trading pair symbol
            market_data: Dictionary containing all market data
                Required keys depend on enabled strategies:
                - order_book, historical_imbalances, price_change_5m
                - candles, current_price
                - funding_rate, funding_history
                - price_change_4h, oi_change_4h, volume_vs_average
        
        Returns:
            Dictionary with:
                - total_score: Weighted final score (0-100)
                - individual_scores: Score breakdown by strategy
                - signals: Trading signals from each strategy
                - recommendation: Final trade recommendation
                - confidence: Statistical confidence level
        """
        individual_scores = {}
        individual_details = {}
        signals = {}
        
        # Run each strategy
        for name, strategy in self.strategies.items():
            try:
                score, details = strategy.analyze(coin, market_data)
                signal = strategy.get_signal(score, details)
                
                individual_scores[name] = score
                individual_details[name] = details
                signals[name] = signal
            except Exception as e:
                print(f"Error in {name} strategy: {e}")
                individual_scores[name] = 0
                signals[name] = "ERROR"
        
        # Calculate weighted total score
        total_score = self._calculate_weighted_score(individual_scores)
        
        # Generate final recommendation
        recommendation = self._generate_recommendation(total_score, signals, individual_details)
        
        # Calculate confidence
        confidence = self._calculate_confidence(individual_scores, signals)
        
        return {
            'coin': coin,
            'total_score': total_score,
            'individual_scores': individual_scores,
            'individual_details': individual_details,
            'signals': signals,
            'recommendation': recommendation,
            'confidence': confidence,
            'timestamp': self._get_timestamp()
        }
    
    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted average of all strategy scores."""
        total = 0.0
        
        total += scores.get('order_book', 0) * self.weights.order_book_imbalance
        total += scores.get('vwap', 0) * self.weights.vwap_deviation
        total += scores.get('funding', 0) * self.weights.funding_rate
        total += scores.get('oi_volume', 0) * self.weights.oi_volume
        total += scores.get('mean_reversion', 0) * self.weights.mean_reversion
        
        return min(100, total)
    
    def _generate_recommendation(
        self, 
        total_score: float, 
        signals: Dict[str, str],
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate actionable trade recommendation."""
        
        # Count signal votes
        long_votes = sum(1 for s in signals.values() if s == "LONG")
        short_votes = sum(1 for s in signals.values() if s == "SHORT")
        total_votes = long_votes + short_votes
        
        # Determine direction
        if total_score < 40:
            direction = "NO_TRADE"
            reason = "Score too low (< 40)"
        elif long_votes > short_votes and long_votes >= 3:
            direction = "LONG"
            reason = f"{long_votes} strategies signal LONG"
        elif short_votes > long_votes and short_votes >= 3:
            direction = "SHORT"
            reason = f"{short_votes} strategies signal SHORT"
        else:
            direction = "NO_TRADE"
            reason = "Mixed signals, no consensus"
        
        # Determine position size based on score
        position_size = self._calculate_position_size(total_score)
        
        # Generate entry/exit levels
        levels = self._calculate_trade_levels(direction, details)
        
        return {
            'action': direction,
            'reason': reason,
            'position_size_pct': position_size,
            'entry_price': levels.get('entry'),
            'stop_loss': levels.get('stop'),
            'take_profit_1': levels.get('tp1'),
            'take_profit_2': levels.get('tp2'),
            'risk_reward_ratio': levels.get('rr_ratio')
        }
    
    def _calculate_position_size(self, score: float) -> float:
        """Calculate position size as % of account based on score.
        
        Score ranges:
        80-100: 2.5% risk (high confidence)
        60-79:  1.5% risk (medium confidence)
        40-59:  0.75% risk (low confidence)
        < 40:   0% (no trade)
        """
        if score >= 80:
            return 2.5
        elif score >= 60:
            return 1.5
        elif score >= 40:
            return 0.75
        else:
            return 0.0
    
    def _calculate_trade_levels(self, direction: str, details: Dict[str, Any]) -> Dict[str, float]:
        """Calculate entry, stop, and target levels based on strategy details."""
        if direction == "NO_TRADE":
            return {}
        
        # Extract key levels from strategy details
        current_price = details.get('vwap', {}).get('current_price', 0)
        vwap = details.get('vwap', {}).get('vwap', current_price)
        std_dev = details.get('vwap', {}).get('std_dev', 0)
        
        if direction == "LONG":
            entry = current_price
            stop = entry - (1.5 * std_dev)  # 1.5 ATR stop
            tp1 = vwap  # First target: VWAP
            tp2 = vwap + (2 * std_dev)  # Second target: +2 std dev
        else:  # SHORT
            entry = current_price
            stop = entry + (1.5 * std_dev)
            tp1 = vwap
            tp2 = vwap - (2 * std_dev)
        
        risk = abs(entry - stop)
        reward = abs(entry - tp2)
        rr_ratio = reward / risk if risk > 0 else 0
        
        return {
            'entry': entry,
            'stop': stop,
            'tp1': tp1,
            'tp2': tp2,
            'rr_ratio': rr_ratio
        }
    
    def _calculate_confidence(self, scores: Dict[str, float], signals: Dict[str, str]) -> float:
        """Calculate statistical confidence in the recommendation.
        
        Based on:
        - Average score across strategies
        - Signal consensus (how many agree)
        - Score distribution (tight = higher confidence)
        """
        # Average score
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        
        # Signal consensus
        signal_list = list(signals.values())
        consensus = max(signal_list.count('LONG'), signal_list.count('SHORT'))
        consensus_pct = consensus / len(signal_list) if signal_list else 0
        
        # Score consistency (low std dev = high confidence)
        score_list = list(scores.values())
        score_std = np.std(score_list) if score_list else 0
        consistency = 1 - (score_std / 50)  # Normalize to 0-1
        
        # Combined confidence
        confidence = (avg_score * 0.5 + consensus_pct * 30 + consistency * 20) / 100
        
        return min(1.0, confidence)
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        from datetime import datetime, timezone
        return int(datetime.now(tz=timezone.utc).timestamp() * 1000)
```

**Testing Requirements**:
- [ ] Test with all strategies returning max scores
- [ ] Test with conflicting signals
- [ ] Test confidence calculation edge cases
- [ ] Validate position sizing logic

---

### Step 3.2: Trade Generator

**File**: `evaluation/trade_generator.py`

**Purpose**: Convert evaluator output into formatted trade recommendations for the agent

**Implementation**:
```python
from typing import Dict, Any
from datetime import datetime, timezone

class TradeGenerator:
    """Formats evaluation results into agent-readable trade recommendations."""
    
    def generate_trade_report(self, evaluation: Dict[str, Any]) -> str:
        """Generate markdown-formatted trade report.
        
        Args:
            evaluation: Output from InstitutionalStrategyEvaluator
        
        Returns:
            Markdown-formatted report string
        """
        coin = evaluation['coin']
        total_score = evaluation['total_score']
        recommendation = evaluation['recommendation']
        confidence = evaluation['confidence']
        
        # Build report
        report = self._build_report_header(coin, total_score, confidence)
        report += self._build_score_breakdown(evaluation['individual_scores'])
        report += self._build_signal_summary(evaluation['signals'])
        report += self._build_trade_recommendation(recommendation)
        report += self._build_strategy_insights(evaluation['individual_details'])
        
        return report
    
    def _build_report_header(self, coin: str, total_score: float, confidence: float) -> str:
        """Build report header with overall metrics."""
        grade = self._score_to_grade(total_score)
        
        return f"""## {coin} Trading Analysis

**Overall Score: {total_score:.1f}/100 ({grade})**
**Confidence Level: {confidence*100:.1f}%**

---

"""
    
    def _build_score_breakdown(self, scores: Dict[str, float]) -> str:
        """Build detailed score breakdown table."""
        lines = ["### Strategy Layer Scores\n"]
        lines.append("| Layer | Score | Rating |")
        lines.append("|-------|-------|--------|")
        
        layer_names = {
            'order_book': 'Order Book Imbalance',
            'vwap': 'VWAP Deviation',
            'funding': 'Funding Rate',
            'oi_volume': 'OI/Volume Analysis',
            'mean_reversion': 'Mean Reversion'
        }
        
        for key, score in scores.items():
            name = layer_names.get(key, key)
            rating = self._score_to_emoji(score)
            lines.append(f"| {name} | {score:.1f} | {rating} |")
        
        lines.append("\n---\n")
        return "\n".join(lines)
    
    def _build_signal_summary(self, signals: Dict[str, str]) -> str:
        """Build signal consensus summary."""
        long_count = sum(1 for s in signals.values() if s == "LONG")
        short_count = sum(1 for s in signals.values() if s == "SHORT")
        neutral_count = sum(1 for s in signals.values() if s == "NEUTRAL")
        
        return f"""### Signal Consensus

- **LONG**: {long_count}/5 strategies
- **SHORT**: {short_count}/5 strategies
- **NEUTRAL**: {neutral_count}/5 strategies

---

"""
    
    def _build_trade_recommendation(self, rec: Dict[str, Any]) -> str:
        """Build actionable trade recommendation."""
        action = rec.get('action', 'NO_TRADE')
        
        if action == "NO_TRADE":
            return f"""### Recommendation: NO TRADE

**Reason**: {rec.get('reason', 'Insufficient setup quality')}

---

"""
        
        return f"""### Recommendation: {action}

**Reason**: {rec.get('reason')}
**Position Size**: {rec.get('position_size_pct', 0):.2f}% of account

**Trade Levels**:
- Entry: ${rec.get('entry_price', 0):.2f}
- Stop Loss: ${rec.get('stop_loss', 0):.2f}
- Take Profit 1: ${rec.get('take_profit_1', 0):.2f}
- Take Profit 2: ${rec.get('take_profit_2', 0):.2f}

**Risk/Reward**: {rec.get('risk_reward_ratio', 0):.2f}:1

---

"""
    
    def _build_strategy_insights(self, details: Dict[str, Any]) -> str:
        """Build detailed insights from each strategy."""
        lines = ["### Strategy Insights\n"]
        
        # Order Book
        ob = details.get('order_book', {})
        if ob:
            imbalance = ob.get('imbalance', 0)
            signal_type = ob.get('signal_type', 'NEUTRAL')
            lines.append(f"**Order Book**: {signal_type}")
            lines.append(f"- Imbalance: {imbalance:+.2f} ({'Bid heavy' if imbalance > 0 else 'Ask heavy'})")
            lines.append("")
        
        # VWAP
        vwap = details.get('vwap', {})
        if vwap:
            z_score = vwap.get('z_score', 0)
            deviation = vwap.get('deviation_level', 'UNKNOWN')
            lines.append(f"**VWAP**: {deviation} deviation")
            lines.append(f"- Z-Score: {z_score:.2f}")
            lines.append(f"- Price vs VWAP: ${vwap.get('current_price', 0):.2f} vs ${vwap.get('vwap', 0):.2f}")
            lines.append("")
        
        # Funding
        funding = details.get('funding', {})
        if funding:
            annualized = funding.get('annualized_rate', 0)
            lines.append(f"**Funding Rate**: {annualized*100:.2f}% annualized")
            lines.append(f"- Opportunity: {funding.get('opportunity_type', 'NONE')}")
            lines.append("")
        
        # OI/Volume
        oi = details.get('oi_volume', {})
        if oi:
            scenario = oi.get('scenario', 'UNKNOWN')
            lines.append(f"**OI/Volume**: {scenario}")
            lines.append(f"- Price change: {oi.get('price_change', 0):+.2f}%")
            lines.append(f"- OI change: {oi.get('oi_change', 0):+.2f}%")
            lines.append("")
        
        # Mean Reversion
        mr = details.get('mean_reversion', {})
        if mr:
            z_score = mr.get('z_score', 0)
            expected = mr.get('expected_move', 0)
            lines.append(f"**Mean Reversion**: {mr.get('deviation_level', 'UNKNOWN')}")
            lines.append(f"- Z-Score: {z_score:.2f}")
            lines.append(f"- Expected move to mean: ${abs(expected):.2f}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 80:
            return "A+"
        elif score >= 70:
            return "A"
        elif score >= 60:
            return "B+"
        elif score >= 50:
            return "B"
        else:
            return "C"
    
    def _score_to_emoji(self, score: float) -> str:
        """Convert score to emoji rating."""
        if score >= 80:
            return "✓✓"
        elif score >= 60:
            return "✓"
        elif score >= 40:
            return "○"
        else:
            return "✗"
```

---

## Phase 4: Integration & Testing

**Timeline**: Week 8-10  
**Goal**: Integrate with existing agent, build backtesting framework

### Step 4.1: Agent Integration

**File**: `agent/agent.py` (modify existing)

**Changes Required**:

1. **Update System Prompt**:
```python
SYSTEM_PROMPT_CORE = f"""You are EMERALD (Effective Market Evaluation and Rigorous Analysis for Logical Decisions), an institutional-grade Hyperliquid trading assistant.

Core Directive:
You operate using 5 quantitative strategy layers:
1. Order Book Imbalance - Market microstructure analysis
2. VWAP Deviation - Statistical mean reversion
3. Funding Rate Analysis - Arbitrage opportunities
4. OI/Volume Divergence - Smart money tracking
5. Mean Reversion - Z-score extremes

Your analysis is purely quantitative. Every trade recommendation includes:
- Numerical score (0-100)
- Statistical confidence level
- Clear entry/stop/target levels
- Position sizing based on setup quality

You do NOT use ICT concepts, patterns, or subjective analysis.

Tool Usage:
When a user requests analysis, you will:
1. Fetch order book data (fetch_order_book)
2. Fetch funding rates (fetch_funding_rate)
3. Fetch open interest (fetch_open_interest)
4. Fetch candle data (fetch_candles_with_volume_analysis)
5. Run complete evaluation via InstitutionalStrategyEvaluator
6. Present formatted results

Be direct, quantitative, and actionable.
"""
```

2. **Add New Tool Registrations**:
```python
from tools.fetch_order_book import fetch_order_book
from tools.fetch_funding import fetch_funding_rate
from tools.fetch_open_interest import fetch_open_interest
from evaluation.strategy_evaluator import InstitutionalStrategyEvaluator
from evaluation.trade_generator import TradeGenerator

# Create evaluator and generator instances
evaluator = InstitutionalStrategyEvaluator()
trade_generator = TradeGenerator()

# Register tools with agent
agent = create_agent(
    model=model,
    tools=[
        fetch_order_book,
        fetch_funding_rate,
        fetch_open_interest,
        fetch_candles_with_volume_analysis,
    ],
    system_prompt=SYSTEM_PROMPT,
)
```

3. **Create Evaluation Wrapper Tool**:
```python
@tool
def analyze_trading_opportunity(
    coin: str,
    interval: str = "1h"
) -> str:
    """Complete institutional analysis of a trading opportunity.
    
    Args:
        coin: Trading pair (e.g., "BTC", "ETH")
        interval: Timeframe for analysis
    
    Returns:
        Formatted markdown report with scores and recommendation
    """
    # Gather all required data
    market_data = {
        'order_book': fetch_order_book(coin),
        'funding_rate': fetch_funding_rate(coin),
        'oi_data': fetch_open_interest(coin),
        'candles': fetch_candles_with_volume_analysis(coin, interval, 48, 100),
        'current_price': get_current_price(coin),
        # Add more data points as needed
    }
    
    # Run evaluation
    evaluation = evaluator.evaluate_trade(coin, market_data)
    
    # Generate report
    report = trade_generator.generate_trade_report(evaluation)
    
    return report
```

---

### Step 4.2: Backtesting Framework

**File**: `backtest/backtester.py`

**Purpose**: Test strategies against historical data

**Implementation**:
```python
from typing import Dict, Any, List
import pandas as pd
from evaluation.strategy_evaluator import InstitutionalStrategyEvaluator
from datetime import datetime, timedelta

class Backtester:
    """Backtest trading strategies on historical data."""
    
    def __init__(self, initial_capital: float = 10000.0):
        """Initialize backtester.
        
        Args:
            initial_capital: Starting account balance
        """
        self.evaluator = InstitutionalStrategyEvaluator()
        self.initial_capital = initial_capital
        self.trades = []
    
    def run_backtest(
        self,
        coin: str,
        start_date: str,
        end_date: str,
        interval: str = "1h"
    ) -> Dict[str, Any]:
        """Run backtest over date range.
        
        Args:
            coin: Trading pair
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Candle interval
        
        Returns:
            Dictionary with performance metrics
        """
        # Fetch historical data for entire period
        historical_data = self._fetch_historical_data(coin, start_date, end_date, interval)
        
        # Sliding window through history
        window_size = 100  # Number of candles needed for analysis
        
        for i in range(window_size, len(historical_data)):
            window = historical_data[i-window_size:i]
            current_candle = historical_data[i]
            
            # Prepare market data for this point in time
            market_data = self._prepare_market_data(window, current_candle)
            
            # Run evaluation
            evaluation = self.evaluator.evaluate_trade(coin, market_data)
            
            # Check if trade signal
            if evaluation['recommendation']['action'] in ['LONG', 'SHORT']:
                trade_result = self._simulate_trade(
                    evaluation,
                    current_candle,
                    historical_data[i:i+100]  # Future candles for exit
                )
                self.trades.append(trade_result)
        
        # Calculate performance metrics
        performance = self._calculate_performance()
        
        return performance
    
    def _fetch_historical_data(self, coin: str, start: str, end: str, interval: str) -> List[Dict]:
        """Fetch historical candle data."""
        # Implementation depends on your data source
        # Could use Hyperliquid API, database, or CSV files
        pass
    
    def _prepare_market_data(self, window: List[Dict], current: Dict) -> Dict[str, Any]:
        """Prepare market data dict for evaluation."""
        # Calculate all required metrics from window
        # This includes VWAP, volume ratios, z-scores, etc.
        pass
    
    def _simulate_trade(
        self,
        evaluation: Dict[str, Any],
        entry_candle: Dict,
        future_candles: List[Dict]
    ) -> Dict[str, Any]:
        """Simulate trade execution and exit."""
        recommendation = evaluation['recommendation']
        direction = recommendation['action']
        entry_price = entry_candle['close']
        stop_loss = recommendation['stop_loss']
        take_profit = recommendation['take_profit_2']
        
        # Simulate trade through future candles
        for candle in future_candles:
            if direction == "LONG":
                if candle['low'] <= stop_loss:
                    # Stopped out
                    exit_price = stop_loss
                    outcome = "LOSS"
                    break
                elif candle['high'] >= take_profit:
                    # Hit target
                    exit_price = take_profit
                    outcome = "WIN"
                    break
            else:  # SHORT
                if candle['high'] >= stop_loss:
                    exit_price = stop_loss
                    outcome = "LOSS"
                    break
                elif candle['low'] <= take_profit:
                    exit_price = take_profit
                    outcome = "WIN"
                    break
        else:
            # No exit triggered, close at last candle
            exit_price = future_candles[-1]['close']
            outcome = "TIMEOUT"
        
        # Calculate PnL
        if direction == "LONG":
            pnl_pct = (exit_price - entry_price) / entry_price * 100
        else:
            pnl_pct = (entry_price - exit_price) / entry_price * 100
        
        return {
            'entry_time': entry_candle['timestamp'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'direction': direction,
            'outcome': outcome,
            'pnl_pct': pnl_pct,
            'score': evaluation['total_score'],
            'confidence': evaluation['confidence']
        }
    
    def _calculate_performance(self) -> Dict[str, Any]:
        """Calculate overall backtest performance."""
        if not self.trades:
            return {"error": "No trades executed"}
        
        df = pd.DataFrame(self.trades)
        
        wins = df[df['outcome'] == 'WIN']
        losses = df[df['outcome'] == 'LOSS']
        
        win_rate = len(wins) / len(df) * 100
        avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0
        
        # Calculate cumulative returns
        df['cumulative_pnl'] = df['pnl_pct'].cumsum()
        
        # Sharpe ratio (simplified)
        returns = df['pnl_pct']
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Max drawdown
        cumulative = (1 + df['pnl_pct'] / 100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'total_trades': len(df),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_return': df['pnl_pct'].sum(),
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'trades_by_score': self._analyze_by_score(df)
        }
    
    def _analyze_by_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by score ranges."""
        ranges = {
            '80-100': df[df['score'] >= 80],
            '60-79': df[(df['score'] >= 60) & (df['score'] < 80)],
            '40-59': df[(df['score'] >= 40) & (df['score'] < 60)]
        }
        
        results = {}
        for range_name, subset in ranges.items():
            if len(subset) > 0:
                wins = subset[subset['outcome'] == 'WIN']
                results[range_name] = {
                    'count': len(subset),
                    'win_rate': len(wins) / len(subset) * 100,
                    'avg_return': subset['pnl_pct'].mean()
                }
        
        return results
```

---

## Phase 5: Production Deployment

**Timeline**: Week 11-12  
**Goal**: Deploy system for live trading

### Step 5.1: Position Management

**File**: `execution/position_manager.py`

**Purpose**: Manage open positions, stops, and targets

```python
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class PositionManager:
    """Manages open trading positions."""
    
    def __init__(self, positions_file: str = "open_positions.json"):
        """Initialize position manager.
        
        Args:
            positions_file: Path to JSON file storing positions
        """
        self.positions_file = positions_file
        self.positions = self._load_positions()
    
    def open_position(
        self,
        coin: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: float,
        size: float,
        evaluation: Dict[str, Any]
    ) -> str:
        """Open a new position.
        
        Returns:
            Position ID
        """
        position_id = self._generate_position_id()
        
        position = {
            'id': position_id,
            'coin': coin,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'size': size,
            'size_remaining': size,
            'entry_time': datetime.now().isoformat(),
            'status': 'OPEN',
            'evaluation_score': evaluation['total_score'],
            'confidence': evaluation['confidence']
        }
        
        self.positions[position_id] = position
        self._save_positions()
        
        return position_id
    
    def update_position(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """Check position against stops/targets and update.
        
        Returns:
            Dictionary with any actions taken (stop hit, target hit, etc.)
        """
        if position_id not in self.positions:
            return {'error': 'Position not found'}
        
        position = self.positions[position_id]
        actions = []
        
        if position['direction'] == 'LONG':
            # Check stop loss
            if current_price <= position['stop_loss']:
                self.close_position(position_id, current_price, reason="STOP_LOSS")
                actions.append('STOPPED_OUT')
            
            # Check targets
            elif current_price >= position['take_profit_2']:
                self.close_position(position_id, current_price, reason="TARGET_2")
                actions.append('TARGET_2_HIT')
            
            elif current_price >= position['take_profit_1'] and position['size_remaining'] == position['size']:
                # Take partial profit at TP1
                self._partial_close(position_id, 0.5, current_price)
                actions.append('TARGET_1_HIT')
        
        else:  # SHORT
            if current_price >= position['stop_loss']:
                self.close_position(position_id, current_price, reason="STOP_LOSS")
                actions.append('STOPPED_OUT')
            
            elif current_price <= position['take_profit_2']:
                self.close_position(position_id, current_price, reason="TARGET_2")
                actions.append('TARGET_2_HIT')
            
            elif current_price <= position['take_profit_1'] and position['size_remaining'] == position['size']:
                self._partial_close(position_id, 0.5, current_price)
                actions.append('TARGET_1_HIT')
        
        self._save_positions()
        return {'actions': actions, 'position': position}
    
    def close_position(self, position_id: str, exit_price: float, reason: str = "MANUAL"):
        """Close a position completely."""
        position = self.positions[position_id]
        
        # Calculate PnL
        if position['direction'] == 'LONG':
            pnl = (exit_price - position['entry_price']) * position['size_remaining']
        else:
            pnl = (position['entry_price'] - exit_price) * position['size_remaining']
        
        position['exit_price'] = exit_price
        position['exit_time'] = datetime.now().isoformat()
        position['status'] = 'CLOSED'
        position['close_reason'] = reason
        position['pnl'] = pnl
        
        self._save_positions()
    
    def _partial_close(self, position_id: str, percentage: float, price: float):
        """Close part of a position."""
        position = self.positions[position_id]
        close_size = position['size'] * percentage
        position['size_remaining'] -= close_size
        
        # Trail stop to breakeven after taking partial profit
        position['stop_loss'] = position['entry_price']
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        return [p for p in self.positions.values() if p['status'] == 'OPEN']
    
    def _load_positions(self) -> Dict[str, Any]:
        """Load positions from file."""
        try:
            with open(self.positions_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_positions(self):
        """Save positions to file."""
        with open(self.positions_file, 'w') as f:
            json.dump(self.positions, f, indent=2)
    
    def _generate_position_id(self) -> str:
        """Generate unique position ID."""
        return f"POS_{datetime.now().strftime('%Y%m%d%H%M%S')}"
```

---

### Step 5.2: Risk Management

**File**: `execution/risk_manager.py`

**Purpose**: Enforce risk limits

```python
class RiskManager:
    """Enforces risk management rules."""
    
    def __init__(
        self,
        max_daily_loss_pct: float = 5.0,
        max_position_size_pct: float = 10.0,
        max_open_positions: int = 3,
        max_correlated_positions: int = 2
    ):
        """Initialize risk manager with limits."""
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_position_size_pct = max_position_size_pct
        self.max_open_positions = max_open_positions
        self.max_correlated_positions = max_correlated_positions
    
    def can_open_position(
        self,
        coin: str,
        size_usd: float,
        account_balance: float,
        open_positions: List[Dict],
        daily_pnl: float
    ) -> tuple[bool, str]:
        """Check if a position can be opened.
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Check daily loss limit
        if daily_pnl < -(self.max_daily_loss_pct / 100 * account_balance):
            return False, f"Daily loss limit reached ({self.max_daily_loss_pct}%)"
        
        # Check max open positions
        if len(open_positions) >= self.max_open_positions:
            return False, f"Max open positions reached ({self.max_open_positions})"
        
        # Check position size
        size_pct = size_usd / account_balance * 100
        if size_pct > self.max_position_size_pct:
            return False, f"Position size too large ({size_pct:.1f}% > {self.max_position_size_pct}%)"
        
        # Check correlation (simplified - just count same coin)
        same_coin_positions = [p for p in open_positions if p['coin'] == coin]
        if len(same_coin_positions) >= self.max_correlated_positions:
            return False, f"Too many {coin} positions open"
        
        return True, "APPROVED"
```

---

### Step 5.3: Monitoring & Alerts

**File**: `execution/monitor.py`

**Purpose**: Monitor positions and send alerts

```python
import time
from datetime import datetime
from typing import List, Dict, Any

class TradingMonitor:
    """Monitors positions and sends alerts."""
    
    def __init__(self, position_manager, risk_manager):
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.alert_log = []
    
    def monitor_loop(self, interval_seconds: int = 60):
        """Main monitoring loop.
        
        Args:
            interval_seconds: How often to check positions
        """
        while True:
            self._check_all_positions()
            time.sleep(interval_seconds)
    
    def _check_all_positions(self):
        """Check all open positions."""
        open_positions = self.position_manager.get_open_positions()
        
        for position in open_positions:
            # Fetch current price
            current_price = self._get_current_price(position['coin'])
            
            # Update position
            result = self.position_manager.update_position(
                position['id'],
                current_price
            )
            
            # Send alerts if needed
            if 'actions' in result and result['actions']:
                self._send_alert(position, result['actions'], current_price)
    
    def _get_current_price(self, coin: str) -> float:
        """Fetch current market price."""
        # Implementation using Hyperliquid API
        pass
    
    def _send_alert(self, position: Dict, actions: List[str], price: float):
        """Send alert notification."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'position_id': position['id'],
            'coin': position['coin'],
            'actions': actions,
            'current_price': price
        }
        
        self.alert_log.append(alert)
        
        # Could integrate with:
        # - Discord webhook
        # - Telegram bot
        # - Email
        # - SMS
        
        print(f"ALERT: {position['coin']} - {', '.join(actions)} at ${price}")
```

---

## Appendix: Key Formulas

### Order Book Imbalance
```
imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

Range: -1 to +1
- Positive = bid pressure (bullish)
- Negative = ask pressure (bearish)
```

### VWAP Calculation
```
VWAP = Σ(Typical Price × Volume) / Σ(Volume)

where Typical Price = (High + Low + Close) / 3
```

### Z-Score
```
z_score = (current_price - mean_price) / std_deviation

Interpretation:
- |z| > 2.0 = Extreme (2+ std devs from mean)
- |z| > 1.5 = High
- |z| > 1.0 = Moderate
```

### Funding Rate Annualization
```
annualized_rate = funding_rate_8h × 3 periods/day × 365 days

Example:
0.01% per 8h = 0.0001 × 3 × 365 = 10.95% annualized
```

### Bollinger Bands
```
Middle Band = 20-period SMA
Upper Band = Middle Band + (2 × std_dev)
Lower Band = Middle Band - (2 × std_dev)
```

### Risk/Reward Ratio
```
RR = (Take Profit - Entry) / (Entry - Stop Loss)

Minimum acceptable: 2:1
Good setups: 3:1 or higher
```

---

## Final Checklist

### Before Starting Development
- [ ] Review entire implementation guide
- [ ] Understand all 5 strategy layers
- [ ] Set up development environment
- [ ] Create git repository with proper structure

### Phase 1 Completion
- [ ] All data fetchers working
- [ ] Caching system functional
- [ ] Unit tests pass for each fetcher
- [ ] Configuration file complete

### Phase 2 Completion
- [ ] All 5 strategy classes implemented
- [ ] Each strategy returns 0-100 score
- [ ] Unit tests pass for each strategy
- [ ] Strategies tested with real data

### Phase 3 Completion
- [ ] Strategy evaluator combines all layers
- [ ] Scoring system produces consistent results
- [ ] Trade generator creates formatted reports
- [ ] Integration tests pass

### Phase 4 Completion
- [ ] Agent integration complete
- [ ] Backtesting framework functional
- [ ] Performance metrics calculated correctly
- [ ] Historical data pipeline working

### Phase 5 Completion
- [ ] Position management system live
- [ ] Risk management enforced
- [ ] Monitoring system running
- [ ] Alert system functional

---

## Support & Questions

For implementation questions, refer to:
- This guide (primary reference)
- Python documentation for NumPy, Pandas
- LangChain documentation for agent integration
- Hyperliquid API documentation

Good luck building EMERALD into an institutional-grade trading system!

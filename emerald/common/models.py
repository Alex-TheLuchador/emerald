"""
Data models for the trading system

Uses Pydantic for validation and serialization
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class SignalAction(str, Enum):
    """Trading signal actions"""
    LONG = "LONG"
    SHORT = "SHORT"
    SKIP = "SKIP"


class Confidence(str, Enum):
    """Signal confidence levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class OrderBookLevel(BaseModel):
    """Single order book level"""
    px: str = Field(..., description="Price")
    sz: str = Field(..., description="Size")
    n: int = Field(..., description="Number of orders")

    @property
    def price(self) -> float:
        return float(self.px)

    @property
    def size(self) -> float:
        return float(self.sz)


class OrderBook(BaseModel):
    """Order book snapshot"""
    coin: str
    levels: List[List[OrderBookLevel]]
    time: int

    @property
    def bids(self) -> List[OrderBookLevel]:
        """Get bid levels"""
        if len(self.levels) >= 1:
            return [OrderBookLevel(**level) if isinstance(level, dict) else level
                    for level in self.levels[0]]
        return []

    @property
    def asks(self) -> List[OrderBookLevel]:
        """Get ask levels"""
        if len(self.levels) >= 2:
            return [OrderBookLevel(**level) if isinstance(level, dict) else level
                    for level in self.levels[1]]
        return []


class Candle(BaseModel):
    """OHLCV candle"""
    t: int = Field(..., description="Timestamp (ms)")
    o: str = Field(..., description="Open")
    h: str = Field(..., description="High")
    l: str = Field(..., description="Low")
    c: str = Field(..., description="Close")
    v: str = Field(..., description="Volume")
    n: int = Field(..., description="Number of trades")

    @property
    def open(self) -> float:
        return float(self.o)

    @property
    def high(self) -> float:
        return float(self.h)

    @property
    def low(self) -> float:
        return float(self.l)

    @property
    def close(self) -> float:
        return float(self.c)

    @property
    def volume(self) -> float:
        return float(self.v)


class PerpData(BaseModel):
    """Perpetual futures market data"""
    funding: Optional[str] = None
    openInterest: Optional[str] = None
    markPx: Optional[str] = None

    @property
    def funding_rate(self) -> float:
        return float(self.funding) if self.funding else 0.0

    @property
    def open_interest(self) -> float:
        return float(self.openInterest) if self.openInterest else 0.0

    @property
    def mark_price(self) -> float:
        return float(self.markPx) if self.markPx else 0.0


class SpotData(BaseModel):
    """Spot market data"""
    midPx: Optional[str] = None

    @property
    def mid_price(self) -> float:
        return float(self.midPx) if self.midPx else 0.0


class MarketData(BaseModel):
    """Complete market data for a coin"""
    coin: str
    order_book: OrderBook
    perp_data: PerpData
    spot_data: SpotData
    candles: List[Candle]
    timestamp: datetime = Field(default_factory=datetime.now)


class MetricResult(BaseModel):
    """Result from a metric calculation"""
    name: str
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class Metrics(BaseModel):
    """Collection of calculated metrics"""
    ob_imbalance: float = 0.0
    funding_annualized: float = 0.0
    vwap: float = 0.0
    vwap_deviation_pct: float = 0.0
    vwap_z_score: float = 0.0
    flow_imbalance: float = 0.0
    oi_change_pct: float = 0.0
    price_change_pct: float = 0.0
    oi_divergence_type: str = "unknown"
    basis_pct: float = 0.0
    current_price: float = 0.0

    # Additional metadata
    extra: Dict[str, Any] = Field(default_factory=dict)


class Signal(BaseModel):
    """Trading signal"""
    action: SignalAction
    convergence_score: int = Field(..., ge=0, le=100)
    confidence: Confidence
    aligned_signals: int
    bullish_signals: int
    bearish_signals: int
    score_breakdown: Dict[str, int]
    signal_breakdown: Dict[str, str]
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime = Field(default_factory=datetime.now)

    # Optional metadata
    coin: Optional[str] = None
    metrics: Optional[Metrics] = None


class HistoricalSnapshot(BaseModel):
    """Historical data snapshot"""
    timestamp: float
    coin: str
    data: Dict[str, Any]


class OISnapshot(BaseModel):
    """Open Interest snapshot"""
    oi: float
    price: float
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

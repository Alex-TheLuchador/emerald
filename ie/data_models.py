"""
Data models for Institutional Engine metrics.

These dataclasses provide clean, structured representations of quantitative
market metrics. They are designed to be:
- Easy to serialize (for JSON output)
- Type-safe (with proper type hints)
- Self-documenting (with clear field names)
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Literal
from datetime import datetime


@dataclass
class OrderBookMetrics:
    """Order book analysis metrics."""

    imbalance: float
    """Bid/ask imbalance ratio (-1 to 1). Positive = bid pressure, negative = ask pressure."""

    imbalance_strength: Literal["strong_bid_pressure", "moderate_bid_pressure", "neutral", "moderate_ask_pressure", "strong_ask_pressure"]
    """Human-readable interpretation of imbalance."""

    top_bid: float
    """Best bid price."""

    top_ask: float
    """Best ask price."""

    spread: float
    """Bid-ask spread in price units."""

    spread_bps: float
    """Bid-ask spread in basis points (0.01% = 1 bp)."""

    total_bid_volume: float
    """Total volume on bid side (top N levels)."""

    total_ask_volume: float
    """Total volume on ask side (top N levels)."""

    depth_analyzed: int
    """Number of order book levels analyzed."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class FundingMetrics:
    """Funding rate analysis metrics."""

    rate_8h: float
    """Current 8-hour funding rate (decimal, e.g., 0.0001 = 0.01%)."""

    annualized_pct: float
    """Annualized funding rate as percentage (e.g., 10.95 = 10.95%)."""

    sentiment: Literal["extreme_bullish", "bullish", "neutral", "bearish", "extreme_bearish"]
    """Market sentiment based on funding rate."""

    is_extreme: bool
    """True if funding rate exceeds 10% annualized threshold."""

    historical_avg_24h: Optional[float] = None
    """24-hour average funding rate (if available)."""

    trend: Optional[Literal["increasing", "decreasing", "stable"]] = None
    """Funding rate trend over last 24h (if available)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class OpenInterestMetrics:
    """Open interest analysis metrics."""

    current_usd: float
    """Current open interest in USD."""

    change_1h_pct: float
    """OI percentage change over last 1 hour."""

    change_4h_pct: float
    """OI percentage change over last 4 hours."""

    change_24h_pct: float
    """OI percentage change over last 24 hours."""

    divergence_type: Literal[
        "strong_bullish",      # Price ↑ + OI ↑
        "weak_bullish",        # Price ↑ + OI ↓
        "strong_bearish",      # Price ↓ + OI ↑
        "weak_bearish",        # Price ↓ + OI ↓
        "neutral"
    ]
    """Price-OI divergence scenario."""

    price_change_4h_pct: Optional[float] = None
    """Price percentage change over 4h (for divergence calculation)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class VWAPMetrics:
    """VWAP deviation analysis metrics."""

    vwap_price: float
    """Volume-weighted average price."""

    current_price: float
    """Current market price."""

    deviation_pct: float
    """Percentage deviation from VWAP (positive = above, negative = below)."""

    z_score: float
    """Number of standard deviations from VWAP."""

    deviation_level: Literal["extreme", "high", "moderate", "low"]
    """Severity of price deviation from VWAP."""

    std_dev: float
    """Standard deviation of prices."""

    bands: Dict[str, float]
    """VWAP bands (similar to Bollinger Bands).
    Keys: upper_2std, upper_1std, vwap, lower_1std, lower_2std
    """

    lookback_candles: int
    """Number of candles used for VWAP calculation."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class VolumeMetrics:
    """Volume analysis metrics."""

    current: float
    """Current volume."""

    avg_20: float
    """20-period average volume."""

    ratio: float
    """Current volume vs. 20-period average (e.g., 1.5 = 50% above average)."""

    significance: Literal["very_high", "high", "normal", "low"]
    """Volume significance level."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class InstitutionalMetrics:
    """Complete institutional metrics package.

    This is the top-level data structure returned by the unified
    fetch_institutional_metrics tool.
    """

    coin: str
    """Trading pair symbol (e.g., "BTC")."""

    timestamp: str
    """ISO 8601 timestamp of data collection."""

    price: float
    """Current market price."""

    order_book: Optional[OrderBookMetrics] = None
    """Order book imbalance metrics (if requested)."""

    funding: Optional[FundingMetrics] = None
    """Funding rate metrics (if requested)."""

    open_interest: Optional[OpenInterestMetrics] = None
    """Open interest metrics (if requested)."""

    vwap: Optional[VWAPMetrics] = None
    """VWAP deviation metrics (if requested)."""

    volume: Optional[VolumeMetrics] = None
    """Volume analysis metrics (if requested)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "coin": self.coin,
            "timestamp": self.timestamp,
            "price": self.price,
        }

        if self.order_book:
            result["order_book"] = self.order_book.to_dict()
        if self.funding:
            result["funding"] = self.funding.to_dict()
        if self.open_interest:
            result["open_interest"] = self.open_interest.to_dict()
        if self.vwap:
            result["vwap"] = self.vwap.to_dict()
        if self.volume:
            result["volume"] = self.volume.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstitutionalMetrics":
        """Create InstitutionalMetrics from dictionary."""
        # Extract base fields
        coin = data["coin"]
        timestamp = data["timestamp"]
        price = data["price"]

        # Reconstruct nested metrics if present
        order_book = OrderBookMetrics(**data["order_book"]) if "order_book" in data else None
        funding = FundingMetrics(**data["funding"]) if "funding" in data else None
        open_interest = OpenInterestMetrics(**data["open_interest"]) if "open_interest" in data else None
        vwap = VWAPMetrics(**data["vwap"]) if "vwap" in data else None
        volume = VolumeMetrics(**data["volume"]) if "volume" in data else None

        return cls(
            coin=coin,
            timestamp=timestamp,
            price=price,
            order_book=order_book,
            funding=funding,
            open_interest=open_interest,
            vwap=vwap,
            volume=volume,
        )

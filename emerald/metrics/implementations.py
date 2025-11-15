"""
Concrete metric implementations

Each metric is a self-contained, pluggable component
"""
import numpy as np
from typing import Optional
from datetime import datetime

from .base import BaseMetric
from ..common.models import MarketData, MetricResult, OISnapshot
from ..common.config import get_config


class OrderBookImbalanceMetric(BaseMetric):
    """Calculate order book bid/ask imbalance"""

    @property
    def name(self) -> str:
        return "order_book_imbalance"

    @property
    def description(self) -> str:
        return "Bid/ask liquidity imbalance (-1 to +1)"

    def calculate(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> MetricResult:
        config = get_config()
        levels = config.calculation.order_book_levels

        bids = market_data.order_book.bids[:levels]
        asks = market_data.order_book.asks[:levels]

        # Sum liquidity (size * price)
        bid_liquidity = sum(b.price * b.size for b in bids)
        ask_liquidity = sum(a.price * a.size for a in asks)

        if bid_liquidity + ask_liquidity == 0:
            imbalance = 0.0
        else:
            imbalance = (bid_liquidity - ask_liquidity) / (bid_liquidity + ask_liquidity)

        return MetricResult(
            name=self.name,
            value=round(imbalance, 4),
            metadata={
                "bid_liquidity": bid_liquidity,
                "ask_liquidity": ask_liquidity
            }
        )


class FundingRateMetric(BaseMetric):
    """Calculate annualized funding rate"""

    @property
    def name(self) -> str:
        return "funding_rate"

    @property
    def description(self) -> str:
        return "Annualized funding rate (%)"

    def calculate(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> MetricResult:
        funding_8h = market_data.perp_data.funding_rate

        # Annualize: funding * 3 periods/day * 365 days * 100 for percentage
        annualized_pct = funding_8h * 3 * 365 * 100

        return MetricResult(
            name=self.name,
            value=round(annualized_pct, 2),
            metadata={
                "funding_8h": funding_8h
            }
        )


class VWAPDeviationMetric(BaseMetric):
    """Calculate VWAP and deviation statistics"""

    @property
    def name(self) -> str:
        return "vwap_deviation"

    @property
    def description(self) -> str:
        return "VWAP deviation and z-score"

    def validate_data(self, market_data: MarketData) -> bool:
        config = get_config()
        return len(market_data.candles) >= config.calculation.vwap_lookback_candles

    def calculate(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> MetricResult:
        config = get_config()
        lookback = config.calculation.vwap_lookback_candles

        candles = market_data.candles[-lookback:]

        # Calculate VWAP
        prices = np.array([c.close for c in candles])
        volumes = np.array([c.volume for c in candles])

        if volumes.sum() == 0:
            return MetricResult(
                name=self.name,
                value=0.0,
                metadata={
                    "vwap": 0.0,
                    "deviation_pct": 0.0,
                    "z_score": 0.0
                }
            )

        vwap = np.sum(prices * volumes) / np.sum(volumes)
        current_price = candles[-1].close

        # Percentage deviation
        deviation_pct = ((current_price - vwap) / vwap) * 100

        # Z-score
        std_dev = np.std(prices)
        z_score = (current_price - vwap) / std_dev if std_dev > 0 else 0

        return MetricResult(
            name=self.name,
            value=round(float(z_score), 2),  # Return z-score as primary value
            metadata={
                "vwap": round(float(vwap), 2),
                "deviation_pct": round(float(deviation_pct), 2),
                "z_score": round(float(z_score), 2),
                "current_price": current_price
            }
        )


class TradeFlowMetric(BaseMetric):
    """Calculate trade flow imbalance (aggressor direction)"""

    @property
    def name(self) -> str:
        return "trade_flow"

    @property
    def description(self) -> str:
        return "Trade flow imbalance (positive = buying, negative = selling)"

    def validate_data(self, market_data: MarketData) -> bool:
        config = get_config()
        return len(market_data.candles) >= config.calculation.flow_lookback_candles

    def calculate(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> MetricResult:
        config = get_config()
        lookback = config.calculation.flow_lookback_candles

        candles = market_data.candles
        recent_candles = candles[-lookback:]

        # Calculate average volume for weighting
        volumes = [c.volume for c in candles[-20:]]
        avg_volume = np.mean(volumes) if volumes else 1.0

        flow_scores = []
        for candle in recent_candles:
            if candle.open == 0:
                continue

            # Price change percentage
            price_change_pct = ((candle.close - candle.open) / candle.open) * 100

            # Volume weight
            volume_weight = candle.volume / avg_volume if avg_volume > 0 else 1.0

            # Flow score = direction * intensity
            flow_score = price_change_pct * volume_weight
            flow_scores.append(flow_score)

        total_flow = sum(flow_scores) if flow_scores else 0.0

        return MetricResult(
            name=self.name,
            value=round(total_flow, 4),
            metadata={
                "avg_volume": avg_volume,
                "num_candles": len(flow_scores)
            }
        )


class OIDivergenceMetric(BaseMetric):
    """Calculate OI vs price divergence"""

    @property
    def name(self) -> str:
        return "oi_divergence"

    @property
    def description(self) -> str:
        return "Open Interest divergence (detects real vs fake moves)"

    def validate_data(self, market_data: MarketData) -> bool:
        return len(market_data.candles) > 0

    def calculate(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> MetricResult:
        config = get_config()
        threshold = config.thresholds.oi_change_threshold

        if not historical_oi:
            return MetricResult(
                name=self.name,
                value=0.0,
                metadata={
                    "oi_change_pct": 0.0,
                    "price_change_pct": 0.0,
                    "divergence_type": "unknown"
                }
            )

        current_oi = market_data.perp_data.open_interest
        historical_oi_value = historical_oi.oi
        current_price = market_data.candles[-1].close
        historical_price = historical_oi.price

        if historical_oi_value == 0 or historical_price == 0:
            return MetricResult(
                name=self.name,
                value=0.0,
                metadata={
                    "oi_change_pct": 0.0,
                    "price_change_pct": 0.0,
                    "divergence_type": "unknown"
                }
            )

        oi_change_pct = ((current_oi - historical_oi_value) / historical_oi_value) * 100
        price_change_pct = ((current_price - historical_price) / historical_price) * 100

        # Determine divergence type
        if oi_change_pct > threshold and price_change_pct > 1:
            divergence_type = "strong_bullish"
        elif oi_change_pct > threshold and price_change_pct < -1:
            divergence_type = "strong_bearish"
        elif oi_change_pct < -threshold and price_change_pct > 1:
            divergence_type = "weak_bullish"
        elif oi_change_pct < -threshold and price_change_pct < -1:
            divergence_type = "weak_bearish"
        else:
            divergence_type = "neutral"

        return MetricResult(
            name=self.name,
            value=oi_change_pct,
            metadata={
                "oi_change_pct": round(oi_change_pct, 2),
                "price_change_pct": round(price_change_pct, 2),
                "divergence_type": divergence_type
            }
        )


class BasisSpreadMetric(BaseMetric):
    """Calculate basis spread (perp vs spot)"""

    @property
    def name(self) -> str:
        return "basis_spread"

    @property
    def description(self) -> str:
        return "Basis spread between perpetual and spot markets (%)"

    def calculate(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> MetricResult:
        perp_price = market_data.perp_data.mark_price
        spot_price = market_data.spot_data.mid_price

        if spot_price == 0:
            return MetricResult(
                name=self.name,
                value=0.0,
                metadata={
                    "perp_price": perp_price,
                    "spot_price": spot_price
                }
            )

        basis_pct = ((perp_price - spot_price) / spot_price) * 100

        return MetricResult(
            name=self.name,
            value=round(basis_pct, 4),
            metadata={
                "perp_price": perp_price,
                "spot_price": spot_price
            }
        )

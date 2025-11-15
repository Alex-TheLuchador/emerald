"""
Convergence Strategy

Multi-metric convergence system for high-probability signals
"""
from typing import Dict, Any, Tuple
from datetime import datetime

from .base import BaseStrategy
from ..common.models import (
    Signal,
    SignalAction,
    Confidence,
    MarketData,
    MetricResult,
    Metrics
)
from ..common.config import get_config


class ConvergenceStrategy(BaseStrategy):
    """
    Multi-metric convergence strategy

    Generates signals when multiple metrics align in the same direction
    """

    @property
    def name(self) -> str:
        return "convergence"

    @property
    def description(self) -> str:
        return "Multi-metric convergence system for high-probability setups"

    def generate_signal(
        self,
        market_data: MarketData,
        metrics: Dict[str, MetricResult]
    ) -> Signal:
        """Generate convergence signal"""
        config = get_config()

        # Convert metrics to dict format for scoring
        metrics_dict = self._metrics_to_dict(metrics, market_data)

        # Calculate convergence score
        score, score_breakdown = self._calculate_score(metrics_dict)

        # Count directional signals
        bullish, bearish, signal_breakdown = self._count_directional_signals(metrics_dict)

        # Determine action
        action = self._determine_action(score, bullish, bearish)

        # Calculate price levels
        levels = self._calculate_levels(
            action,
            metrics_dict.get("current_price", 0),
            metrics_dict.get("vwap", 0),
            metrics_dict.get("vwap_z_score", 0)
        )

        # Determine confidence
        confidence = self._determine_confidence(score, max(bullish, bearish))

        return Signal(
            action=action,
            convergence_score=score,
            confidence=confidence,
            aligned_signals=max(bullish, bearish),
            bullish_signals=bullish,
            bearish_signals=bearish,
            score_breakdown=score_breakdown,
            signal_breakdown=signal_breakdown,
            entry_price=levels["entry"],
            stop_loss=levels["stop"],
            take_profit=levels["target"],
            coin=market_data.coin,
            timestamp=datetime.now()
        )

    def _metrics_to_dict(
        self,
        metrics: Dict[str, MetricResult],
        market_data: MarketData
    ) -> Dict[str, Any]:
        """Convert MetricResult objects to dict for backward compatibility"""
        result = {}

        # Extract primary values and metadata
        if "order_book_imbalance" in metrics:
            result["ob_imbalance"] = metrics["order_book_imbalance"].value

        if "funding_rate" in metrics:
            result["funding_annualized"] = metrics["funding_rate"].value

        if "vwap_deviation" in metrics:
            vwap_metric = metrics["vwap_deviation"]
            result["vwap"] = vwap_metric.metadata.get("vwap", 0)
            result["vwap_deviation_pct"] = vwap_metric.metadata.get("deviation_pct", 0)
            result["vwap_z_score"] = vwap_metric.value
            result["current_price"] = vwap_metric.metadata.get("current_price", 0)

        if "trade_flow" in metrics:
            result["flow_imbalance"] = metrics["trade_flow"].value

        if "oi_divergence" in metrics:
            oi_metric = metrics["oi_divergence"]
            result["oi_change_pct"] = oi_metric.metadata.get("oi_change_pct", 0)
            result["price_change_pct"] = oi_metric.metadata.get("price_change_pct", 0)
            result["oi_divergence_type"] = oi_metric.metadata.get("divergence_type", "unknown")

        if "basis_spread" in metrics:
            result["basis_pct"] = metrics["basis_spread"].value

        # Fallback for current price
        if "current_price" not in result and market_data.candles:
            result["current_price"] = market_data.candles[-1].close

        return result

    def _calculate_score(self, metrics: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
        """Calculate convergence score (0-100)"""
        config = get_config()
        score = 0
        breakdown = {}

        # Order Book Imbalance
        ob_imbalance = abs(metrics.get("ob_imbalance", 0))
        if ob_imbalance > config.thresholds.order_book_imbalance_extreme:
            points = config.scoring.order_book_extreme
            breakdown["order_book"] = points
            score += points
        elif ob_imbalance > config.thresholds.order_book_imbalance:
            points = config.scoring.order_book_strong
            breakdown["order_book"] = points
            score += points

        # Trade Flow
        flow_imbalance = abs(metrics.get("flow_imbalance", 0))
        if flow_imbalance > config.thresholds.trade_flow_strong:
            points = config.scoring.trade_flow_strong
            breakdown["trade_flow"] = points
            score += points
        elif flow_imbalance > config.thresholds.trade_flow_moderate:
            points = config.scoring.trade_flow_moderate
            breakdown["trade_flow"] = points
            score += points

        # VWAP Deviation
        vwap_z = abs(metrics.get("vwap_z_score", 0))
        if vwap_z > config.thresholds.vwap_z_score_extreme:
            points = config.scoring.vwap_extreme
            breakdown["vwap"] = points
            score += points
        elif vwap_z > config.thresholds.vwap_z_score_stretched:
            points = config.scoring.vwap_stretched
            breakdown["vwap"] = points
            score += points

        # Funding Rate
        funding = abs(metrics.get("funding_annualized", 0))
        if funding > config.thresholds.funding_extreme:
            points = config.scoring.funding_extreme
            breakdown["funding"] = points
            score += points
        elif funding > config.thresholds.funding_elevated:
            points = config.scoring.funding_elevated
            breakdown["funding"] = points
            score += points

        # Open Interest Divergence
        oi_type = metrics.get("oi_divergence_type", "unknown")
        if oi_type in ["strong_bullish", "strong_bearish"]:
            points = config.scoring.oi_strong
            breakdown["oi"] = points
            score += points
        elif oi_type in ["weak_bullish", "weak_bearish"]:
            points = config.scoring.oi_weak
            breakdown["oi"] = points
            score += points

        # Funding-Basis Alignment
        funding_val = metrics.get("funding_annualized", 0)
        basis = metrics.get("basis_pct", 0)

        funding_extreme = abs(funding_val) > config.thresholds.funding_extreme
        basis_extreme = abs(basis) > config.thresholds.basis_threshold

        if funding_extreme and basis_extreme:
            funding_positive = funding_val > config.thresholds.funding_extreme
            basis_positive = basis > config.thresholds.basis_threshold

            if funding_positive == basis_positive:
                points = config.scoring.funding_basis_aligned
                breakdown["funding_basis"] = points
                score += points
            else:
                points = config.scoring.funding_basis_diverged
                breakdown["funding_basis"] = points
                score += points

        # Cap at 100
        score = min(100, max(0, score))

        return score, breakdown

    def _count_directional_signals(
        self,
        metrics: Dict[str, Any]
    ) -> Tuple[int, int, Dict[str, str]]:
        """Count bullish vs bearish signals"""
        config = get_config()
        bullish = 0
        bearish = 0
        details = {}

        # Order Book
        ob = metrics.get("ob_imbalance", 0)
        if ob > config.thresholds.order_book_imbalance:
            bullish += 1
            details["order_book"] = f"Bullish ({ob:.2f})"
        elif ob < -config.thresholds.order_book_imbalance:
            bearish += 1
            details["order_book"] = f"Bearish ({ob:.2f})"

        # Trade Flow
        flow = metrics.get("flow_imbalance", 0)
        if flow > config.thresholds.trade_flow_moderate:
            bullish += 1
            details["trade_flow"] = f"Bullish ({flow:.2f})"
        elif flow < -config.thresholds.trade_flow_moderate:
            bearish += 1
            details["trade_flow"] = f"Bearish ({flow:.2f})"

        # VWAP (mean reversion)
        vwap_z = metrics.get("vwap_z_score", 0)
        if vwap_z > config.thresholds.vwap_z_score_stretched:
            bearish += 1
            details["vwap"] = f"Bearish (overextended +{vwap_z:.2f}σ)"
        elif vwap_z < -config.thresholds.vwap_z_score_stretched:
            bullish += 1
            details["vwap"] = f"Bullish (oversold {vwap_z:.2f}σ)"

        # Funding (contrarian)
        funding = metrics.get("funding_annualized", 0)
        if funding > config.thresholds.funding_extreme:
            bearish += 1
            details["funding"] = f"Bearish (crowded longs {funding:.1f}%)"
        elif funding < -config.thresholds.funding_extreme:
            bullish += 1
            details["funding"] = f"Bullish (crowded shorts {funding:.1f}%)"

        # OI Divergence
        oi_type = metrics.get("oi_divergence_type", "unknown")
        if oi_type == "strong_bullish":
            bullish += 1
            details["oi"] = "Bullish (new longs opening)"
        elif oi_type == "strong_bearish":
            bearish += 1
            details["oi"] = "Bearish (new shorts opening)"
        elif oi_type == "weak_bullish":
            bearish += 1
            details["oi"] = "Bearish (fake rally)"
        elif oi_type == "weak_bearish":
            bullish += 1
            details["oi"] = "Bullish (fake dump)"

        return bullish, bearish, details

    def _determine_action(
        self,
        score: int,
        bullish: int,
        bearish: int
    ) -> SignalAction:
        """Determine trading action"""
        config = get_config()

        if score < config.signal.min_convergence_score:
            return SignalAction.SKIP

        if bullish >= config.signal.min_aligned_signals and bullish > bearish:
            return SignalAction.LONG
        elif bearish >= config.signal.min_aligned_signals and bearish > bullish:
            return SignalAction.SHORT
        else:
            return SignalAction.SKIP

    def _calculate_levels(
        self,
        action: SignalAction,
        current_price: float,
        vwap: float,
        vwap_z_score: float
    ) -> Dict[str, float]:
        """Calculate entry, stop, and target prices"""
        if action == SignalAction.SKIP or current_price == 0:
            return {"entry": 0, "stop": 0, "target": 0}

        if vwap == 0:
            vwap = current_price

        if action == SignalAction.LONG:
            entry = current_price
            stop = entry * 0.98  # 2% stop
            target = max(vwap * 1.01, entry * 1.015)  # 1.5% target
        else:  # SHORT
            entry = current_price
            stop = entry * 1.02  # 2% stop
            target = min(vwap * 0.99, entry * 0.985)  # 1.5% target

        return {
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "target": round(target, 2)
        }

    def _determine_confidence(self, score: int, aligned: int) -> Confidence:
        """Determine confidence level"""
        if score >= 85 and aligned >= 4:
            return Confidence.HIGH
        elif score >= 70 and aligned >= 3:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW

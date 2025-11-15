"""Metrics calculation system"""
from .base import BaseMetric, MetricRegistry
from .implementations import (
    OrderBookImbalanceMetric,
    FundingRateMetric,
    VWAPDeviationMetric,
    TradeFlowMetric,
    OIDivergenceMetric,
    BasisSpreadMetric
)

# Register default metrics
registry = MetricRegistry()
registry.register(OrderBookImbalanceMetric())
registry.register(FundingRateMetric())
registry.register(VWAPDeviationMetric())
registry.register(TradeFlowMetric())
registry.register(OIDivergenceMetric())
registry.register(BasisSpreadMetric())

__all__ = [
    "BaseMetric",
    "MetricRegistry",
    "registry",
    "OrderBookImbalanceMetric",
    "FundingRateMetric",
    "VWAPDeviationMetric",
    "TradeFlowMetric",
    "OIDivergenceMetric",
    "BasisSpreadMetric",
]

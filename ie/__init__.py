"""
Institutional Engine (IE) - Data Infrastructure Layer

This module provides institutional-grade market data fetching and calculation
utilities. The IE layer is responsible for:

1. Fetching raw market data from exchanges (order book, funding, OI)
2. Performing quantitative calculations (imbalances, z-scores, etc.)
3. Returning clean, structured metrics to the AI agent

The IE layer does NOT make trading decisions - it only provides data.
All strategy and decision-making is handled by the AI agent.
"""

from ie.calculations import (
    calculate_order_book_imbalance,
    calculate_vwap,
    calculate_z_score,
    calculate_funding_annualized,
    calculate_oi_change,
    calculate_volume_ratio,
)

from ie.data_models import (
    OrderBookMetrics,
    FundingMetrics,
    OpenInterestMetrics,
    VWAPMetrics,
    VolumeMetrics,
    InstitutionalMetrics,
)

__version__ = "0.1.0"
__all__ = [
    # Calculation functions
    "calculate_order_book_imbalance",
    "calculate_vwap",
    "calculate_z_score",
    "calculate_funding_annualized",
    "calculate_oi_change",
    "calculate_volume_ratio",
    # Data models
    "OrderBookMetrics",
    "FundingMetrics",
    "OpenInterestMetrics",
    "VWAPMetrics",
    "VolumeMetrics",
    "InstitutionalMetrics",
]

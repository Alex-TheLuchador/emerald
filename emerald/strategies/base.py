"""
Base strategy interface

All strategies implement this interface for signal generation
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..common.models import Signal, MarketData, MetricResult


class BaseStrategy(ABC):
    """Base class for all trading strategies"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Strategy description"""
        pass

    @abstractmethod
    def generate_signal(
        self,
        market_data: MarketData,
        metrics: Dict[str, MetricResult]
    ) -> Signal:
        """
        Generate trading signal from market data and metrics

        Args:
            market_data: Current market data
            metrics: Calculated metrics

        Returns:
            Trading signal
        """
        pass

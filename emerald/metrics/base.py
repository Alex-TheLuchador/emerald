"""
Base metric interface for pluggable metrics system

All metrics implement the BaseMetric interface and can be registered dynamically
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..common.models import MarketData, MetricResult, OISnapshot


class BaseMetric(ABC):
    """Base class for all metrics"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Metric name (unique identifier)"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description"""
        pass

    @abstractmethod
    def calculate(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> MetricResult:
        """
        Calculate metric from market data

        Args:
            market_data: Current market data
            historical_oi: Optional historical OI snapshot

        Returns:
            MetricResult with calculated value and metadata
        """
        pass

    def validate_data(self, market_data: MarketData) -> bool:
        """
        Validate that market data is sufficient for calculation

        Args:
            market_data: Market data to validate

        Returns:
            True if data is valid
        """
        return True


class MetricRegistry:
    """Registry for managing metrics"""

    def __init__(self):
        """Initialize empty registry"""
        self._metrics: Dict[str, BaseMetric] = {}

    def register(self, metric: BaseMetric):
        """
        Register a metric

        Args:
            metric: Metric instance to register
        """
        self._metrics[metric.name] = metric

    def unregister(self, name: str):
        """
        Unregister a metric

        Args:
            name: Metric name to remove
        """
        self._metrics.pop(name, None)

    def get(self, name: str) -> Optional[BaseMetric]:
        """
        Get metric by name

        Args:
            name: Metric name

        Returns:
            Metric instance or None
        """
        return self._metrics.get(name)

    def list_metrics(self) -> List[str]:
        """
        List all registered metrics

        Returns:
            List of metric names
        """
        return list(self._metrics.keys())

    def calculate_all(
        self,
        market_data: MarketData,
        historical_oi: Optional[OISnapshot] = None
    ) -> Dict[str, MetricResult]:
        """
        Calculate all registered metrics

        Args:
            market_data: Current market data
            historical_oi: Optional historical OI snapshot

        Returns:
            Dictionary mapping metric name to result
        """
        results = {}
        for name, metric in self._metrics.items():
            try:
                if metric.validate_data(market_data):
                    result = metric.calculate(market_data, historical_oi)
                    results[name] = result
            except Exception as e:
                # Log error but continue with other metrics
                print(f"Error calculating {name}: {e}")
        return results

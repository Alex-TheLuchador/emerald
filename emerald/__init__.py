"""
Emerald Trading System v2.0

Decoupled architecture for cryptocurrency trading signals
"""
__version__ = "2.0.0"

from .data.hyperliquid_client import HyperliquidClient
from .metrics import registry as metric_registry
from .strategies import ConvergenceStrategy
from .common.config import get_config

__all__ = [
    "HyperliquidClient",
    "metric_registry",
    "ConvergenceStrategy",
    "get_config",
]

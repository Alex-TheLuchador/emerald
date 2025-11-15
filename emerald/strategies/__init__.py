"""Trading strategies and signal generation"""
from .base import BaseStrategy
from .convergence import ConvergenceStrategy

__all__ = ["BaseStrategy", "ConvergenceStrategy"]

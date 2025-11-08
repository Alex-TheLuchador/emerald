"""
Configuration settings for EMERALD trading agent.

This module centralizes all configurable parameters for both the tool
and agent behavior, making them easy to adjust without touching core logic.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class IntervalConstraints:
    """Constraints for a specific candle interval."""
    
    max_lookback_hours: float
    """Maximum number of hours to look back for this interval."""
    
    interval_minutes: int
    """Number of minutes in one candle for this interval."""
    
    max_candles: int = 250
    """Maximum number of candles to return (safety cap)."""


# Interval configuration - the single source of truth
INTERVAL_CONSTRAINTS: Dict[str, IntervalConstraints] = {
    "1m": IntervalConstraints(
        max_lookback_hours=1.5,
        interval_minutes=1,
    ),
    "5m": IntervalConstraints(
        max_lookback_hours=6,
        interval_minutes=5,
    ),
    "15m": IntervalConstraints(
        max_lookback_hours=24,
        interval_minutes=15,
    ),
    "1h": IntervalConstraints(
        max_lookback_hours=84,
        interval_minutes=60,
    ),
    "4h": IntervalConstraints(
        max_lookback_hours=336,
        interval_minutes=240,
    ),
    "1d": IntervalConstraints(
        max_lookback_hours=2016,
        interval_minutes=1440,
    ),
}


def get_interval_constraint(interval: str) -> IntervalConstraints:
    """
    Get constraints for a given interval.
    
    Args:
        interval: The interval string (case-insensitive).
        
    Returns:
        IntervalConstraints for the interval.
        
    Raises:
        ValueError: If interval is not recognized.
    """
    normalized = interval.lower()
    if normalized not in INTERVAL_CONSTRAINTS:
        valid = ", ".join(INTERVAL_CONSTRAINTS.keys())
        raise ValueError(
            f"Unrecognized interval '{interval}'. "
            f"Valid intervals: {valid}"
        )
    return INTERVAL_CONSTRAINTS[normalized]


def generate_constraint_text() -> str:
    """
    Generate human-readable constraint text for system prompts.
    
    Returns:
        Formatted string listing all interval constraints.
    """
    lines = [
        f"  - {interval} interval must look back no more than {c.max_lookback_hours} hours."
        for interval, c in INTERVAL_CONSTRAINTS.items()
    ]
    return "\n".join(lines)


# Tool configuration
@dataclass
class ToolConfig:
    """Configuration for the Hyperliquid data fetching tool."""
    
    api_url: str = "https://api.hyperliquid.xyz/info"
    """Hyperliquid API endpoint."""
    
    request_timeout: int = 15
    """HTTP request timeout in seconds."""
    
    max_candles_absolute: int = 250
    """Absolute maximum candles to return (safety cap)."""
    
    default_output_subdir: str = "agent_outputs"
    """Default subdirectory for saved output files."""


# Agent configuration
@dataclass
class AgentConfig:
    """Configuration for the agent behavior."""
    
    max_tool_calls_per_response: int = 3
    """Maximum number of tool invocations in a single response."""
    
    max_iterations: int = 5
    """Maximum agent reasoning iterations."""
    
    model_temperature: float = 0.25
    """Model temperature for response generation."""
    
    max_tokens: int = 2048
    """Maximum tokens in model response."""
    
    model_timeout: int = 45
    """Model API call timeout in seconds."""
    
    max_retries: int = 2
    """Maximum retry attempts for model calls."""


# Institutional Engine (IE) configuration
@dataclass
class IEConfig:
    """Configuration for Institutional Engine tools."""

    # Cache TTLs (time-to-live in seconds)
    order_book_cache_ttl: int = 2
    """Order book cache TTL (2 seconds - data changes rapidly)."""

    funding_cache_ttl: int = 300
    """Funding rate cache TTL (5 minutes - changes every 8 hours)."""

    oi_cache_ttl: int = 300
    """Open interest cache TTL (5 minutes)."""

    # Order book settings
    default_order_book_depth: int = 10
    """Default number of order book levels to analyze."""

    max_order_book_depth: int = 20
    """Maximum order book depth allowed."""

    # Imbalance thresholds
    strong_imbalance_threshold: float = 0.4
    """Threshold for strong bid/ask pressure (absolute value)."""

    moderate_imbalance_threshold: float = 0.2
    """Threshold for moderate bid/ask pressure (absolute value)."""

    # Funding rate thresholds
    extreme_funding_threshold_pct: float = 10.0
    """Annualized funding rate threshold for extreme (%)."""

    high_funding_threshold_pct: float = 5.0
    """Annualized funding rate threshold for high (%)."""

    # VWAP/z-score thresholds
    extreme_z_score: float = 2.0
    """Z-score threshold for extreme deviation."""

    high_z_score: float = 1.5
    """Z-score threshold for high deviation."""

    moderate_z_score: float = 1.0
    """Z-score threshold for moderate deviation."""

    # OI divergence threshold
    oi_divergence_threshold_pct: float = 1.5
    """Minimum % change to consider significant for OI/price divergence."""

    # Volume thresholds
    high_volume_ratio: float = 1.5
    """Volume ratio threshold for high volume (vs average)."""

    very_high_volume_ratio: float = 2.0
    """Volume ratio threshold for very high volume (vs average)."""

    # Convergence scoring weights
    order_book_weight: int = 25
    """Points awarded for order book signal in convergence score."""

    funding_weight: int = 20
    """Points awarded for funding signal in convergence score."""

    oi_weight: int = 30
    """Points awarded for OI divergence signal in convergence score."""

    vwap_weight: int = 25
    """Points awarded for VWAP signal in convergence score."""

    # Setup grading thresholds
    a_plus_threshold: int = 70
    """Convergence score threshold for A+ grade."""

    a_threshold: int = 50
    """Convergence score threshold for A grade."""

    b_threshold: int = 30
    """Convergence score threshold for B grade."""


# Global instances - import these in your code
TOOL_CONFIG = ToolConfig()
AGENT_CONFIG = AgentConfig()
IE_CONFIG = IEConfig()

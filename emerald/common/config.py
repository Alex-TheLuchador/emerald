"""
Configuration management using Pydantic Settings

Supports environment variables and .env files
"""
from typing import List, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class APIConfig(BaseSettings):
    """API configuration"""
    hyperliquid_url: str = Field(
        default="https://api.hyperliquid.xyz/info",
        description="Hyperliquid API URL"
    )
    timeout: int = Field(default=30, description="API timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class MetricThresholds(BaseSettings):
    """Metric thresholds"""
    order_book_imbalance: float = 0.4
    order_book_imbalance_extreme: float = 0.6
    trade_flow_moderate: float = 0.3
    trade_flow_strong: float = 0.5
    vwap_z_score_stretched: float = 1.5
    vwap_z_score_extreme: float = 2.0
    funding_elevated: float = 7.0
    funding_extreme: float = 10.0
    oi_change_threshold: float = 3.0
    basis_threshold: float = 0.3

    model_config = SettingsConfigDict(
        env_prefix="THRESHOLD_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class ScoringWeights(BaseSettings):
    """Scoring weights for signal generation"""
    order_book_extreme: int = 25
    order_book_strong: int = 15
    trade_flow_strong: int = 25
    trade_flow_moderate: int = 15
    vwap_extreme: int = 30
    vwap_stretched: int = 20
    funding_extreme: int = 20
    funding_elevated: int = 10
    oi_strong: int = 20
    oi_weak: int = 10
    funding_basis_aligned: int = 15
    funding_basis_diverged: int = -20

    model_config = SettingsConfigDict(
        env_prefix="SCORING_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class CalculationParams(BaseSettings):
    """Calculation parameters"""
    vwap_lookback_candles: int = 60
    flow_lookback_candles: int = 10
    oi_lookback_hours: int = 4
    order_book_levels: int = 10

    model_config = SettingsConfigDict(
        env_prefix="CALC_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class SignalConfig(BaseSettings):
    """Signal generation configuration"""
    min_convergence_score: int = 70
    min_aligned_signals: int = 3

    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class UIConfig(BaseSettings):
    """UI configuration"""
    refresh_interval_seconds: int = 90
    coins: List[str] = Field(default=["BTC", "ETH", "SOL"])

    model_config = SettingsConfigDict(
        env_prefix="UI_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class StorageConfig(BaseSettings):
    """Storage configuration"""
    oi_retention_hours: int = 168  # 7 days
    funding_retention_hours: int = 168
    orderbook_retention_hours: int = 1
    snapshot_interval_minutes: int = 15

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class AppConfig(BaseSettings):
    """Main application configuration"""
    # Sub-configurations
    api: APIConfig = Field(default_factory=APIConfig)
    thresholds: MetricThresholds = Field(default_factory=MetricThresholds)
    scoring: ScoringWeights = Field(default_factory=ScoringWeights)
    calculation: CalculationParams = Field(default_factory=CalculationParams)
    signal: SignalConfig = Field(default_factory=SignalConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # General settings
    environment: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration from environment"""
        return cls(
            api=APIConfig(),
            thresholds=MetricThresholds(),
            scoring=ScoringWeights(),
            calculation=CalculationParams(),
            signal=SignalConfig(),
            ui=UIConfig(),
            storage=StorageConfig()
        )


# Global config instance
_config: AppConfig = None


def get_config() -> AppConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment"""
    global _config
    _config = AppConfig.load()
    return _config

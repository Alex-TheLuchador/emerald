"""
Configuration for the strategy monitor
"""

# API Configuration
HYPERLIQUID_API_URL = "https://api.hyperliquid.xyz/info"

# Coins to monitor
COINS = ["BTC", "ETH", "SOL"]

# Metric Thresholds (from strategy document)
THRESHOLDS = {
    "order_book_imbalance": 0.4,        # Strong pressure threshold
    "order_book_imbalance_extreme": 0.6, # Very strong pressure
    "trade_flow_moderate": 0.3,
    "trade_flow_strong": 0.5,
    "vwap_z_score_stretched": 1.5,
    "vwap_z_score_extreme": 2.0,
    "funding_elevated": 7.0,            # % annualized
    "funding_extreme": 10.0,            # % annualized
    "oi_change_threshold": 3.0,         # % change
    "basis_threshold": 0.3,             # % spread
}

# Calculation Parameters
VWAP_LOOKBACK_CANDLES = 60  # 60 x 1m = 1 hour
FLOW_LOOKBACK_CANDLES = 10  # 10 x 1m = 10 minutes
OI_LOOKBACK_HOURS = 4       # Compare OI from 4 hours ago

# Scoring Weights
SCORING = {
    "order_book_extreme": 25,
    "order_book_strong": 15,
    "trade_flow_strong": 25,
    "trade_flow_moderate": 15,
    "vwap_extreme": 30,
    "vwap_stretched": 20,
    "funding_extreme": 20,
    "funding_elevated": 10,
    "oi_strong": 20,
    "oi_weak": 10,
    "funding_basis_aligned": 15,
    "funding_basis_diverged": -20,
}

# Signal Generation
MIN_CONVERGENCE_SCORE = 70
MIN_ALIGNED_SIGNALS = 3

# UI Configuration
REFRESH_INTERVAL_SECONDS = 2
ORDER_BOOK_LEVELS = 10  # Top N levels to analyze

# Database
DB_PATH = "strategy_monitor/oi_history.db"

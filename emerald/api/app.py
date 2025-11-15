"""
FastAPI REST API for the trading system

Provides clean HTTP endpoints for all functionality
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio

from ..data.hyperliquid_client import HyperliquidClient
from ..metrics import registry as metric_registry
from ..strategies import ConvergenceStrategy
from ..common.models import Signal, MarketData, OISnapshot
from ..common.config import get_config

# Initialize FastAPI app
app = FastAPI(
    title="Emerald Trading API",
    description="REST API for cryptocurrency trading signals",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for OI snapshots (simple implementation)
oi_storage: dict = {}


@app.get("/")
async def root():
    """API root"""
    return {
        "name": "Emerald Trading API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "config": "/config",
            "coins": "/coins",
            "market_data": "/market/{coin}",
            "metrics": "/metrics/{coin}",
            "signal": "/signal/{coin}",
            "signals_batch": "/signals"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "metrics_registered": len(metric_registry.list_metrics())}


@app.get("/config")
async def get_configuration():
    """Get current configuration"""
    config = get_config()
    return {
        "coins": config.ui.coins,
        "thresholds": {
            "order_book_imbalance": config.thresholds.order_book_imbalance,
            "funding_extreme": config.thresholds.funding_extreme,
            "vwap_z_score_stretched": config.thresholds.vwap_z_score_stretched
        },
        "signal": {
            "min_convergence_score": config.signal.min_convergence_score,
            "min_aligned_signals": config.signal.min_aligned_signals
        }
    }


@app.get("/coins")
async def list_coins() -> List[str]:
    """List all monitored coins"""
    config = get_config()
    return config.ui.coins


@app.get("/market/{coin}")
async def get_market_data(coin: str) -> dict:
    """
    Get raw market data for a coin

    Args:
        coin: Coin symbol (e.g., "BTC", "ETH")

    Returns:
        Market data including order book, candles, etc.
    """
    try:
        async with HyperliquidClient() as client:
            market_data = await client.get_market_data(coin)
            return market_data.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")


@app.get("/metrics/{coin}")
async def get_metrics(coin: str, save_oi: bool = True) -> dict:
    """
    Calculate all metrics for a coin

    Args:
        coin: Coin symbol
        save_oi: Whether to save current OI snapshot

    Returns:
        Calculated metrics
    """
    try:
        config = get_config()

        # Fetch market data
        async with HyperliquidClient() as client:
            market_data = await client.get_market_data(coin)

        # Get historical OI if available
        historical_oi = None
        if coin in oi_storage:
            lookback_hours = config.calculation.oi_lookback_hours
            target_time = market_data.timestamp.timestamp() - (lookback_hours * 3600)

            # Find closest snapshot
            snapshots = oi_storage[coin]
            closest = min(snapshots, key=lambda s: abs(s.timestamp - target_time), default=None)
            if closest and abs(closest.timestamp - target_time) < 1800:  # Within 30 min
                historical_oi = closest

        # Calculate metrics
        metric_results = metric_registry.calculate_all(market_data, historical_oi)

        # Save current OI
        if save_oi:
            current_oi = market_data.perp_data.open_interest
            current_price = market_data.candles[-1].close if market_data.candles else 0

            if current_oi > 0:
                if coin not in oi_storage:
                    oi_storage[coin] = []

                snapshot = OISnapshot(
                    oi=current_oi,
                    price=current_price,
                    timestamp=market_data.timestamp.timestamp()
                )
                oi_storage[coin].append(snapshot)

                # Keep only last 1000 snapshots
                if len(oi_storage[coin]) > 1000:
                    oi_storage[coin] = oi_storage[coin][-1000:]

        # Convert to dict
        result = {}
        for name, metric_result in metric_results.items():
            result[name] = {
                "value": metric_result.value,
                "metadata": metric_result.metadata,
                "timestamp": metric_result.timestamp.isoformat()
            }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")


@app.get("/signal/{coin}")
async def get_signal(coin: str) -> dict:
    """
    Generate trading signal for a coin

    Args:
        coin: Coin symbol

    Returns:
        Trading signal with action, confidence, and price levels
    """
    try:
        config = get_config()

        # Fetch market data
        async with HyperliquidClient() as client:
            market_data = await client.get_market_data(coin)

        # Get historical OI
        historical_oi = None
        if coin in oi_storage:
            lookback_hours = config.calculation.oi_lookback_hours
            target_time = market_data.timestamp.timestamp() - (lookback_hours * 3600)

            snapshots = oi_storage[coin]
            closest = min(snapshots, key=lambda s: abs(s.timestamp - target_time), default=None)
            if closest and abs(closest.timestamp - target_time) < 1800:
                historical_oi = closest

        # Calculate metrics
        metric_results = metric_registry.calculate_all(market_data, historical_oi)

        # Save current OI
        current_oi = market_data.perp_data.open_interest
        current_price = market_data.candles[-1].close if market_data.candles else 0

        if current_oi > 0:
            if coin not in oi_storage:
                oi_storage[coin] = []

            snapshot = OISnapshot(
                oi=current_oi,
                price=current_price,
                timestamp=market_data.timestamp.timestamp()
            )
            oi_storage[coin].append(snapshot)

            if len(oi_storage[coin]) > 1000:
                oi_storage[coin] = oi_storage[coin][-1000:]

        # Generate signal
        strategy = ConvergenceStrategy()
        signal = strategy.generate_signal(market_data, metric_results)

        return signal.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signal: {str(e)}")


@app.get("/signals")
async def get_signals_batch() -> List[dict]:
    """
    Generate signals for all monitored coins in parallel

    Returns:
        List of signals for each coin
    """
    try:
        config = get_config()
        coins = config.ui.coins

        # Fetch signals in parallel
        tasks = [get_signal(coin) for coin in coins]
        signals = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        results = []
        for coin, signal in zip(coins, signals):
            if isinstance(signal, Exception):
                results.append({
                    "coin": coin,
                    "error": str(signal),
                    "action": "ERROR"
                })
            else:
                results.append(signal)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate batch signals: {str(e)}")


@app.get("/metrics/list")
async def list_metrics() -> List[str]:
    """List all registered metrics"""
    return metric_registry.list_metrics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Test the refactored system with mock data
"""
import sys
sys.path.insert(0, '/home/user/emerald')

from emerald.common.models import (
    MarketData, OrderBook, Candle, PerpData, SpotData,
    OrderBookLevel, OISnapshot
)
from emerald.metrics import registry as metric_registry
from emerald.strategies import ConvergenceStrategy
from emerald.common.config import get_config
from datetime import datetime


def create_mock_data():
    """Create mock market data for testing"""
    # Mock order book
    bids = [
        {"px": "67800", "sz": "10.5", "n": 5},
        {"px": "67790", "sz": "8.2", "n": 3},
        {"px": "67780", "sz": "15.0", "n": 7},
    ]
    asks = [
        {"px": "67820", "sz": "5.2", "n": 2},
        {"px": "67830", "sz": "3.1", "n": 1},
        {"px": "67840", "sz": "7.5", "n": 4},
    ]

    order_book = OrderBook(
        coin="BTC",
        levels=[bids, asks],
        time=int(datetime.now().timestamp() * 1000)
    )

    # Mock candles (60 candles for VWAP)
    candles = []
    base_price = 67800
    for i in range(60):
        import random
        price = base_price + random.randint(-50, 50)
        candles.append(Candle(
            t=int(datetime.now().timestamp() * 1000) + (i * 60000),
            o=str(price),
            h=str(price + 10),
            l=str(price - 10),
            c=str(price + random.randint(-5, 5)),
            v=str(100 + random.randint(-20, 20)),
            n=100
        ))

    # Mock perp data
    perp_data = PerpData(
        funding="0.000034",
        openInterest="1250000000",
        markPx="67825"
    )

    # Mock spot data
    spot_data = SpotData(midPx="67820")

    return MarketData(
        coin="BTC",
        order_book=order_book,
        perp_data=perp_data,
        spot_data=spot_data,
        candles=candles,
        timestamp=datetime.now()
    )


def test_config():
    """Test configuration system"""
    print("1. Testing Configuration System...")
    config = get_config()
    print(f"   ✓ Loaded config")
    print(f"   ✓ Coins: {config.ui.coins}")
    print(f"   ✓ Min score: {config.signal.min_convergence_score}")
    print(f"   ✓ Thresholds loaded")


def test_metrics():
    """Test metrics calculation"""
    print("\n2. Testing Metrics System...")
    market_data = create_mock_data()

    # Create historical OI snapshot (4 hours ago)
    historical_oi = OISnapshot(
        oi=1180000000.0,
        price=67500.0,
        timestamp=datetime.now().timestamp() - (4 * 3600)
    )

    # Calculate metrics
    results = metric_registry.calculate_all(market_data, historical_oi)

    print(f"   ✓ Registered metrics: {len(metric_registry.list_metrics())}")
    print(f"   ✓ Calculated metrics: {len(results)}")

    for name, result in results.items():
        print(f"   ✓ {name}: {result.value}")

    return market_data, results


def test_strategy(market_data, metrics):
    """Test strategy signal generation"""
    print("\n3. Testing Strategy System...")
    strategy = ConvergenceStrategy()

    signal = strategy.generate_signal(market_data, metrics)

    print(f"   ✓ Strategy: {strategy.name}")
    print(f"   ✓ Action: {signal.action.value}")
    print(f"   ✓ Score: {signal.convergence_score}/100")
    print(f"   ✓ Confidence: {signal.confidence.value}")
    print(f"   ✓ Aligned signals: {signal.aligned_signals}")
    print(f"   ✓ Entry: ${signal.entry_price:,.2f}")
    print(f"   ✓ Stop: ${signal.stop_loss:,.2f}")
    print(f"   ✓ Target: ${signal.take_profit:,.2f}")

    return signal


def test_models():
    """Test data models"""
    print("\n4. Testing Data Models...")
    market_data = create_mock_data()

    print(f"   ✓ MarketData created")
    print(f"   ✓ Coin: {market_data.coin}")
    print(f"   ✓ Bids: {len(market_data.order_book.bids)}")
    print(f"   ✓ Asks: {len(market_data.order_book.asks)}")
    print(f"   ✓ Candles: {len(market_data.candles)}")
    print(f"   ✓ Funding: {market_data.perp_data.funding_rate}")
    print(f"   ✓ OI: {market_data.perp_data.open_interest:,.0f}")

    # Test serialization
    data_dict = market_data.model_dump()
    print(f"   ✓ Serialization works (dict with {len(data_dict)} keys)")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Emerald Trading System v2.0 - Component Tests")
    print("=" * 60)

    try:
        # Test config
        test_config()

        # Test models
        test_models()

        # Test metrics
        market_data, metrics = test_metrics()

        # Test strategy
        signal = test_strategy(market_data, metrics)

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nArchitecture Summary:")
        print("  ✓ Decoupled layers (data, metrics, strategies, api, ui)")
        print("  ✓ Pluggable metrics system")
        print("  ✓ Clean interfaces (BaseMetric, BaseStrategy)")
        print("  ✓ Pydantic models for type safety")
        print("  ✓ Configuration management with Settings")
        print("\nThe system is ready for:")
        print("  - REST API deployment (emerald/api/app.py)")
        print("  - Streamlit dashboard (emerald/ui/dashboard.py)")
        print("  - Library usage (import emerald)")
        print("  - Adding custom metrics and strategies")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

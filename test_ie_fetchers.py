"""
Comprehensive test suite for IE data fetchers.

Tests all three data fetchers (order book, funding, OI) with live Hyperliquid API.
Run this to verify Phase 2 implementation.

Usage:
    python test_ie_fetchers.py
"""

import sys
from pathlib import Path
import time

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.ie_fetch_order_book import fetch_order_book_metrics
from tools.ie_fetch_funding import fetch_funding_metrics
from tools.ie_fetch_open_interest import fetch_open_interest_metrics
from ie.cache import get_cache


def print_header(title: str):
    """Print formatted test section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(metrics: dict, indent: str = "  "):
    """Print metrics in formatted way."""
    for key, value in metrics.items():
        if key == "cached":
            continue
        if isinstance(value, float):
            print(f"{indent}{key}: {value:.4f}")
        elif isinstance(value, bool):
            print(f"{indent}{key}: {'Yes' if value else 'No'}")
        else:
            print(f"{indent}{key}: {value}")


def test_order_book():
    """Test order book fetcher."""
    print_header("TEST 1: Order Book Fetcher")

    coins = ["BTC", "ETH", "SOL"]
    results = {}

    for coin in coins:
        print(f"\n📊 Fetching {coin} order book...")
        start_time = time.time()

        result = fetch_order_book_metrics(coin, depth=10, use_cache=False)
        elapsed_ms = (time.time() - start_time) * 1000

        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            results[coin] = None
        else:
            print(f"  ✓ Success ({elapsed_ms:.0f}ms)")
            print_result(result)
            results[coin] = result

    # Test cache
    if results["BTC"]:
        print(f"\n🔄 Testing cache with BTC...")
        start_time = time.time()
        cached_result = fetch_order_book_metrics("BTC", depth=10, use_cache=True)
        elapsed_ms = (time.time() - start_time) * 1000

        if cached_result.get("cached"):
            print(f"  ✓ Cache hit! ({elapsed_ms:.0f}ms)")
            print(f"  Speedup: {results['BTC']} -> cached")
        else:
            print(f"  ⚠️  Cache miss (data may have expired)")

    return all(r is not None for r in results.values())


def test_funding():
    """Test funding rate fetcher."""
    print_header("TEST 2: Funding Rate Fetcher")

    coins = ["BTC", "ETH", "SOL"]
    results = {}

    for coin in coins:
        print(f"\n💰 Fetching {coin} funding rate...")
        start_time = time.time()

        result = fetch_funding_metrics(coin, lookback_hours=24, use_cache=False)
        elapsed_ms = (time.time() - start_time) * 1000

        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            results[coin] = None
        else:
            print(f"  ✓ Success ({elapsed_ms:.0f}ms)")
            print_result(result)

            # Interpret
            print(f"\n  📝 Interpretation:")
            print(f"     Annualized: {result['annualized_pct']:.2f}%")
            print(f"     Sentiment: {result['sentiment']}")
            if result['is_extreme']:
                print(f"     ⚠️  EXTREME funding detected!")

            results[coin] = result

    return all(r is not None for r in results.values())


def test_open_interest():
    """Test open interest fetcher."""
    print_header("TEST 3: Open Interest Fetcher")

    coins = ["BTC", "ETH", "SOL"]
    results = {}

    for coin in coins:
        print(f"\n📈 Fetching {coin} open interest...")
        start_time = time.time()

        result = fetch_open_interest_metrics(coin, use_cache=False)
        elapsed_ms = (time.time() - start_time) * 1000

        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            results[coin] = None
        else:
            print(f"  ✓ Success ({elapsed_ms:.0f}ms)")
            print_result(result)

            # Interpret
            print(f"\n  📝 Interpretation:")
            print(f"     Current OI: ${result['current_usd']:,.0f}")
            print(f"     Price: ${result['current_price']:,.2f}")

            if result['change_4h_pct'] is not None:
                print(f"     OI Change (4h): {result['change_4h_pct']:+.2f}%")
                print(f"     Price Change (4h): {result['price_change_4h_pct']:+.2f}%")
                print(f"     Divergence: {result['divergence_type']}")
            else:
                print(f"     ⚠️  Not enough historical data yet")
                print(f"        (Run this test again in 1-4 hours for divergence)")

            results[coin] = result

    return all(r is not None for r in results.values())


def test_cache_performance():
    """Test cache system performance."""
    print_header("TEST 4: Cache Performance")

    coin = "BTC"

    # First call (miss)
    print(f"\n🔄 First call (cache miss):")
    start_time = time.time()
    result1 = fetch_order_book_metrics(coin, use_cache=True)
    time1_ms = (time.time() - start_time) * 1000
    print(f"  Time: {time1_ms:.0f}ms")
    print(f"  Cached: {result1.get('cached', False)}")

    # Second call (hit)
    print(f"\n🔄 Second call (cache hit):")
    start_time = time.time()
    result2 = fetch_order_book_metrics(coin, use_cache=True)
    time2_ms = (time.time() - start_time) * 1000
    print(f"  Time: {time2_ms:.0f}ms")
    print(f"  Cached: {result2.get('cached', False)}")

    if result2.get('cached'):
        speedup = time1_ms / time2_ms
        print(f"\n  ✓ Cache working!")
        print(f"    Speedup: {speedup:.1f}x faster")
        print(f"    Savings: {time1_ms - time2_ms:.0f}ms")
        return True
    else:
        print(f"\n  ⚠️  Cache miss (may have expired)")
        return False


def test_integrated_analysis():
    """Test using all three fetchers together."""
    print_header("TEST 5: Integrated Analysis")

    coin = "BTC"
    print(f"\n🔍 Complete institutional analysis for {coin}...")

    # Fetch all metrics
    print(f"\n  Fetching order book...")
    ob_metrics = fetch_order_book_metrics(coin, depth=10)

    print(f"  Fetching funding rate...")
    funding_metrics = fetch_funding_metrics(coin)

    print(f"  Fetching open interest...")
    oi_metrics = fetch_open_interest_metrics(coin)

    # Check for errors
    errors = []
    if "error" in ob_metrics:
        errors.append(f"Order book: {ob_metrics['error']}")
    if "error" in funding_metrics:
        errors.append(f"Funding: {funding_metrics['error']}")
    if "error" in oi_metrics:
        errors.append(f"OI: {oi_metrics['error']}")

    if errors:
        print(f"\n  ❌ Errors:")
        for error in errors:
            print(f"     {error}")
        return False

    # Present unified analysis
    print(f"\n  ✓ All metrics fetched successfully!")
    print(f"\n" + "─" * 70)
    print(f"  INSTITUTIONAL METRICS SUMMARY - {coin}")
    print(f"─" * 70)

    print(f"\n  📊 ORDER BOOK:")
    print(f"     Imbalance: {ob_metrics['imbalance']:+.4f} ({ob_metrics['imbalance_strength']})")
    print(f"     Spread: ${ob_metrics['spread']:.2f} ({ob_metrics['spread_bps']:.2f} bps)")

    print(f"\n  💰 FUNDING:")
    print(f"     Rate (8h): {funding_metrics['rate_8h']:.6f}")
    print(f"     Annualized: {funding_metrics['annualized_pct']:.2f}%")
    print(f"     Sentiment: {funding_metrics['sentiment']}")

    print(f"\n  📈 OPEN INTEREST:")
    print(f"     Current: ${oi_metrics['current_usd']:,.0f}")
    if oi_metrics['change_4h_pct'] is not None:
        print(f"     Change (4h): {oi_metrics['change_4h_pct']:+.2f}%")
        print(f"     Divergence: {oi_metrics['divergence_type']}")

    # Simple convergence analysis
    print(f"\n  🎯 CONVERGENCE ANALYSIS:")
    signals = []

    if ob_metrics['imbalance'] > 0.3:
        signals.append("✓ Order book shows bid pressure")
    elif ob_metrics['imbalance'] < -0.3:
        signals.append("✓ Order book shows ask pressure")

    if funding_metrics['is_extreme']:
        signals.append(f"✓ Extreme funding ({funding_metrics['sentiment']})")

    if oi_metrics.get('divergence_type') in ['strong_bullish', 'strong_bearish']:
        signals.append(f"✓ Strong OI divergence ({oi_metrics['divergence_type']})")

    if signals:
        for signal in signals:
            print(f"     {signal}")
    else:
        print(f"     No strong signals detected")

    return True


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "=" * 70)
    print("  IE DATA FETCHERS - COMPREHENSIVE TEST SUITE")
    print("  Phase 2: Testing with Live Hyperliquid API")
    print("=" * 70)

    results = {
        "Order Book": False,
        "Funding": False,
        "Open Interest": False,
        "Cache": False,
        "Integrated": False,
    }

    try:
        results["Order Book"] = test_order_book()
        results["Funding"] = test_funding()
        results["Open Interest"] = test_open_interest()
        results["Cache"] = test_cache_performance()
        results["Integrated"] = test_integrated_analysis()

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Print summary
    print_header("TEST RESULTS SUMMARY")

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name:.<50} {status}")

    # Cache stats
    cache = get_cache()
    stats = cache.get_stats()
    print(f"\n  Cache Statistics:")
    print(f"    Hits: {stats['hits']}")
    print(f"    Misses: {stats['misses']}")
    print(f"    Hit Rate: {stats['hit_rate_pct']:.1f}%")
    print(f"    Entries: {stats['entries']}")

    # Final verdict
    all_passed = all(results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("  Phase 2 Complete! Ready for Phase 3.")
    else:
        print("  ⚠️  SOME TESTS FAILED")
        print("  Review errors above and retry.")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

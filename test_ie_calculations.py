"""
Test script for IE calculation functions.

This script validates that all calculation functions work correctly
with sample data. Run this before integrating IE into the agent.

Usage:
    python test_ie_calculations.py
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ie.calculations import (
    calculate_order_book_imbalance,
    calculate_vwap,
    calculate_z_score,
    calculate_funding_annualized,
    calculate_oi_change,
    determine_oi_divergence,
    calculate_volume_ratio,
    calculate_vwap_bands,
    calculate_spread_bps,
    validate_candles,
)


def test_order_book_imbalance():
    """Test order book imbalance calculation."""
    print("\n" + "="*60)
    print("TEST: Order Book Imbalance")
    print("="*60)

    # Test case 1: Strong bid pressure
    bids = [(100, 10), (99.5, 8), (99, 5)]
    asks = [(100.5, 2), (101, 3), (101.5, 2)]
    imbalance, strength = calculate_order_book_imbalance(bids, asks, depth=3)
    print(f"\nCase 1 - Heavy bids:")
    print(f"  Bids: {bids}")
    print(f"  Asks: {asks}")
    print(f"  Imbalance: {imbalance:.4f}")
    print(f"  Strength: {strength}")
    assert imbalance > 0.4, "Should show strong bid pressure"
    assert strength == "strong_bid_pressure"
    print("  ✓ PASSED")

    # Test case 2: Strong ask pressure
    bids = [(100, 2), (99.5, 1), (99, 1)]
    asks = [(100.5, 8), (101, 10), (101.5, 7)]
    imbalance, strength = calculate_order_book_imbalance(bids, asks, depth=3)
    print(f"\nCase 2 - Heavy asks:")
    print(f"  Bids: {bids}")
    print(f"  Asks: {asks}")
    print(f"  Imbalance: {imbalance:.4f}")
    print(f"  Strength: {strength}")
    assert imbalance < -0.4, "Should show strong ask pressure"
    assert strength == "strong_ask_pressure"
    print("  ✓ PASSED")

    # Test case 3: Balanced
    bids = [(100, 5), (99.5, 5), (99, 5)]
    asks = [(100.5, 5), (101, 5), (101.5, 5)]
    imbalance, strength = calculate_order_book_imbalance(bids, asks, depth=3)
    print(f"\nCase 3 - Balanced:")
    print(f"  Imbalance: {imbalance:.4f}")
    print(f"  Strength: {strength}")
    assert abs(imbalance) < 0.1, "Should be near zero"
    assert strength == "neutral"
    print("  ✓ PASSED")


def test_vwap():
    """Test VWAP calculation."""
    print("\n" + "="*60)
    print("TEST: VWAP Calculation")
    print("="*60)

    candles = [
        {"high": 100, "low": 98, "close": 99, "volume": 1000},
        {"high": 102, "low": 99, "close": 101, "volume": 1500},
        {"high": 103, "low": 100, "close": 102, "volume": 2000},
    ]

    vwap = calculate_vwap(candles)
    print(f"\nCandles: {len(candles)}")
    print(f"VWAP: {vwap:.2f}")

    # VWAP should be weighted toward higher volume candles
    # Candle 3 has highest volume and highest prices, so VWAP should be > simple avg
    simple_avg = sum((c['high'] + c['low'] + c['close']) / 3 for c in candles) / len(candles)
    print(f"Simple average: {simple_avg:.2f}")
    assert vwap > simple_avg, "VWAP should be higher due to volume weighting"
    print("✓ PASSED")


def test_z_score():
    """Test z-score calculation."""
    print("\n" + "="*60)
    print("TEST: Z-Score Calculation")
    print("="*60)

    prices = [100, 101, 99, 100, 102, 98, 100, 99, 101, 100]

    # Test extreme high
    z_score, std_dev, level = calculate_z_score(108, prices)
    print(f"\nCase 1 - Extreme high (108):")
    print(f"  Mean: {sum(prices)/len(prices):.2f}")
    print(f"  Std Dev: {std_dev:.2f}")
    print(f"  Z-Score: {z_score:.2f}")
    print(f"  Level: {level}")
    assert z_score > 2.0, "Should be extreme"
    assert level == "extreme"
    print("  ✓ PASSED")

    # Test extreme low
    z_score, std_dev, level = calculate_z_score(92, prices)
    print(f"\nCase 2 - Extreme low (92):")
    print(f"  Z-Score: {z_score:.2f}")
    print(f"  Level: {level}")
    assert z_score < -2.0, "Should be extreme"
    assert level == "extreme"
    print("  ✓ PASSED")

    # Test normal
    z_score, std_dev, level = calculate_z_score(100, prices)
    print(f"\nCase 3 - At mean (100):")
    print(f"  Z-Score: {z_score:.2f}")
    print(f"  Level: {level}")
    assert abs(z_score) < 0.5, "Should be near zero"
    print("  ✓ PASSED")


def test_funding():
    """Test funding rate calculations."""
    print("\n" + "="*60)
    print("TEST: Funding Rate")
    print("="*60)

    # Test positive funding
    annualized, sentiment, is_extreme = calculate_funding_annualized(0.0001)
    print(f"\nCase 1 - Positive funding (0.0001):")
    print(f"  Annualized: {annualized:.2f}%")
    print(f"  Sentiment: {sentiment}")
    print(f"  Extreme: {is_extreme}")
    assert annualized > 10, "Should be > 10%"
    assert is_extreme, "Should be flagged as extreme"
    print("  ✓ PASSED")

    # Test negative funding
    annualized, sentiment, is_extreme = calculate_funding_annualized(-0.0002)
    print(f"\nCase 2 - Negative funding (-0.0002):")
    print(f"  Annualized: {annualized:.2f}%")
    print(f"  Sentiment: {sentiment}")
    print(f"  Extreme: {is_extreme}")
    assert annualized < -10, "Should be < -10%"
    assert is_extreme, "Should be flagged as extreme"
    print("  ✓ PASSED")

    # Test neutral
    annualized, sentiment, is_extreme = calculate_funding_annualized(0.00001)
    print(f"\nCase 3 - Neutral funding (0.00001):")
    print(f"  Annualized: {annualized:.2f}%")
    print(f"  Sentiment: {sentiment}")
    print(f"  Extreme: {is_extreme}")
    assert abs(annualized) < 5, "Should be near neutral"
    assert not is_extreme, "Should not be extreme"
    print("  ✓ PASSED")


def test_oi_divergence():
    """Test OI divergence scenarios."""
    print("\n" + "="*60)
    print("TEST: OI Divergence")
    print("="*60)

    # Strong bullish: Price ↑ + OI ↑
    scenario = determine_oi_divergence(3.5, 5.0)
    print(f"\nCase 1 - Price +3.5%, OI +5.0%:")
    print(f"  Scenario: {scenario}")
    assert scenario == "strong_bullish"
    print("  ✓ PASSED")

    # Weak bullish: Price ↑ + OI ↓
    scenario = determine_oi_divergence(3.5, -4.0)
    print(f"\nCase 2 - Price +3.5%, OI -4.0%:")
    print(f"  Scenario: {scenario}")
    assert scenario == "weak_bullish"
    print("  ✓ PASSED")

    # Strong bearish: Price ↓ + OI ↑
    scenario = determine_oi_divergence(-3.5, 5.0)
    print(f"\nCase 3 - Price -3.5%, OI +5.0%:")
    print(f"  Scenario: {scenario}")
    assert scenario == "strong_bearish"
    print("  ✓ PASSED")

    # Weak bearish: Price ↓ + OI ↓
    scenario = determine_oi_divergence(-3.5, -4.0)
    print(f"\nCase 4 - Price -3.5%, OI -4.0%:")
    print(f"  Scenario: {scenario}")
    assert scenario == "weak_bearish"
    print("  ✓ PASSED")


def test_volume_ratio():
    """Test volume ratio calculation."""
    print("\n" + "="*60)
    print("TEST: Volume Ratio")
    print("="*60)

    volumes = [100, 110, 95, 105, 100, 98, 102, 100]

    # High volume
    ratio, avg, significance = calculate_volume_ratio(180, volumes, lookback=8)
    print(f"\nCase 1 - High volume (180):")
    print(f"  Average: {avg:.2f}")
    print(f"  Ratio: {ratio:.2f}")
    print(f"  Significance: {significance}")
    assert ratio > 1.5, "Should be high ratio"
    assert significance == "high"
    print("  ✓ PASSED")

    # Normal volume
    ratio, avg, significance = calculate_volume_ratio(100, volumes, lookback=8)
    print(f"\nCase 2 - Normal volume (100):")
    print(f"  Ratio: {ratio:.2f}")
    print(f"  Significance: {significance}")
    assert significance == "normal"
    print("  ✓ PASSED")


def test_vwap_bands():
    """Test VWAP bands calculation."""
    print("\n" + "="*60)
    print("TEST: VWAP Bands")
    print("="*60)

    vwap = 100.0
    std_dev = 2.0

    bands = calculate_vwap_bands(vwap, std_dev)
    print(f"\nVWAP: {vwap}")
    print(f"Std Dev: {std_dev}")
    print(f"Bands:")
    for name, value in bands.items():
        print(f"  {name}: {value:.2f}")

    assert bands['upper_2std'] == 104.0
    assert bands['upper_1std'] == 102.0
    assert bands['vwap'] == 100.0
    assert bands['lower_1std'] == 98.0
    assert bands['lower_2std'] == 96.0
    print("✓ PASSED")


def test_spread_bps():
    """Test spread calculation in basis points."""
    print("\n" + "="*60)
    print("TEST: Spread (Basis Points)")
    print("="*60)

    bid = 99.5
    ask = 100.5
    mid = 100.0

    spread_bps = calculate_spread_bps(bid, ask, mid)
    print(f"\nBid: {bid}")
    print(f"Ask: {ask}")
    print(f"Mid: {mid}")
    print(f"Spread: {spread_bps:.2f} bps")

    # 1.0 spread on 100 mid = 1% = 100 bps
    assert spread_bps == 100.0
    print("✓ PASSED")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "="*60)
    print("IE CALCULATIONS TEST SUITE")
    print("="*60)

    try:
        test_order_book_imbalance()
        test_vwap()
        test_z_score()
        test_funding()
        test_oi_divergence()
        test_volume_ratio()
        test_vwap_bands()
        test_spread_bps()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print("\nIE calculation functions are working correctly!")
        print("Ready to proceed with Phase 2: Data Fetchers")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

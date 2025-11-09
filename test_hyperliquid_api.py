"""
Standalone test script to verify Hyperliquid API multi-timeframe support.
Tests all timeframes needed for ICT/SMC strategy.
"""

import requests
import json
from datetime import datetime, timezone

API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}

def test_timeframe(coin, interval, hours, limit):
    """Test fetching candles for a specific timeframe."""
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    # Calculate interval in minutes
    interval_map = {
        "1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080
    }
    interval_mins = interval_map.get(interval, 60)

    # Calculate start time
    start_ms_from_hours = now_ms - int(hours) * 3_600_000
    start_ms_from_limit = now_ms - int(limit) * interval_mins * 60_000
    start_ms = min(start_ms_from_hours, start_ms_from_limit)

    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": start_ms,
            "endTime": now_ms,
            "numCandles": int(limit),
        },
    }

    try:
        r = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
        status = r.status_code

        if status == 200:
            data = r.json()
            # Extract candles from response
            candles = []
            if isinstance(data, dict):
                candles = data.get("candles") or data.get("data") or data.get("result") or []
            elif isinstance(data, list):
                candles = data

            return status, len(candles), None
        else:
            return status, 0, f"HTTP {status}"

    except Exception as e:
        return 0, 0, str(e)


def main():
    print("=" * 60)
    print("Hyperliquid API Multi-Timeframe Test for ICT/SMC")
    print("=" * 60)
    print()

    # Test configuration: (interval, hours, candle_limit)
    tests = [
        ("1d", 720, 30, "Daily (HTF bias)"),
        ("4h", 192, 50, "4-Hour (HTF bias)"),
        ("1h", 100, 100, "1-Hour (dealing range)"),
        ("5m", 12, 150, "5-Minute (entry execution)"),
        ("1w", 5040, 20, "Weekly (optional HTF bias)"),
    ]

    results = []

    for interval, hours, limit, description in tests:
        print(f"Testing {interval:3s} ({description})...", end=" ")
        status, candle_count, error = test_timeframe("BTC", interval, hours, limit)

        if status == 200 and candle_count > 0:
            print(f"✓ {candle_count:3d} candles")
            results.append((interval, True, candle_count))
        else:
            error_msg = error or "No candles returned"
            print(f"✗ {error_msg}")
            results.append((interval, False, 0))

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")
    print()

    for interval, success, count in results:
        status_icon = "✓" if success else "✗"
        count_str = f"{count} candles" if success else "FAILED"
        print(f"  {status_icon} {interval:3s}: {count_str}")

    print()

    if passed == total:
        print("✅ All timeframes working - Ready for ICT/SMC implementation!")
    elif passed >= 4:
        print("⚠️  Most timeframes working - Can proceed with minor adjustments")
    else:
        print("❌ Critical timeframes failing - API investigation needed")

    print()
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

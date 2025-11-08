"""
Detailed API Response Diagnostic Tool

This script fetches raw responses from Hyperliquid API and prints
the exact structure so we can fix the parsers properly.
"""

import requests
import json
from pprint import pprint
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}

print("=" * 80)
print("HYPERLIQUID API RESPONSE DIAGNOSTIC")
print("=" * 80)

# Test 1: Order Book
print("\n1. ORDER BOOK (l2Book) - Testing BTC")
print("-" * 80)
try:
    payload = {"type": "l2Book", "coin": "BTC"}
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"✓ Status: {response.status_code}")
    print(f"Response type: {type(data)}")
    print(f"Response structure:")

    if isinstance(data, dict):
        print(f"  - Dict with keys: {list(data.keys())}")
        for key, value in data.items():
            print(f"  - {key}: {type(value)}")
            if isinstance(value, list) and len(value) > 0:
                print(f"    - First item type: {type(value[0])}")
                if len(value[0]) > 0 if isinstance(value[0], (list, tuple)) else False:
                    print(f"    - First item sample: {value[0][:2]}")
    elif isinstance(data, list):
        print(f"  - List with {len(data)} elements")
        for i, item in enumerate(data[:3]):  # Show first 3 items
            print(f"  - [{i}] type: {type(item)}, length: {len(item) if isinstance(item, (list, dict)) else 'N/A'}")
            if isinstance(item, list) and len(item) > 0:
                print(f"    - First element: {item[0]}")

    print("\nFull response (formatted):")
    pprint(data)

except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Meta and Asset Contexts (for funding + OI)
print("\n\n2. META AND ASSET CONTEXTS (metaAndAssetCtxs)")
print("-" * 80)
try:
    payload = {"type": "metaAndAssetCtxs"}
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"✓ Status: {response.status_code}")
    print(f"Response type: {type(data)}")

    if isinstance(data, list):
        print(f"List with {len(data)} elements")
        for i, item in enumerate(data):
            print(f"\n[{i}] - Type: {type(item)}")
            if isinstance(item, dict):
                print(f"  Keys: {list(item.keys())}")
            elif isinstance(item, list):
                print(f"  Length: {len(item)}")
                if len(item) > 0:
                    print(f"  First item type: {type(item[0])}")
                    if isinstance(item[0], dict):
                        print(f"  First item keys: {list(item[0].keys())}")
                        print(f"  First item sample:")
                        pprint(item[0])

                        # Look for BTC specifically
                        print(f"\n  Searching for BTC in element [{i}]...")
                        btc_found = False
                        for ctx_item in item[:5]:  # Check first 5
                            if isinstance(ctx_item, dict):
                                # Check all fields for BTC
                                for key, value in ctx_item.items():
                                    if isinstance(value, str) and "BTC" in value.upper():
                                        print(f"    Found BTC in field '{key}': {value}")
                                        print(f"    Full item:")
                                        pprint(ctx_item)
                                        btc_found = True
                                        break
                            if btc_found:
                                break

    print("\n\nFull response structure (first 2 elements):")
    if isinstance(data, list) and len(data) >= 2:
        print("\n[0] - Meta:")
        pprint(data[0])
        print("\n[1] - Asset Contexts (first 3 items):")
        if isinstance(data[1], list):
            pprint(data[1][:3])

except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Funding History
print("\n\n3. FUNDING HISTORY (fundingHistory) - Testing BTC")
print("-" * 80)
try:
    import time
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (24 * 3600 * 1000)  # 24 hours ago

    payload = {
        "type": "fundingHistory",
        "coin": "BTC",
        "startTime": start_ms
    }
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"✓ Status: {response.status_code}")
    print(f"Response type: {type(data)}")

    if isinstance(data, list):
        print(f"List with {len(data)} elements")
        if len(data) > 0:
            print(f"First item type: {type(data[0])}")
            print(f"First item:")
            pprint(data[0])

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nPlease share this output so we can fix the parsers!")

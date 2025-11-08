"""
Diagnostic script to inspect actual Hyperliquid API responses.
This will help us fix the IE parsers to match the real API format.
"""

import requests
import json

API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}

print("=" * 70)
print("HYPERLIQUID API DIAGNOSTIC")
print("=" * 70)

# Test 1: Order Book
print("\n1. Testing Order Book API...")
try:
    payload = {"type": "l2Book", "coin": "BTC"}
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response type: {type(data)}")
    print(f"Response preview:")
    print(json.dumps(data, indent=2)[:500])  # First 500 chars
except Exception as e:
    print(f"Error: {e}")

# Test 2: Meta and Asset Contexts (for funding & OI)
print("\n2. Testing Meta/Asset API...")
try:
    payload = {"type": "metaAndAssetCtxs"}
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response type: {type(data)}")
    if isinstance(data, list):
        print(f"List length: {len(data)}")
        for i, item in enumerate(data):
            print(f"\nItem {i} type: {type(item)}")
            if isinstance(item, list):
                print(f"  Sub-list length: {len(item)}")
                if item:
                    print(f"  First element type: {type(item[0])}")
                    print(f"  First element preview:")
                    print(json.dumps(item[0], indent=2)[:300])
            elif isinstance(item, dict):
                print(f"  Keys: {list(item.keys())[:10]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: All Asset Contexts
print("\n3. Testing All Asset Contexts...")
try:
    payload = {"type": "allAssetCtxs"}
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response type: {type(data)}")
    if isinstance(data, list) and data:
        print(f"List length: {len(data)}")
        print(f"First item type: {type(data[0])}")
        if isinstance(data[0], dict):
            print(f"First item keys: {list(data[0].keys())}")
            print(f"First item preview:")
            print(json.dumps(data[0], indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("Diagnostic complete!")
print("=" * 70)

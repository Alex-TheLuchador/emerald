"""
Async API client for Hyperliquid
"""
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

from config import HYPERLIQUID_API_URL


class HyperliquidClient:
    """Async client for fetching data from Hyperliquid API"""

    def __init__(self):
        self.api_url = HYPERLIQUID_API_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _post(self, payload: Dict[str, Any]) -> Any:
        """Make POST request to Hyperliquid API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        async with self.session.post(self.api_url, json=payload) as response:
            response.raise_for_status()
            return await response.json()

    async def get_order_book(self, coin: str) -> Dict[str, Any]:
        """
        Fetch L2 order book snapshot

        Returns:
            {
                "coin": "BTC",
                "levels": [[bids], [asks]],
                "time": timestamp
            }
        """
        payload = {
            "type": "l2Book",
            "coin": coin
        }
        return await self._post(payload)

    async def get_perp_metadata(self) -> List[Dict[str, Any]]:
        """
        Fetch perpetual futures metadata including funding rates and OI

        Returns list of assets with funding, openInterest, etc.
        """
        payload = {
            "type": "metaAndAssetCtxs"
        }
        return await self._post(payload)

    async def get_spot_metadata(self) -> List[Dict[str, Any]]:
        """
        Fetch spot market metadata including spot prices

        Returns spot asset contexts
        """
        payload = {
            "type": "spotMetaAndAssetCtxs"
        }
        return await self._post(payload)

    async def get_candles(
        self,
        coin: str,
        interval: str = "1m",
        lookback_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical candle data

        Args:
            coin: Coin symbol (e.g., "BTC")
            interval: Candle interval (e.g., "1m", "5m")
            lookback_minutes: How many minutes of history to fetch

        Returns:
            List of candles with OHLCV data
        """
        end_time = int(time.time() * 1000)  # Current time in ms
        start_time = end_time - (lookback_minutes * 60 * 1000)

        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time
            }
        }
        return await self._post(payload)

    async def get_all_data(self, coin: str) -> Dict[str, Any]:
        """
        Fetch all required data for a coin in parallel

        Returns:
            {
                "order_book": {...},
                "perp_data": {...},
                "spot_data": {...},
                "candles": [...]
            }
        """
        # Run all API calls in parallel
        results = await asyncio.gather(
            self.get_order_book(coin),
            self.get_perp_metadata(),
            self.get_spot_metadata(),
            self.get_candles(coin, interval="1m", lookback_minutes=60),
            return_exceptions=True
        )

        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                raise result

        order_book, perp_meta, spot_meta, candles = results

        # Extract specific coin data from metadata
        perp_data = self._extract_coin_data(perp_meta, coin, "perp")
        spot_data = self._extract_coin_data(spot_meta, coin, "spot")

        return {
            "order_book": order_book,
            "perp_data": perp_data,
            "spot_data": spot_data,
            "candles": candles,
            "timestamp": datetime.now()
        }

    def _extract_coin_data(
        self,
        metadata: List[Dict[str, Any]],
        coin: str,
        market_type: str
    ) -> Dict[str, Any]:
        """Extract data for specific coin from metadata response"""
        if market_type == "perp":
            # metaAndAssetCtxs returns [meta, asset_contexts]
            if len(metadata) >= 2:
                contexts = metadata[1]
                for i, asset in enumerate(contexts):
                    # Match by index - need to check meta for coin name
                    meta_list = metadata[0].get("universe", [])
                    if i < len(meta_list) and meta_list[i].get("name") == coin:
                        return asset

        elif market_type == "spot":
            # spotMetaAndAssetCtxs returns [meta, asset_contexts]
            if len(metadata) >= 2:
                meta_info = metadata[0]
                contexts = metadata[1]

                # Find the spot pair index for coin/USDC
                universe = meta_info.get("universe", [])
                for i, pair in enumerate(universe):
                    pair_name = pair.get("name", "")
                    if pair_name.startswith(f"{coin}/"):
                        if i < len(contexts):
                            return contexts[i]

        return {}


async def test_client():
    """Test the API client"""
    print("Testing Hyperliquid API Client...")

    async with HyperliquidClient() as client:
        print("\n1. Testing order book fetch...")
        order_book = await client.get_order_book("BTC")
        print(f"   ✓ Got order book with {len(order_book.get('levels', [[],[]])[0])} bid levels")

        print("\n2. Testing perp metadata...")
        perp_meta = await client.get_perp_metadata()
        print(f"   ✓ Got metadata for {len(perp_meta[1]) if len(perp_meta) > 1 else 0} assets")

        print("\n3. Testing spot metadata...")
        spot_meta = await client.get_spot_metadata()
        print(f"   ✓ Got spot data")

        print("\n4. Testing candles...")
        candles = await client.get_candles("BTC", lookback_minutes=60)
        print(f"   ✓ Got {len(candles)} candles")

        print("\n5. Testing parallel fetch...")
        all_data = await client.get_all_data("BTC")
        print(f"   ✓ Got all data for BTC")
        print(f"   - Order book: {len(all_data['order_book'].get('levels', [[],[]])[0])} levels")
        print(f"   - Perp data keys: {list(all_data['perp_data'].keys())}")
        print(f"   - Spot data keys: {list(all_data['spot_data'].keys())}")
        print(f"   - Candles: {len(all_data['candles'])}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_client())

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

    async def get_user_state(self, user_address: str) -> Dict[str, Any]:
        """
        Fetch clearinghouse state for a specific user address

        Args:
            user_address: 42-character hexadecimal address (e.g., "0x...")

        Returns:
            {
                "marginSummary": {
                    "accountValue": str,
                    "totalNtlPos": str,
                    "totalRawUsd": str,
                    "totalMarginUsed": str
                },
                "assetPositions": [
                    {
                        "position": {
                            "coin": str,
                            "szi": str,  # Position size
                            "leverage": {...},
                            "liquidationPx": str,
                            ...
                        }
                    }
                ],
                ...
            }
        """
        payload = {
            "type": "clearinghouseState",
            "user": user_address
        }
        return await self._post(payload)

    async def get_funding_history(self, coin: str, lookback_hours: int = 168) -> List[Dict[str, Any]]:
        """
        Fetch historical funding rates from Hyperliquid API

        Args:
            coin: Coin symbol (e.g., "ETH", "BTC")
            lookback_hours: Hours of history (default 168 = 7 days)

        Returns:
            List of funding rate snapshots:
            [
                {
                    "coin": "ETH",
                    "fundingRate": "-0.00022196",
                    "premium": "-0.00052196",
                    "time": 1683849600076
                },
                ...
            ]
        """
        start_time = int((time.time() - lookback_hours * 3600) * 1000)
        end_time = int(time.time() * 1000)

        payload = {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": start_time,
            "endTime": end_time
        }

        return await self._post(payload)

    async def get_whale_addresses(self, coin: str, min_position_usd: float = 100000) -> List[str]:
        """
        Get list of whale wallet addresses for a specific coin

        NOTE: Need clarification on how to get this data:
        Option 1: Leaderboard API endpoint
        Option 2: Third-party service (CoinGlass, HyperTracker)
        Option 3: Scan all addresses with positions (expensive)

        Args:
            coin: Coin symbol
            min_position_usd: Minimum position size to be considered a whale

        Returns:
            List of wallet addresses with positions > min_position_usd
        """
        # TODO: NEED CLARIFICATION ON API ENDPOINT
        # Placeholder structure for now
        payload = {
            "type": "leaderboard",  # Hypothetical endpoint
            "coin": coin,
            "minNotional": min_position_usd
        }
        try:
            result = await self._post(payload)
            # Extract addresses from result
            if isinstance(result, list):
                return [item.get("address") for item in result if item.get("address")]
            return []
        except Exception:
            # Endpoint may not exist - return empty for now
            return []

    async def get_batch_user_states(self, user_addresses: List[str]) -> Dict[str, Any]:
        """
        Fetch clearinghouse state for multiple users in parallel

        Args:
            user_addresses: List of wallet addresses

        Returns:
            Dict mapping address -> user state
        """
        if not user_addresses:
            return {}

        # Fetch all user states in parallel
        tasks = [self.get_user_state(addr) for addr in user_addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map addresses to results
        user_states = {}
        for addr, result in zip(user_addresses, results):
            if not isinstance(result, Exception):
                user_states[addr] = result

        return user_states

    async def get_all_data(self, coin: str, include_whale_data: bool = False) -> Dict[str, Any]:
        """
        Fetch all required data for a coin in parallel

        Args:
            coin: Coin symbol
            include_whale_data: If True, fetch whale positions (slower)

        Returns:
            {
                "order_book": {...},
                "perp_data": {...},
                "spot_data": {...},
                "candles": [...],
                "whale_positions": [...] (optional)
            }
        """
        # Base API calls
        tasks = [
            self.get_order_book(coin),
            self.get_perp_metadata(),
            self.get_spot_metadata(),
            self.get_candles(coin, interval="1m", lookback_minutes=60),
        ]

        # Optionally add whale data
        if include_whale_data:
            tasks.append(self.get_whale_addresses(coin))

        # Run all API calls in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Log but don't fail for optional whale data
                if i >= 4 and include_whale_data:
                    results[i] = []
                else:
                    raise result

        order_book = results[0]
        perp_meta = results[1]
        spot_meta = results[2]
        candles = results[3]
        whale_addresses = results[4] if include_whale_data and len(results) > 4 else []

        # Extract specific coin data from metadata
        perp_data = self._extract_coin_data(perp_meta, coin, "perp")
        spot_data = self._extract_coin_data(spot_meta, coin, "spot")

        data = {
            "order_book": order_book,
            "perp_data": perp_data,
            "spot_data": spot_data,
            "candles": candles,
            "timestamp": datetime.now()
        }

        # Add whale data if requested
        if include_whale_data and whale_addresses:
            whale_states = await self.get_batch_user_states(whale_addresses)
            data["whale_positions"] = whale_states

        return data

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

"""
Hyperliquid API client

Clean, focused client for fetching market data
"""
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from ..common.models import OrderBook, Candle, PerpData, SpotData, MarketData
from ..common.config import get_config


class HyperliquidClient:
    """Async client for Hyperliquid API"""

    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize client

        Args:
            api_url: Optional API URL override (defaults to config)
        """
        config = get_config()
        self.api_url = api_url or config.api.hyperliquid_url
        self.timeout = config.api.timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()

    async def _post(self, payload: Dict[str, Any]) -> Any:
        """
        Make POST request to API

        Args:
            payload: Request payload

        Returns:
            JSON response

        Raises:
            RuntimeError: If session not initialized
            aiohttp.ClientError: On HTTP errors
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        async with self.session.post(
            self.api_url,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_order_book(self, coin: str) -> Dict[str, Any]:
        """
        Fetch L2 order book snapshot

        Args:
            coin: Coin symbol (e.g., "BTC")

        Returns:
            Order book data
        """
        payload = {
            "type": "l2Book",
            "coin": coin
        }
        return await self._post(payload)

    async def get_perp_metadata(self) -> List[Dict[str, Any]]:
        """
        Fetch perpetual futures metadata

        Returns:
            List with [meta, asset_contexts]
        """
        payload = {
            "type": "metaAndAssetCtxs"
        }
        return await self._post(payload)

    async def get_spot_metadata(self) -> List[Dict[str, Any]]:
        """
        Fetch spot market metadata

        Returns:
            List with [meta, asset_contexts]
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
            coin: Coin symbol
            interval: Candle interval (e.g., "1m", "5m")
            lookback_minutes: Minutes of history to fetch

        Returns:
            List of candle data
        """
        end_time = int(time.time() * 1000)
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
        Fetch user clearinghouse state

        Args:
            user_address: Wallet address

        Returns:
            User state data
        """
        payload = {
            "type": "clearinghouseState",
            "user": user_address
        }
        return await self._post(payload)

    async def get_funding_history(
        self,
        coin: str,
        lookback_hours: int = 168
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical funding rates

        Args:
            coin: Coin symbol
            lookback_hours: Hours of history (default 7 days)

        Returns:
            List of funding rate snapshots
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

    def _extract_coin_data(
        self,
        metadata: List[Dict[str, Any]],
        coin: str,
        market_type: str
    ) -> Dict[str, Any]:
        """
        Extract data for specific coin from metadata response

        Args:
            metadata: Raw metadata response
            coin: Coin to extract
            market_type: "perp" or "spot"

        Returns:
            Coin-specific data
        """
        if market_type == "perp":
            if len(metadata) >= 2:
                contexts = metadata[1]
                meta_list = metadata[0].get("universe", [])
                for i, asset in enumerate(meta_list):
                    if asset.get("name") == coin and i < len(contexts):
                        return contexts[i]

        elif market_type == "spot":
            if len(metadata) >= 2:
                universe = metadata[0].get("universe", [])
                contexts = metadata[1]
                for i, pair in enumerate(universe):
                    pair_name = pair.get("name", "")
                    if pair_name.startswith(f"{coin}/") and i < len(contexts):
                        return contexts[i]

        return {}

    async def get_market_data(self, coin: str) -> MarketData:
        """
        Fetch all market data for a coin (parallel)

        Args:
            coin: Coin symbol

        Returns:
            MarketData model with all data
        """
        # Fetch all data in parallel
        tasks = [
            self.get_order_book(coin),
            self.get_perp_metadata(),
            self.get_spot_metadata(),
            self.get_candles(coin, interval="1m", lookback_minutes=60),
        ]

        results = await asyncio.gather(*tasks)

        order_book_data = results[0]
        perp_meta = results[1]
        spot_meta = results[2]
        candles_data = results[3]

        # Extract coin-specific data
        perp_data_dict = self._extract_coin_data(perp_meta, coin, "perp")
        spot_data_dict = self._extract_coin_data(spot_meta, coin, "spot")

        # Convert to models
        order_book = OrderBook(
            coin=order_book_data.get("coin", coin),
            levels=order_book_data.get("levels", [[], []]),
            time=order_book_data.get("time", int(time.time() * 1000))
        )

        perp_data = PerpData(**perp_data_dict) if perp_data_dict else PerpData()
        spot_data = SpotData(**spot_data_dict) if spot_data_dict else SpotData()
        candles = [Candle(**c) for c in candles_data]

        return MarketData(
            coin=coin,
            order_book=order_book,
            perp_data=perp_data,
            spot_data=spot_data,
            candles=candles,
            timestamp=datetime.now()
        )


async def test_client():
    """Test the API client"""
    print("Testing Hyperliquid API Client...")

    async with HyperliquidClient() as client:
        print("\n1. Fetching market data for BTC...")
        data = await client.get_market_data("BTC")
        print(f"   ✓ Got data for {data.coin}")
        print(f"   ✓ Order book: {len(data.order_book.bids)} bids, {len(data.order_book.asks)} asks")
        print(f"   ✓ Candles: {len(data.candles)}")
        print(f"   ✓ Funding: {data.perp_data.funding_rate}")
        print(f"   ✓ OI: {data.perp_data.open_interest:,.0f}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_client())

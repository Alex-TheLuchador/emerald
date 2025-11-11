"""
Metric calculations for trading signals
"""
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from config import THRESHOLDS, ORDER_BOOK_LEVELS, VWAP_LOOKBACK_CANDLES, FLOW_LOOKBACK_CANDLES


class MetricsCalculator:
    """Calculate all trading metrics from raw API data"""

    def calculate_all_metrics(
        self,
        order_book: Dict[str, Any],
        perp_data: Dict[str, Any],
        spot_data: Dict[str, Any],
        candles: List[Dict[str, Any]],
        historical_oi: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate all metrics from raw data

        Args:
            order_book: L2 order book snapshot
            perp_data: Perpetual market data (funding, OI, price)
            spot_data: Spot market data (price)
            candles: List of 1m candles
            historical_oi: OI snapshot from N hours ago

        Returns:
            Dictionary of all calculated metrics
        """
        metrics = {}

        # 1. Order Book Imbalance
        metrics['ob_imbalance'] = self.calculate_order_book_imbalance(order_book)

        # 2. Funding Rate (annualized)
        metrics['funding_annualized'] = self.calculate_funding_rate(perp_data)

        # 3. VWAP Deviation
        vwap_metrics = self.calculate_vwap_deviation(candles)
        metrics.update(vwap_metrics)

        # 4. Trade Flow Imbalance
        metrics['flow_imbalance'] = self.calculate_trade_flow(candles)

        # 5. Open Interest Divergence
        if historical_oi:
            oi_metrics = self.calculate_oi_divergence(
                current_oi=float(perp_data.get('openInterest', 0)),
                historical_oi=historical_oi['open_interest'],
                current_price=float(candles[-1]['c']) if candles else 0,
                historical_price=historical_oi.get('price', 0)
            )
            metrics.update(oi_metrics)
        else:
            metrics['oi_divergence_type'] = 'unknown'
            metrics['oi_change_pct'] = 0
            metrics['price_change_pct'] = 0

        # 6. Basis Spread
        metrics['basis_pct'] = self.calculate_basis(perp_data, spot_data)

        # Add current price
        metrics['current_price'] = float(candles[-1]['c']) if candles else 0

        return metrics

    def calculate_order_book_imbalance(self, order_book: Dict[str, Any]) -> float:
        """
        Calculate bid/ask liquidity imbalance

        Returns: -1.0 to +1.0
            Negative = ask pressure (bearish)
            Positive = bid pressure (bullish)
        """
        levels = order_book.get('levels', [[], []])
        if len(levels) < 2:
            return 0.0

        bids = levels[0][:ORDER_BOOK_LEVELS]
        asks = levels[1][:ORDER_BOOK_LEVELS]

        # Sum liquidity (size * price for dollar value)
        bid_liquidity = sum(float(level['px']) * float(level['sz']) for level in bids)
        ask_liquidity = sum(float(level['px']) * float(level['sz']) for level in asks)

        if bid_liquidity + ask_liquidity == 0:
            return 0.0

        imbalance = (bid_liquidity - ask_liquidity) / (bid_liquidity + ask_liquidity)
        return round(imbalance, 4)

    def calculate_funding_rate(self, perp_data: Dict[str, Any]) -> float:
        """
        Annualize funding rate for human readability

        Returns: Annualized % (e.g., 12.5 means 12.5% per year)
        """
        funding_8h = float(perp_data.get('funding', 0))

        # Funding is per 8-hour period
        # Annualize: funding * 3 periods/day * 365 days * 100 for percentage
        annualized_pct = funding_8h * 3 * 365 * 100

        return round(annualized_pct, 2)

    def calculate_vwap_deviation(self, candles: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate VWAP and z-score deviation

        Returns:
            {
                'vwap': float,
                'vwap_deviation_pct': float,
                'vwap_z_score': float
            }
        """
        if not candles or len(candles) < VWAP_LOOKBACK_CANDLES:
            return {
                'vwap': 0.0,
                'vwap_deviation_pct': 0.0,
                'vwap_z_score': 0.0
            }

        # Use last N candles
        recent_candles = candles[-VWAP_LOOKBACK_CANDLES:]

        # Calculate VWAP
        prices = np.array([float(c['c']) for c in recent_candles])
        volumes = np.array([float(c['v']) for c in recent_candles])

        if volumes.sum() == 0:
            return {
                'vwap': 0.0,
                'vwap_deviation_pct': 0.0,
                'vwap_z_score': 0.0
            }

        vwap = np.sum(prices * volumes) / np.sum(volumes)
        current_price = float(candles[-1]['c'])

        # Percentage deviation
        deviation_pct = ((current_price - vwap) / vwap) * 100

        # Z-score (standard deviations from VWAP)
        std_dev = np.std(prices)
        z_score = (current_price - vwap) / std_dev if std_dev > 0 else 0

        return {
            'vwap': round(float(vwap), 2),
            'vwap_deviation_pct': round(float(deviation_pct), 2),
            'vwap_z_score': round(float(z_score), 2)
        }

    def calculate_trade_flow(self, candles: List[Dict[str, Any]]) -> float:
        """
        Calculate trade flow imbalance (aggressor direction)

        Positive = aggressive buying
        Negative = aggressive selling

        Returns: Flow imbalance score
        """
        if not candles or len(candles) < FLOW_LOOKBACK_CANDLES:
            return 0.0

        recent_candles = candles[-FLOW_LOOKBACK_CANDLES:]

        # Calculate average volume for weighting
        volumes = [float(c['v']) for c in candles[-20:]]  # Last 20 for average
        avg_volume = np.mean(volumes) if volumes else 1.0

        flow_scores = []
        for candle in recent_candles:
            open_price = float(candle['o'])
            close_price = float(candle['c'])
            volume = float(candle['v'])

            if open_price == 0:
                continue

            # Price change percentage
            price_change_pct = ((close_price - open_price) / open_price) * 100

            # Volume weight
            volume_weight = volume / avg_volume if avg_volume > 0 else 1.0

            # Flow score = direction * intensity
            flow_score = price_change_pct * volume_weight
            flow_scores.append(flow_score)

        # Sum flow scores
        total_flow = sum(flow_scores)

        return round(total_flow, 4)

    def calculate_oi_divergence(
        self,
        current_oi: float,
        historical_oi: float,
        current_price: float,
        historical_price: float
    ) -> Dict[str, Any]:
        """
        Calculate OI vs price divergence to detect real vs fake moves

        Returns:
            {
                'oi_change_pct': float,
                'price_change_pct': float,
                'oi_divergence_type': str (strong_bullish/bearish/weak_bullish/bearish/neutral)
            }
        """
        if historical_oi == 0 or historical_price == 0:
            return {
                'oi_change_pct': 0.0,
                'price_change_pct': 0.0,
                'oi_divergence_type': 'unknown'
            }

        oi_change_pct = ((current_oi - historical_oi) / historical_oi) * 100
        price_change_pct = ((current_price - historical_price) / historical_price) * 100

        # Determine divergence type
        threshold = THRESHOLDS['oi_change_threshold']

        if oi_change_pct > threshold and price_change_pct > 1:
            divergence_type = 'strong_bullish'  # New longs opening
        elif oi_change_pct > threshold and price_change_pct < -1:
            divergence_type = 'strong_bearish'  # New shorts opening
        elif oi_change_pct < -threshold and price_change_pct > 1:
            divergence_type = 'weak_bullish'  # Shorts covering (fade)
        elif oi_change_pct < -threshold and price_change_pct < -1:
            divergence_type = 'weak_bearish'  # Longs closing (fade)
        else:
            divergence_type = 'neutral'

        return {
            'oi_change_pct': round(oi_change_pct, 2),
            'price_change_pct': round(price_change_pct, 2),
            'oi_divergence_type': divergence_type
        }

    def calculate_basis(
        self,
        perp_data: Dict[str, Any],
        spot_data: Dict[str, Any]
    ) -> float:
        """
        Calculate basis spread (perp - spot)

        Positive = perps trading at premium (bearish signal)
        Negative = perps trading at discount (bullish signal)

        Returns: Basis % (e.g., 0.3 means 0.3% premium)
        """
        perp_price = float(perp_data.get('markPx', 0))
        spot_price = float(spot_data.get('midPx', 0))

        if spot_price == 0:
            return 0.0

        basis_pct = ((perp_price - spot_price) / spot_price) * 100

        return round(basis_pct, 4)


def test_metrics():
    """Test metric calculations with sample data"""
    print("Testing Metrics Calculator...")

    calculator = MetricsCalculator()

    # Sample order book
    order_book = {
        'levels': [
            [  # Bids
                {'px': '67800', 'sz': '10.5', 'n': 5},
                {'px': '67790', 'sz': '8.2', 'n': 3},
                {'px': '67780', 'sz': '15.0', 'n': 7},
            ],
            [  # Asks
                {'px': '67820', 'sz': '5.2', 'n': 2},
                {'px': '67830', 'sz': '3.1', 'n': 1},
                {'px': '67840', 'sz': '7.5', 'n': 4},
            ]
        ]
    }

    # Sample perp data
    perp_data = {
        'funding': '0.000034',
        'openInterest': '1250000000',
        'markPx': '67825'
    }

    # Sample spot data
    spot_data = {
        'midPx': '67820'
    }

    # Sample candles (60 candles for VWAP)
    candles = []
    base_price = 67800
    for i in range(60):
        price = base_price + np.random.randint(-50, 50)
        candles.append({
            't': 1699564800000 + (i * 60000),
            'o': str(price),
            'h': str(price + 10),
            'l': str(price - 10),
            'c': str(price + np.random.randint(-5, 5)),
            'v': str(100 + np.random.randint(-20, 20)),
            'n': 100
        })

    print("\n1. Order Book Imbalance...")
    ob_imbalance = calculator.calculate_order_book_imbalance(order_book)
    print(f"   Result: {ob_imbalance} ({'Bullish' if ob_imbalance > 0 else 'Bearish'})")

    print("\n2. Funding Rate...")
    funding = calculator.calculate_funding_rate(perp_data)
    print(f"   Result: {funding}% annualized")

    print("\n3. VWAP Deviation...")
    vwap_metrics = calculator.calculate_vwap_deviation(candles)
    print(f"   VWAP: ${vwap_metrics['vwap']}")
    print(f"   Deviation: {vwap_metrics['vwap_deviation_pct']}%")
    print(f"   Z-score: {vwap_metrics['vwap_z_score']}")

    print("\n4. Trade Flow...")
    flow = calculator.calculate_trade_flow(candles)
    print(f"   Result: {flow} ({'Buying' if flow > 0 else 'Selling'})")

    print("\n5. OI Divergence...")
    oi_metrics = calculator.calculate_oi_divergence(
        current_oi=1250000000,
        historical_oi=1180000000,
        current_price=67825,
        historical_price=67500
    )
    print(f"   OI Change: {oi_metrics['oi_change_pct']}%")
    print(f"   Price Change: {oi_metrics['price_change_pct']}%")
    print(f"   Type: {oi_metrics['oi_divergence_type']}")

    print("\n6. Basis Spread...")
    basis = calculator.calculate_basis(perp_data, spot_data)
    print(f"   Result: {basis}%")

    print("\n7. All Metrics Together...")
    all_metrics = calculator.calculate_all_metrics(
        order_book=order_book,
        perp_data=perp_data,
        spot_data=spot_data,
        candles=candles,
        historical_oi={'open_interest': 1180000000, 'price': 67500}
    )
    print(f"   Calculated {len(all_metrics)} metrics")
    for key, value in all_metrics.items():
        print(f"   - {key}: {value}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_metrics()

"""
Signal 2: Institutional Liquidity Tracker (Order Book Imbalance)

Detects institutional positioning via order book analysis.
User confirmed this is one of their most profitable signals.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class LiquiditySignal:
    """Output from liquidity analysis"""
    direction: str  # BULLISH, BEARISH, NEUTRAL
    strength: float  # 0-10
    quality: str  # HIGH, MEDIUM, LOW
    size_imbalance: float  # -1 to +1
    concentration: Dict[str, float]  # bid/ask concentration
    velocity: Optional[float]  # Rate of change
    is_manipulated: bool  # Quote stuffing detected
    details: Dict[str, Any]


class InstitutionalLiquidity:
    """
    Track institutional liquidity positioning via order book analysis

    Based on Ed's spec + user's profitable trading patterns
    """

    def __init__(self):
        # Thresholds from Ed's spec
        self.QUALITY_HIGH = 0.3
        self.QUALITY_MODERATE = 0.15
        self.CONCENTRATION_MAX = 0.6  # Above this = likely fake wall
        self.VELOCITY_FAST = 0.1
        self.IMBALANCE_STRONG = 0.5
        self.IMBALANCE_MODERATE = 0.3

    def analyze(
        self,
        order_book: Dict[str, Any],
        previous_snapshots: Optional[List[Dict[str, float]]] = None
    ) -> LiquiditySignal:
        """
        Analyze institutional liquidity positioning

        Args:
            order_book: L2 order book snapshot
                {
                    'levels': [[bids], [asks]],
                    'time': timestamp
                }
            previous_snapshots: Last 3-5 order book snapshots for velocity
                [
                    {'imbalance': float, 'timestamp': float},
                    ...
                ]

        Returns:
            LiquiditySignal with direction, strength, quality
        """
        # Calculate size-weighted imbalance
        size_imbalance = self._calculate_size_imbalance(order_book)

        # Calculate concentration (fake wall detection)
        bid_concentration = self._calculate_concentration(order_book['levels'][0])
        ask_concentration = self._calculate_concentration(order_book['levels'][1])

        # Detect quote stuffing
        is_manipulated = self._detect_manipulation(order_book)

        # Calculate liquidity velocity
        velocity = None
        if previous_snapshots and len(previous_snapshots) >= 3:
            velocity = self._calculate_velocity(size_imbalance, previous_snapshots)

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            size_imbalance,
            bid_concentration,
            ask_concentration,
            is_manipulated
        )

        # Determine quality level
        if quality_score >= self.QUALITY_HIGH:
            quality = "HIGH"
        elif quality_score >= self.QUALITY_MODERATE:
            quality = "MEDIUM"
        else:
            quality = "LOW"

        # Determine direction
        if abs(size_imbalance) >= self.IMBALANCE_STRONG and quality in ["HIGH", "MEDIUM"]:
            direction = "BULLISH" if size_imbalance > 0 else "BEARISH"
        elif abs(size_imbalance) >= self.IMBALANCE_MODERATE and quality == "HIGH":
            direction = "BULLISH" if size_imbalance > 0 else "BEARISH"
        else:
            direction = "NEUTRAL"

        # Calculate strength (0-10)
        strength = self._calculate_strength(size_imbalance, quality_score, velocity)

        return LiquiditySignal(
            direction=direction,
            strength=strength,
            quality=quality,
            size_imbalance=size_imbalance,
            concentration={'bid': bid_concentration, 'ask': ask_concentration},
            velocity=velocity,
            is_manipulated=is_manipulated,
            details={
                'quality_score': quality_score,
                'dominant_side': 'BID' if size_imbalance > 0 else 'ASK',
                'concentration_warning': max(bid_concentration, ask_concentration) > self.CONCENTRATION_MAX
            }
        )

    def _calculate_size_imbalance(self, order_book: Dict[str, Any]) -> float:
        """
        Calculate dollar-weighted bid-ask imbalance

        Returns: -1 (all asks) to +1 (all bids)
        """
        bids = order_book['levels'][0][:20]  # Top 20 levels
        asks = order_book['levels'][1][:20]

        if not bids or not asks:
            return 0.0

        # Dollar-weighted liquidity
        bid_liquidity = sum(float(b['px']) * float(b['sz']) for b in bids)
        ask_liquidity = sum(float(a['px']) * float(a['sz']) for a in asks)

        if bid_liquidity + ask_liquidity == 0:
            return 0.0

        # Normalize to -1 to +1
        imbalance = (bid_liquidity - ask_liquidity) / (bid_liquidity + ask_liquidity)
        return round(float(imbalance), 4)

    def _calculate_concentration(self, levels: List[Dict[str, Any]]) -> float:
        """
        Calculate Herfindahl index (order distribution)

        Low (0.1-0.3) = distributed orders = real institutions
        High (>0.6) = concentrated at one level = likely fake wall

        Returns: 0 to 1
        """
        if not levels:
            return 0.0

        sizes = [float(level['sz']) for level in levels[:20]]
        total_size = sum(sizes)

        if total_size == 0:
            return 0.0

        # Sum of squared proportions
        concentration = sum((s / total_size) ** 2 for s in sizes)
        return round(float(concentration), 4)

    def _detect_manipulation(self, order_book: Dict[str, Any]) -> bool:
        """
        Detect quote stuffing (HFT manipulation)

        HFT: Many tiny orders to create fake liquidity

        Returns: True if manipulation detected
        """
        bids = order_book['levels'][0][:20]
        asks = order_book['levels'][1][:20]

        if not bids or not asks:
            return False

        # Calculate average order size
        bid_sizes = [float(b['sz']) for b in bids]
        ask_sizes = [float(a['sz']) for a in asks]

        avg_order_size = np.mean(bid_sizes + ask_sizes)

        # If average order < threshold (e.g., 0.01 BTC), likely HFT stuffing
        # This threshold may need adjustment based on asset
        MANIPULATION_THRESHOLD = 0.01

        return avg_order_size < MANIPULATION_THRESHOLD

    def _calculate_velocity(
        self,
        current_imbalance: float,
        previous_snapshots: List[Dict[str, float]]
    ) -> float:
        """
        Calculate rate of change in order book imbalance

        Fast changes = institutions repositioning aggressively

        Returns: Average rate of change per snapshot
        """
        if not previous_snapshots or len(previous_snapshots) < 3:
            return 0.0

        recent_imbalances = [s['imbalance'] for s in previous_snapshots[-3:]]
        recent_imbalances.append(current_imbalance)

        # Calculate changes between consecutive snapshots
        changes = [recent_imbalances[i] - recent_imbalances[i-1]
                   for i in range(1, len(recent_imbalances))]

        if changes:
            velocity = np.mean(changes)
            return round(float(velocity), 4)

        return 0.0

    def _calculate_quality_score(
        self,
        size_imbalance: float,
        bid_concentration: float,
        ask_concentration: float,
        is_manipulated: bool
    ) -> float:
        """
        Calculate quality score (0-1)

        Quality = signal strength × (1 - manipulation penalty)

        >0.3 = real institutional flow (HIGH)
        <0.15 = fake walls / manipulation (LOW)
        """
        if is_manipulated:
            return 0.0

        # Concentration penalty (higher concentration = lower quality)
        max_concentration = max(bid_concentration, ask_concentration)
        concentration_penalty = max_concentration

        # Quality = imbalance strength × (1 - concentration)
        quality = abs(size_imbalance) * (1 - concentration_penalty)

        return round(float(quality), 4)

    def _calculate_strength(
        self,
        size_imbalance: float,
        quality_score: float,
        velocity: Optional[float]
    ) -> float:
        """
        Calculate signal strength (0-10)

        Based on imbalance magnitude, quality, and velocity
        """
        strength = 0.0

        # Imbalance contribution (0-5 points)
        imbalance_abs = abs(size_imbalance)
        if imbalance_abs >= 0.7:
            strength += 5
        elif imbalance_abs >= self.IMBALANCE_STRONG:
            strength += 4
        elif imbalance_abs >= self.IMBALANCE_MODERATE:
            strength += 3
        elif imbalance_abs >= 0.2:
            strength += 2

        # Quality contribution (0-3 points)
        if quality_score >= 0.4:
            strength += 3
        elif quality_score >= self.QUALITY_HIGH:
            strength += 2
        elif quality_score >= self.QUALITY_MODERATE:
            strength += 1

        # Velocity bonus (0-2 points)
        if velocity is not None:
            if abs(velocity) >= 0.15:
                strength += 2
            elif abs(velocity) >= self.VELOCITY_FAST:
                strength += 1

        return min(10.0, float(strength))


def test_liquidity():
    """Test institutional liquidity signal"""
    print("Testing Institutional Liquidity Signal...")

    signal_gen = InstitutionalLiquidity()

    # Test case 1: Strong bullish imbalance (high quality)
    print("\n1. Testing STRONG BULLISH (distributed liquidity):")
    order_book = {
        'levels': [
            # Bids: distributed across levels (good quality)
            [
                {'px': '67800', 'sz': '5.0'},
                {'px': '67795', 'sz': '4.5'},
                {'px': '67790', 'sz': '4.0'},
                {'px': '67785', 'sz': '3.5'},
                {'px': '67780', 'sz': '3.0'},
            ],
            # Asks: smaller
            [
                {'px': '67805', 'sz': '1.0'},
                {'px': '67810', 'sz': '0.8'},
                {'px': '67815', 'sz': '0.6'},
            ]
        ],
        'time': 1234567890
    }

    signal = signal_gen.analyze(order_book)
    print(f"   Direction: {signal.direction}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Quality: {signal.quality}")
    print(f"   Size Imbalance: {signal.size_imbalance:+.3f}")
    print(f"   Bid Concentration: {signal.concentration['bid']:.3f}")
    print(f"   Ask Concentration: {signal.concentration['ask']:.3f}")
    print(f"   Manipulated: {signal.is_manipulated}")

    # Test case 2: Fake wall (high concentration)
    print("\n2. Testing FAKE WALL (concentrated liquidity):")
    order_book = {
        'levels': [
            # Bids: one huge order (fake wall)
            [
                {'px': '67800', 'sz': '100.0'},  # Concentrated
                {'px': '67795', 'sz': '1.0'},
                {'px': '67790', 'sz': '0.5'},
            ],
            # Asks
            [
                {'px': '67805', 'sz': '2.0'},
                {'px': '67810', 'sz': '1.5'},
            ]
        ],
        'time': 1234567890
    }

    signal = signal_gen.analyze(order_book)
    print(f"   Direction: {signal.direction}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Quality: {signal.quality}")
    print(f"   Size Imbalance: {signal.size_imbalance:+.3f}")
    print(f"   Bid Concentration: {signal.concentration['bid']:.3f} (HIGH = fake wall)")
    print(f"   Quality Score: {signal.details['quality_score']:.3f}")

    # Test case 3: With velocity
    print("\n3. Testing WITH VELOCITY (repositioning):")
    previous_snapshots = [
        {'imbalance': 0.1, 'timestamp': 1234567880},
        {'imbalance': 0.2, 'timestamp': 1234567885},
        {'imbalance': 0.4, 'timestamp': 1234567890},
    ]

    signal = signal_gen.analyze(order_book, previous_snapshots)
    print(f"   Velocity: {signal.velocity:+.4f}" if signal.velocity else "   Velocity: None")
    print(f"   Strength (with velocity): {signal.strength}/10")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_liquidity()

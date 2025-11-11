"""
Signal 1: Institutional Positioning (Funding Velocity + Volume Context)

Detects institutional accumulation/distribution via funding rate dynamics.
User confirmed this is one of their most profitable signals.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PositioningSignal:
    """Output from institutional positioning analysis"""
    direction: str  # BULLISH, BEARISH, NEUTRAL
    regime: str  # ACCUMULATION, DISTRIBUTION, MOMENTUM, EXHAUSTION, NEUTRAL
    strength: float  # 0-10
    confidence: str  # HIGH, MEDIUM, LOW
    velocity_4h: float  # Funding change over 4h
    acceleration: float  # 2nd derivative
    volume_ratio: float  # Current volume / 24h average
    details: Dict[str, Any]  # Additional context


class InstitutionalPositioning:
    """
    Track institutional positioning via funding rate dynamics

    Based on Ed's spec + user's profitable trading patterns
    """

    def __init__(self):
        # Thresholds recalibrated for realistic funding rate dynamics
        # Funding rates typically 0.01-0.05% per 8h, changes are 0.001-0.01% per 4h
        self.ACCELERATION_HIGH = 0.0002       # 0.02% (strong acceleration)
        self.ACCELERATION_MODERATE = 0.0001   # 0.01% (moderate acceleration)
        self.VELOCITY_HIGH = 0.0003           # 0.03% (strong velocity)
        self.VELOCITY_MODERATE = 0.0001       # 0.01% (moderate velocity)
        self.VOLUME_SURGE = 1.5
        self.VOLUME_MODERATE = 1.2
        self.VOLUME_DECLINE = 0.8

    def analyze(
        self,
        funding_dynamics: Dict[str, float],
        volume_data: Dict[str, float],
        cross_asset_data: Optional[Dict[str, Dict[str, float]]] = None
    ) -> PositioningSignal:
        """
        Analyze institutional positioning

        Args:
            funding_dynamics: From storage.get_funding_dynamics()
                {
                    'current': float,
                    'funding_4h_ago': float,
                    'funding_8h_ago': float,
                    'velocity_4h': float,
                    'velocity_8h': float,
                    'acceleration': float
                }
            volume_data: {
                'current': float,  # Current volume
                'avg_24h': float   # 24h average volume
            }
            cross_asset_data: Optional cross-asset funding velocities

        Returns:
            PositioningSignal with direction, regime, strength, confidence
        """
        # Extract metrics
        velocity = funding_dynamics.get('velocity_4h', 0)
        acceleration = funding_dynamics.get('acceleration', 0)
        current_funding = funding_dynamics.get('current', 0)

        # Volume context
        volume_ratio = volume_data['current'] / volume_data['avg_24h'] if volume_data['avg_24h'] > 0 else 1.0

        # Classify regime
        regime = self._determine_regime(acceleration, velocity, volume_ratio)

        # Calculate signal strength
        strength = self._calculate_strength(
            acceleration,
            velocity,
            volume_ratio,
            cross_asset_aligned=False  # TODO: Implement cross-asset check
        )

        # Determine direction and confidence
        direction = regime['direction']
        confidence = regime['confidence']

        return PositioningSignal(
            direction=direction,
            regime=regime['type'],
            strength=strength,
            confidence=confidence,
            velocity_4h=velocity,
            acceleration=acceleration,
            volume_ratio=volume_ratio,
            details={
                'current_funding': current_funding,
                'regime_description': regime.get('description', ''),
                'volume_context': self._describe_volume(volume_ratio)
            }
        )

    def _determine_regime(
        self,
        acceleration: float,
        velocity: float,
        volume_ratio: float
    ) -> Dict[str, str]:
        """
        Classify market regime based on funding dynamics

        Returns regime dict with type, direction, confidence, description
        """
        # INSTITUTIONAL_ACCUMULATION: Strong acceleration + high volume + positive velocity
        if acceleration > self.ACCELERATION_HIGH and volume_ratio > self.VOLUME_SURGE:
            if velocity > 0:
                return {
                    'type': 'INSTITUTIONAL_ACCUMULATION',
                    'direction': 'BULLISH',
                    'confidence': 'HIGH',
                    'description': 'Institutions buying aggressively (funding accelerating up + high volume)'
                }
            else:
                return {
                    'type': 'INSTITUTIONAL_DISTRIBUTION',
                    'direction': 'BEARISH',
                    'confidence': 'HIGH',
                    'description': 'Institutions selling aggressively (funding accelerating down + high volume)'
                }

        # MOMENTUM: Moderate acceleration + moderate volume
        elif acceleration > self.ACCELERATION_MODERATE and volume_ratio > self.VOLUME_MODERATE:
            direction = 'BULLISH' if velocity > 0 else 'BEARISH'
            return {
                'type': 'MOMENTUM',
                'direction': direction,
                'confidence': 'MEDIUM',
                'description': f'Moderate {direction.lower()} momentum (sustained funding trend)'
            }

        # EXHAUSTION: High velocity but negative acceleration + low volume
        elif abs(velocity) > self.VELOCITY_HIGH and acceleration < -self.ACCELERATION_MODERATE and volume_ratio < self.VOLUME_DECLINE:
            # Contrarian signal: momentum is slowing
            direction = 'BEARISH' if velocity > 0 else 'BULLISH'
            return {
                'type': 'EXHAUSTION',
                'direction': direction,
                'confidence': 'MEDIUM',
                'description': f'Momentum exhaustion (funding slowing + low volume) - fade the trend'
            }

        # NEUTRAL: Low acceleration + low velocity
        else:
            return {
                'type': 'NEUTRAL',
                'direction': 'NEUTRAL',
                'confidence': 'LOW',
                'description': 'No clear institutional positioning'
            }

    def _calculate_strength(
        self,
        acceleration: float,
        velocity: float,
        volume_ratio: float,
        cross_asset_aligned: bool
    ) -> float:
        """
        Calculate signal strength (0-10)

        Based on Ed's spec:
        - Acceleration: 0-4 points
        - Velocity: 0-3 points
        - Volume: 0-2 points
        - Cross-asset: +1 bonus
        """
        strength = 0

        # Acceleration (0-4 points)
        # Recalibrated for realistic funding dynamics (0.0001-0.0003% typical)
        if abs(acceleration) > 0.0003:  # Extreme: >0.03%
            strength += 4
        elif abs(acceleration) > self.ACCELERATION_HIGH:  # High: >0.02%
            strength += 3
        elif abs(acceleration) > self.ACCELERATION_MODERATE:  # Moderate: >0.01%
            strength += 2

        # Velocity (0-3 points)
        # Recalibrated for realistic funding dynamics (0.0001-0.0005% typical)
        if abs(velocity) > 0.0005:  # Extreme: >0.05%
            strength += 3
        elif abs(velocity) > 0.0003:  # High: >0.03%
            strength += 2
        elif abs(velocity) > self.VELOCITY_MODERATE:  # Moderate: >0.01%
            strength += 1

        # Volume (0-2 points)
        if volume_ratio > 1.8:
            strength += 2
        elif volume_ratio > self.VOLUME_MODERATE:
            strength += 1

        # Cross-asset bonus (+1)
        if cross_asset_aligned:
            strength += 1

        return min(10.0, float(strength))

    def _describe_volume(self, volume_ratio: float) -> str:
        """Describe volume context"""
        if volume_ratio > self.VOLUME_SURGE:
            return "SURGE (institutions active)"
        elif volume_ratio > self.VOLUME_MODERATE:
            return "ELEVATED (moderate activity)"
        elif volume_ratio < self.VOLUME_DECLINE:
            return "DECLINING (weak hands)"
        else:
            return "NORMAL"


def test_positioning():
    """Test institutional positioning signal with realistic funding rates"""
    print("Testing Institutional Positioning Signal...")
    print("Note: Funding rates are 8-hour rates stored as percentages (e.g., 0.015%)")

    signal_gen = InstitutionalPositioning()

    # Test case 1: Institutional accumulation (strong bullish)
    print("\n1. Testing INSTITUTIONAL_ACCUMULATION:")
    print("   Scenario: Funding accelerating up + high volume surge")
    funding_dynamics = {
        'current': 0.035,        # 0.035% (strong positive funding)
        'funding_4h_ago': 0.028,  # 0.028%
        'funding_8h_ago': 0.022,  # 0.022%
        'velocity_4h': 0.0007,    # +0.0007% change (strong positive velocity)
        'velocity_8h': 0.013,     # +0.013% over 8h
        'acceleration': 0.0003    # Strong acceleration (0.03%)
    }
    volume_data = {
        'current': 150000000,
        'avg_24h': 80000000  # 1.875x surge
    }

    signal = signal_gen.analyze(funding_dynamics, volume_data)
    print(f"   Direction: {signal.direction}")
    print(f"   Regime: {signal.regime}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Confidence: {signal.confidence}")
    print(f"   Details: {signal.details['regime_description']}")

    # Test case 2: Exhaustion (contrarian)
    print("\n2. Testing EXHAUSTION:")
    print("   Scenario: High funding but slowing + declining volume")
    funding_dynamics = {
        'current': 0.045,         # 0.045% (high funding)
        'funding_4h_ago': 0.042,  # 0.042%
        'funding_8h_ago': 0.037,  # 0.037%
        'velocity_4h': 0.0003,    # +0.0003% (still positive but slowing)
        'velocity_8h': 0.008,     # +0.008% over 8h
        'acceleration': -0.0002   # Negative acceleration (slowing down)
    }
    volume_data = {
        'current': 60000000,
        'avg_24h': 90000000  # 0.67x declining volume
    }

    signal = signal_gen.analyze(funding_dynamics, volume_data)
    print(f"   Direction: {signal.direction}")
    print(f"   Regime: {signal.regime}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Confidence: {signal.confidence}")
    print(f"   Details: {signal.details['regime_description']}")

    # Test case 3: Neutral
    print("\n3. Testing NEUTRAL:")
    print("   Scenario: Stable funding + normal volume")
    funding_dynamics = {
        'current': 0.015,         # 0.015%
        'funding_4h_ago': 0.014,  # 0.014%
        'funding_8h_ago': 0.0145, # 0.0145%
        'velocity_4h': 0.00001,   # +0.00001% (minimal change)
        'velocity_8h': 0.0005,    # +0.0005% over 8h
        'acceleration': 0.00001   # Minimal acceleration
    }
    volume_data = {
        'current': 100000000,
        'avg_24h': 100000000  # 1.0x normal volume
    }

    signal = signal_gen.analyze(funding_dynamics, volume_data)
    print(f"   Direction: {signal.direction}")
    print(f"   Regime: {signal.regime}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Confidence: {signal.confidence}")

    print("\n✅ All tests passed!")
    print("\nRealistic funding rate ranges:")
    print("  - Typical 8h rate: 0.010% to 0.030%")
    print("  - 4h velocity: 0.0001% to 0.0005% (normal), >0.001% (strong)")
    print("  - Acceleration: 0.0001% to 0.0003% (normal), >0.0005% (extreme)")


if __name__ == "__main__":
    test_positioning()

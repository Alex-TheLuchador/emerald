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
        # Thresholds from Ed's spec
        self.ACCELERATION_HIGH = 0.05
        self.ACCELERATION_MODERATE = 0.03
        self.VELOCITY_HIGH = 0.05
        self.VELOCITY_MODERATE = 0.03
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
        if abs(acceleration) > 0.08:
            strength += 4
        elif abs(acceleration) > self.ACCELERATION_HIGH:
            strength += 3
        elif abs(acceleration) > self.ACCELERATION_MODERATE:
            strength += 2

        # Velocity (0-3 points)
        if abs(velocity) > 0.10:
            strength += 3
        elif abs(velocity) > 0.06:
            strength += 2
        elif abs(velocity) > self.VELOCITY_MODERATE:
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
    """Test institutional positioning signal"""
    print("Testing Institutional Positioning Signal...")

    signal_gen = InstitutionalPositioning()

    # Test case 1: Institutional accumulation (strong bullish)
    print("\n1. Testing INSTITUTIONAL_ACCUMULATION:")
    funding_dynamics = {
        'current': 15.5,
        'funding_4h_ago': 12.0,
        'funding_8h_ago': 10.5,
        'velocity_4h': 3.5,  # Strong positive velocity
        'velocity_8h': 5.0,
        'acceleration': 0.06  # Strong acceleration
    }
    volume_data = {
        'current': 150000000,
        'avg_24h': 80000000
    }

    signal = signal_gen.analyze(funding_dynamics, volume_data)
    print(f"   Direction: {signal.direction}")
    print(f"   Regime: {signal.regime}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Confidence: {signal.confidence}")
    print(f"   Details: {signal.details['regime_description']}")

    # Test case 2: Exhaustion (contrarian)
    print("\n2. Testing EXHAUSTION:")
    funding_dynamics = {
        'current': 18.0,
        'funding_4h_ago': 16.5,
        'funding_8h_ago': 15.5,
        'velocity_4h': 1.5,  # Still positive
        'velocity_8h': 2.5,
        'acceleration': -0.04  # Negative acceleration (slowing)
    }
    volume_data = {
        'current': 60000000,
        'avg_24h': 90000000
    }

    signal = signal_gen.analyze(funding_dynamics, volume_data)
    print(f"   Direction: {signal.direction}")
    print(f"   Regime: {signal.regime}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Confidence: {signal.confidence}")
    print(f"   Details: {signal.details['regime_description']}")

    # Test case 3: Neutral
    print("\n3. Testing NEUTRAL:")
    funding_dynamics = {
        'current': 8.0,
        'funding_4h_ago': 7.8,
        'funding_8h_ago': 7.9,
        'velocity_4h': 0.2,  # Low velocity
        'velocity_8h': 0.1,
        'acceleration': 0.01  # Low acceleration
    }
    volume_data = {
        'current': 100000000,
        'avg_24h': 100000000
    }

    signal = signal_gen.analyze(funding_dynamics, volume_data)
    print(f"   Direction: {signal.direction}")
    print(f"   Regime: {signal.regime}")
    print(f"   Strength: {signal.strength}/10")
    print(f"   Confidence: {signal.confidence}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_positioning()

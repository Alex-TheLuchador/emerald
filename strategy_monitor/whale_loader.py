"""
Whale address loader and validator
"""
from typing import List, Set
from pathlib import Path


def load_whale_addresses(file_path: str = "whale_addresses.txt") -> List[str]:
    """
    Load whale addresses from file

    Args:
        file_path: Path to whale addresses file (relative to strategy_monitor/)

    Returns:
        List of validated whale addresses
    """
    # Get absolute path
    base_dir = Path(__file__).parent
    full_path = base_dir / file_path

    if not full_path.exists():
        print(f"⚠️  Whale address file not found: {full_path}")
        return []

    addresses = []

    with open(full_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Validate format
            if not line.startswith('0x') or len(line) != 42:
                print(f"⚠️  Invalid address at line {line_num}: {line}")
                continue

            addresses.append(line.lower())  # Normalize to lowercase

    # Remove duplicates while preserving order
    seen: Set[str] = set()
    unique_addresses = []
    for addr in addresses:
        if addr not in seen:
            seen.add(addr)
            unique_addresses.append(addr)

    print(f"✅ Loaded {len(unique_addresses)} whale addresses")
    return unique_addresses


def test_whale_loader():
    """Test whale address loader"""
    print("Testing Whale Address Loader...")

    addresses = load_whale_addresses()

    if addresses:
        print(f"\nSample addresses:")
        for addr in addresses[:3]:
            print(f"  - {addr}")

        if len(addresses) > 3:
            print(f"  ... and {len(addresses) - 3} more")
    else:
        print("\n⚠️  No addresses loaded")


if __name__ == "__main__":
    test_whale_loader()

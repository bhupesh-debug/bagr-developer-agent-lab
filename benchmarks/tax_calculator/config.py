"""Tax calculation configuration."""
from typing import Dict

REGIONAL_RATES: Dict[str, float] = {
    "TIER_A": 0.05,
    "TIER_B": 0.08,
    "TIER_C": 0.12,
}

LUXURY_THRESHOLD = 1000.0
LUXURY_SURCHARGE = 0.03

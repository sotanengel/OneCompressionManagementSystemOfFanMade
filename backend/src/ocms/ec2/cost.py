from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

ON_DEMAND_RATES: dict[str, Decimal] = {
    "g5.xlarge": Decimal("1.006"),
    "g5.2xlarge": Decimal("1.212"),
    "g5.4xlarge": Decimal("1.624"),
    "g5.8xlarge": Decimal("2.448"),
    "g6e.xlarge": Decimal("0.8406"),
    "g6e.2xlarge": Decimal("1.681"),
    "g6.xlarge": Decimal("0.80536"),
}

SPOT_DISCOUNT = 0.7
DEFAULT_RATE = Decimal("1.006")


@dataclass
class CostEstimate:
    instance_type: str
    max_runtime_hours: int
    spot: bool
    on_demand_rate_usd_hr: Decimal
    estimated_cost_usd: Decimal
    spot_discount_pct: float | None


def estimate_cost(
    instance_type: str,
    max_runtime_hours: int,
    spot: bool,
) -> CostEstimate:
    rate = ON_DEMAND_RATES.get(instance_type, DEFAULT_RATE)
    if spot:
        effective_rate = rate * Decimal(str(SPOT_DISCOUNT))
        discount = SPOT_DISCOUNT
    else:
        effective_rate = rate
        discount = None
    total = effective_rate * max_runtime_hours
    return CostEstimate(
        instance_type=instance_type,
        max_runtime_hours=max_runtime_hours,
        spot=spot,
        on_demand_rate_usd_hr=rate,
        estimated_cost_usd=total.quantize(Decimal("0.0001")),
        spot_discount_pct=discount,
    )

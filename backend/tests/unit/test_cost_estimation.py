from decimal import Decimal

from ocms.ec2.cost import estimate_cost


def test_g5_xlarge_on_demand_2h() -> None:
    result = estimate_cost(instance_type="g5.xlarge", max_runtime_hours=2, spot=False)
    assert result.on_demand_rate_usd_hr == Decimal("1.006")
    assert result.estimated_cost_usd == Decimal("2.012")
    assert result.spot is False
    assert result.spot_discount_pct is None


def test_g5_xlarge_spot_2h() -> None:
    result = estimate_cost(instance_type="g5.xlarge", max_runtime_hours=2, spot=True)
    assert result.spot is True
    assert result.spot_discount_pct == 0.7
    assert result.estimated_cost_usd < Decimal("2.012")


def test_g6e_xlarge_on_demand() -> None:
    result = estimate_cost(instance_type="g6e.xlarge", max_runtime_hours=1, spot=False)
    assert result.estimated_cost_usd > Decimal("0")


def test_unknown_instance_falls_back() -> None:
    result = estimate_cost(instance_type="unknown.xlarge", max_runtime_hours=1, spot=False)
    assert result.estimated_cost_usd > Decimal("0")

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ocms.api.auth import verify_cognito_jwt
from ocms.api.deps import get_db
from ocms.api.schemas import CostSummaryResponse
from ocms.core.models import Job
from ocms.storage.repository import JobRepository

router = APIRouter(
    prefix="/cost",
    tags=["cost"],
    dependencies=[Depends(verify_cognito_jwt)],
)

BUDGET_WARNING_USD = Decimal("50")
BUDGET_HARD_LIMIT_USD = Decimal("100")

_PERIOD_DAYS: dict[str, int | None] = {
    "week": 7,
    "month": 30,
    "all": None,
}


def _effective_cost(job: Job) -> Decimal:
    return job.actual_cost_usd or job.estimated_cost_usd or Decimal("0")


def _filter_by_period(jobs: list[Job], period: str) -> list[Job]:
    days = _PERIOD_DAYS.get(period)
    if days is None:
        return jobs
    cutoff = datetime.now(UTC) - timedelta(days=days)
    return [j for j in jobs if j.created_at >= cutoff]


def compute_summary(
    jobs: list[Job],
    *,
    period: str = "week",
    group_by: str | None = None,
) -> CostSummaryResponse:
    filtered = _filter_by_period(jobs, period)
    total = sum((_effective_cost(j) for j in filtered), Decimal("0"))

    by_model: dict[str, Decimal] = {}
    if group_by == "model":
        for job in filtered:
            by_model[job.model_id] = by_model.get(job.model_id, Decimal("0")) + _effective_cost(job)

    return CostSummaryResponse(
        total_usd=total,
        by_model={k: v for k, v in by_model.items()},
        budget_warning=total >= BUDGET_WARNING_USD,
    )


def total_cost_all_jobs(jobs: list[Job]) -> Decimal:
    return sum((_effective_cost(j) for j in jobs), Decimal("0"))


@router.get("/summary", response_model=CostSummaryResponse)
def get_cost_summary(
    period: str = "week",
    group_by: str | None = None,
    db: Session = Depends(get_db),
) -> CostSummaryResponse:
    repo = JobRepository(db)
    jobs = repo.list_all()
    return compute_summary(jobs, period=period, group_by=group_by)

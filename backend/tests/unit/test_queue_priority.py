from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from ocms.core.models import FeatureFlags, Job, JobStatus
from ocms.storage.repository import JobRepository


def _pending_job(
    priority: int = 0,
    created_offset_seconds: int = 0,
) -> Job:
    return Job(
        job_id=uuid.uuid4(),
        model_id="meta-llama/Llama-3.1-8B",
        quant_method="GPTQ",
        bits=4,
        instance_type="g5.xlarge",
        region="us-east-1",
        spot=False,
        max_runtime_hours=2,
        status=JobStatus.PENDING,
        feature_flags=FeatureFlags(),
        created_at=datetime.now(UTC) - timedelta(seconds=created_offset_seconds),
        priority=priority,
    )


class TestListPendingByPriority:
    def test_higher_priority_comes_first(self) -> None:
        low = _pending_job(priority=0)
        high = _pending_job(priority=10)

        session = MagicMock()
        repo = JobRepository(session)

        result = repo._sort_pending_by_priority([low, high])
        assert result[0].priority == 10
        assert result[1].priority == 0

    def test_same_priority_older_job_comes_first(self) -> None:
        newer = _pending_job(priority=5, created_offset_seconds=0)
        older = _pending_job(priority=5, created_offset_seconds=60)

        session = MagicMock()
        repo = JobRepository(session)

        result = repo._sort_pending_by_priority([newer, older])
        assert result[0].created_at < result[1].created_at

    def test_mixed_priority_and_age(self) -> None:
        a = _pending_job(priority=0, created_offset_seconds=0)
        b = _pending_job(priority=5, created_offset_seconds=0)
        c = _pending_job(priority=5, created_offset_seconds=30)
        d = _pending_job(priority=10, created_offset_seconds=0)

        session = MagicMock()
        repo = JobRepository(session)

        result = repo._sort_pending_by_priority([a, b, c, d])
        assert result[0].priority == 10
        assert result[1].priority == 5
        assert result[1].created_at < result[2].created_at
        assert result[3].priority == 0

    def test_empty_list_returns_empty(self) -> None:
        session = MagicMock()
        repo = JobRepository(session)
        assert repo._sort_pending_by_priority([]) == []

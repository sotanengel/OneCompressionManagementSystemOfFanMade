from __future__ import annotations

import json
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ocms.api.routers.log_stream import _format_sse_event, router
from ocms.core.models import JobLog


def _make_log(message: str, level: str = "INFO", source: str = "userdata") -> JobLog:
    return JobLog(
        log_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        level=level,
        source=source,
        message=message,
    )


class TestFormatSseEvent:
    def test_returns_sse_format(self) -> None:
        log = _make_log("hello")
        event = _format_sse_event(log)
        assert event.startswith("id: ")
        assert "data: " in event
        assert event.endswith("\n\n")

    def test_data_is_valid_json(self) -> None:
        log = _make_log("test message")
        event = _format_sse_event(log)
        data_line = next(line for line in event.split("\n") if line.startswith("data: "))
        payload = json.loads(data_line[len("data: ") :])
        assert payload["message"] == "test message"
        assert payload["level"] == "INFO"
        assert payload["source"] == "userdata"
        assert "timestamp" in payload
        assert "log_id" in payload

    def test_id_field_is_timestamp_iso(self) -> None:
        log = _make_log("x")
        event = _format_sse_event(log)
        id_line = next(line for line in event.split("\n") if line.startswith("id: "))
        ts_str = id_line[len("id: ") :]
        datetime.fromisoformat(ts_str)

    def test_error_level_preserved(self) -> None:
        log = _make_log("fail", level="ERROR")
        event = _format_sse_event(log)
        data_line = next(line for line in event.split("\n") if line.startswith("data: "))
        payload = json.loads(data_line[len("data: ") :])
        assert payload["level"] == "ERROR"


class TestLogStreamEndpoint:
    @pytest.fixture
    def mock_repo(self) -> Generator[MagicMock, None, None]:
        with patch("ocms.api.routers.log_stream.JobRepository") as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance
            yield instance

    @pytest.fixture
    def client(self) -> Generator[TestClient, None, None]:
        from unittest.mock import MagicMock

        from fastapi import FastAPI

        from ocms.api.deps import get_db

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: MagicMock()
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    def test_returns_404_for_unknown_job(self, client: TestClient, mock_repo: MagicMock) -> None:
        mock_repo.get.return_value = None
        resp = client.get(f"/jobs/{uuid.uuid4()}/log-stream")
        assert resp.status_code == 404

    def test_content_type_is_event_stream(self, client: TestClient, mock_repo: MagicMock) -> None:
        from decimal import Decimal

        from ocms.core.models import FeatureFlags, Job, JobStatus

        job = Job(
            job_id=uuid.uuid4(),
            user_id=None,
            model_id="Qwen/Qwen3-1.7B",
            quant_method="GPTQ",
            bits=4,
            instance_type="g5.xlarge",
            region="us-east-1",
            spot=False,
            max_runtime_hours=4,
            feature_flags=FeatureFlags(),
            status=JobStatus.COMPLETED,
            ec2_instance_id=None,
            s3_output_prefix=None,
            estimated_cost_usd=Decimal("1.00"),
            actual_cost_usd=None,
            created_at=datetime.now(UTC),
            started_at=None,
            completed_at=None,
            failure_reason=None,
            rerun_script_path=None,
            git_commit_onecompression=None,
            git_commit_sotanengel=None,
        )
        mock_repo.get.return_value = job
        mock_repo.get_logs_since.return_value = []

        resp = client.get(f"/jobs/{job.job_id}/log-stream")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import boto3
from moto import mock_aws

from ocms.cloudwatch.gpu_metrics import GpuMetricsPoller


def test_poll_inserts_log_when_metrics_available() -> None:
    job_id = uuid.uuid4()
    mock_repo = MagicMock()
    poller = GpuMetricsPoller(region="us-east-1")

    with patch.object(poller, "_get_latest_metric") as mock_get:
        mock_get.side_effect = [85.5, 42.0]
        poller.poll(job_id=job_id, instance_id="i-abc", repo=mock_repo)

    mock_repo.append_log.assert_called_once()
    call_kwargs = mock_repo.append_log.call_args.kwargs
    assert call_kwargs["job_id"] == job_id
    assert call_kwargs["level"] == "INFO"
    assert call_kwargs["source"] == "cloudwatch"
    assert "gpu" in call_kwargs["message"].lower()
    assert "85.5" in call_kwargs["message"]


def test_poll_with_no_metrics_does_not_insert() -> None:
    job_id = uuid.uuid4()
    mock_repo = MagicMock()
    poller = GpuMetricsPoller(region="us-east-1")

    with patch.object(poller, "_get_latest_metric") as mock_get:
        mock_get.return_value = None
        poller.poll(job_id=job_id, instance_id="i-none", repo=mock_repo)

    mock_repo.append_log.assert_not_called()


def test_poll_includes_mem_utilization_when_available() -> None:
    job_id = uuid.uuid4()
    mock_repo = MagicMock()
    poller = GpuMetricsPoller(region="us-east-1")

    with patch.object(poller, "_get_latest_metric") as mock_get:
        mock_get.side_effect = [70.0, 55.0]
        poller.poll(job_id=job_id, instance_id="i-abc", repo=mock_repo)

    message = mock_repo.append_log.call_args.kwargs["message"]
    assert "70.0" in message
    assert "55.0" in message


def test_poll_uses_cwagent_namespace() -> None:
    job_id = uuid.uuid4()
    mock_repo = MagicMock()
    poller = GpuMetricsPoller(region="us-east-1")

    with patch.object(poller, "_get_latest_metric") as mock_get:
        mock_get.return_value = None
        poller.poll(job_id=job_id, instance_id="i-test", repo=mock_repo)
        for c in mock_get.call_args_list:
            namespace = c.kwargs.get("namespace")
            assert namespace == "CWAgent"


@mock_aws
def test_get_latest_metric_returns_none_when_no_data() -> None:
    poller = GpuMetricsPoller(region="us-east-1")
    client = boto3.client("cloudwatch", region_name="us-east-1")
    result = poller._get_latest_metric(
        client,
        namespace="CWAgent",
        metric_name="nvidia_smi_utilization_gpu",
        instance_id="i-notexist",
    )
    assert result is None

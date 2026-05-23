from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3


class GpuMetricsPoller:
    """Polls CloudWatch for GPU metrics and appends to job_logs."""

    _GPU_METRICS = [
        "nvidia_smi_utilization_gpu",
        "nvidia_smi_utilization_memory",
    ]

    def __init__(self, region: str = "us-east-1") -> None:
        self._region = region

    def poll(self, *, job_id: uuid.UUID, instance_id: str, repo: Any) -> None:
        client = boto3.client("cloudwatch", region_name=self._region)
        readings: dict[str, float] = {}
        for metric_name in self._GPU_METRICS:
            value = self._get_latest_metric(
                client,
                namespace="CWAgent",
                metric_name=metric_name,
                instance_id=instance_id,
            )
            if value is not None:
                readings[metric_name] = value

        if not readings:
            return

        gpu_util = readings.get("nvidia_smi_utilization_gpu")
        mem_util = readings.get("nvidia_smi_utilization_memory")
        parts = []
        if gpu_util is not None:
            parts.append(f"gpu_util={gpu_util:.1f}%")
        if mem_util is not None:
            parts.append(f"mem_util={mem_util:.1f}%")

        repo.append_log(
            job_id=job_id,
            level="INFO",
            source="cloudwatch",
            message="GPU metrics: " + ", ".join(parts),
        )

    def _get_latest_metric(
        self,
        client: Any,
        *,
        namespace: str,
        metric_name: str,
        instance_id: str,
    ) -> float | None:
        end = datetime.now(UTC)
        start = end - timedelta(minutes=5)
        resp = client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start,
            EndTime=end,
            Period=300,
            Statistics=["Average"],
        )
        datapoints = resp.get("Datapoints", [])
        if not datapoints:
            return None
        latest = max(datapoints, key=lambda d: d["Timestamp"])
        return float(latest["Average"])

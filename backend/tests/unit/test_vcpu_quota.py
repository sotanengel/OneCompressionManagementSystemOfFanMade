from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from ocms.ec2.launcher import VcpuQuotaExceededError, check_vcpu_quota


class TestVcpuQuotaCheck:
    def test_raises_when_used_vcpus_would_exceed_limit(self) -> None:
        with patch("ocms.ec2.launcher.boto3") as mock_boto3:
            ec2 = MagicMock()
            mock_boto3.client.return_value = ec2
            ec2.describe_instance_types.return_value = {
                "InstanceTypes": [{"VCpuInfo": {"DefaultVCpus": 8}}]
            }
            ec2.describe_instances.return_value = {
                "Reservations": [
                    {
                        "Instances": [
                            {"CpuOptions": {"CoreCount": 4, "ThreadsPerCore": 2}},  # 8 vCPUs
                            {"CpuOptions": {"CoreCount": 4, "ThreadsPerCore": 2}},  # 8 vCPUs
                            {"CpuOptions": {"CoreCount": 4, "ThreadsPerCore": 2}},  # 8 vCPUs
                        ]
                    }
                ]
            }
            # Used: 24, Requested: 8, Limit: 32 (default) — 24+8=32, should pass
            # Let's set limit low to trigger the error
            with (
                patch.dict(os.environ, {"OCMS_VCPU_LIMIT": "28"}),
                pytest.raises(VcpuQuotaExceededError),
            ):
                check_vcpu_quota(instance_type="g5.2xlarge", region="us-east-1")

    def test_passes_when_within_quota(self) -> None:
        with patch("ocms.ec2.launcher.boto3") as mock_boto3:
            ec2 = MagicMock()
            mock_boto3.client.return_value = ec2
            ec2.describe_instance_types.return_value = {
                "InstanceTypes": [{"VCpuInfo": {"DefaultVCpus": 4}}]
            }
            ec2.describe_instances.return_value = {
                "Reservations": [
                    {"Instances": [{"CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 2}}]}
                ]
            }
            with patch.dict(os.environ, {"OCMS_VCPU_LIMIT": "32"}):
                check_vcpu_quota(instance_type="g5.xlarge", region="us-east-1")  # should not raise

    def test_passes_when_no_running_instances(self) -> None:
        with patch("ocms.ec2.launcher.boto3") as mock_boto3:
            ec2 = MagicMock()
            mock_boto3.client.return_value = ec2
            ec2.describe_instance_types.return_value = {
                "InstanceTypes": [{"VCpuInfo": {"DefaultVCpus": 4}}]
            }
            ec2.describe_instances.return_value = {"Reservations": []}
            check_vcpu_quota(instance_type="g5.xlarge", region="us-east-1")

    def test_raises_on_unknown_instance_type(self) -> None:
        with patch("ocms.ec2.launcher.boto3") as mock_boto3:
            ec2 = MagicMock()
            mock_boto3.client.return_value = ec2
            ec2.describe_instance_types.return_value = {"InstanceTypes": []}
            with pytest.raises(ValueError, match="Unknown instance type"):
                check_vcpu_quota(instance_type="unknown.xlarge", region="us-east-1")

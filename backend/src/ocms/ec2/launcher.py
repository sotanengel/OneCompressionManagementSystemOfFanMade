from __future__ import annotations

import os
from typing import TYPE_CHECKING, cast

import boto3

if TYPE_CHECKING:
    from mypy_boto3_ec2.literals import InstanceTypeType

_DEFAULT_VCPU_LIMIT = 32


class VcpuQuotaExceededError(Exception):
    pass


def check_vcpu_quota(instance_type: str, region: str) -> None:
    ec2 = boto3.client("ec2", region_name=region)

    # AWS publishes new instance types regularly; the literal in botocore-stubs
    # lags behind. Accept any string the caller passes through.
    it_response = ec2.describe_instance_types(
        InstanceTypes=[cast("InstanceTypeType", instance_type)]
    )
    if not it_response["InstanceTypes"]:
        raise ValueError(f"Unknown instance type: {instance_type}")
    requested_vcpus = it_response["InstanceTypes"][0]["VCpuInfo"]["DefaultVCpus"]

    running = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running", "pending"]}]
    )
    used_vcpus = sum(
        inst.get("CpuOptions", {}).get("CoreCount", 0)
        * inst.get("CpuOptions", {}).get("ThreadsPerCore", 1)
        for reservation in running["Reservations"]
        for inst in reservation["Instances"]
    )

    limit = int(os.environ.get("OCMS_VCPU_LIMIT", _DEFAULT_VCPU_LIMIT))
    if used_vcpus + requested_vcpus > limit:
        raise VcpuQuotaExceededError(
            f"vCPU quota exceeded: need {requested_vcpus}, using {used_vcpus}/{limit}"
        )

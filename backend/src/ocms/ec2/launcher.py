from __future__ import annotations

import os

import boto3

_DEFAULT_VCPU_LIMIT = 32


class VcpuQuotaExceededError(Exception):
    pass


def check_vcpu_quota(instance_type: str, region: str) -> None:
    ec2 = boto3.client("ec2", region_name=region)

    it_response = ec2.describe_instance_types(InstanceTypes=[instance_type])  # type: ignore[list-item]
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

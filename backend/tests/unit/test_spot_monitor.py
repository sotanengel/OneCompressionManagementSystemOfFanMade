from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from ocms.core.models import FeatureFlags, Job, JobStatus
from ocms.ec2.script_generator import generate_userdata


def _make_job(checkpoint: bool = True) -> Job:
    return Job(
        job_id=uuid.uuid4(),
        user_id=None,
        model_id="Qwen/Qwen3-1.7B",
        quant_method="GPTQ",
        bits=4,
        instance_type="g5.xlarge",
        region="us-east-1",
        spot=True,
        max_runtime_hours=4,
        feature_flags=FeatureFlags(checkpoint=checkpoint),
        status=JobStatus.PENDING,
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


class TestSpotMonitorInUserdata:
    def test_imdsv2_token_present_when_checkpoint_enabled(self) -> None:
        job = _make_job(checkpoint=True)
        userdata = generate_userdata(job)
        assert "169.254.169.254" in userdata

    def test_spot_action_endpoint_present_when_checkpoint_enabled(self) -> None:
        job = _make_job(checkpoint=True)
        userdata = generate_userdata(job)
        assert "spot/instance-action" in userdata

    def test_imdsv2_not_present_when_checkpoint_disabled(self) -> None:
        job = _make_job(checkpoint=False)
        userdata = generate_userdata(job)
        assert "spot/instance-action" not in userdata

    def test_sigterm_trap_present_when_checkpoint_enabled(self) -> None:
        job = _make_job(checkpoint=True)
        userdata = generate_userdata(job)
        assert "trap" in userdata
        assert "SIGTERM" in userdata

    def test_pgrep_guarded_with_set_e(self) -> None:
        job = _make_job(checkpoint=True)
        userdata = generate_userdata(job)
        # Rule #6: set +e before pgrep, set -e after
        assert "set +e" in userdata
        assert "set -e" in userdata

    def test_checkpoint_s3_upload_path_in_userdata(self) -> None:
        job = _make_job(checkpoint=True)
        userdata = generate_userdata(job)
        job_id = str(job.job_id)
        assert job_id in userdata
        assert "checkpoint" in userdata.lower()

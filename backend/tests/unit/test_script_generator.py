import os
import uuid
from datetime import UTC, datetime

from ocms.core.models import FeatureFlags, Job, JobStatus
from ocms.ec2.script_generator import generate_rerun_script, generate_userdata


def _make_job(**overrides) -> Job:  # type: ignore[no-untyped-def]
    defaults = dict(
        job_id=uuid.uuid4(),
        model_id="meta-llama/Llama-3.1-8B",
        quant_method="GPTQ",
        bits=4,
        instance_type="g5.xlarge",
        region="us-east-1",
        spot=False,
        max_runtime_hours=4,
        status=JobStatus.PENDING,
        feature_flags=FeatureFlags(),
        created_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return Job(**defaults)


# Rule #7: POLL_EXIT_WHEN_TRAINING_EC2_NOT_RUNNING must be set
def test_userdata_contains_poll_exit_flag() -> None:
    script = generate_userdata(_make_job())
    assert "POLL_EXIT_WHEN_TRAINING_EC2_NOT_RUNNING=1" in script


# Rule #6: pgrep must be wrapped with set +e / set -e
def test_userdata_wraps_pgrep_with_set_guards() -> None:
    script = generate_userdata(_make_job())
    if "pgrep" in script:
        assert "set +e" in script and "set -e" in script


# Rule #10: STATE_DIR must be absolute path
def test_userdata_state_dir_is_absolute() -> None:
    script = generate_userdata(_make_job())
    lines = script.splitlines()
    state_dir_lines = [ln for ln in lines if "STATE_DIR=" in ln and not ln.strip().startswith("#")]
    assert len(state_dir_lines) > 0, "STATE_DIR must be defined in userdata"
    for line in state_dir_lines:
        value = line.split("STATE_DIR=", 1)[1].strip().strip('"').strip("'")  # noqa: E501
        assert os.path.isabs(value), f"STATE_DIR must be absolute: {value}"


def test_userdata_contains_model_id() -> None:
    job = _make_job(model_id="Qwen/Qwen3-8B")
    script = generate_userdata(job)
    assert "Qwen/Qwen3-8B" in script


def test_userdata_check_env_preflight_flag_when_enabled() -> None:
    job = _make_job(feature_flags=FeatureFlags(check_env_preflight=True))
    script = generate_userdata(job)
    assert "--check-env" in script


def test_userdata_no_check_env_flag_when_disabled() -> None:
    job = _make_job(feature_flags=FeatureFlags(check_env_preflight=False))
    script = generate_userdata(job)
    assert "--check-env" not in script


def test_userdata_checkpoint_flag_when_enabled() -> None:
    job = _make_job(feature_flags=FeatureFlags(checkpoint=True))
    script = generate_userdata(job)
    assert "checkpoint" in script.lower() or "SIGTERM" in script


def test_rerun_script_is_standalone(tmp_path) -> None:  # type: ignore[no-untyped-def]
    job = _make_job()
    generate_rerun_script(job, output_dir=str(tmp_path))
    script_path = tmp_path / f"job-{job.job_id}-launch.sh"
    assert script_path.exists()
    content = script_path.read_text()
    assert "#!/usr/bin/env bash" in content
    assert str(job.job_id) in content


def test_rerun_script_is_executable(tmp_path) -> None:  # type: ignore[no-untyped-def]
    job = _make_job()
    generate_rerun_script(job, output_dir=str(tmp_path))
    script_path = tmp_path / f"job-{job.job_id}-launch.sh"
    assert os.access(script_path, os.X_OK)

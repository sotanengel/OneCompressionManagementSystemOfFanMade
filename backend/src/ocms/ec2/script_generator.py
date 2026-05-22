from __future__ import annotations

import stat
from pathlib import Path

from ocms.core.models import Job

_USERDATA_TEMPLATE = """\
#!/usr/bin/env bash
# OneCompression quantization job — job_id: {job_id}
# AUTO-GENERATED — do not edit manually
set -euo pipefail

# Rule #7: auto-terminate EC2 when training process exits
export POLL_EXIT_WHEN_TRAINING_EC2_NOT_RUNNING=1

# Rule #10: STATE_DIR must be an absolute path
export STATE_DIR=/opt/ocms/state/{job_id}
mkdir -p "$STATE_DIR"

MODEL_ID="{model_id}"
QUANT_METHOD="{quant_method}"
BITS={bits}
INSTANCE_TYPE="{instance_type}"
JOB_ID="{job_id}"

# Rule #6: wrap pgrep with set +e / set -e
check_already_running() {{
    set +e
    pgrep -f "onecomp" > /dev/null 2>&1
    local rc=$?
    set -e
    return $rc
}}

if check_already_running; then
    echo "WARNING: onecomp process already running, skipping"
    exit 0
fi

{checkpoint_trap}

# Run OneCompression quantization
onecomp \\
    --model "$MODEL_ID" \\
    --wbits "$BITS" \\
    --method "$QUANT_METHOD" \\
    --save-dir "$STATE_DIR/output" \\
    {check_env_flag}

echo "Quantization complete"

# Upload to S3 with Transfer Acceleration (Rule #4)
aws s3 sync "$STATE_DIR/output/" "s3://ocms-artifacts/{job_id}/output/" \\
    --endpoint-url https://s3-accelerate.amazonaws.com

echo "Upload complete"

# Signal completion
POLL_EXIT_WHEN_TRAINING_EC2_NOT_RUNNING=1 \\
    shutdown -h now
"""

_CHECKPOINT_TRAP = """\
# Rule: checkpoint on SIGTERM (Spot interruption)
checkpoint_on_sigterm() {
    echo "SIGTERM received — uploading checkpoint"
    aws s3 sync "$STATE_DIR/" "s3://ocms-artifacts/$JOB_ID/checkpoint/" \\
        --endpoint-url https://s3-accelerate.amazonaws.com || true
    exit 0
}
trap checkpoint_on_sigterm SIGTERM SIGINT
"""


def generate_userdata(job: Job) -> str:
    check_env_flag = "--check-env \\" if job.feature_flags.check_env_preflight else ""
    checkpoint_trap = _CHECKPOINT_TRAP if job.feature_flags.checkpoint else ""
    return _USERDATA_TEMPLATE.format(
        job_id=str(job.job_id),
        model_id=job.model_id,
        quant_method=job.quant_method,
        bits=job.bits,
        instance_type=job.instance_type,
        check_env_flag=check_env_flag,
        checkpoint_trap=checkpoint_trap,
    )


_RERUN_TEMPLATE = """\
#!/usr/bin/env bash
# OneCompression re-run script — job_id: {job_id}
# Generated from job parameters — standalone, no DB dependency
set -euo pipefail

export POLL_EXIT_WHEN_TRAINING_EC2_NOT_RUNNING=1
export STATE_DIR=/opt/ocms/state/{job_id}

MODEL_ID="{model_id}"
QUANT_METHOD="{quant_method}"
BITS={bits}
INSTANCE_TYPE="{instance_type}"
REGION="{region}"
SPOT={spot}
MAX_RUNTIME_HOURS={max_runtime_hours}
JOB_ID="{job_id}"
FEATURE_CHECK_ENV_PREFLIGHT={check_env_preflight}
FEATURE_CHECKPOINT={checkpoint}

echo "Re-running job $JOB_ID"
echo "Model: $MODEL_ID | Method: $QUANT_METHOD | Bits: $BITS"
echo "Instance: $INSTANCE_TYPE | Spot: $SPOT | Region: $REGION"
"""


def generate_rerun_script(job: Job, output_dir: str = "scripts/jobs") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    script_path = Path(output_dir) / f"job-{job.job_id}-launch.sh"
    content = _RERUN_TEMPLATE.format(
        job_id=str(job.job_id),
        model_id=job.model_id,
        quant_method=job.quant_method,
        bits=job.bits,
        instance_type=job.instance_type,
        region=job.region,
        spot=str(job.spot).lower(),
        max_runtime_hours=job.max_runtime_hours,
        check_env_preflight=str(job.feature_flags.check_env_preflight).lower(),
        checkpoint=str(job.feature_flags.checkpoint).lower(),
    )
    script_path.write_text(content)
    script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return str(script_path)

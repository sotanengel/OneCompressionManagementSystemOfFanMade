from __future__ import annotations

import subprocess
import sys


class PreflightError(Exception):
    pass


def pip_dry_run_validate(packages: list[str]) -> None:
    """Validate packages can be installed before launching EC2 (Rule #3).

    Raises PreflightError if any package cannot be resolved.
    Never passes --profile (Rule #5).
    """
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--dry-run",
        "--quiet",
        *packages,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")
        raise PreflightError(f"pip dry-run failed for packages {packages}: {stderr}")

from unittest.mock import MagicMock, patch

import pytest

from ocms.ec2.preflight import PreflightError, pip_dry_run_validate


def _make_run(returncode: int):  # type: ignore[no-untyped-def]
    mock = MagicMock()
    mock.returncode = returncode
    mock.stderr = b"" if returncode == 0 else b"ERROR: No matching distribution"
    return mock


def test_dry_run_passes_on_exit_0() -> None:
    with patch("ocms.ec2.preflight.subprocess.run", return_value=_make_run(0)):
        pip_dry_run_validate(["torch", "transformers"])


def test_dry_run_raises_on_exit_nonzero() -> None:
    with (
        patch("ocms.ec2.preflight.subprocess.run", return_value=_make_run(1)),
        pytest.raises(PreflightError, match="pip dry-run failed"),
    ):
        pip_dry_run_validate(["nonexistent-package-xyz"])


def test_dry_run_never_uses_profile_flag() -> None:
    captured_args: list = []

    def capture(*args, **kwargs):  # type: ignore[no-untyped-def]
        captured_args.extend(args[0])
        return _make_run(0)

    with patch("ocms.ec2.preflight.subprocess.run", side_effect=capture):
        pip_dry_run_validate(["torch"])

    assert "--profile" not in captured_args, "Rule #5: --profile must not be used in subprocess"

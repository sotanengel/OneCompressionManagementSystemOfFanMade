import json
import uuid
from unittest.mock import MagicMock, patch

from ocms.sqs.sync_daemon import SyncDaemon


def _make_sqs_message(job_id: str) -> dict:
    return {
        "Messages": [
            {
                "MessageId": "msg-123",
                "ReceiptHandle": "handle-abc",
                "Body": json.dumps({"job_id": job_id, "s3_prefix": f"s3://bucket/{job_id}/"}),
            }
        ]
    }


def test_poll_once_calls_s3_sync() -> None:
    job_id = str(uuid.uuid4())
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = _make_sqs_message(job_id)
    mock_sqs.delete_message.return_value = {}

    captured_cmd: list = []

    def mock_run(cmd, **kwargs) -> MagicMock:  # type: ignore[no-untyped-def]
        captured_cmd.extend(cmd)
        result = MagicMock()
        result.returncode = 0
        return result

    daemon = SyncDaemon(
        queue_url="https://sqs.us-east-1.amazonaws.com/123/ocms", local_base="/tmp/ocms"
    )

    with (
        patch("ocms.sqs.sync_daemon.boto3.client", return_value=mock_sqs),
        patch("ocms.sqs.sync_daemon.subprocess.run", side_effect=mock_run),
    ):
        daemon.poll_once()

    assert "s3" in captured_cmd or "aws" in captured_cmd or any("sync" in c for c in captured_cmd)


def test_poll_once_no_profile_in_subprocess() -> None:
    job_id = str(uuid.uuid4())
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = _make_sqs_message(job_id)
    mock_sqs.delete_message.return_value = {}

    captured_cmd: list = []

    def mock_run(cmd, **kwargs) -> MagicMock:  # type: ignore[no-untyped-def]
        captured_cmd.extend(cmd)
        result = MagicMock()
        result.returncode = 0
        return result

    daemon = SyncDaemon(
        queue_url="https://sqs.us-east-1.amazonaws.com/123/ocms", local_base="/tmp/ocms"
    )

    with (
        patch("ocms.sqs.sync_daemon.boto3.client", return_value=mock_sqs),
        patch("ocms.sqs.sync_daemon.subprocess.run", side_effect=mock_run),
    ):
        daemon.poll_once()

    assert "--profile" not in captured_cmd, "Rule #5: --profile must not appear in subprocess"


def test_poll_once_noop_when_no_messages() -> None:
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {"Messages": []}

    daemon = SyncDaemon(
        queue_url="https://sqs.us-east-1.amazonaws.com/123/ocms", local_base="/tmp/ocms"
    )

    with (
        patch("ocms.sqs.sync_daemon.boto3.client", return_value=mock_sqs),
        patch("ocms.sqs.sync_daemon.subprocess.run") as mock_run,
    ):
        daemon.poll_once()

    mock_run.assert_not_called()

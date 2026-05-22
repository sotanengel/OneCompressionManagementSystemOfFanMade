from __future__ import annotations

import json
import subprocess
from typing import Any

import boto3


class SyncDaemon:
    """SQS-triggered local sync daemon.

    Polls SQS for completed job notifications and runs `aws s3 sync`
    to download artifacts locally.

    Never passes --profile in subprocess calls (Rule #5).
    """

    def __init__(self, queue_url: str, local_base: str) -> None:
        self._queue_url = queue_url
        self._local_base = local_base

    def poll_once(self) -> None:
        sqs = boto3.client("sqs")
        response = sqs.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5,
        )
        messages = response.get("Messages", [])
        for msg in messages:
            self._handle(sqs, msg)

    def _handle(self, sqs: Any, msg: Any) -> None:
        body = json.loads(msg["Body"])
        job_id = body["job_id"]
        s3_prefix = body["s3_prefix"]
        local_dir = f"{self._local_base}/{job_id}"

        # Rule #5: no --profile in subprocess
        cmd = ["aws", "s3", "sync", s3_prefix, local_dir]
        subprocess.run(cmd, check=True)

        sqs.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=msg["ReceiptHandle"],
        )

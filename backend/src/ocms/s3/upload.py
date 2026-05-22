from __future__ import annotations

import boto3

_TRANSFER_ACCELERATION_ENDPOINT = "https://s3-accelerate.amazonaws.com"


def upload_model_output(
    local_path: str,
    bucket: str,
    key: str,
    region: str,
) -> None:
    """Upload model output to S3 using Transfer Acceleration (Rule #4).

    Never passes --profile or profile_name (Rule #5).
    Uses in-region EC2 + Transfer Acceleration to avoid Japan→us-east-1 bottleneck.
    """
    client = boto3.client(
        "s3",
        region_name=region,
        endpoint_url=_TRANSFER_ACCELERATION_ENDPOINT,
    )
    client.upload_file(
        Filename=local_path,
        Bucket=bucket,
        Key=key,
    )

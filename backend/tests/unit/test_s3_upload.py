from unittest.mock import MagicMock, patch

from ocms.s3.upload import upload_model_output


def test_upload_uses_transfer_acceleration_endpoint() -> None:
    captured_kwargs: dict = {}

    def mock_upload(Filename, Bucket, Key, ExtraArgs=None, **kwargs) -> None:  # type: ignore[no-untyped-def]
        captured_kwargs.update(kwargs)

    mock_client = MagicMock()
    mock_client.upload_file.side_effect = mock_upload

    captured_client_kwargs: dict = {}

    def mock_boto3_client(service, **kwargs) -> MagicMock:  # type: ignore[no-untyped-def]
        captured_client_kwargs.update(kwargs)
        return mock_client

    with patch("ocms.s3.upload.boto3.client", side_effect=mock_boto3_client):
        upload_model_output(
            local_path="/tmp/model.bin",
            bucket="ocms-artifacts",
            key="job-123/output/model.bin",
            region="us-east-1",
        )

    assert "endpoint_url" in captured_client_kwargs, (
        "Transfer Acceleration endpoint_url must be set"
    )
    assert "s3-accelerate" in captured_client_kwargs["endpoint_url"], (
        "Rule #4: endpoint_url must contain s3-accelerate"
    )


def test_upload_no_profile_in_client_call() -> None:
    mock_client = MagicMock()
    captured_client_kwargs: dict = {}

    def mock_boto3_client(service, **kwargs) -> MagicMock:  # type: ignore[no-untyped-def]
        captured_client_kwargs.update(kwargs)
        return mock_client

    with patch("ocms.s3.upload.boto3.client", side_effect=mock_boto3_client):
        upload_model_output(
            local_path="/tmp/model.bin",
            bucket="ocms-artifacts",
            key="job-123/output/model.bin",
            region="us-east-1",
        )

    assert "profile_name" not in captured_client_kwargs, "Rule #5: profile_name must not be passed"

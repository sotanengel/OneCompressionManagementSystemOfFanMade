from __future__ import annotations

import json
import os
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from ocms.config import get_secret


class TestGetSecret:
    def test_returns_secret_string_from_secrets_manager(self) -> None:
        with mock_aws():
            client = boto3.client("secretsmanager", region_name="us-east-1")
            client.create_secret(Name="ocms/hf-token", SecretString="hf_test_token_abc")

            with patch.dict(os.environ, {"OCMS_AWS_REGION": "us-east-1"}):
                result = get_secret("ocms/hf-token")

        assert result == "hf_test_token_abc"

    def test_returns_json_field_when_secret_is_json(self) -> None:
        with mock_aws():
            client = boto3.client("secretsmanager", region_name="us-east-1")
            payload = json.dumps({"password": "supersecret"})
            client.create_secret(Name="ocms/db-password", SecretString=payload)

            with patch.dict(os.environ, {"OCMS_AWS_REGION": "us-east-1"}):
                result = get_secret("ocms/db-password")

        assert result == payload

    def test_falls_back_to_env_var_when_secret_not_found(self) -> None:
        with (
            mock_aws(),
            patch.dict(
                os.environ,
                {"OCMS_AWS_REGION": "us-east-1", "OCMS_SECRET_OCMS_HF_TOKEN": "env_token"},
            ),
        ):
            result = get_secret("ocms/hf-token")

        assert result == "env_token"

    def test_raises_when_secret_missing_and_no_env_fallback(self) -> None:
        env = {k: v for k, v in os.environ.items() if "HF_TOKEN" not in k}
        env["OCMS_AWS_REGION"] = "us-east-1"
        with (
            mock_aws(),
            patch.dict(os.environ, env, clear=True),
            pytest.raises(RuntimeError, match="Secret not found"),
        ):
            get_secret("ocms/hf-token")

    def test_userdata_contains_secretsmanager_fetch(self) -> None:
        import uuid
        from datetime import UTC, datetime

        from ocms.core.models import FeatureFlags, Job, JobStatus
        from ocms.ec2.script_generator import generate_userdata

        job = Job(
            job_id=uuid.uuid4(),
            model_id="meta-llama/Llama-3.1-8B",
            quant_method="GPTQ",
            bits=4,
            instance_type="g5.xlarge",
            region="us-east-1",
            spot=False,
            max_runtime_hours=2,
            status=JobStatus.PENDING,
            feature_flags=FeatureFlags(),
            created_at=datetime.now(UTC),
        )
        script = generate_userdata(job)
        assert "secretsmanager" in script
        assert "ocms/hf-token" in script
        assert "--profile" not in script

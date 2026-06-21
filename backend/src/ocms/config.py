from __future__ import annotations

import os
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OCMS_", case_sensitive=False)

    database_url: str
    s3_bucket: str
    cognito_user_pool_id: str
    cognito_client_id: str
    aws_region: str = "us-east-1"
    cognito_region: str | None = None
    max_concurrent_jobs: int = 10
    cost_warn_usd: float = 50.0
    cost_hard_stop_usd: float = 100.0
    cors_origins: list[str] = []

    @property
    def effective_cognito_region(self) -> str:
        return self.cognito_region or self.aws_region

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return value
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    # `BaseSettings` populates required fields from the environment, but mypy
    # only sees the dataclass-like constructor signature. `model_validate({})`
    # is the documented escape hatch that triggers the same env-loading.
    return Settings.model_validate({})


def get_secret(secret_name: str) -> str:
    region = os.environ.get("OCMS_AWS_REGION", "us-east-1")
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except ClientError:
        pass

    env_key = "OCMS_SECRET_" + secret_name.upper().replace("/", "_").replace("-", "_")
    value = os.environ.get(env_key)
    if value is not None:
        return value

    raise RuntimeError(f"Secret not found: {secret_name!r} (tried Secrets Manager and {env_key})")

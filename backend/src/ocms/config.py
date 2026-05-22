from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OCMS_", case_sensitive=False)

    database_url: str
    aws_region: str = "us-east-1"
    max_concurrent_jobs: int = 10
    cost_warn_usd: float = 50.0
    cost_hard_stop_usd: float = 100.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

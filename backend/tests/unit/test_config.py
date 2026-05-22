import pytest

from ocms.config import Settings


def test_settings_reads_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCMS_DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
    monkeypatch.setenv("OCMS_AWS_REGION", "us-east-1")
    s = Settings()
    assert s.database_url == "postgresql+psycopg://user:pass@localhost/db"


def test_settings_reads_aws_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCMS_DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
    monkeypatch.setenv("OCMS_AWS_REGION", "ap-northeast-1")
    s = Settings()
    assert s.aws_region == "ap-northeast-1"


def test_settings_default_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCMS_DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
    monkeypatch.delenv("OCMS_AWS_REGION", raising=False)
    s = Settings()
    assert s.aws_region == "us-east-1"


def test_settings_missing_database_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OCMS_DATABASE_URL", raising=False)
    with pytest.raises(Exception):  # noqa: B017
        Settings()

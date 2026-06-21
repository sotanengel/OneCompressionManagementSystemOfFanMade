from __future__ import annotations

import os

os.environ.setdefault(
    "OCMS_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db"
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from ocms.config import Settings  # noqa: E402
from ocms.main import create_app  # noqa: E402


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "database_url": "postgresql+psycopg://u:p@localhost/db",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_cors_middleware_absent_when_origins_unset() -> None:
    app = create_app(settings=_settings())
    client = TestClient(app)
    response = client.get(
        "/health", headers={"Origin": "https://example.com"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in {k.lower() for k in response.headers}


def test_cors_allows_whitelisted_origin() -> None:
    app = create_app(
        settings=_settings(cors_origins=["https://app.example.com"])
    )
    client = TestClient(app)
    response = client.get(
        "/health", headers={"Origin": "https://app.example.com"}
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


def test_cors_rejects_unlisted_origin() -> None:
    app = create_app(
        settings=_settings(cors_origins=["https://app.example.com"])
    )
    client = TestClient(app)
    response = client.get(
        "/health", headers={"Origin": "https://evil.example.com"}
    )
    assert response.status_code == 200
    # Starlette omits the ACAO header for unmatched origins, so callers
    # cannot read the response in a browser.
    assert "access-control-allow-origin" not in {k.lower() for k in response.headers}


def test_cors_methods_restricted_to_safe_set() -> None:
    app = create_app(
        settings=_settings(cors_origins=["https://app.example.com"])
    )
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    allowed = {
        m.strip().upper()
        for m in response.headers.get("access-control-allow-methods", "").split(",")
        if m.strip()
    }
    assert "DELETE" not in allowed
    assert {"GET", "POST", "OPTIONS"}.issubset(allowed)


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        ("", []),
        ("https://a.example.com", ["https://a.example.com"]),
        (
            "https://a.example.com, https://b.example.com",
            ["https://a.example.com", "https://b.example.com"],
        ),
    ],
)
def test_settings_cors_origins_parses_csv(env_value: str, expected: list[str]) -> None:
    s = Settings(  # type: ignore[arg-type]
        database_url="postgresql+psycopg://u:p@localhost/db",
        cors_origins=env_value,
    )
    assert s.cors_origins == expected

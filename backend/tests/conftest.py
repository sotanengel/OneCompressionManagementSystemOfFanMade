import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Ensure required settings are present when ocms.main / ocms.config is imported
# at collection time. Individual tests can still override via monkeypatch.
os.environ.setdefault(
    "OCMS_DATABASE_URL",
    "postgresql+psycopg://ocms:ocms_local@localhost:5432/ocms",
)
os.environ.setdefault("OCMS_S3_BUCKET", "ocms-bucket")
os.environ.setdefault("OCMS_COGNITO_USER_POOL_ID", "us-east-1_TESTPOOL")
os.environ.setdefault("OCMS_COGNITO_CLIENT_ID", "test-client-id")

from ocms.api.auth import verify_cognito_jwt  # noqa: E402
from ocms.storage.db import Base  # noqa: E402


@pytest.fixture(autouse=True)
def _bypass_cognito_for_imported_app() -> Generator[None, None, None]:
    """Override the JWT dep on the module-level `ocms.main:app`.

    Per-test apps built with `FastAPI()` aren't covered here — those tests
    should override the dep themselves, the same way they already override
    `get_db`.
    """
    try:
        from ocms.main import app
    except Exception:
        yield
        return
    app.dependency_overrides[verify_cognito_jwt] = lambda: "test-user-id"
    try:
        yield
    finally:
        app.dependency_overrides.pop(verify_cognito_jwt, None)


def _db_url() -> str:
    return os.environ.get(
        "OCMS_DATABASE_URL",
        "postgresql+psycopg://ocms:ocms_local@localhost:5432/ocms",
    )


@pytest.fixture(scope="session")
def db_engine():  # type: ignore[no-untyped-def]
    engine = create_engine(_db_url())
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:  # type: ignore[no-untyped-def]
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ocms.storage.db import Base


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

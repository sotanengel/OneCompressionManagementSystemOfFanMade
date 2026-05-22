from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    url = os.environ.get("OCMS_DATABASE_URL")
    if not url:
        raise RuntimeError("OCMS_DATABASE_URL environment variable is not set")
    return url


def make_engine():  # type: ignore[no-untyped-def]
    return create_engine(_get_database_url())


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_session() -> Session:
    engine = make_engine()
    SessionLocal.configure(bind=engine)
    return SessionLocal()

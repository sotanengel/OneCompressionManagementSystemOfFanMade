from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    url = os.environ.get("OCMS_DATABASE_URL")
    if not url:
        raise RuntimeError("OCMS_DATABASE_URL environment variable is not set")
    return url


def make_engine() -> Engine:
    return create_engine(
        _get_database_url(),
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_session() -> Session:
    engine = make_engine()
    SessionLocal.configure(bind=engine)
    return SessionLocal()

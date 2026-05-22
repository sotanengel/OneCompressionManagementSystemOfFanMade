from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from ocms.storage.db import SessionLocal, make_engine


def get_db() -> Generator[Session, None, None]:
    engine = make_engine()
    SessionLocal.configure(bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

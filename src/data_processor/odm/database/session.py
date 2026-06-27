"""SQLAlchemy session factory."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from data_processor.odm.database.engine import create_database_engine

SessionFactory = sessionmaker(
    bind=create_database_engine(), autoflush=False, expire_on_commit=False
)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

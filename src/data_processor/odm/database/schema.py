"""Prototype schema helpers for the current SQLAlchemy models."""

from sqlalchemy import text

from data_processor.config.settings import get_settings
from data_processor.odm.database import models
from data_processor.odm.database.base import Base
from data_processor.odm.database.engine import create_database_engine


def create_current_schema() -> None:
    """Create the current prototype schema without keeping migration history."""
    settings = get_settings()
    engine = create_database_engine(settings)

    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.database_schema}"'))

    Base.metadata.create_all(bind=engine)


__all__ = ["create_current_schema", "models"]

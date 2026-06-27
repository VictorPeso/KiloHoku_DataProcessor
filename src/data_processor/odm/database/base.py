"""SQLAlchemy declarative base for the astronomy schema."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from data_processor.config.settings import get_settings


def _metadata() -> MetaData:
    settings = get_settings()
    naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
    return MetaData(schema=settings.database_schema, naming_convention=naming_convention)


class Base(DeclarativeBase):
    metadata = _metadata()

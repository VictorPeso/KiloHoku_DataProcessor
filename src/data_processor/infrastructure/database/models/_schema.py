"""Shared database schema constants."""

from data_processor.infrastructure.database.base import Base

ASTRONOMY_SCHEMA = Base.metadata.schema or "astronomy"

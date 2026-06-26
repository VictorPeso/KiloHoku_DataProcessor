"""Compatibility import for the PostgreSQL source file repository."""

from data_processor.infrastructure.database.repositories.source_file_repository import (
    PostgresSourceFileRepository,
)

__all__ = ["PostgresSourceFileRepository"]

"""Compatibility import for the PostgreSQL job repository."""

from data_processor.infrastructure.database.repositories.job_repository import PostgresJobRepository

__all__ = ["PostgresJobRepository"]

"""Tests for PostgreSQL job repository query construction."""

from sqlalchemy.dialects import postgresql

from data_processor.infrastructure.database.repositories.job_repository import (
    build_claim_pending_jobs_statement,
)


def test_claim_pending_jobs_statement_uses_skip_locked() -> None:
    statement = build_claim_pending_jobs_statement(batch_size=10)

    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "FOR UPDATE SKIP LOCKED" in compiled
    assert "processing_jobs.status IN" in compiled
    assert "ORDER BY astronomy.processing_jobs.priority DESC" in compiled
    assert "LIMIT" in compiled

"""PostgreSQL implementation of the job repository."""

from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from data_processor.core.application.ports.job_repository import ClaimedJob
from data_processor.infrastructure.database.models.processing_job import ProcessingJob

PENDING_JOB_STATUSES = ("pending", "retry_pending")


def build_claim_pending_jobs_statement(batch_size: int) -> Select[tuple[ProcessingJob]]:
    return (
        select(ProcessingJob)
        .where(ProcessingJob.status.in_(PENDING_JOB_STATUSES))
        .order_by(ProcessingJob.priority.desc(), ProcessingJob.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )


class PostgresJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def claim_pending_jobs(self, *, worker_id: str, batch_size: int) -> list[ClaimedJob]:
        now = datetime.now(UTC)
        statement = build_claim_pending_jobs_statement(batch_size)
        jobs = list(self._session.scalars(statement))

        for job in jobs:
            job.status = "claimed"
            job.locked_by = worker_id
            job.locked_at = now
            job.attempts += 1
            job.updated_at = now

        return [_to_claimed_job(job) for job in jobs]

    def mark_processing(self, *, job_id: int, current_step: str | None = None) -> None:
        job = self._get_job(job_id)
        now = datetime.now(UTC)
        job.status = "processing"
        job.current_step = current_step
        job.started_at = job.started_at or now
        job.updated_at = now

    def mark_completed(self, *, job_id: int, warnings: bool = False) -> None:
        job = self._get_job(job_id)
        now = datetime.now(UTC)
        job.status = "completed_with_warnings" if warnings else "completed"
        job.progress_percent = 100
        job.finished_at = now
        job.updated_at = now

    def mark_failed(self, *, job_id: int, error_code: str, error_message: str) -> None:
        job = self._get_job(job_id)
        now = datetime.now(UTC)
        job.status = "failed"
        job.error_code = error_code
        job.error_message = error_message
        job.finished_at = now
        job.updated_at = now

    def _get_job(self, job_id: int) -> ProcessingJob:
        job = self._session.get(ProcessingJob, job_id)
        if job is None:
            raise LookupError(f"Processing job not found: {job_id}")
        return job


def _to_claimed_job(job: ProcessingJob) -> ClaimedJob:
    return ClaimedJob(
        id=job.id,
        source_file_id=job.source_file_id,
        status=job.status,
        attempts=job.attempts,
        progress_percent=job.progress_percent,
        locked_by=job.locked_by,
        locked_at=job.locked_at,
    )

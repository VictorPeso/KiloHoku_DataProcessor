"""Port for reading, claiming, and updating processing jobs."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ClaimedJob:
    id: int
    source_file_id: int
    status: str
    attempts: int
    progress_percent: Decimal
    locked_by: str | None
    locked_at: datetime | None


class JobRepository(Protocol):
    def claim_pending_jobs(self, *, worker_id: str, batch_size: int) -> list[ClaimedJob]:
        """Claim pending jobs for a worker inside the current transaction."""

    def mark_processing(self, *, job_id: int, current_step: str | None = None) -> None:
        """Mark a claimed job as actively processing."""

    def mark_completed(self, *, job_id: int, warnings: bool = False) -> None:
        """Mark a job as completed."""

    def mark_failed(self, *, job_id: int, error_code: str, error_message: str) -> None:
        """Mark a job as failed."""

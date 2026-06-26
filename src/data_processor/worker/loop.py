"""Main polling loop for the autonomous worker."""

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from data_processor.config.settings import Settings, get_settings
from data_processor.infrastructure.database.repositories import PostgresJobRepository
from data_processor.infrastructure.database.session import session_scope
from data_processor.worker.job_runner import JobRunner
from data_processor.worker.scheduler import PollingScheduler

logger = logging.getLogger(__name__)

SessionScopeFactory = Callable[[], AbstractContextManager[Session]]


class WorkerLoop:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        session_factory: SessionScopeFactory = session_scope,
        job_runner: JobRunner | None = None,
        scheduler: PollingScheduler | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._session_factory = session_factory
        self._job_runner = job_runner or JobRunner()
        self._scheduler = scheduler or PollingScheduler(self._settings.poll_interval_seconds)

    def run_once(self) -> int:
        """Run one polling cycle and return the number of claimed jobs."""

        with self._session_factory() as session:
            job_repository = PostgresJobRepository(session)
            jobs = job_repository.claim_pending_jobs(
                worker_id=self._settings.worker_id,
                batch_size=self._settings.job_batch_size,
            )

            if not jobs:
                logger.info("No pending processing jobs found")
                return 0

            logger.info("Claimed %s processing job(s)", len(jobs))

            for job in jobs:
                try:
                    self._job_runner.run(job=job, job_repository=job_repository)
                except NotImplementedError as exc:
                    logger.warning("Job %s cannot run yet: %s", job.id, exc)
                    job_repository.mark_failed(
                        job_id=job.id,
                        error_code="NOT_IMPLEMENTED",
                        error_message=str(exc),
                    )
                except Exception:
                    logger.exception("Job %s failed unexpectedly", job.id)
                    job_repository.mark_failed(
                        job_id=job.id,
                        error_code="UNEXPECTED_ERROR",
                        error_message="Unexpected error while processing job",
                    )

            return len(jobs)

    def run_forever(self) -> None:
        logger.info("Starting data processor worker loop")
        while True:
            self.run_once()
            self._scheduler.wait_until_next_cycle()

"""Job execution adapter."""

import logging

from data_processor.core.application.ports.job_repository import ClaimedJob, JobRepository

logger = logging.getLogger(__name__)


class JobRunner:
    """Runs a claimed job.

    The real VOTable import and scientific processing pipeline is intentionally
    not implemented yet.
    """

    def run(self, *, job: ClaimedJob, job_repository: JobRepository) -> None:
        logger.info("Starting processing job %s", job.id)
        job_repository.mark_processing(
            job_id=job.id,
            current_step="VOTable importer not implemented yet",
        )

        raise NotImplementedError("VOTable processing pipeline is not implemented yet")

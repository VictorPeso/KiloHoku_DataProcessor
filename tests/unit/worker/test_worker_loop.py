"""Tests for the worker polling loop."""

from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any

from data_processor.config.settings import Settings
from data_processor.core.application.ports.job_repository import ClaimedJob
from data_processor.worker.loop import WorkerLoop


class FakeSession:
    def __init__(self) -> None:
        self.jobs: list[Any] = []

    def scalars(self, statement: Any) -> list[Any]:
        return self.jobs

    def get(self, model: type[Any], entity_id: int) -> Any:
        return next(job for job in self.jobs if job.id == entity_id)


class FakeJob:
    def __init__(self) -> None:
        self.id = 1
        self.source_file_id = 10
        self.status = "pending"
        self.attempts = 0
        self.progress_percent = Decimal("0")
        self.locked_by = None
        self.locked_at = None
        self.priority = 0
        self.created_at = None
        self.updated_at = None
        self.current_step = None
        self.started_at = None
        self.finished_at = None
        self.error_code = None
        self.error_message = None


class SuccessfulRunner:
    def run(self, *, job: ClaimedJob, job_repository: Any) -> None:
        job_repository.mark_completed(job_id=job.id)


class NoWaitScheduler:
    def wait_until_next_cycle(self) -> None:
        return None


def test_worker_loop_claims_and_runs_one_cycle() -> None:
    fake_session = FakeSession()
    fake_session.jobs.append(FakeJob())

    @contextmanager
    def session_factory() -> Iterator[FakeSession]:
        yield fake_session

    settings = Settings(
        DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/test",
        WORKER_ID="test-worker",
        JOB_BATCH_SIZE=1,
    )

    loop = WorkerLoop(
        settings=settings,
        session_factory=session_factory,
        job_runner=SuccessfulRunner(),
        scheduler=NoWaitScheduler(),
    )

    claimed_count = loop.run_once()

    assert claimed_count == 1
    assert fake_session.jobs[0].status == "completed"
    assert fake_session.jobs[0].locked_by == "test-worker"

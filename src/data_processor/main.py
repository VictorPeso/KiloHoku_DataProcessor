"""Entrypoint for the autonomous processing worker."""

from data_processor.config.logging import configure_logging
from data_processor.config.settings import get_settings
from data_processor.worker.loop import WorkerLoop


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    WorkerLoop(settings=settings).run_forever()


if __name__ == "__main__":
    main()

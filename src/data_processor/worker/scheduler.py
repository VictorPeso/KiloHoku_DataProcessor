"""Polling schedule helpers."""

from time import sleep


class PollingScheduler:
    def __init__(self, poll_interval_seconds: int) -> None:
        self._poll_interval_seconds = poll_interval_seconds

    def wait_until_next_cycle(self) -> None:
        sleep(self._poll_interval_seconds)

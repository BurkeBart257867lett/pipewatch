"""Simple interval-based scheduler for running pipeline health checks periodically."""

import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SchedulerStop(Exception):
    """Raised to signal the scheduler loop should stop (useful in tests)."""


class Scheduler:
    """Runs a callable repeatedly at a fixed interval."""

    def __init__(self, interval_seconds: int, task: Callable[[], None], max_runs: Optional[int] = None):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be a positive integer")
        self.interval_seconds = interval_seconds
        self.task = task
        self.max_runs = max_runs
        self._run_count = 0
        self._stopped = False

    def stop(self) -> None:
        """Signal the scheduler to stop after the current run."""
        self._stopped = True

    @property
    def run_count(self) -> int:
        return self._run_count

    def run(self, sleep_fn: Callable[[float], None] = time.sleep) -> None:
        """Start the scheduling loop.

        Args:
            sleep_fn: Injected sleep function, defaults to time.sleep.
                      Override in tests to avoid real delays.
        """
        logger.info("Scheduler starting — interval=%ds max_runs=%s", self.interval_seconds, self.max_runs)
        while not self._stopped:
            if self.max_runs is not None and self._run_count >= self.max_runs:
                logger.info("Scheduler reached max_runs=%d, stopping.", self.max_runs)
                break
            try:
                logger.debug("Scheduler executing task (run #%d)", self._run_count + 1)
                self.task()
            except Exception as exc:  # noqa: BLE001
                logger.error("Task raised an exception: %s", exc)
            self._run_count += 1
            if self._stopped:
                break
            if self.max_runs is not None and self._run_count >= self.max_runs:
                break
            logger.debug("Scheduler sleeping for %ds", self.interval_seconds)
            sleep_fn(self.interval_seconds)
        logger.info("Scheduler stopped after %d run(s).", self._run_count)

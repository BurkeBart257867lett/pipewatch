"""Tests for pipewatch.scheduler."""

import pytest
from unittest.mock import MagicMock
from pipewatch.scheduler import Scheduler


def _noop_sleep(seconds: float) -> None:  # noqa: ARG001
    pass


def test_task_called_once_when_max_runs_is_1():
    task = MagicMock()
    scheduler = Scheduler(interval_seconds=5, task=task, max_runs=1)
    scheduler.run(sleep_fn=_noop_sleep)
    task.assert_called_once()
    assert scheduler.run_count == 1


def test_task_called_n_times_for_max_runs():
    task = MagicMock()
    scheduler = Scheduler(interval_seconds=1, task=task, max_runs=4)
    scheduler.run(sleep_fn=_noop_sleep)
    assert task.call_count == 4
    assert scheduler.run_count == 4


def test_sleep_called_between_runs():
    sleep = MagicMock()
    task = MagicMock()
    scheduler = Scheduler(interval_seconds=10, task=task, max_runs=3)
    scheduler.run(sleep_fn=sleep)
    # sleep should be called max_runs-1 times (not after the last run)
    assert sleep.call_count == 2
    sleep.assert_called_with(10)


def test_stop_halts_loop_early():
    calls = []

    def task():
        calls.append(1)
        if len(calls) >= 2:
            scheduler.stop()

    scheduler = Scheduler(interval_seconds=1, task=task)
    scheduler.run(sleep_fn=_noop_sleep)
    assert len(calls) == 2
    assert scheduler.run_count == 2


def test_exception_in_task_does_not_crash_scheduler():
    task = MagicMock(side_effect=[RuntimeError("boom"), None])
    scheduler = Scheduler(interval_seconds=1, task=task, max_runs=2)
    scheduler.run(sleep_fn=_noop_sleep)  # should not raise
    assert scheduler.run_count == 2


def test_invalid_interval_raises():
    with pytest.raises(ValueError, match="positive integer"):
        Scheduler(interval_seconds=0, task=lambda: None)

    with pytest.raises(ValueError, match="positive integer"):
        Scheduler(interval_seconds=-5, task=lambda: None)


def test_run_count_starts_at_zero():
    scheduler = Scheduler(interval_seconds=60, task=lambda: None, max_runs=0)
    assert scheduler.run_count == 0
    scheduler.run(sleep_fn=_noop_sleep)
    assert scheduler.run_count == 0

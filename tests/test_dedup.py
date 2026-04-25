"""Tests for pipewatch.dedup alert deduplication."""

import json
import time
from pathlib import Path

import pytest

from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus
from pipewatch.dedup import (
    DedupState,
    deduplicate_alerts,
    DEFAULT_WINDOW_SECONDS,
)


def _make_alert(source="src", metric="latency", status=MetricStatus.WARNING) -> Alert:
    return Alert(source=source, metric_name=metric, status=status, value=99.0, threshold=80.0)


@pytest.fixture
def dfile(tmp_path) -> Path:
    return tmp_path / "dedup.json"


# --- DedupState unit tests ---

def test_first_alert_not_duplicate():
    state = DedupState()
    alert = _make_alert()
    assert not state.is_duplicate(alert)


def test_alert_duplicate_after_record():
    state = DedupState(window_seconds=60)
    alert = _make_alert()
    now = time.time()
    state.record(alert, now=now)
    assert state.is_duplicate(alert, now=now + 30)


def test_alert_not_duplicate_after_window_expires():
    state = DedupState(window_seconds=60)
    alert = _make_alert()
    now = time.time()
    state.record(alert, now=now)
    assert not state.is_duplicate(alert, now=now + 61)


def test_different_metrics_not_duplicate():
    state = DedupState(window_seconds=300)
    a1 = _make_alert(metric="latency")
    a2 = _make_alert(metric="error_rate")
    now = time.time()
    state.record(a1, now=now)
    assert not state.is_duplicate(a2, now=now + 1)


def test_different_status_not_duplicate():
    state = DedupState(window_seconds=300)
    a_warn = _make_alert(status=MetricStatus.WARNING)
    a_crit = _make_alert(status=MetricStatus.CRITICAL)
    now = time.time()
    state.record(a_warn, now=now)
    assert not state.is_duplicate(a_crit, now=now + 1)


def test_roundtrip_serialization():
    state = DedupState(window_seconds=120)
    alert = _make_alert()
    state.record(alert, now=1000.0)
    restored = DedupState.from_dict(state.to_dict())
    assert restored.window_seconds == 120
    assert restored.is_duplicate(alert, now=1050.0)


# --- deduplicate_alerts integration tests ---

def test_no_duplicates_on_first_run(dfile):
    alerts = [_make_alert(metric="m1"), _make_alert(metric="m2")]
    result = deduplicate_alerts(alerts, state_path=str(dfile))
    assert len(result) == 2


def test_second_run_suppresses_duplicates(dfile):
    now = time.time()
    alerts = [_make_alert(metric="m1")]
    deduplicate_alerts(alerts, state_path=str(dfile), window_seconds=60, now=now)
    result = deduplicate_alerts(alerts, state_path=str(dfile), window_seconds=60, now=now + 10)
    assert result == []


def test_second_run_passes_after_window(dfile):
    now = time.time()
    alerts = [_make_alert(metric="m1")]
    deduplicate_alerts(alerts, state_path=str(dfile), window_seconds=60, now=now)
    result = deduplicate_alerts(alerts, state_path=str(dfile), window_seconds=60, now=now + 61)
    assert len(result) == 1


def test_state_persisted_to_disk(dfile):
    now = time.time()
    alerts = [_make_alert()]
    deduplicate_alerts(alerts, state_path=str(dfile), now=now)
    assert dfile.exists()
    data = json.loads(dfile.read_text())
    assert "seen" in data
    assert len(data["seen"]) == 1

"""Tests for pipewatch.watchdog."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.history import HistoryEntry
from pipewatch.watchdog import (
    StalenessAlert,
    check_staleness,
    format_staleness_report,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_metric(source: str, name: str = "row_count") -> Metric:
    return Metric(source=source, name=name, tags={})


def _make_result(source: str) -> MetricResult:
    return MetricResult(metric=_make_metric(source), value=10.0, status=MetricStatus.OK)


def _make_entry(source: str, age_seconds: float) -> HistoryEntry:
    ts = _NOW - timedelta(seconds=age_seconds)
    return HistoryEntry(timestamp=ts, results=[_make_result(source)])


# ---------------------------------------------------------------------------
# check_staleness
# ---------------------------------------------------------------------------

def test_no_alert_when_source_reported_recently():
    entries = [_make_entry("db", 60)]
    alerts = check_staleness(entries, sources=["db"], threshold_seconds=3600, now=_NOW)
    assert alerts == []


def test_alert_when_source_exceeds_threshold():
    entries = [_make_entry("db", 7200)]
    alerts = check_staleness(entries, sources=["db"], threshold_seconds=3600, now=_NOW)
    assert len(alerts) == 1
    assert alerts[0].source == "db"
    assert alerts[0].stale_seconds == pytest.approx(7200)


def test_alert_when_source_never_reported():
    alerts = check_staleness([], sources=["db"], threshold_seconds=3600, now=_NOW)
    assert len(alerts) == 1
    assert alerts[0].last_seen is None
    assert alerts[0].stale_seconds == float("inf")


def test_only_stale_sources_alerted():
    entries = [
        _make_entry("fresh", 100),
        _make_entry("old", 9000),
    ]
    alerts = check_staleness(
        entries, sources=["fresh", "old"], threshold_seconds=3600, now=_NOW
    )
    assert len(alerts) == 1
    assert alerts[0].source == "old"


def test_latest_timestamp_used_per_source():
    """Multiple entries for same source — only the most recent matters."""
    entries = [
        _make_entry("db", 9000),
        _make_entry("db", 30),   # recent entry should prevent alert
    ]
    alerts = check_staleness(entries, sources=["db"], threshold_seconds=3600, now=_NOW)
    assert alerts == []


# ---------------------------------------------------------------------------
# format_staleness_report
# ---------------------------------------------------------------------------

def test_format_no_alerts():
    report = format_staleness_report([])
    assert "All sources" in report


def test_format_with_alert_never_seen():
    alert = StalenessAlert(source="db", last_seen=None, stale_seconds=float("inf"))
    report = format_staleness_report([alert])
    assert "db" in report
    assert "never reported" in report


def test_format_with_alert_old_timestamp():
    ts = _NOW - timedelta(seconds=5000)
    alert = StalenessAlert(source="api", last_seen=ts, stale_seconds=5000)
    report = format_staleness_report([alert])
    assert "api" in report
    assert "5000s ago" in report

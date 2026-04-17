"""Tests for pipewatch.anomaly."""
from __future__ import annotations
from unittest.mock import MagicMock
from pipewatch.anomaly import detect_anomalies, format_anomaly_report, AnomalyAlert
from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.history import HistoryEntry
import datetime


def _make_metric(name="lag"):
    return Metric(name=name, source_query="SELECT 1", warning_threshold=None, critical_threshold=None)


def _make_result(value, name="lag", source="db"):
    m = _make_metric(name)
    return MetricResult(metric=m, value=value, status=MetricStatus.OK, source=source)


def _make_history(values, name="lag", source="db"):
    entries = []
    for v in values:
        r = _make_result(v, name=name, source=source)
        entries.append(HistoryEntry(timestamp=datetime.datetime.utcnow().isoformat(), results=[r]))
    return entries


def test_no_alert_when_no_history():
    result = _make_result(999.0)
    alerts = detect_anomalies([result], [], z_threshold=2.5, min_history=5)
    assert alerts == []


def test_no_alert_when_insufficient_history():
    history = _make_history([1, 2, 3])
    result = _make_result(999.0)
    alerts = detect_anomalies([result], history, z_threshold=2.5, min_history=5)
    assert alerts == []


def test_no_alert_when_within_threshold():
    history = _make_history([10, 10, 10, 10, 10])
    result = _make_result(10.0)
    alerts = detect_anomalies([result], history, z_threshold=2.5, min_history=5)
    assert alerts == []


def test_alert_on_large_deviation():
    history = _make_history([10, 10, 10, 10, 10, 10, 10, 10, 10, 10])
    result = _make_result(100.0)
    alerts = detect_anomalies([result], history, z_threshold=2.5, min_history=5)
    assert len(alerts) == 1
    assert alerts[0].metric_name == "lag"
    assert alerts[0].source == "db"
    assert alerts[0].z_score > 2.5


def test_no_alert_when_stddev_zero():
    history = _make_history([5, 5, 5, 5, 5])
    result = _make_result(5.0)
    alerts = detect_anomalies([result], history, z_threshold=2.5, min_history=5)
    assert alerts == []


def test_format_no_anomalies():
    assert format_anomaly_report([]) == "No anomalies detected."


def test_format_with_anomalies():
    alert = AnomalyAlert(source="db", metric_name="lag", current_value=100,
                         mean=10, stddev=2, z_score=45.0, threshold=2.5)
    report = format_anomaly_report([alert])
    assert "Anomalies detected" in report
    assert "lag" in report
    assert "z=45.00" in report


def test_multiple_metrics_independent():
    history_lag = _make_history([10]*10, name="lag")
    history_err = _make_history([1]*10, name="errors")
    history = history_lag + history_err
    results = [_make_result(100.0, name="lag"), _make_result(1.0, name="errors")]
    alerts = detect_anomalies(results, history, z_threshold=2.5, min_history=5)
    assert len(alerts) == 1
    assert alerts[0].metric_name == "lag"

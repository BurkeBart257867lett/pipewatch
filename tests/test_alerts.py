"""Tests for pipewatch.alerts module."""

import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.alerts import Alert, evaluate_alerts, format_alert_summary


def _make_result(
    name: str,
    value: float,
    status: MetricStatus,
    warning: float | None = None,
    critical: float | None = None,
    source: str = "test_source",
) -> MetricResult:
    metric = Metric(name=name, query="SELECT 1", warning_threshold=warning, critical_threshold=critical)
    return MetricResult(source=source, metric=metric, value=value, status=status)


def test_no_alerts_when_all_ok():
    results = [
        _make_result("row_count", 100, MetricStatus.OK),
        _make_result("latency", 0.5, MetricStatus.OK),
    ]
    assert evaluate_alerts(results) == []


def test_warning_alert_generated():
    result = _make_result("row_count", 150, MetricStatus.WARNING, warning=100)
    alerts = evaluate_alerts([result])
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.status == MetricStatus.WARNING
    assert alert.metric_name == "row_count"
    assert alert.value == 150
    assert "100" in alert.message


def test_critical_alert_generated():
    result = _make_result("latency", 9.9, MetricStatus.CRITICAL, critical=5.0)
    alerts = evaluate_alerts([result])
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.status == MetricStatus.CRITICAL
    assert "5.0" in alert.message


def test_mixed_results_only_unhealthy_alerted():
    results = [
        _make_result("a", 10, MetricStatus.OK),
        _make_result("b", 200, MetricStatus.WARNING, warning=100),
        _make_result("c", 999, MetricStatus.CRITICAL, critical=500),
    ]
    alerts = evaluate_alerts(results)
    assert len(alerts) == 2
    statuses = {a.status for a in alerts}
    assert MetricStatus.WARNING in statuses
    assert MetricStatus.CRITICAL in statuses


def test_alert_str_contains_source_and_name():
    result = _make_result("error_rate", 0.8, MetricStatus.CRITICAL, critical=0.5, source="prod_db")
    alert = evaluate_alerts([result])[0]
    text = str(alert)
    assert "prod_db" in text
    assert "error_rate" in text
    assert "CRITICAL" in text


def test_format_alert_summary_no_alerts():
    summary = format_alert_summary([])
    assert "healthy" in summary.lower()


def test_format_alert_summary_with_alerts():
    result = _make_result("lag", 300, MetricStatus.WARNING, warning=200)
    alerts = evaluate_alerts([result])
    summary = format_alert_summary(alerts)
    assert "1 alert" in summary
    assert "lag" in summary

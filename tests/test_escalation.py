"""Tests for pipewatch.escalation."""
import json
import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.escalation import (
    EscalationState,
    EscalationAlert,
    evaluate_escalations,
    format_escalation_report,
    _key,
)


def _make_result(source: str, name: str, status: str, value: float = 1.0) -> MetricResult:
    m = Metric(name=name, query="q")
    return MetricResult(source=source, metric=m, value=value, status=status)


@pytest.fixture
def efile(tmp_path):
    return str(tmp_path / "escalation.json")


def test_no_alert_below_threshold(efile):
    results = [_make_result("src", "lag", MetricStatus.WARNING)]
    alerts = evaluate_escalations(results, efile, threshold=3)
    assert alerts == []


def test_alert_at_threshold(efile):
    r = _make_result("src", "lag", MetricStatus.WARNING)
    for _ in range(2):
        alerts = evaluate_escalations([r], efile, threshold=3)
        assert alerts == []
    alerts = evaluate_escalations([r], efile, threshold=3)
    assert len(alerts) == 1
    assert alerts[0].source == "src"
    assert alerts[0].metric == "lag"
    assert alerts[0].consecutive_count == 3


def test_alert_continues_beyond_threshold(efile):
    r = _make_result("src", "lag", MetricStatus.CRITICAL)
    for _ in range(5):
        evaluate_escalations([r], efile, threshold=2)
    alerts = evaluate_escalations([r], efile, threshold=2)
    assert len(alerts) == 1
    assert alerts[0].consecutive_count == 6


def test_reset_on_ok(efile):
    r_bad = _make_result("src", "lag", MetricStatus.WARNING)
    r_ok = _make_result("src", "lag", MetricStatus.OK)
    for _ in range(3):
        evaluate_escalations([r_bad], efile, threshold=3)
    # Now reset
    evaluate_escalations([r_ok], efile, threshold=3)
    # Should not alert immediately after reset
    alerts = evaluate_escalations([r_bad], efile, threshold=3)
    assert alerts == []


def test_state_persisted_across_calls(efile):
    r = _make_result("src", "errors", MetricStatus.CRITICAL)
    evaluate_escalations([r], efile, threshold=2)
    # Second call with fresh function invocation reads persisted state
    alerts = evaluate_escalations([r], efile, threshold=2)
    assert len(alerts) == 1


def test_multiple_metrics_independent(efile):
    r1 = _make_result("src", "lag", MetricStatus.WARNING)
    r2 = _make_result("src", "errors", MetricStatus.OK)
    for _ in range(3):
        alerts = evaluate_escalations([r1, r2], efile, threshold=3)
    assert any(a.metric == "lag" for a in alerts)
    assert not any(a.metric == "errors" for a in alerts)


def test_format_no_alerts():
    assert format_escalation_report([]) == "No escalation alerts."


def test_format_with_alerts():
    a = EscalationAlert(source="src", metric="lag", consecutive_count=4, status=MetricStatus.CRITICAL)
    report = format_escalation_report([a])
    assert "ESCALATION" in report
    assert "lag" in report
    assert "4" in report


def test_state_roundtrip():
    s = EscalationState(source="s", metric="m", consecutive_unhealthy=5, last_status=MetricStatus.WARNING)
    assert EscalationState.from_dict(s.to_dict()) == s

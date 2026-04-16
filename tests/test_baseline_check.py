"""Tests for pipewatch/baseline_check.py"""
import pytest
from pipewatch.baseline import set_baseline
from pipewatch.baseline_check import check_baselines, format_deviation_summary, DeviationAlert
from pipewatch.metrics import MetricResult, MetricStatus


def _make_result(source, name, value):
    return MetricResult(source=source, metric_name=name, value=value, status=MetricStatus.OK, message="ok")


@pytest.fixture
def bfile(tmp_path):
    return str(tmp_path / "b.json")


def test_no_alert_when_no_baseline(bfile):
    results = [_make_result("s", "m", 100)]
    assert check_baselines(results, baseline_path=bfile) == []


def test_no_alert_within_threshold(bfile):
    set_baseline("s", "m", 100.0, bfile)
    results = [_make_result("s", "m", 110)]
    alerts = check_baselines(results, threshold_pct=20.0, baseline_path=bfile)
    assert alerts == []


def test_alert_on_positive_deviation(bfile):
    set_baseline("s", "m", 100.0, bfile)
    results = [_make_result("s", "m", 130)]
    alerts = check_baselines(results, threshold_pct=20.0, baseline_path=bfile)
    assert len(alerts) == 1
    assert alerts[0].deviation_pct == pytest.approx(30.0)


def test_alert_on_negative_deviation(bfile):
    set_baseline("s", "m", 100.0, bfile)
    results = [_make_result("s", "m", 70)]
    alerts = check_baselines(results, threshold_pct=20.0, baseline_path=bfile)
    assert len(alerts) == 1
    assert alerts[0].deviation_pct == pytest.approx(-30.0)


def test_multiple_results_only_deviating_alerted(bfile):
    set_baseline("s", "a", 100.0, bfile)
    set_baseline("s", "b", 200.0, bfile)
    results = [_make_result("s", "a", 105), _make_result("s", "b", 300)]
    alerts = check_baselines(results, threshold_pct=20.0, baseline_path=bfile)
    assert len(alerts) == 1
    assert alerts[0].metric_name == "b"


def test_format_no_alerts():
    assert "No baseline" in format_deviation_summary([])


def test_format_with_alerts(bfile):
    a = DeviationAlert("s", "m", 130, 100, 30.0, 20.0)
    summary = format_deviation_summary([a])
    assert "1 found" in summary
    assert "BASELINE" in summary

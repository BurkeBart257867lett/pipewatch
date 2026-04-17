"""Tests for pipewatch.trend."""
import json
import pytest
from unittest.mock import patch
from pipewatch.trend import compute_trends, format_trend_report, TrendSummary
from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.history import HistoryEntry


def _make_metric(name="row_count"):
    return Metric(name=name, source="db", query="SELECT 1")


def _make_result(value, name="row_count", source="db"):
    m = Metric(name=name, source=source, query="SELECT 1")
    return MetricResult(source=source, metric=m, value=value, status=MetricStatus.OK)


def _make_history_entries(values, name="row_count", source="db"):
    entries = []
    for v in values:
        r = _make_result(v, name=name, source=source)
        entries.append(HistoryEntry(timestamp="2024-01-01T00:00:00", results=[r]))
    return entries


def test_no_trend_when_no_history():
    result = _make_result(100.0)
    with patch("pipewatch.trend.load_history", return_value=[]):
        summaries = compute_trends([result], history_path="fake.json")
    assert summaries == []


def test_trend_computed_correctly():
    history = _make_history_entries([80.0, 90.0, 100.0, 110.0, 120.0])
    result = _make_result(150.0)
    with patch("pipewatch.trend.load_history", return_value=history):
        summaries = compute_trends([result], history_path="fake.json", window=5)
    assert len(summaries) == 1
    s = summaries[0]
    assert s.average_value == pytest.approx(100.0)
    assert s.current_value == 150.0
    assert s.delta_pct == pytest.approx(50.0)


def test_trend_negative_deviation():
    history = _make_history_entries([100.0] * 5)
    result = _make_result(80.0)
    with patch("pipewatch.trend.load_history", return_value=history):
        summaries = compute_trends([result], history_path="fake.json", window=5)
    assert summaries[0].delta_pct == pytest.approx(-20.0)


def test_window_limits_history():
    history = _make_history_entries([10.0] * 8 + [200.0, 200.0])
    result = _make_result(200.0)
    with patch("pipewatch.trend.load_history", return_value=history):
        summaries = compute_trends([result], history_path="fake.json", window=2)
    assert summaries[0].window == 2
    assert summaries[0].average_value == pytest.approx(200.0)


def test_skips_result_with_none_value():
    history = _make_history_entries([100.0, 100.0])
    result = _make_result(None)
    with patch("pipewatch.trend.load_history", return_value=history):
        summaries = compute_trends([result], history_path="fake.json")
    assert summaries == []


def test_format_trend_report_empty():
    assert format_trend_report([]) == "No trend data available."


def test_format_trend_report_shows_entries():
    s = TrendSummary(source="db", metric_name="rows", current_value=110.0,
                     average_value=100.0, delta_pct=10.0, window=5)
    report = format_trend_report([s])
    assert "Trend Report:" in report
    assert "rows" in report
    assert "10.0%" in report

"""Tests for pipewatch.metrics and pipewatch.collector."""

import pytest

from pipewatch.config import PipewatchConfig, SourceConfig
from pipewatch.collector import collect_all
from pipewatch.metrics import (
    Metric,
    MetricStatus,
    evaluate_metric,
)


# ---------------------------------------------------------------------------
# evaluate_metric
# ---------------------------------------------------------------------------

def _make_metric(value: float) -> Metric:
    return Metric(name="latency_seconds", value=value, source="test_source", unit="s")


def test_evaluate_ok_no_thresholds():
    result = evaluate_metric(_make_metric(5.0))
    assert result.status == MetricStatus.OK
    assert result.is_healthy


def test_evaluate_ok_below_warning():
    result = evaluate_metric(_make_metric(3.0), warning_threshold=5.0, critical_threshold=10.0)
    assert result.status == MetricStatus.OK


def test_evaluate_warning():
    result = evaluate_metric(_make_metric(6.0), warning_threshold=5.0, critical_threshold=10.0)
    assert result.status == MetricStatus.WARNING
    assert not result.is_healthy
    assert "warning threshold" in result.message


def test_evaluate_critical():
    result = evaluate_metric(_make_metric(12.0), warning_threshold=5.0, critical_threshold=10.0)
    assert result.status == MetricStatus.CRITICAL
    assert "critical threshold" in result.message


def test_evaluate_critical_without_warning():
    """Critical threshold alone should still trigger CRITICAL."""
    result = evaluate_metric(_make_metric(15.0), critical_threshold=10.0)
    assert result.status == MetricStatus.CRITICAL


def test_metric_repr():
    m = Metric(name="row_count", value=42.0, source="db", unit="rows")
    assert "db/row_count=42.0 rows" in repr(m)


# ---------------------------------------------------------------------------
# collect_all
# ---------------------------------------------------------------------------

def _make_config(**source_kwargs) -> PipewatchConfig:
    defaults = {"name": "demo", "type": "postgres", "dsn": "postgresql://localhost/demo"}
    defaults.update(source_kwargs)
    return PipewatchConfig(sources=[SourceConfig(**defaults)])


def test_collect_all_returns_results():
    config = _make_config()
    results = collect_all(config)
    assert len(results) > 0


def test_collect_all_with_thresholds():
    config = _make_config(
        thresholds={"row_count": {"warning": 1.0, "critical": 5.0}}
    )
    results = collect_all(config)
    row_count_results = [r for r in results if r.metric.name == "row_count"]
    assert row_count_results, "Expected at least one row_count metric"


def test_collect_all_empty_sources():
    config = PipewatchConfig(sources=[])
    results = collect_all(config)
    assert results == []

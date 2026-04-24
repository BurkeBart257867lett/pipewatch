"""Tests for pipewatch.correlation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from pipewatch.correlation import (
    CorrelationResult,
    _describe_strength,
    _pearson,
    compute_correlations,
    format_correlation_report,
)
from pipewatch.history import HistoryEntry
from pipewatch.metrics import Metric, MetricResult, MetricStatus


def _make_metric(name: str, source: str = "src") -> Metric:
    return Metric(name=name, source=source, query="q")


def _make_result(metric: Metric, value: float) -> MetricResult:
    return MetricResult(metric=metric, value=value, status=MetricStatus.OK)


def _make_entry(results: List[MetricResult], ts: float = 0.0) -> HistoryEntry:
    return HistoryEntry(
        timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
        results=results,
    )


# ---------------------------------------------------------------------------
# _pearson
# ---------------------------------------------------------------------------

def test_pearson_perfect_positive():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 4.0, 6.0, 8.0, 10.0]
    r = _pearson(xs, ys)
    assert r is not None
    assert abs(r - 1.0) < 1e-9


def test_pearson_perfect_negative():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [10.0, 8.0, 6.0, 4.0, 2.0]
    r = _pearson(xs, ys)
    assert r is not None
    assert abs(r + 1.0) < 1e-9


def test_pearson_returns_none_for_constant_series():
    xs = [3.0, 3.0, 3.0]
    ys = [1.0, 2.0, 3.0]
    assert _pearson(xs, ys) is None


def test_pearson_returns_none_for_single_point():
    assert _pearson([1.0], [1.0]) is None


# ---------------------------------------------------------------------------
# _describe_strength
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("r, expected", [
    (0.95, "very strong"),
    (-0.95, "very strong"),
    (0.75, "strong"),
    (0.5, "moderate"),
    (0.25, "weak"),
    (0.05, "negligible"),
])
def test_describe_strength(r, expected):
    assert _describe_strength(r) == expected


# ---------------------------------------------------------------------------
# compute_correlations
# ---------------------------------------------------------------------------

def _build_entries(n: int = 10) -> List[HistoryEntry]:
    m1 = _make_metric("latency", "db")
    m2 = _make_metric("errors", "db")
    entries = []
    for i in range(n):
        r1 = _make_result(m1, float(i))
        r2 = _make_result(m2, float(i) * 2)  # perfect positive correlation
        entries.append(_make_entry([r1, r2], ts=float(i)))
    return entries


def test_no_correlations_when_no_history():
    assert compute_correlations([]) == []


def test_no_correlations_below_min_samples():
    entries = _build_entries(n=4)
    assert compute_correlations(entries, min_samples=5) == []


def test_correlations_detected():
    entries = _build_entries(n=10)
    results = compute_correlations(entries, min_samples=5)
    assert len(results) == 1
    assert abs(results[0].coefficient - 1.0) < 1e-6
    assert results[0].sample_size == 10


def test_min_abs_r_filter():
    entries = _build_entries(n=10)
    results = compute_correlations(entries, min_samples=5, min_abs_r=0.99)
    assert len(results) == 1
    results_filtered = compute_correlations(entries, min_samples=5, min_abs_r=1.01)
    assert results_filtered == []


def test_results_sorted_by_abs_coefficient_descending():
    m1 = _make_metric("a", "s")
    m2 = _make_metric("b", "s")
    m3 = _make_metric("c", "s")
    entries = []
    for i in range(10):
        r1 = _make_result(m1, float(i))
        r2 = _make_result(m2, float(i))          # r=1.0 with m1
        r3 = _make_result(m3, float(i % 3))      # weaker with m1
        entries.append(_make_entry([r1, r2, r3], ts=float(i)))
    results = compute_correlations(entries, min_samples=5)
    coeffs = [abs(r.coefficient) for r in results]
    assert coeffs == sorted(coeffs, reverse=True)


# ---------------------------------------------------------------------------
# format_correlation_report
# ---------------------------------------------------------------------------

def test_format_empty():
    assert format_correlation_report([]) == "No significant correlations found."


def test_format_non_empty():
    c = CorrelationResult("db", "latency", "db", "errors", 0.987, 10)
    report = format_correlation_report([c])
    assert "Metric Correlations" in report
    assert "db/latency" in report
    assert "0.987" in report

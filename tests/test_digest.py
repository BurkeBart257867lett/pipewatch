"""Tests for pipewatch.digest."""

from __future__ import annotations

import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.digest import DigestSummary, build_digest, format_digest


def _make_result(source: str, name: str, value: float, status: MetricStatus) -> MetricResult:
    metric = Metric(name=name, query="SELECT 1", warning_threshold=None, critical_threshold=None)
    return MetricResult(source=source, metric=metric, value=value, status=status)


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

def test_empty_results_gives_zero_totals():
    summary = build_digest([])
    assert summary.total == 0
    assert summary.ok == 0
    assert summary.warning == 0
    assert summary.critical == 0
    assert summary.by_source == {}


def test_all_ok_results():
    results = [
        _make_result("src_a", "m1", 1.0, MetricStatus.OK),
        _make_result("src_a", "m2", 2.0, MetricStatus.OK),
    ]
    summary = build_digest(results)
    assert summary.total == 2
    assert summary.ok == 2
    assert summary.warning == 0
    assert summary.critical == 0
    assert summary.by_source["src_a"]["ok"] == 2


def test_mixed_statuses_counted_correctly():
    results = [
        _make_result("src_a", "m1", 1.0, MetricStatus.OK),
        _make_result("src_a", "m2", 5.0, MetricStatus.WARNING),
        _make_result("src_b", "m3", 9.0, MetricStatus.CRITICAL),
        _make_result("src_b", "m4", 2.0, MetricStatus.OK),
    ]
    summary = build_digest(results)
    assert summary.total == 4
    assert summary.ok == 2
    assert summary.warning == 1
    assert summary.critical == 1


def test_by_source_split():
    results = [
        _make_result("alpha", "m1", 1.0, MetricStatus.OK),
        _make_result("beta", "m2", 5.0, MetricStatus.WARNING),
        _make_result("beta", "m3", 9.0, MetricStatus.CRITICAL),
    ]
    summary = build_digest(results)
    assert summary.by_source["alpha"]["ok"] == 1
    assert summary.by_source["beta"]["warning"] == 1
    assert summary.by_source["beta"]["critical"] == 1


# ---------------------------------------------------------------------------
# DigestSummary.__str__
# ---------------------------------------------------------------------------

def test_str_contains_totals():
    summary = DigestSummary(total=3, ok=1, warning=1, critical=1)
    text = str(summary)
    assert "Total metrics" in text
    assert "3" in text


def test_str_contains_source_breakdown():
    results = [
        _make_result("db1", "rows", 100.0, MetricStatus.OK),
        _make_result("db1", "lag", 50.0, MetricStatus.WARNING),
    ]
    text = str(build_digest(results))
    assert "db1" in text
    assert "ok=1" in text
    assert "warn=1" in text


# ---------------------------------------------------------------------------
# format_digest convenience wrapper
# ---------------------------------------------------------------------------

def test_format_digest_returns_string():
    results = [_make_result("src", "m", 1.0, MetricStatus.OK)]
    out = format_digest(results)
    assert isinstance(out, str)
    assert "Pipewatch Digest" in out

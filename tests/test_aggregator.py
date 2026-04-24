"""Tests for pipewatch.aggregator."""

import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.aggregator import (
    AggregatedGroup,
    aggregate_by_source,
    aggregate_by_metric,
    aggregate_by_tag,
    format_aggregation_report,
)


def _make_result(
    source: str,
    name: str,
    value: float,
    status: MetricStatus = MetricStatus.OK,
    tags: dict | None = None,
) -> MetricResult:
    metric = Metric(name=name, query="q", tags=tags or {})
    return MetricResult(source=source, metric=metric, value=value, status=status)


# ---------------------------------------------------------------------------
# AggregatedGroup properties
# ---------------------------------------------------------------------------

def test_health_ratio_empty_group():
    grp = AggregatedGroup(group_key="x")
    assert grp.health_ratio == 1.0


def test_avg_value_none_when_no_values():
    grp = AggregatedGroup(group_key="x")
    assert grp.avg_value is None
    assert grp.min_value is None
    assert grp.max_value is None


def test_str_representation():
    grp = AggregatedGroup(group_key="src", total=2, ok_count=1, warning_count=1, values=[1.0, 3.0])
    s = str(grp)
    assert "src" in s
    assert "total=2" in s
    assert "warn=1" in s


# ---------------------------------------------------------------------------
# aggregate_by_source
# ---------------------------------------------------------------------------

def test_aggregate_by_source_groups_correctly():
    results = [
        _make_result("db", "rows", 10.0, MetricStatus.OK),
        _make_result("db", "lag", 5.0, MetricStatus.WARNING),
        _make_result("api", "latency", 200.0, MetricStatus.CRITICAL),
    ]
    groups = aggregate_by_source(results)
    assert set(groups.keys()) == {"db", "api"}
    assert groups["db"].total == 2
    assert groups["db"].ok_count == 1
    assert groups["db"].warning_count == 1
    assert groups["api"].critical_count == 1


def test_aggregate_by_source_avg_value():
    results = [
        _make_result("db", "rows", 10.0),
        _make_result("db", "lag", 20.0),
    ]
    groups = aggregate_by_source(results)
    assert groups["db"].avg_value == pytest.approx(15.0)
    assert groups["db"].min_value == pytest.approx(10.0)
    assert groups["db"].max_value == pytest.approx(20.0)


def test_aggregate_by_source_empty():
    assert aggregate_by_source([]) == {}


# ---------------------------------------------------------------------------
# aggregate_by_metric
# ---------------------------------------------------------------------------

def test_aggregate_by_metric_groups_correctly():
    results = [
        _make_result("db", "rows", 1.0),
        _make_result("api", "rows", 2.0),
        _make_result("db", "latency", 50.0, MetricStatus.CRITICAL),
    ]
    groups = aggregate_by_metric(results)
    assert groups["rows"].total == 2
    assert groups["rows"].avg_value == pytest.approx(1.5)
    assert groups["latency"].critical_count == 1


# ---------------------------------------------------------------------------
# aggregate_by_tag
# ---------------------------------------------------------------------------

def test_aggregate_by_tag_groups_by_tag_value():
    results = [
        _make_result("db", "m", 1.0, tags={"env": "prod"}),
        _make_result("db", "m", 2.0, tags={"env": "prod"}),
        _make_result("db", "m", 3.0, tags={"env": "staging"}),
    ]
    groups = aggregate_by_tag(results, "env")
    assert groups["prod"].total == 2
    assert groups["staging"].total == 1


def test_aggregate_by_tag_untagged_bucket():
    results = [
        _make_result("db", "m", 1.0, tags={}),
    ]
    groups = aggregate_by_tag(results, "env")
    assert "<untagged>" in groups


# ---------------------------------------------------------------------------
# format_aggregation_report
# ---------------------------------------------------------------------------

def test_format_aggregation_report_empty():
    assert format_aggregation_report({}) == "No data to aggregate."


def test_format_aggregation_report_contains_keys():
    results = [
        _make_result("db", "rows", 5.0),
        _make_result("api", "latency", 100.0, MetricStatus.WARNING),
    ]
    groups = aggregate_by_source(results)
    report = format_aggregation_report(groups)
    assert "db" in report
    assert "api" in report
    assert "\n" in report

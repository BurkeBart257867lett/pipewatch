"""Tests for pipewatch.dependency."""

from __future__ import annotations

import json
import os

import pytest

from pipewatch.dependency import (
    BlockedAlert,
    DependencyGraph,
    check_dependencies,
    format_blocked_report,
    load_graph,
    save_graph,
)
from pipewatch.metrics import Metric, MetricResult, MetricStatus


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_metric(name: str, source: str) -> Metric:
    return Metric(name=name, source=source, query="select 1")


def _make_result(name: str, source: str, status: MetricStatus, value: float = 1.0) -> MetricResult:
    return MetricResult(metric=_make_metric(name, source), value=value, status=status)


# ---------------------------------------------------------------------------
# DependencyGraph unit tests
# ---------------------------------------------------------------------------

def test_add_and_upstream():
    g = DependencyGraph()
    g.add_dependency("orders", "payments")
    assert g.upstream("orders") == ["payments"]


def test_no_duplicate_edges():
    g = DependencyGraph()
    g.add_dependency("orders", "payments")
    g.add_dependency("orders", "payments")
    assert g.upstream("orders") == ["payments"]


def test_upstream_empty_for_unknown():
    g = DependencyGraph()
    assert g.upstream("nonexistent") == []


def test_roundtrip_serialisation():
    g = DependencyGraph()
    g.add_dependency("a", "b")
    g.add_dependency("a", "c")
    restored = DependencyGraph.from_dict(g.to_dict())
    assert restored.upstream("a") == ["b", "c"]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_save_and_load(tmp_path):
    path = str(tmp_path / "graph.json")
    g = DependencyGraph()
    g.add_dependency("x", "y")
    save_graph(g, path)
    loaded = load_graph(path)
    assert loaded.upstream("x") == ["y"]


def test_load_missing_returns_empty(tmp_path):
    path = str(tmp_path / "missing.json")
    g = load_graph(path)
    assert g.edges == {}


# ---------------------------------------------------------------------------
# check_dependencies
# ---------------------------------------------------------------------------

def test_no_blocked_when_no_graph():
    results = [
        _make_result("m", "src", MetricStatus.CRITICAL),
    ]
    g = DependencyGraph()
    clean, blocked = check_dependencies(results, g)
    assert len(clean) == 1
    assert blocked == []


def test_downstream_blocked_when_upstream_critical():
    results = [
        _make_result("m1", "payments", MetricStatus.CRITICAL),
        _make_result("m2", "orders", MetricStatus.CRITICAL),
    ]
    g = DependencyGraph()
    g.add_dependency("orders", "payments")
    clean, blocked = check_dependencies(results, g)
    sources_clean = {r.metric.source for r in clean}
    assert "payments" in sources_clean
    assert len(blocked) == 1
    assert blocked[0].source == "orders"
    assert blocked[0].blocked_by == "payments"


def test_ok_upstream_does_not_block():
    results = [
        _make_result("m1", "payments", MetricStatus.OK),
        _make_result("m2", "orders", MetricStatus.CRITICAL),
    ]
    g = DependencyGraph()
    g.add_dependency("orders", "payments")
    clean, blocked = check_dependencies(results, g)
    assert len(blocked) == 0
    assert len(clean) == 2


# ---------------------------------------------------------------------------
# format_blocked_report
# ---------------------------------------------------------------------------

def test_format_no_blocked():
    report = format_blocked_report([])
    assert "No results" in report


def test_format_with_blocked():
    result = _make_result("m", "orders", MetricStatus.CRITICAL)
    alerts = [BlockedAlert(source="orders", blocked_by="payments", result=result)]
    report = format_blocked_report(alerts)
    assert "BLOCKED" in report
    assert "payments" in report

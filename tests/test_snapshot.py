"""Tests for pipewatch.snapshot."""

from __future__ import annotations

import os
import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.snapshot import (
    Snapshot,
    SnapshotDiff,
    diff_snapshots,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


def _make_result(source: str, name: str, value: float, status: MetricStatus) -> MetricResult:
    return MetricResult(
        metric=Metric(source=source, name=name, tags=[]),
        value=value,
        status=status,
    )


@pytest.fixture
def snap_dir(tmp_path):
    return str(tmp_path / "snapshots")


def test_save_and_load_roundtrip(snap_dir):
    results = [_make_result("db", "row_count", 100.0, MetricStatus.OK)]
    snap = save_snapshot(results, name="baseline", store_dir=snap_dir)
    assert snap.name == "baseline"
    assert len(snap.results) == 1

    loaded = load_snapshot("baseline", store_dir=snap_dir)
    assert loaded is not None
    assert loaded.name == "baseline"
    assert len(loaded.results) == 1
    assert loaded.results[0].metric.name == "row_count"
    assert loaded.results[0].value == 100.0
    assert loaded.results[0].status == MetricStatus.OK


def test_load_missing_returns_none(snap_dir):
    result = load_snapshot("nonexistent", store_dir=snap_dir)
    assert result is None


def test_list_snapshots_empty(snap_dir):
    assert list_snapshots(store_dir=snap_dir) == []


def test_list_snapshots_returns_names(snap_dir):
    save_snapshot([], name="alpha", store_dir=snap_dir)
    save_snapshot([], name="beta", store_dir=snap_dir)
    names = list_snapshots(store_dir=snap_dir)
    assert "alpha" in names
    assert "beta" in names
    assert len(names) == 2


def test_diff_no_changes():
    r = _make_result("src", "m", 10.0, MetricStatus.OK)
    before = Snapshot(name="a", captured_at="t1", results=[r])
    after = Snapshot(name="b", captured_at="t2", results=[r])
    diff = diff_snapshots(before, after)
    assert diff.added == []
    assert diff.removed == []
    assert diff.changed == []


def test_diff_detects_added():
    r1 = _make_result("src", "m1", 10.0, MetricStatus.OK)
    r2 = _make_result("src", "m2", 20.0, MetricStatus.WARNING)
    before = Snapshot(name="a", captured_at="t1", results=[r1])
    after = Snapshot(name="b", captured_at="t2", results=[r1, r2])
    diff = diff_snapshots(before, after)
    assert len(diff.added) == 1
    assert diff.added[0].metric.name == "m2"


def test_diff_detects_removed():
    r1 = _make_result("src", "m1", 10.0, MetricStatus.OK)
    r2 = _make_result("src", "m2", 20.0, MetricStatus.OK)
    before = Snapshot(name="a", captured_at="t1", results=[r1, r2])
    after = Snapshot(name="b", captured_at="t2", results=[r1])
    diff = diff_snapshots(before, after)
    assert len(diff.removed) == 1
    assert diff.removed[0].metric.name == "m2"


def test_diff_detects_value_change():
    before_r = _make_result("src", "m", 10.0, MetricStatus.OK)
    after_r = _make_result("src", "m", 50.0, MetricStatus.WARNING)
    before = Snapshot(name="a", captured_at="t1", results=[before_r])
    after = Snapshot(name="b", captured_at="t2", results=[after_r])
    diff = diff_snapshots(before, after)
    assert len(diff.changed) == 1
    b, a = diff.changed[0]
    assert b.value == 10.0
    assert a.value == 50.0


def test_diff_str_no_differences():
    before = Snapshot(name="a", captured_at="t1", results=[])
    after = Snapshot(name="b", captured_at="t2", results=[])
    diff = diff_snapshots(before, after)
    assert "no differences" in str(diff)


def test_diff_str_shows_changes():
    r1 = _make_result("src", "m", 5.0, MetricStatus.CRITICAL)
    before = Snapshot(name="a", captured_at="t1", results=[])
    after = Snapshot(name="b", captured_at="t2", results=[r1])
    diff = diff_snapshots(before, after)
    text = str(diff)
    assert "+" in text
    assert "m" in text


def test_snapshot_to_dict_and_from_dict():
    r = _make_result("api", "latency", 42.5, MetricStatus.WARNING)
    snap = Snapshot(name="test", captured_at="2024-01-01T00:00:00+00:00", results=[r])
    d = snap.to_dict()
    assert d["name"] == "test"
    assert len(d["results"]) == 1
    restored = Snapshot.from_dict(d)
    assert restored.name == "test"
    assert restored.results[0].value == 42.5
    assert restored.results[0].status == MetricStatus.WARNING

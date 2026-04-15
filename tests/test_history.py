"""Tests for pipewatch.history module."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from pipewatch.history import (
    HistoryEntry,
    append_results,
    load_history,
    MAX_HISTORY_ENTRIES,
)
from pipewatch.metrics import MetricStatus


@pytest.fixture
def history_file(tmp_path):
    return tmp_path / "history.json"


def _make_result(source="src", name="lag", value=5.0, status=MetricStatus.OK):
    metric = MagicMock()
    metric.source = source
    metric.name = name
    result = MagicMock()
    result.metric = metric
    result.value = value
    result.status = status
    return result


def test_load_empty_when_file_missing(history_file):
    entries = load_history(path=history_file)
    assert entries == []


def test_append_and_load(history_file):
    results = [_make_result(source="db", name="row_count", value=100.0)]
    append_results(results, path=history_file)
    entries = load_history(path=history_file)
    assert len(entries) == 1
    assert entries[0].source == "db"
    assert entries[0].metric_name == "row_count"
    assert entries[0].value == 100.0
    assert entries[0].status == MetricStatus.OK.value


def test_multiple_appends_accumulate(history_file):
    append_results([_make_result(value=1.0)], path=history_file)
    append_results([_make_result(value=2.0)], path=history_file)
    entries = load_history(path=history_file)
    assert len(entries) == 2


def test_filter_by_source(history_file):
    append_results([_make_result(source="a"), _make_result(source="b")], path=history_file)
    entries = load_history(path=history_file, source="a")
    assert all(e.source == "a" for e in entries)
    assert len(entries) == 1


def test_filter_by_metric_name(history_file):
    append_results(
        [_make_result(name="lag"), _make_result(name="errors")],
        path=history_file,
    )
    entries = load_history(path=history_file, metric_name="lag")
    assert len(entries) == 1
    assert entries[0].metric_name == "lag"


def test_history_trimmed_to_max(history_file):
    batch = [_make_result(value=float(i)) for i in range(MAX_HISTORY_ENTRIES + 50)]
    append_results(batch, path=history_file)
    entries = load_history(path=history_file)
    assert len(entries) == MAX_HISTORY_ENTRIES


def test_corrupt_history_file_returns_empty(history_file):
    history_file.write_text("not valid json")
    entries = load_history(path=history_file)
    assert entries == []


def test_entry_from_dict_roundtrip():
    data = {
        "timestamp": "2024-01-01T00:00:00+00:00",
        "source": "kafka",
        "metric_name": "consumer_lag",
        "value": 42.0,
        "status": "warning",
    }
    entry = HistoryEntry.from_dict(data)
    assert entry.source == "kafka"
    assert entry.value == 42.0

"""Tests for pipewatch.export."""

from __future__ import annotations

import csv
import io
import json

import pytest

from pipewatch.export import export_csv, export_json, export_results, export_text
from pipewatch.metrics import Metric, MetricResult, MetricStatus


def _make_result(
    source: str = "db",
    name: str = "row_count",
    value: float = 42.0,
    status: MetricStatus = MetricStatus.OK,
    warn: float | None = 100.0,
    crit: float | None = 200.0,
) -> MetricResult:
    metric = Metric(source=source, name=name, warning_threshold=warn, critical_threshold=crit)
    return MetricResult(metric=metric, value=value, status=status)


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------

def test_export_json_structure():
    result = _make_result()
    raw = export_json([result])
    data = json.loads(raw)
    assert len(data) == 1
    row = data[0]
    assert row["source"] == "db"
    assert row["name"] == "row_count"
    assert row["value"] == 42.0
    assert row["status"] == MetricStatus.OK.value


def test_export_json_empty():
    raw = export_json([])
    assert json.loads(raw) == []


# ---------------------------------------------------------------------------
# export_csv
# ---------------------------------------------------------------------------

def test_export_csv_has_header_and_row():
    result = _make_result(value=7.5, status=MetricStatus.WARNING)
    raw = export_csv([result])
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["status"] == MetricStatus.WARNING.value
    assert float(rows[0]["value"]) == pytest.approx(7.5)


def test_export_csv_empty_has_only_header():
    raw = export_csv([])
    reader = csv.DictReader(io.StringIO(raw))
    assert list(reader) == []


# ---------------------------------------------------------------------------
# export_text
# ---------------------------------------------------------------------------

def test_export_text_contains_values():
    result = _make_result(source="api", name="latency", value=0.123)
    text = export_text([result])
    assert "api" in text
    assert "latency" in text
    assert "OK" in text


def test_export_text_empty():
    assert "No results" in export_text([])


# ---------------------------------------------------------------------------
# export_results dispatch
# ---------------------------------------------------------------------------

def test_export_results_json():
    result = _make_result()
    out = export_results([result], fmt="json")
    assert json.loads(out)[0]["name"] == "row_count"


def test_export_results_csv():
    result = _make_result()
    out = export_results([result], fmt="csv")
    assert "row_count" in out


def test_export_results_text():
    result = _make_result()
    out = export_results([result], fmt="text")
    assert "row_count" in out


def test_export_results_invalid_format():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_results([], fmt="xml")

"""Tests for pipewatch/baseline.py"""
import json
import pytest
from pipewatch.baseline import (
    BaselineEntry,
    load_baselines,
    save_baselines,
    set_baseline,
    get_baseline,
    deviation_pct,
    _key,
)


@pytest.fixture
def bfile(tmp_path):
    return str(tmp_path / "baseline.json")


def test_load_empty_when_missing(bfile):
    assert load_baselines(bfile) == {}


def test_set_and_get_baseline(bfile):
    set_baseline("src", "row_count", 1000.0, bfile)
    entry = get_baseline("src", "row_count", bfile)
    assert entry is not None
    assert entry.baseline_value == 1000.0
    assert entry.source == "src"
    assert entry.metric_name == "row_count"


def test_get_missing_returns_none(bfile):
    assert get_baseline("x", "y", bfile) is None


def test_save_and_load_roundtrip(bfile):
    baselines = {
        _key("a", "m"): BaselineEntry("a", "m", 42.0),
        _key("b", "n"): BaselineEntry("b", "n", 7.5),
    }
    save_baselines(baselines, bfile)
    loaded = load_baselines(bfile)
    assert len(loaded) == 2
    assert loaded[_key("a", "m")].baseline_value == 42.0


def test_overwrite_baseline(bfile):
    set_baseline("src", "latency", 50.0, bfile)
    set_baseline("src", "latency", 75.0, bfile)
    entry = get_baseline("src", "latency", bfile)
    assert entry.baseline_value == 75.0


def test_deviation_pct_positive():
    assert deviation_pct(120, 100) == pytest.approx(20.0)


def test_deviation_pct_negative():
    assert deviation_pct(80, 100) == pytest.approx(-20.0)


def test_deviation_pct_zero_baseline():
    assert deviation_pct(5, 0) is None

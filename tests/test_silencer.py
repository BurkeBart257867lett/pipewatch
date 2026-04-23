"""Tests for pipewatch.silencer."""

import json
import pytest
from datetime import datetime, timezone, timedelta

from pipewatch.silencer import (
    SilenceRule,
    add_silence,
    remove_silence,
    is_silenced,
    list_active_silences,
)


@pytest.fixture
def sfile(tmp_path):
    return str(tmp_path / "silences.json")


def test_load_empty_when_missing(sfile):
    assert list_active_silences(path=sfile) == []


def test_add_and_list(sfile):
    add_silence("src", "metric_a", "maintenance", path=sfile)
    rules = list_active_silences(path=sfile)
    assert len(rules) == 1
    assert rules[0].source == "src"
    assert rules[0].metric == "metric_a"


def test_is_silenced_returns_true(sfile):
    add_silence("src", "metric_a", "planned", path=sfile)
    assert is_silenced("src", "metric_a", path=sfile) is True


def test_is_silenced_returns_false_for_unknown(sfile):
    assert is_silenced("src", "nonexistent", path=sfile) is False


def test_expired_rule_not_active(sfile):
    past = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
    add_silence("src", "metric_b", "expired", expires_at=past, path=sfile)
    assert is_silenced("src", "metric_b", path=sfile) is False
    assert list_active_silences(path=sfile) == []


def test_future_expiry_is_active(sfile):
    future = (datetime.now(tz=timezone.utc) + timedelta(hours=2)).isoformat()
    add_silence("src", "metric_c", "window", expires_at=future, path=sfile)
    assert is_silenced("src", "metric_c", path=sfile) is True


def test_remove_silence(sfile):
    add_silence("src", "metric_a", "reason", path=sfile)
    count = remove_silence("src", "metric_a", path=sfile)
    assert count == 1
    assert is_silenced("src", "metric_a", path=sfile) is False


def test_remove_nonexistent_returns_zero(sfile):
    count = remove_silence("src", "ghost", path=sfile)
    assert count == 0


def test_roundtrip_serialisation(sfile):
    future = (datetime.now(tz=timezone.utc) + timedelta(days=1)).isoformat()
    add_silence("db", "row_count", "deploy", expires_at=future, path=sfile)
    with open(sfile) as fh:
        data = json.load(fh)
    assert data[0]["source"] == "db"
    assert data[0]["expires_at"] == future

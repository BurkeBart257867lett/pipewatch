"""Tests for pipewatch.throttle."""

import json
import time
import pytest
from pathlib import Path

from pipewatch.throttle import (
    ThrottleState,
    filter_throttled,
    _load_state,
    _save_state,
)


@pytest.fixture
def tfile(tmp_path):
    return str(tmp_path / "throttle.json")


# --- ThrottleState unit tests ---

def test_should_fire_when_no_history():
    state = ThrottleState()
    assert state.should_fire("src:metric", 60) is True


def test_should_not_fire_within_cooldown():
    state = ThrottleState()
    state.record("src:metric")
    assert state.should_fire("src:metric", 3600) is False


def test_should_fire_after_cooldown(monkeypatch):
    state = ThrottleState()
    state.last_fired["src:metric"] = time.time() - 100
    assert state.should_fire("src:metric", 60) is True


def test_record_updates_timestamp():
    state = ThrottleState()
    before = time.time()
    state.record("k")
    assert state.last_fired["k"] >= before


def test_roundtrip_serialisation():
    state = ThrottleState(last_fired={"a:b": 123.456})
    restored = ThrottleState.from_dict(state.to_dict())
    assert restored.last_fired == {"a:b": 123.456}


# --- persistence helpers ---

def test_load_state_missing_file(tmp_path):
    state = _load_state(tmp_path / "no_such.json")
    assert state.last_fired == {}


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "t.json"
    state = ThrottleState(last_fired={"x:y": 999.0})
    _save_state(state, path)
    loaded = _load_state(path)
    assert loaded.last_fired == {"x:y": 999.0}


def test_load_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not json{{")
    state = _load_state(path)
    assert state.last_fired == {}


# --- filter_throttled integration ---

def test_all_fire_on_first_call(tfile):
    keys = ["a:m1", "b:m2"]
    result = filter_throttled(keys, cooldown_seconds=60, throttle_file=tfile)
    assert result == keys


def test_second_call_within_cooldown_suppressed(tfile):
    keys = ["a:m1"]
    filter_throttled(keys, cooldown_seconds=3600, throttle_file=tfile)
    result = filter_throttled(keys, cooldown_seconds=3600, throttle_file=tfile)
    assert result == []


def test_second_call_after_cooldown_fires(tmp_path):
    tfile = str(tmp_path / "t.json")
    path = Path(tfile)
    # Pre-seed with old timestamp
    state = ThrottleState(last_fired={"a:m1": time.time() - 200})
    _save_state(state, path)
    result = filter_throttled(["a:m1"], cooldown_seconds=60, throttle_file=tfile)
    assert result == ["a:m1"]


def test_mixed_throttled_and_allowed(tmp_path):
    tfile = str(tmp_path / "t.json")
    path = Path(tfile)
    state = ThrottleState(last_fired={"hot": time.time()})
    _save_state(state, path)
    result = filter_throttled(["hot", "cold"], cooldown_seconds=3600, throttle_file=tfile)
    assert result == ["cold"]

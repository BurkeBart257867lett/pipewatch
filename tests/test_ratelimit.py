"""Tests for pipewatch.ratelimit."""

import json
import time
from pathlib import Path

import pytest

from pipewatch.ratelimit import (
    ChannelRateState,
    clear_channel,
    get_state,
    save_state,
)


@pytest.fixture
def rfile(tmp_path: Path) -> Path:
    return tmp_path / "rl.json"


def test_is_allowed_when_no_history(rfile: Path):
    state = get_state("slack", window_seconds=60, max_alerts=5, path=rfile)
    assert state.is_allowed() is True


def test_is_blocked_when_limit_reached(rfile: Path):
    now = time.time()
    state = ChannelRateState(channel="slack", window_seconds=60, max_alerts=3,
                             timestamps=[now - 5, now - 3, now - 1])
    assert state.is_allowed(now=now) is False


def test_allowed_after_window_expires(rfile: Path):
    now = time.time()
    old = now - 120
    state = ChannelRateState(channel="slack", window_seconds=60, max_alerts=2,
                             timestamps=[old, old])
    assert state.is_allowed(now=now) is True


def test_remaining_decrements_on_record(rfile: Path):
    now = time.time()
    state = ChannelRateState(channel="pagerduty", window_seconds=60, max_alerts=5)
    assert state.remaining(now=now) == 5
    state.record(now=now)
    assert state.remaining(now=now) == 4


def test_remaining_never_negative(rfile: Path):
    now = time.time()
    state = ChannelRateState(channel="email", window_seconds=60, max_alerts=2,
                             timestamps=[now - 5, now - 3, now - 1])
    assert state.remaining(now=now) == 0


def test_save_and_load_roundtrip(rfile: Path):
    now = time.time()
    state = ChannelRateState(channel="webhook", window_seconds=300, max_alerts=10,
                             timestamps=[now - 10, now - 5])
    save_state(state, path=rfile)
    loaded = get_state("webhook", window_seconds=300, max_alerts=10, path=rfile)
    assert loaded.channel == "webhook"
    assert len(loaded.timestamps) == 2


def test_get_state_returns_fresh_when_missing(rfile: Path):
    state = get_state("new-channel", window_seconds=120, max_alerts=4, path=rfile)
    assert state.timestamps == []
    assert state.max_alerts == 4


def test_clear_channel_removes_entry(rfile: Path):
    state = ChannelRateState(channel="slack", window_seconds=60, max_alerts=3,
                             timestamps=[time.time()])
    save_state(state, path=rfile)
    clear_channel("slack", path=rfile)
    raw = json.loads(rfile.read_text())
    assert "slack" not in raw


def test_to_dict_and_from_dict_roundtrip():
    now = time.time()
    state = ChannelRateState(channel="teams", window_seconds=60, max_alerts=5,
                             timestamps=[now - 2, now - 1])
    restored = ChannelRateState.from_dict(state.to_dict())
    assert restored.channel == state.channel
    assert restored.window_seconds == state.window_seconds
    assert restored.timestamps == state.timestamps

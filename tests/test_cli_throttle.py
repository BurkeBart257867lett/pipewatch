"""Tests for pipewatch.cli_throttle."""

import argparse
import time
import pytest
from pathlib import Path

from pipewatch.throttle import ThrottleState, _save_state
from pipewatch.cli_throttle import (
    add_throttle_subcommand,
    cmd_throttle_show,
    cmd_throttle_clear,
)


@pytest.fixture
def tfile(tmp_path):
    return str(tmp_path / "throttle.json")


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_throttle_subcommand(sub)
    return p


def _make_args(tfile, throttle_cmd, key=None):
    ns = argparse.Namespace(
        throttle_file=tfile,
        throttle_cmd=throttle_cmd,
        key=key,
    )
    return ns


def test_add_throttle_subcommand_registers(parser):
    args = parser.parse_args(["throttle", "show"])
    assert args.command == "throttle"


def test_show_empty_state(tfile, capsys):
    cmd_throttle_show(_make_args(tfile, "show"))
    out = capsys.readouterr().out
    assert "No throttle entries" in out


def test_show_with_entries(tmp_path, capsys):
    path = tmp_path / "t.json"
    state = ThrottleState(last_fired={"src:metric": 1_700_000_000.0})
    _save_state(state, path)
    cmd_throttle_show(_make_args(str(path), "show"))
    out = capsys.readouterr().out
    assert "src:metric" in out
    assert "1700000000" in out


def test_clear_all(tmp_path, capsys):
    path = tmp_path / "t.json"
    state = ThrottleState(last_fired={"a": 1.0, "b": 2.0})
    _save_state(state, path)
    cmd_throttle_clear(_make_args(str(path), "clear"))
    out = capsys.readouterr().out
    assert "cleared" in out.lower()
    from pipewatch.throttle import _load_state
    assert _load_state(path).last_fired == {}


def test_clear_specific_key(tmp_path, capsys):
    path = tmp_path / "t.json"
    state = ThrottleState(last_fired={"a": 1.0, "b": 2.0})
    _save_state(state, path)
    cmd_throttle_clear(_make_args(str(path), "clear", key="a"))
    from pipewatch.throttle import _load_state
    remaining = _load_state(path).last_fired
    assert "a" not in remaining
    assert "b" in remaining


def test_clear_missing_key_prints_not_found(tmp_path, capsys):
    path = tmp_path / "t.json"
    state = ThrottleState(last_fired={})
    _save_state(state, path)
    cmd_throttle_clear(_make_args(str(path), "clear", key="ghost"))
    out = capsys.readouterr().out
    assert "not found" in out.lower()

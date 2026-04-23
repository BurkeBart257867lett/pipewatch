"""Tests for pipewatch.cli_silencer sub-commands."""

import sys
import pytest
from argparse import ArgumentParser
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from pipewatch.cli_silencer import add_silence_subcommand
from pipewatch.silencer import add_silence, list_active_silences


@pytest.fixture
def parser():
    p = ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    add_silence_subcommand(sub)
    return p


@pytest.fixture
def sfile(tmp_path):
    return str(tmp_path / "silences.json")


def test_add_silence_subcommand_registers(parser):
    args = parser.parse_args(["silence", "add", "src", "m", "reason"])
    assert args.source == "src"
    assert args.metric == "m"
    assert args.reason == "reason"
    assert args.expires_at is None


def test_cmd_silence_add_prints_message(parser, sfile, capsys):
    args = parser.parse_args(
        ["silence", "--silence-file", sfile, "add", "src", "m", "deploy"]
    )
    args.func(args)
    out = capsys.readouterr().out
    assert "src/m" in out
    assert "deploy" in out


def test_cmd_silence_list_empty(parser, sfile, capsys):
    args = parser.parse_args(["silence", "--silence-file", sfile, "list"])
    args.func(args)
    assert "No active silences" in capsys.readouterr().out


def test_cmd_silence_list_shows_rules(parser, sfile, capsys):
    add_silence("src", "lag", "maintenance", path=sfile)
    args = parser.parse_args(["silence", "--silence-file", sfile, "list"])
    args.func(args)
    assert "src/lag" in capsys.readouterr().out


def test_cmd_silence_remove_success(parser, sfile, capsys):
    add_silence("src", "lag", "reason", path=sfile)
    args = parser.parse_args(["silence", "--silence-file", sfile, "remove", "src", "lag"])
    args.func(args)
    assert "Removed" in capsys.readouterr().out


def test_cmd_silence_remove_missing_exits(parser, sfile):
    args = parser.parse_args(["silence", "--silence-file", sfile, "remove", "x", "y"])
    with pytest.raises(SystemExit) as exc:
        args.func(args)
    assert exc.value.code == 1

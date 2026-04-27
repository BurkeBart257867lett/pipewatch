"""Tests for pipewatch.cli_runbook."""
import argparse
import pytest
from pathlib import Path
from unittest.mock import patch

from pipewatch.cli_runbook import (
    add_runbook_subcommand,
    cmd_runbook_add,
    cmd_runbook_remove,
    cmd_runbook_show,
    cmd_runbook_list,
)
from pipewatch.runbook import add_runbook, RunbookEntry


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_runbook_subcommand(sub)
    return p


@pytest.fixture
def rfile(tmp_path: Path) -> Path:
    return tmp_path / "runbooks.json"


def _make_args(rfile, **kwargs) -> argparse.Namespace:
    defaults = dict(runbook_file=str(rfile))
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_runbook_subcommand_registers(parser):
    args = parser.parse_args(["runbook", "list"])
    assert args.command == "runbook"


def test_cmd_runbook_add_prints_message(rfile, capsys):
    args = _make_args(rfile, source="db", metric="rows", url="https://wiki", note="")
    rc = cmd_runbook_add(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Runbook registered" in out
    assert "db/rows" in out


def test_cmd_runbook_remove_success(rfile, capsys):
    add_runbook(rfile, RunbookEntry(source="db", metric="rows", url="https://wiki"))
    args = _make_args(rfile, source="db", metric="rows")
    rc = cmd_runbook_remove(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "removed" in out


def test_cmd_runbook_remove_missing(rfile, capsys):
    args = _make_args(rfile, source="db", metric="rows")
    rc = cmd_runbook_remove(args)
    assert rc == 1
    assert "No runbook" in capsys.readouterr().out


def test_cmd_runbook_show_found(rfile, capsys):
    add_runbook(rfile, RunbookEntry(source="api", metric="latency", url="https://a"))
    args = _make_args(rfile, source="api", metric="latency")
    rc = cmd_runbook_show(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "https://a" in out


def test_cmd_runbook_show_not_found(rfile, capsys):
    args = _make_args(rfile, source="api", metric="latency")
    rc = cmd_runbook_show(args)
    assert rc == 1
    assert "No runbook" in capsys.readouterr().out


def test_cmd_runbook_list_empty(rfile, capsys):
    args = _make_args(rfile)
    rc = cmd_runbook_list(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No runbooks" in out


def test_cmd_runbook_list_shows_entries(rfile, capsys):
    add_runbook(rfile, RunbookEntry(source="s3", metric="age", url="https://b"))
    args = _make_args(rfile)
    rc = cmd_runbook_list(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "s3/age" in out

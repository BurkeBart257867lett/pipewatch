"""Tests for pipewatch.suppression and pipewatch.cli_suppression."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta

import pytest

from pipewatch.suppression import (
    SuppressionRule,
    add_suppression,
    is_suppressed,
    list_suppressions,
    remove_suppression,
)
from pipewatch.cli_suppression import (
    add_suppression_subcommand,
    cmd_suppression_add,
    cmd_suppression_list,
    cmd_suppression_remove,
)


@pytest.fixture
def sfile(tmp_path):
    return str(tmp_path / "suppressions.json")


def test_load_empty_when_missing(sfile):
    assert list_suppressions(path=sfile) == []


def test_add_and_list(sfile):
    add_suppression("src_a", "row_count", "maintenance", None, path=sfile)
    rules = list_suppressions(path=sfile)
    assert len(rules) == 1
    assert rules[0].source == "src_a"
    assert rules[0].metric == "row_count"


def test_add_wildcard_metric(sfile):
    add_suppression("src_b", None, "planned outage", None, path=sfile)
    rules = list_suppressions(path=sfile)
    assert rules[0].metric is None


def test_is_suppressed_returns_true(sfile):
    add_suppression("src_a", "row_count", "maint", None, path=sfile)
    assert is_suppressed("src_a", "row_count", path=sfile) is True


def test_is_suppressed_wildcard_matches_any_metric(sfile):
    add_suppression("src_a", None, "maint", None, path=sfile)
    assert is_suppressed("src_a", "latency", path=sfile) is True
    assert is_suppressed("src_a", "row_count", path=sfile) is True


def test_is_suppressed_returns_false_for_unknown(sfile):
    assert is_suppressed("src_x", "row_count", path=sfile) is False


def test_expired_rule_not_active(sfile):
    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    add_suppression("src_a", "row_count", "old", past, path=sfile)
    assert is_suppressed("src_a", "row_count", path=sfile) is False


def test_future_rule_is_active(sfile):
    future = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    add_suppression("src_a", "row_count", "upcoming", future, path=sfile)
    assert is_suppressed("src_a", "row_count", path=sfile) is True


def test_remove_suppression(sfile):
    add_suppression("src_a", "row_count", "maint", None, path=sfile)
    removed = remove_suppression("src_a", "row_count", path=sfile)
    assert removed == 1
    assert list_suppressions(path=sfile) == []


def test_remove_nonexistent_returns_zero(sfile):
    assert remove_suppression("no_such", None, path=sfile) == 0


def test_add_subcommand_registers():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_suppression_subcommand(sub)
    args = parser.parse_args(["suppression", "list"])
    assert args.cmd == "suppression"


def test_cmd_suppression_add_prints(sfile, capsys):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_suppression_subcommand(sub)
    args = parser.parse_args(["--suppression-file", sfile,
                               "suppression", "add", "src_a", "--metric", "lag", "--reason", "deploy"])
    # patch file arg
    args.suppression_file = sfile
    rc = cmd_suppression_add(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "src_a" in out
    assert "lag" in out


def test_cmd_suppression_list_empty(sfile, capsys):
    ns = argparse.Namespace(suppression_file=sfile)
    rc = cmd_suppression_list(ns)
    assert rc == 0
    assert "No active" in capsys.readouterr().out

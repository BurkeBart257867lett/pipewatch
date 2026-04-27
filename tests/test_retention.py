"""Tests for pipewatch.retention and pipewatch.cli_retention."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pipewatch.retention import RetentionPolicy, PruneResult, prune_history, format_prune_result
from pipewatch.cli_retention import add_retention_subcommand


@pytest.fixture()
def hfile(tmp_path: Path) -> str:
    return str(tmp_path / "history.json")


def _write_entries(path: str, timestamps: list[str]) -> None:
    entries = [{"timestamp": ts, "results": []} for ts in timestamps]
    Path(path).write_text(json.dumps(entries))


def _now_iso(delta_days: int = 0) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=delta_days)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# RetentionPolicy.is_valid
# ---------------------------------------------------------------------------

def test_policy_invalid_when_both_none():
    assert RetentionPolicy().is_valid() is False


def test_policy_valid_with_max_age():
    assert RetentionPolicy(max_age_days=7).is_valid() is True


def test_policy_valid_with_max_entries():
    assert RetentionPolicy(max_entries=100).is_valid() is True


# ---------------------------------------------------------------------------
# prune_history — max_age_days
# ---------------------------------------------------------------------------

def test_prune_by_age_removes_old_entries(hfile: str):
    _write_entries(hfile, [_now_iso(10), _now_iso(5), _now_iso(1)])
    result = prune_history(hfile, RetentionPolicy(max_age_days=7))
    assert result.removed == 1
    assert result.kept == 2


def test_prune_by_age_keeps_all_recent(hfile: str):
    _write_entries(hfile, [_now_iso(1), _now_iso(2)])
    result = prune_history(hfile, RetentionPolicy(max_age_days=30))
    assert result.removed == 0
    assert result.kept == 2


# ---------------------------------------------------------------------------
# prune_history — max_entries
# ---------------------------------------------------------------------------

def test_prune_by_count_keeps_most_recent(hfile: str):
    timestamps = [_now_iso(i) for i in range(5, 0, -1)]  # 5 entries
    _write_entries(hfile, timestamps)
    result = prune_history(hfile, RetentionPolicy(max_entries=3))
    assert result.removed == 2
    assert result.kept == 3


def test_prune_by_count_noop_when_under_limit(hfile: str):
    _write_entries(hfile, [_now_iso(1), _now_iso(2)])
    result = prune_history(hfile, RetentionPolicy(max_entries=10))
    assert result.removed == 0


# ---------------------------------------------------------------------------
# prune_history — empty / missing file
# ---------------------------------------------------------------------------

def test_prune_empty_file_returns_zero(hfile: str):
    result = prune_history(hfile, RetentionPolicy(max_age_days=7))
    assert result.removed == 0
    assert result.kept == 0


# ---------------------------------------------------------------------------
# format_prune_result
# ---------------------------------------------------------------------------

def test_format_prune_result_singular():
    assert "1 entry" in format_prune_result(PruneResult(removed=1, kept=4))


def test_format_prune_result_plural():
    assert "3 entries" in format_prune_result(PruneResult(removed=3, kept=7))


# ---------------------------------------------------------------------------
# CLI — add_retention_subcommand
# ---------------------------------------------------------------------------

@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_retention_subcommand(p.add_subparsers(dest="cmd"))
    return p


def test_add_retention_subcommand_registers(parser: argparse.ArgumentParser):
    args = parser.parse_args(["retention", "prune", "--max-age-days", "30"])
    assert args.max_age_days == 30


def test_cmd_retention_prune_no_policy_returns_2(parser: argparse.ArgumentParser, hfile: str, capsys):
    args = parser.parse_args(["retention", "prune", "--history-file", hfile])
    exit_code = args.func(args)
    assert exit_code == 2


def test_cmd_retention_prune_returns_zero(parser: argparse.ArgumentParser, hfile: str):
    _write_entries(hfile, [_now_iso(1)])
    args = parser.parse_args(
        ["retention", "prune", "--history-file", hfile, "--max-entries", "5"]
    )
    exit_code = args.func(args)
    assert exit_code == 0

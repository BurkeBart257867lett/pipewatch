"""Tests for pipewatch.tags and pipewatch.cli_tags."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.tags import TagFilter, collect_all_tags, filter_results


def _make_result(name: str, tags: list[str] | None = None) -> MetricResult:
    m = Metric(source="src", name=name, query="q", tags=tags or [])
    return MetricResult(metric=m, value=1.0, status=MetricStatus.OK)


# ---------------------------------------------------------------------------
# TagFilter
# ---------------------------------------------------------------------------

def test_empty_filter_matches_everything():
    tf = TagFilter()
    assert tf.matches(_make_result("x", ["a", "b"])) is True


def test_filter_matches_when_all_tags_present():
    tf = TagFilter.from_list(["prod", "critical"])
    assert tf.matches(_make_result("x", ["prod", "critical", "extra"])) is True


def test_filter_does_not_match_when_tag_missing():
    tf = TagFilter.from_list(["prod", "critical"])
    assert tf.matches(_make_result("x", ["prod"])) is False


def test_filter_bool_false_when_empty():
    assert not TagFilter()


def test_filter_bool_true_when_has_tags():
    assert TagFilter.from_list(["a"])


# ---------------------------------------------------------------------------
# filter_results
# ---------------------------------------------------------------------------

def test_filter_results_no_tags_returns_all():
    results = [_make_result("a"), _make_result("b")]
    assert filter_results(results) == results


def test_filter_results_selects_matching():
    r1 = _make_result("a", ["prod"])
    r2 = _make_result("b", ["dev"])
    assert filter_results([r1, r2], ["prod"]) == [r1]


def test_filter_results_empty_when_no_match():
    r = _make_result("a", ["dev"])
    assert filter_results([r], ["prod"]) == []


# ---------------------------------------------------------------------------
# collect_all_tags
# ---------------------------------------------------------------------------

def test_collect_all_tags_sorted_unique():
    results = [
        _make_result("a", ["z", "a"]),
        _make_result("b", ["a", "m"]),
    ]
    assert collect_all_tags(results) == ["a", "m", "z"]


def test_collect_all_tags_empty():
    assert collect_all_tags([]) == []


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def test_add_tags_subcommand_registers():
    from pipewatch.cli_tags import add_tags_subcommand

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_tags_subcommand(sub)
    args = parser.parse_args(["tags", "list"])
    assert args.tags_cmd == "list"


def test_cmd_tags_list_prints_tags(capsys):
    from pipewatch.cli_tags import cmd_tags_list
    from pipewatch.history import HistoryEntry
    import datetime

    r = _make_result("m", ["prod"])
    entry = HistoryEntry(timestamp=datetime.datetime.utcnow().isoformat(), results=[r])
    args = MagicMock(history_file="dummy.json")

    with patch("pipewatch.cli_tags.load_history", return_value=[entry]):
        cmd_tags_list(args)

    out = capsys.readouterr().out
    assert "prod" in out


def test_cmd_tags_filter_prints_filtered(capsys):
    from pipewatch.cli_tags import cmd_tags_filter
    from pipewatch.history import HistoryEntry
    import datetime

    r1 = _make_result("m1", ["prod"])
    r2 = _make_result("m2", ["dev"])
    entry = HistoryEntry(timestamp=datetime.datetime.utcnow().isoformat(), results=[r1, r2])
    args = MagicMock(history_file="dummy.json", tag=["prod"])

    with patch("pipewatch.cli_tags.load_history", return_value=[entry]):
        cmd_tags_filter(args)

    out = capsys.readouterr().out
    assert "m1" in out
    assert "m2" not in out

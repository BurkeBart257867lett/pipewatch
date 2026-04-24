"""Tests for pipewatch.cli_snapshot."""

from __future__ import annotations

import argparse
import sys
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.cli_snapshot import (
    add_snapshot_subcommand,
    cmd_snapshot_diff,
    cmd_snapshot_list,
)
from pipewatch.metrics import Metric, MetricResult, MetricStatus
from pipewatch.snapshot import Snapshot


def _make_result(source="src", name="m", value=1.0, status=MetricStatus.OK):
    return MetricResult(
        metric=Metric(source=source, name=name, tags=[]),
        value=value,
        status=status,
    )


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    add_snapshot_subcommand(sub)
    return p


def test_add_snapshot_subcommand_registers(parser):
    args = parser.parse_args(["snapshot", "list"])
    assert args.cmd == "snapshot"
    assert args.snapshot_cmd == "list"


def test_snapshot_save_subcommand_registered(parser):
    args = parser.parse_args(["snapshot", "save", "my-snap"])
    assert args.snapshot_name == "my-snap"


def test_snapshot_diff_subcommand_registered(parser):
    args = parser.parse_args(["snapshot", "diff", "snap1", "snap2"])
    assert args.before == "snap1"
    assert args.after == "snap2"
    assert args.fail_on_change is False


def test_snapshot_diff_fail_on_change_flag(parser):
    args = parser.parse_args(["snapshot", "diff", "a", "b", "--fail-on-change"])
    assert args.fail_on_change is True


def test_cmd_snapshot_list_empty(capsys, tmp_path):
    args = argparse.Namespace(store_dir=str(tmp_path / "snaps"))
    cmd_snapshot_list(args)
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_cmd_snapshot_list_shows_names(capsys, tmp_path):
    from pipewatch.snapshot import save_snapshot

    store = str(tmp_path / "snaps")
    save_snapshot([_make_result()], name="release-1", store_dir=store)
    args = argparse.Namespace(store_dir=store)
    cmd_snapshot_list(args)
    out = capsys.readouterr().out
    assert "release-1" in out


def test_cmd_snapshot_diff_missing_before(tmp_path, capsys):
    args = argparse.Namespace(
        before="ghost",
        after="also-ghost",
        store_dir=str(tmp_path),
        fail_on_change=False,
    )
    with pytest.raises(SystemExit) as exc:
        cmd_snapshot_diff(args)
    assert exc.value.code == 1


def test_cmd_snapshot_diff_no_changes_exits_0(tmp_path):
    from pipewatch.snapshot import save_snapshot

    store = str(tmp_path / "snaps")
    r = _make_result()
    save_snapshot([r], name="snap-a", store_dir=store)
    save_snapshot([r], name="snap-b", store_dir=store)
    args = argparse.Namespace(
        before="snap-a",
        after="snap-b",
        store_dir=store,
        fail_on_change=True,
    )
    # Should not raise
    cmd_snapshot_diff(args)


def test_cmd_snapshot_diff_fail_on_change_exits_1(tmp_path):
    from pipewatch.snapshot import save_snapshot

    store = str(tmp_path / "snaps")
    r1 = _make_result(value=10.0, status=MetricStatus.OK)
    r2 = _make_result(value=99.0, status=MetricStatus.CRITICAL)
    save_snapshot([r1], name="before", store_dir=store)
    save_snapshot([r2], name="after", store_dir=store)
    args = argparse.Namespace(
        before="before",
        after="after",
        store_dir=store,
        fail_on_change=True,
    )
    with pytest.raises(SystemExit) as exc:
        cmd_snapshot_diff(args)
    assert exc.value.code == 1

"""CLI subcommands for snapshot management."""

from __future__ import annotations

import argparse
import sys

from pipewatch.snapshot import (
    diff_snapshots,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)

_DEFAULT_DIR = ".pipewatch/snapshots"


def cmd_snapshot_save(args: argparse.Namespace) -> None:
    """Capture current metrics and save as a named snapshot."""
    from pipewatch.config import load_config
    from pipewatch.collector import collect_all

    cfg = load_config(args.config)
    results = collect_all(cfg)
    snap = save_snapshot(results, name=args.snapshot_name, store_dir=args.store_dir)
    print(f"Snapshot '{snap.name}' saved at {snap.captured_at} ({len(snap.results)} metrics).")


def cmd_snapshot_list(args: argparse.Namespace) -> None:
    """List all saved snapshots."""
    names = list_snapshots(store_dir=args.store_dir)
    if not names:
        print("No snapshots found.")
        return
    for name in names:
        print(f"  {name}")


def cmd_snapshot_diff(args: argparse.Namespace) -> None:
    """Show diff between two named snapshots."""
    before = load_snapshot(args.before, store_dir=args.store_dir)
    after = load_snapshot(args.after, store_dir=args.store_dir)

    if before is None:
        print(f"Snapshot '{args.before}' not found.", file=sys.stderr)
        sys.exit(1)
    if after is None:
        print(f"Snapshot '{args.after}' not found.", file=sys.stderr)
        sys.exit(1)

    diff = diff_snapshots(before, after)
    print(f"Diff: '{args.before}' -> '{args.after}'")
    print(str(diff))

    has_changes = diff.added or diff.removed or diff.changed
    sys.exit(1 if (has_changes and args.fail_on_change) else 0)


def add_snapshot_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    snap_parser = subparsers.add_parser("snapshot", help="Manage metric snapshots")
    snap_sub = snap_parser.add_subparsers(dest="snapshot_cmd", required=True)

    # save
    save_p = snap_sub.add_parser("save", help="Save current metrics as a snapshot")
    save_p.add_argument("snapshot_name", help="Name for the snapshot")
    save_p.add_argument("--config", default="pipewatch.yaml")
    save_p.add_argument("--store-dir", default=_DEFAULT_DIR, dest="store_dir")
    save_p.set_defaults(func=cmd_snapshot_save)

    # list
    list_p = snap_sub.add_parser("list", help="List saved snapshots")
    list_p.add_argument("--store-dir", default=_DEFAULT_DIR, dest="store_dir")
    list_p.set_defaults(func=cmd_snapshot_list)

    # diff
    diff_p = snap_sub.add_parser("diff", help="Diff two snapshots")
    diff_p.add_argument("before", help="Name of the baseline snapshot")
    diff_p.add_argument("after", help="Name of the comparison snapshot")
    diff_p.add_argument("--store-dir", default=_DEFAULT_DIR, dest="store_dir")
    diff_p.add_argument(
        "--fail-on-change",
        action="store_true",
        dest="fail_on_change",
        help="Exit with code 1 when differences are found",
    )
    diff_p.set_defaults(func=cmd_snapshot_diff)

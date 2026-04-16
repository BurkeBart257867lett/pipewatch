"""CLI subcommands for baseline management."""
from __future__ import annotations

import argparse
from typing import List

from pipewatch.baseline import set_baseline, get_baseline, load_baselines, DEFAULT_BASELINE_PATH
from pipewatch.baseline_check import check_baselines, format_deviation_summary
from pipewatch.metrics import MetricResult


def cmd_baseline_set(args: argparse.Namespace) -> None:
    set_baseline(args.source, args.metric, float(args.value), args.baseline_file)
    print(f"Baseline set: {args.source}/{args.metric} = {args.value}")


def cmd_baseline_show(args: argparse.Namespace) -> None:
    baselines = load_baselines(args.baseline_file)
    if not baselines:
        print("No baselines stored.")
        return
    for entry in baselines.values():
        print(f"  {entry.source}/{entry.metric_name}: {entry.baseline_value}")


def cmd_baseline_check(args: argparse.Namespace) -> None:
    """Check latest results against baselines (stub: reads from history)."""
    from pipewatch.history import load_history
    entries = load_history(args.history_file)
    if not entries:
        print("No history to check.")
        return
    latest = entries[-1]
    alerts = check_baselines(latest.results, threshold_pct=args.threshold, baseline_path=args.baseline_file)
    print(format_deviation_summary(alerts))


def add_baseline_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("baseline", help="Manage metric baselines")
    bp = p.add_subparsers(dest="baseline_cmd", required=True)

    ps = bp.add_parser("set", help="Set a baseline value")
    ps.add_argument("source")
    ps.add_argument("metric")
    ps.add_argument("value", type=float)
    ps.add_argument("--baseline-file", default=DEFAULT_BASELINE_PATH)
    ps.set_defaults(func=cmd_baseline_set)

    psh = bp.add_parser("show", help="Show all stored baselines")
    psh.add_argument("--baseline-file", default=DEFAULT_BASELINE_PATH)
    psh.set_defaults(func=cmd_baseline_show)

    pc = bp.add_parser("check", help="Check latest history against baselines")
    pc.add_argument("--baseline-file", default=DEFAULT_BASELINE_PATH)
    pc.add_argument("--history-file", default=".pipewatch_history.json")
    pc.add_argument("--threshold", type=float, default=20.0, metavar="PCT",
                    help="Deviation %% threshold (default: 20)")
    pc.set_defaults(func=cmd_baseline_check)

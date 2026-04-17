"""CLI subcommand for trend analysis."""
from __future__ import annotations
import argparse
from pipewatch.config import load_config
from pipewatch.collector import collect_all
from pipewatch.trend import compute_trends, format_trend_report
from pipewatch.history import DEFAULT_HISTORY_PATH


def cmd_trend(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    results = collect_all(config)

    summaries = compute_trends(
        results,
        history_path=args.history,
        window=args.window,
    )

    if args.source:
        summaries = [s for s in summaries if s.source == args.source]

    if args.threshold is not None:
        summaries = [s for s in summaries if abs(s.delta_pct) >= args.threshold]

    print(format_trend_report(summaries))


def add_trend_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("trend", help="Show metric trends vs historical average")
    p.add_argument("--config", default="pipewatch.yaml", help="Config file path")
    p.add_argument(
        "--history",
        default=DEFAULT_HISTORY_PATH,
        help="History file path",
    )
    p.add_argument(
        "--window",
        type=int,
        default=10,
        help="Number of historical runs to average over",
    )
    p.add_argument(
        "--source",
        default=None,
        help="Filter trends to a specific source",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Only show trends with abs(delta_pct) >= threshold",
    )
    p.set_defaults(func=cmd_trend)

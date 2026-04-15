"""CLI entry point for pipewatch using argparse."""

import argparse
import sys
from pathlib import Path

from pipewatch.config import load_config
from pipewatch.collector import collect_all
from pipewatch.alerts import evaluate_alerts, format_alert_summary
from pipewatch.history import append_results, load_history, DEFAULT_HISTORY_PATH
from pipewatch.reporter import run_report, print_report


def cmd_run(args) -> int:
    config = load_config(args.config)
    results = collect_all(config)
    run_report(results)
    print_report(results)

    if args.save_history:
        path = Path(args.history_path) if args.history_path else DEFAULT_HISTORY_PATH
        append_results(results, path=path)
        print(f"[history] Saved {len(results)} result(s) to {path}")

    alerts = evaluate_alerts(results)
    if alerts:
        print(format_alert_summary(alerts))
        return 1
    return 0


def cmd_history(args) -> int:
    path = Path(args.history_path) if args.history_path else DEFAULT_HISTORY_PATH
    entries = load_history(
        path=path,
        source=args.source or None,
        metric_name=args.metric or None,
    )
    if not entries:
        print("No history found.")
        return 0
    print(f"{'Timestamp':<32} {'Source':<20} {'Metric':<24} {'Value':>10}  Status")
    print("-" * 95)
    for e in entries[-args.limit:]:
        print(f"{e.timestamp:<32} {e.source:<20} {e.metric_name:<24} {e.value:>10.2f}  {e.status}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Monitor and alert on data pipeline health metrics.",
    )
    parser.add_argument("-c", "--config", default="pipewatch.yaml", help="Path to config file")

    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Collect metrics and evaluate alerts")
    run_p.add_argument("--save-history", action="store_true", help="Persist results to history")
    run_p.add_argument("--history-path", default=None, help="Custom history file path")
    run_p.set_defaults(func=cmd_run)

    hist_p = sub.add_parser("history", help="View stored metric history")
    hist_p.add_argument("--source", default=None, help="Filter by source name")
    hist_p.add_argument("--metric", default=None, help="Filter by metric name")
    hist_p.add_argument("--limit", type=int, default=50, help="Max rows to display")
    hist_p.add_argument("--history-path", default=None, help="Custom history file path")
    hist_p.set_defaults(func=cmd_history)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

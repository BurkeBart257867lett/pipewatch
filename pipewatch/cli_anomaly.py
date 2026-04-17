"""CLI subcommand for anomaly detection."""
from __future__ import annotations
import argparse

from pipewatch.config import load_config
from pipewatch.collector import collect_all
from pipewatch.history import load_history
from pipewatch.anomaly import detect_anomalies, format_anomaly_report

DEFAULT_HISTORY = "pipewatch_history.json"
DEFAULT_Z = 2.5
DEFAULT_MIN = 5


def cmd_anomaly(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    results = collect_all(config)
    history = load_history(args.history_file)
    alerts = detect_anomalies(
        results,
        history,
        z_threshold=args.z_threshold,
        min_history=args.min_history,
    )
    print(format_anomaly_report(alerts))
    if alerts and args.exit_code:
        raise SystemExit(2)


def add_anomaly_subcommand(subparsers) -> None:
    p = subparsers.add_parser("anomaly", help="Detect anomalies in current metrics vs history")
    p.add_argument("--config", default="pipewatch.yaml")
    p.add_argument("--history-file", default=DEFAULT_HISTORY)
    p.add_argument("--z-threshold", type=float, default=DEFAULT_Z,
                   help="Z-score threshold for anomaly (default: 2.5)")
    p.add_argument("--min-history", type=int, default=DEFAULT_MIN,
                   help="Minimum history points required (default: 5)")
    p.add_argument("--exit-code", action="store_true",
                   help="Exit with code 2 if anomalies found")
    p.set_defaults(func=cmd_anomaly)

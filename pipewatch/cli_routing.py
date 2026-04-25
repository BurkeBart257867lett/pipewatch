"""CLI subcommand for alert routing."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List

from pipewatch.alerts import evaluate_alerts
from pipewatch.collector import collect_all
from pipewatch.config import load_config
from pipewatch.routing import RouteRule, format_routing_report, route_alerts

_DEFAULT_RULES_FILE = "routing_rules.json"


def _load_rules(path: str) -> List[RouteRule]:
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text())
    return [RouteRule.from_dict(r) for r in raw]


def cmd_route(args: Namespace) -> int:
    config = load_config(args.config)
    results = collect_all(config)
    alerts = evaluate_alerts(results)
    rules = _load_rules(args.rules)
    routed = route_alerts(alerts, rules, default_channel=args.default_channel)
    print(format_routing_report(routed))
    return 1 if any(routed.values()) else 0


def add_routing_subcommand(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "route", help="Route alerts to named channels based on rules"
    )
    p.add_argument("--config", default="pipewatch.yml", help="Config file path")
    p.add_argument(
        "--rules",
        default=_DEFAULT_RULES_FILE,
        help="JSON file containing routing rules",
    )
    p.add_argument(
        "--default-channel",
        default="default",
        dest="default_channel",
        help="Channel for unmatched alerts",
    )
    p.set_defaults(func=cmd_route)

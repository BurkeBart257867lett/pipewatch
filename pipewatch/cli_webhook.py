"""CLI subcommand: pipewatch webhook — send alerts to a webhook endpoint."""

from __future__ import annotations

import argparse
import sys

from pipewatch.collector import collect_all
from pipewatch.alerts import evaluate_alerts
from pipewatch.config import load_config
from pipewatch.webhook import WebhookConfig, send_webhook


def cmd_webhook(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    results = collect_all(config)
    alerts = evaluate_alerts(results)

    if not alerts:
        print("No alerts to send.")
        return 0

    wh_config = WebhookConfig(
        url=args.url,
        method=args.method,
        timeout=args.timeout,
        include_source=not args.no_source,
        include_tags=not args.no_tags,
    )

    result = send_webhook(alerts, wh_config)
    if result.success:
        print(f"Webhook delivered {len(alerts)} alert(s) → {result.url} [{result.status_code}]")
        return 0
    else:
        print(f"Webhook failed: {result.error}", file=sys.stderr)
        return 1


def add_webhook_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("webhook", help="Send alerts to a webhook endpoint")
    p.add_argument("url", help="Webhook URL to POST alerts to")
    p.add_argument("--method", default="POST", choices=["POST", "PUT"], help="HTTP method")
    p.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    p.add_argument("--no-source", action="store_true", help="Omit source field from payload")
    p.add_argument("--no-tags", action="store_true", help="Omit tags field from payload")
    p.add_argument("--config", default="pipewatch.yaml", help="Config file path")
    p.set_defaults(func=cmd_webhook)

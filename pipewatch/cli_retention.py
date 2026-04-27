"""CLI sub-command: `pipewatch retention prune`."""

from __future__ import annotations

import argparse
import sys

from pipewatch.retention import RetentionPolicy, prune_history, format_prune_result

_DEFAULT_HISTORY = "pipewatch_history.json"


def cmd_retention_prune(args: argparse.Namespace) -> int:
    policy = RetentionPolicy(
        max_age_days=args.max_age_days,
        max_entries=args.max_entries,
    )
    if not policy.is_valid():
        print("Error: specify --max-age-days and/or --max-entries.", file=sys.stderr)
        return 2

    result = prune_history(args.history_file, policy)
    print(format_prune_result(result))
    return 0


def add_retention_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "retention",
        help="Prune old history entries according to a retention policy.",
    )
    sub = parser.add_subparsers(dest="retention_cmd")

    prune_p = sub.add_parser("prune", help="Remove history entries that exceed the policy.")
    prune_p.add_argument(
        "--history-file",
        default=_DEFAULT_HISTORY,
        help="Path to the history JSON file (default: %(default)s).",
    )
    prune_p.add_argument(
        "--max-age-days",
        type=int,
        default=None,
        metavar="N",
        help="Drop entries older than N days.",
    )
    prune_p.add_argument(
        "--max-entries",
        type=int,
        default=None,
        metavar="N",
        help="Keep only the N most recent entries.",
    )
    prune_p.set_defaults(func=cmd_retention_prune)

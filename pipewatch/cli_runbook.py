"""CLI subcommand: runbook — manage remediation links for metrics."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.runbook import (
    RunbookEntry,
    add_runbook,
    remove_runbook,
    lookup_runbook,
    load_runbooks,
    format_runbook_list,
    DEFAULT_RUNBOOK_FILE,
)


def cmd_runbook_add(args: argparse.Namespace) -> int:
    path = Path(args.runbook_file)
    entry = RunbookEntry(
        source=args.source,
        metric=args.metric,
        url=args.url,
        note=args.note or "",
    )
    add_runbook(path, entry)
    print(f"Runbook registered: [{args.source}/{args.metric}] -> {args.url}")
    return 0


def cmd_runbook_remove(args: argparse.Namespace) -> int:
    path = Path(args.runbook_file)
    removed = remove_runbook(path, args.source, args.metric)
    if removed:
        print(f"Runbook removed: [{args.source}/{args.metric}]")
        return 0
    print(f"No runbook found for [{args.source}/{args.metric}]")
    return 1


def cmd_runbook_show(args: argparse.Namespace) -> int:
    path = Path(args.runbook_file)
    entry = lookup_runbook(path, args.source, args.metric)
    if entry:
        print(str(entry))
        return 0
    print(f"No runbook for [{args.source}/{args.metric}]")
    return 1


def cmd_runbook_list(args: argparse.Namespace) -> int:
    path = Path(args.runbook_file)
    entries = load_runbooks(path)
    print(format_runbook_list(entries))
    return 0


def add_runbook_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("runbook", help="Manage remediation runbook links")
    p.add_argument("--runbook-file", default=DEFAULT_RUNBOOK_FILE)
    sub = p.add_subparsers(dest="runbook_cmd", required=True)

    add_p = sub.add_parser("add", help="Register a runbook URL")
    add_p.add_argument("source")
    add_p.add_argument("metric")
    add_p.add_argument("url")
    add_p.add_argument("--note", default="")
    add_p.set_defaults(func=cmd_runbook_add)

    rm_p = sub.add_parser("remove", help="Remove a runbook entry")
    rm_p.add_argument("source")
    rm_p.add_argument("metric")
    rm_p.set_defaults(func=cmd_runbook_remove)

    show_p = sub.add_parser("show", help="Show runbook for a metric")
    show_p.add_argument("source")
    show_p.add_argument("metric")
    show_p.set_defaults(func=cmd_runbook_show)

    list_p = sub.add_parser("list", help="List all runbooks")
    list_p.set_defaults(func=cmd_runbook_list)

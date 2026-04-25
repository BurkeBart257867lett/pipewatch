"""CLI subcommand for managing suppression rules."""

from __future__ import annotations

import argparse

from pipewatch.suppression import (
    DEFAULT_SUPPRESSION_FILE,
    add_suppression,
    is_suppressed,
    list_suppressions,
    remove_suppression,
)


def cmd_suppression_add(args: argparse.Namespace) -> int:
    rule = add_suppression(
        source=args.source,
        metric=args.metric,
        reason=args.reason,
        expires_at=args.expires_at,
        path=args.suppression_file,
    )
    scope = f"metric '{rule.metric}'" if rule.metric else "all metrics"
    print(f"Suppression added: source='{rule.source}' {scope} reason='{rule.reason}' expires={rule.expires_at or 'never'}")
    return 0


def cmd_suppression_remove(args: argparse.Namespace) -> int:
    removed = remove_suppression(
        source=args.source,
        metric=args.metric,
        path=args.suppression_file,
    )
    print(f"Removed {removed} suppression rule(s).")
    return 0


def cmd_suppression_list(args: argparse.Namespace) -> int:
    rules = list_suppressions(path=args.suppression_file)
    active = [r for r in rules if r.is_active()]
    if not active:
        print("No active suppression rules.")
        return 0
    for r in active:
        scope = r.metric or "*"
        print(f"  source={r.source}  metric={scope}  reason={r.reason}  expires={r.expires_at or 'never'}")
    return 0


def cmd_suppression_check(args: argparse.Namespace) -> int:
    suppressed = is_suppressed(
        source=args.source,
        metric=args.metric,
        path=args.suppression_file,
    )
    status = "SUPPRESSED" if suppressed else "not suppressed"
    print(f"{args.source}/{args.metric}: {status}")
    return 1 if suppressed else 0


def add_suppression_subcommand(subparsers: argparse.Action) -> None:
    p = subparsers.add_parser("suppression", help="Manage alert suppression rules")
    p.add_argument("--suppression-file", default=DEFAULT_SUPPRESSION_FILE)
    sub = p.add_subparsers(dest="suppression_cmd", required=True)

    add_p = sub.add_parser("add", help="Add a suppression rule")
    add_p.add_argument("source")
    add_p.add_argument("--metric", default=None)
    add_p.add_argument("--reason", default="")
    add_p.add_argument("--expires-at", dest="expires_at", default=None)
    add_p.set_defaults(func=cmd_suppression_add)

    rm_p = sub.add_parser("remove", help="Remove a suppression rule")
    rm_p.add_argument("source")
    rm_p.add_argument("--metric", default=None)
    rm_p.set_defaults(func=cmd_suppression_remove)

    ls_p = sub.add_parser("list", help="List active suppression rules")
    ls_p.set_defaults(func=cmd_suppression_list)

    chk_p = sub.add_parser("check", help="Check if a metric is suppressed")
    chk_p.add_argument("source")
    chk_p.add_argument("metric")
    chk_p.set_defaults(func=cmd_suppression_check)

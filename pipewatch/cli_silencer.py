"""CLI sub-commands for managing alert silences."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace

from pipewatch.silencer import (
    DEFAULT_SILENCE_FILE,
    add_silence,
    remove_silence,
    list_active_silences,
)


def cmd_silence_add(args: Namespace) -> None:
    rule = add_silence(
        source=args.source,
        metric=args.metric,
        reason=args.reason,
        expires_at=args.expires_at,
        path=args.silence_file,
    )
    expiry_str = rule.expires_at or "indefinite"
    print(f"Silenced {rule.source}/{rule.metric} until {expiry_str}: {rule.reason}")


def cmd_silence_remove(args: Namespace) -> None:
    count = remove_silence(
        source=args.source,
        metric=args.metric,
        path=args.silence_file,
    )
    if count == 0:
        print(f"No silence rule found for {args.source}/{args.metric}.")
        sys.exit(1)
    print(f"Removed {count} silence rule(s) for {args.source}/{args.metric}.")


def cmd_silence_list(args: Namespace) -> None:
    rules = list_active_silences(path=args.silence_file)
    if not rules:
        print("No active silences.")
        return
    for r in rules:
        expiry_str = r.expires_at or "indefinite"
        print(f"  {r.source}/{r.metric}  expires={expiry_str}  reason={r.reason}")


def add_silence_subcommand(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser("silence", help="Manage alert silences")
    p.add_argument("--silence-file", default=DEFAULT_SILENCE_FILE)
    sub = p.add_subparsers(dest="silence_cmd", required=True)

    add_p = sub.add_parser("add", help="Add a silence rule")
    add_p.add_argument("source")
    add_p.add_argument("metric")
    add_p.add_argument("reason")
    add_p.add_argument("--expires-at", dest="expires_at", default=None,
                       help="ISO-8601 expiry timestamp (UTC)")
    add_p.set_defaults(func=cmd_silence_add)

    rm_p = sub.add_parser("remove", help="Remove a silence rule")
    rm_p.add_argument("source")
    rm_p.add_argument("metric")
    rm_p.set_defaults(func=cmd_silence_remove)

    ls_p = sub.add_parser("list", help="List active silences")
    ls_p.set_defaults(func=cmd_silence_list)

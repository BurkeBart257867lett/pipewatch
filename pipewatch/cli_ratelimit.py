"""CLI subcommand for inspecting and managing alert rate limits."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pipewatch.ratelimit import _load, clear_channel, _DEFAULT_PATH


def cmd_ratelimit_show(args: argparse.Namespace) -> int:
    path = Path(args.state_file)
    raw = _load(path)
    if not raw:
        print("No rate limit state recorded.")
        return 0
    now = time.time()
    print(f"{'CHANNEL':<24} {'WINDOW(s)':<12} {'MAX':<6} {'USED':<6} {'REMAINING':<10}")
    print("-" * 62)
    for channel, d in sorted(raw.items()):
        window = d["window_seconds"]
        max_alerts = d["max_alerts"]
        cutoff = now - window
        used = sum(1 for t in d.get("timestamps", []) if t >= cutoff)
        remaining = max(0, max_alerts - used)
        print(f"{channel:<24} {window:<12} {max_alerts:<6} {used:<6} {remaining:<10}")
    return 0


def cmd_ratelimit_clear(args: argparse.Namespace) -> int:
    path = Path(args.state_file)
    if args.channel == "--all":
        if path.exists():
            path.write_text(json.dumps({}))
        print("All rate limit state cleared.")
    else:
        clear_channel(args.channel, path)
        print(f"Rate limit state cleared for channel: {args.channel}")
    return 0


def add_ratelimit_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("ratelimit", help="Manage alert rate limits")
    p.add_argument("--state-file", default=str(_DEFAULT_PATH),
                   help="Path to rate limit state file")
    sub = p.add_subparsers(dest="ratelimit_cmd", required=True)

    sub.add_parser("show", help="Show current rate limit state per channel")

    clear_p = sub.add_parser("clear", help="Clear rate limit state for a channel")
    clear_p.add_argument("channel", help="Channel name or --all to clear everything")

    def _dispatch(args: argparse.Namespace) -> int:
        if args.ratelimit_cmd == "show":
            return cmd_ratelimit_show(args)
        if args.ratelimit_cmd == "clear":
            return cmd_ratelimit_clear(args)
        return 1

    p.set_defaults(func=_dispatch)

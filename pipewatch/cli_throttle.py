"""CLI sub-commands for managing alert throttle state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipewatch.throttle import DEFAULT_THROTTLE_FILE, _load_state, _save_state


def cmd_throttle_show(args: argparse.Namespace) -> None:
    """Print current throttle state."""
    path = Path(args.throttle_file)
    state = _load_state(path)
    if not state.last_fired:
        print("No throttle entries recorded.")
        return
    print(f"{'Alert Key':<45} {'Last Fired (epoch)':>20}")
    print("-" * 67)
    for key, ts in sorted(state.last_fired.items()):
        print(f"{key:<45} {ts:>20.2f}")


def cmd_throttle_clear(args: argparse.Namespace) -> None:
    """Clear throttle state (optionally for a specific key)."""
    path = Path(args.throttle_file)
    state = _load_state(path)
    if args.key:
        removed = state.last_fired.pop(args.key, None)
        if removed is None:
            print(f"Key '{args.key}' not found in throttle state.")
        else:
            _save_state(state, path)
            print(f"Cleared throttle for '{args.key}'.")
    else:
        state.last_fired.clear()
        _save_state(state, path)
        print("All throttle entries cleared.")


def add_throttle_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'throttle' subcommand group."""
    throttle_parser = subparsers.add_parser(
        "throttle", help="Manage alert throttle state"
    )
    throttle_parser.add_argument(
        "--throttle-file",
        default=DEFAULT_THROTTLE_FILE,
        help="Path to throttle state file",
    )
    sub = throttle_parser.add_subparsers(dest="throttle_cmd", required=True)

    # show
    sub.add_parser("show", help="Show current throttle state")

    # clear
    clear_p = sub.add_parser("clear", help="Clear throttle entries")
    clear_p.add_argument(
        "--key", default=None, help="Specific alert key to clear (clears all if omitted)"
    )

    throttle_parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> None:
    if args.throttle_cmd == "show":
        cmd_throttle_show(args)
    elif args.throttle_cmd == "clear":
        cmd_throttle_clear(args)

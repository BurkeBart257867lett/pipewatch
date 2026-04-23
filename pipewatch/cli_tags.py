"""CLI sub-command: tags — list tags and filter reports by tag."""
from __future__ import annotations

import argparse
import sys

from pipewatch.history import load_history
from pipewatch.tags import collect_all_tags, filter_results


def cmd_tags_list(args: argparse.Namespace) -> None:
    """Print every tag seen in recent history."""
    entries = load_history(args.history_file)
    if not entries:
        print("No history found.")
        return
    results = [r for entry in entries for r in entry.results]
    tags = collect_all_tags(results)
    if not tags:
        print("No tags found in history.")
        return
    print(f"Known tags ({len(tags)}):")
    for tag in tags:
        print(f"  {tag}")


def cmd_tags_filter(args: argparse.Namespace) -> None:
    """Show the most recent history entry filtered to matching tags."""
    entries = load_history(args.history_file)
    if not entries:
        print("No history found.")
        sys.exit(0)

    latest = entries[-1]
    filtered = filter_results(latest.results, args.tag)
    if not filtered:
        print("No results match the given tag(s).")
        sys.exit(0)

    print(f"Results matching tags {args.tag} ({latest.timestamp}):")
    for r in filtered:
        print(f"  [{r.status.value}] {r.metric.source}/{r.metric.name} = {r.value}")


def add_tags_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    tags_parser = subparsers.add_parser("tags", help="Tag-based filtering utilities")
    tags_sub = tags_parser.add_subparsers(dest="tags_cmd", required=True)

    # tags list
    list_p = tags_sub.add_parser("list", help="List all known tags from history")
    list_p.add_argument("--history-file", default=".pipewatch_history.json")
    list_p.set_defaults(func=cmd_tags_list)

    # tags filter
    filter_p = tags_sub.add_parser("filter", help="Filter latest results by tag")
    filter_p.add_argument("tag", nargs="+", help="One or more tags to require")
    filter_p.add_argument("--history-file", default=".pipewatch_history.json")
    filter_p.set_defaults(func=cmd_tags_filter)

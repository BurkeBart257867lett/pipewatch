"""CLI subcommands for managing the pipeline dependency graph."""

from __future__ import annotations

import argparse
import sys

from pipewatch.collector import collect_all
from pipewatch.config import load_config
from pipewatch.dependency import (
    check_dependencies,
    format_blocked_report,
    load_graph,
    save_graph,
)

_DEFAULT_GRAPH = ".pipewatch/dependencies.json"


def cmd_dep_add(args: argparse.Namespace) -> int:
    graph = load_graph(args.graph_file)
    graph.add_dependency(args.source, args.depends_on)
    save_graph(graph, args.graph_file)
    print(f"Added: '{args.source}' depends on '{args.depends_on}'")
    return 0


def cmd_dep_list(args: argparse.Namespace) -> int:
    graph = load_graph(args.graph_file)
    if not graph.edges:
        print("No dependencies defined.")
        return 0
    for source, upstreams in sorted(graph.edges.items()):
        for up in upstreams:
            print(f"  {source} -> {up}")
    return 0


def cmd_dep_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    results = collect_all(cfg)
    graph = load_graph(args.graph_file)
    clean, blocked = check_dependencies(results, graph)
    print(format_blocked_report(blocked))
    if blocked:
        return 1
    return 0


def add_dependency_subcommand(subparsers: argparse._SubParsersAction) -> None:
    dep_parser = subparsers.add_parser("dependency", help="Manage source dependencies")
    dep_sub = dep_parser.add_subparsers(dest="dep_cmd")

    # add
    p_add = dep_sub.add_parser("add", help="Declare a dependency between sources")
    p_add.add_argument("source", help="Downstream source name")
    p_add.add_argument("depends_on", help="Upstream source name")
    p_add.add_argument("--graph-file", default=_DEFAULT_GRAPH)
    p_add.set_defaults(func=cmd_dep_add)

    # list
    p_list = dep_sub.add_parser("list", help="List all declared dependencies")
    p_list.add_argument("--graph-file", default=_DEFAULT_GRAPH)
    p_list.set_defaults(func=cmd_dep_list)

    # check
    p_check = dep_sub.add_parser(
        "check", help="Check which results are blocked by unhealthy upstreams"
    )
    p_check.add_argument("--config", default="pipewatch.yaml")
    p_check.add_argument("--graph-file", default=_DEFAULT_GRAPH)
    p_check.set_defaults(func=cmd_dep_check)

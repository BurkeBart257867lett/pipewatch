"""CLI sub-command: pipewatch export — run pipeline checks and write results."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

from pipewatch.collector import collect_all
from pipewatch.config import load_config
from pipewatch.export import SUPPORTED_FORMATS, export_results


def cmd_export(args: Namespace) -> int:
    """Collect metrics and export them in the requested format.

    Returns an exit code: 0 on success, 1 on error.
    """
    try:
        config = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"[pipewatch] Failed to load config: {exc}", file=sys.stderr)
        return 1

    results = collect_all(config)

    if not results:
        print("[pipewatch] No metric results collected.", file=sys.stderr)
        return 1

    output = export_results(results, fmt=args.format)

    if args.output:
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(output, encoding="utf-8")
        print(f"[pipewatch] Results written to {dest}")
    else:
        sys.stdout.write(output)

    return 0


def add_export_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    """Register the *export* sub-command on an existing subparsers action."""
    parser: ArgumentParser = subparsers.add_parser(
        "export",
        help="Collect metrics and export results to a file or stdout.",
    )
    parser.add_argument(
        "--config",
        default="pipewatch.yaml",
        help="Path to the pipewatch configuration file (default: pipewatch.yaml).",
    )
    parser.add_argument(
        "--format",
        choices=SUPPORTED_FORMATS,
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    parser.set_defaults(func=cmd_export)

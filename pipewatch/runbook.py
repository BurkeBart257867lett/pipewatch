"""Runbook link registry: attach remediation URLs to metric/source pairs."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

DEFAULT_RUNBOOK_FILE = "runbooks.json"


@dataclass
class RunbookEntry:
    source: str
    metric: str
    url: str
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "RunbookEntry":
        return RunbookEntry(
            source=d["source"],
            metric=d["metric"],
            url=d["url"],
            note=d.get("note", ""),
        )

    def __str__(self) -> str:
        parts = [f"[{self.source}/{self.metric}] {self.url}"]
        if self.note:
            parts.append(f"  note: {self.note}")
        return "\n".join(parts)


def _load_raw(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)


def _save_raw(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(entries, f, indent=2)


def load_runbooks(path: Path) -> list[RunbookEntry]:
    return [RunbookEntry.from_dict(d) for d in _load_raw(path)]


def add_runbook(path: Path, entry: RunbookEntry) -> None:
    entries = load_runbooks(path)
    entries = [e for e in entries if not (e.source == entry.source and e.metric == entry.metric)]
    entries.append(entry)
    _save_raw(path, [e.to_dict() for e in entries])


def remove_runbook(path: Path, source: str, metric: str) -> bool:
    entries = load_runbooks(path)
    filtered = [e for e in entries if not (e.source == source and e.metric == metric)]
    if len(filtered) == len(entries):
        return False
    _save_raw(path, [e.to_dict() for e in filtered])
    return True


def lookup_runbook(path: Path, source: str, metric: str) -> Optional[RunbookEntry]:
    for e in load_runbooks(path):
        if e.source == source and e.metric == metric:
            return e
    return None


def format_runbook_list(entries: list[RunbookEntry]) -> str:
    if not entries:
        return "No runbooks registered."
    return "\n".join(str(e) for e in entries)

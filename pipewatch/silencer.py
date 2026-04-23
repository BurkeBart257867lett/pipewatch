"""Silence (suppress) alerts for specific metrics during maintenance windows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

DEFAULT_SILENCE_FILE = ".pipewatch_silences.json"


@dataclass
class SilenceRule:
    source: str
    metric: str
    reason: str
    expires_at: Optional[str] = None  # ISO-8601 or None for indefinite

    def is_active(self) -> bool:
        """Return True if this rule is currently in effect."""
        if self.expires_at is None:
            return True
        expiry = datetime.fromisoformat(self.expires_at)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(tz=timezone.utc) < expiry

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "SilenceRule":
        return SilenceRule(
            source=d["source"],
            metric=d["metric"],
            reason=d["reason"],
            expires_at=d.get("expires_at"),
        )


def _load_rules(path: str) -> List[SilenceRule]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as fh:
        raw = json.load(fh)
    return [SilenceRule.from_dict(r) for r in raw]


def _save_rules(path: str, rules: List[SilenceRule]) -> None:
    with open(path, "w") as fh:
        json.dump([r.to_dict() for r in rules], fh, indent=2)


def add_silence(source: str, metric: str, reason: str,
                expires_at: Optional[str] = None,
                path: str = DEFAULT_SILENCE_FILE) -> SilenceRule:
    rules = _load_rules(path)
    rule = SilenceRule(source=source, metric=metric, reason=reason, expires_at=expires_at)
    rules.append(rule)
    _save_rules(path, rules)
    return rule


def remove_silence(source: str, metric: str,
                   path: str = DEFAULT_SILENCE_FILE) -> int:
    """Remove all rules matching source+metric. Returns count removed."""
    rules = _load_rules(path)
    kept = [r for r in rules if not (r.source == source and r.metric == metric)]
    removed = len(rules) - len(kept)
    _save_rules(path, kept)
    return removed


def is_silenced(source: str, metric: str,
                path: str = DEFAULT_SILENCE_FILE) -> bool:
    """Return True if there is an active silence rule for this source+metric."""
    for rule in _load_rules(path):
        if rule.source == source and rule.metric == metric and rule.is_active():
            return True
    return False


def list_active_silences(path: str = DEFAULT_SILENCE_FILE) -> List[SilenceRule]:
    return [r for r in _load_rules(path) if r.is_active()]

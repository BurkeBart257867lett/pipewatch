"""Suppression rules: skip alerting for specific metric/source combos during maintenance windows."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_SUPPRESSION_FILE = ".pipewatch_suppressions.json"


@dataclass
class SuppressionRule:
    source: str
    metric: Optional[str]  # None means suppress all metrics for the source
    reason: str
    expires_at: Optional[str]  # ISO-8601 string, None means indefinite

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return True
        ts = datetime.fromisoformat(self.expires_at)
        return (now or datetime.utcnow()) < ts

    def matches(self, source: str, metric: str) -> bool:
        if self.source != source:
            return False
        if self.metric is not None and self.metric != metric:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "metric": self.metric,
            "reason": self.reason,
            "expires_at": self.expires_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "SuppressionRule":
        return SuppressionRule(
            source=d["source"],
            metric=d.get("metric"),
            reason=d.get("reason", ""),
            expires_at=d.get("expires_at"),
        )


def _load_rules(path: str) -> List[SuppressionRule]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [SuppressionRule.from_dict(r) for r in data]


def _save_rules(rules: List[SuppressionRule], path: str) -> None:
    Path(path).write_text(json.dumps([r.to_dict() for r in rules], indent=2))


def add_suppression(source: str, metric: Optional[str], reason: str,
                    expires_at: Optional[str], path: str = DEFAULT_SUPPRESSION_FILE) -> SuppressionRule:
    rules = _load_rules(path)
    rule = SuppressionRule(source=source, metric=metric, reason=reason, expires_at=expires_at)
    rules.append(rule)
    _save_rules(rules, path)
    return rule


def list_suppressions(path: str = DEFAULT_SUPPRESSION_FILE) -> List[SuppressionRule]:
    return _load_rules(path)


def is_suppressed(source: str, metric: str, path: str = DEFAULT_SUPPRESSION_FILE,
                  now: Optional[datetime] = None) -> bool:
    rules = _load_rules(path)
    return any(r.matches(source, metric) and r.is_active(now) for r in rules)


def remove_suppression(source: str, metric: Optional[str],
                       path: str = DEFAULT_SUPPRESSION_FILE) -> int:
    rules = _load_rules(path)
    before = len(rules)
    rules = [r for r in rules if not (r.source == source and r.metric == metric)]
    _save_rules(rules, path)
    return before - len(rules)

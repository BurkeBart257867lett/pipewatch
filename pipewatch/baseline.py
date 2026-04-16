"""Baseline management: store and compare metric baselines."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Optional

DEFAULT_BASELINE_PATH = ".pipewatch_baseline.json"


@dataclass
class BaselineEntry:
    source: str
    metric_name: str
    baseline_value: float

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "BaselineEntry":
        return BaselineEntry(
            source=d["source"],
            metric_name=d["metric_name"],
            baseline_value=float(d["baseline_value"]),
        )


def _key(source: str, metric_name: str) -> str:
    return f"{source}::{metric_name}"


def load_baselines(path: str = DEFAULT_BASELINE_PATH) -> Dict[str, BaselineEntry]:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {_key(e["source"], e["metric_name"]): BaselineEntry.from_dict(e) for e in raw}


def save_baselines(baselines: Dict[str, BaselineEntry], path: str = DEFAULT_BASELINE_PATH) -> None:
    with open(path, "w") as f:
        json.dump([e.to_dict() for e in baselines.values()], f, indent=2)


def set_baseline(source: str, metric_name: str, value: float, path: str = DEFAULT_BASELINE_PATH) -> None:
    baselines = load_baselines(path)
    baselines[_key(source, metric_name)] = BaselineEntry(source, metric_name, value)
    save_baselines(baselines, path)


def get_baseline(source: str, metric_name: str, path: str = DEFAULT_BASELINE_PATH) -> Optional[BaselineEntry]:
    return load_baselines(path).get(_key(source, metric_name))


def deviation_pct(current: float, baseline: float) -> Optional[float]:
    """Return percentage deviation from baseline, or None if baseline is zero."""
    if baseline == 0:
        return None
    return ((current - baseline) / abs(baseline)) * 100

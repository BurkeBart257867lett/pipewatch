"""Webhook notification channel for pipewatch alerts."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.alerts import Alert


@dataclass
class WebhookConfig:
    url: str
    method: str = "POST"
    headers: dict = field(default_factory=lambda: {"Content-Type": "application/json"})
    timeout: int = 10
    include_source: bool = True
    include_tags: bool = True


@dataclass
class WebhookResult:
    url: str
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            return f"WebhookResult(url={self.url!r}, status={self.status_code})"
        return f"WebhookResult(url={self.url!r}, error={self.error!r})"


def _build_payload(alerts: List[Alert], config: WebhookConfig) -> dict:
    entries = []
    for a in alerts:
        entry: dict = {"metric": a.result.metric.name, "status": a.result.status.value}
        if config.include_source:
            entry["source"] = a.result.metric.source
        if config.include_tags and a.result.metric.tags:
            entry["tags"] = a.result.metric.tags
        if a.result.value is not None:
            entry["value"] = a.result.value
        entries.append(entry)
    return {"alerts": entries, "count": len(entries)}


def send_webhook(alerts: List[Alert], config: WebhookConfig) -> WebhookResult:
    """Send alerts to a webhook endpoint. Returns a WebhookResult."""
    if not alerts:
        return WebhookResult(url=config.url, success=True, status_code=0)

    payload = _build_payload(alerts, config)
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        config.url,
        data=body,
        headers=config.headers,
        method=config.method,
    )
    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as resp:
            return WebhookResult(url=config.url, success=True, status_code=resp.status)
    except urllib.error.HTTPError as exc:
        return WebhookResult(url=config.url, success=False, status_code=exc.code, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return WebhookResult(url=config.url, success=False, error=str(exc))

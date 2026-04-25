# Webhook Notification Integration

The `webhook` subcommand sends active pipewatch alerts to an HTTP endpoint as a JSON POST request.

## Usage

```bash
pipewatch webhook https://hooks.example.com/alerts
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `url` | *(required)* | Webhook URL to deliver alerts to |
| `--method` | `POST` | HTTP method (`POST` or `PUT`) |
| `--timeout` | `10` | Request timeout in seconds |
| `--no-source` | `False` | Omit `source` field from each alert entry |
| `--no-tags` | `False` | Omit `tags` field from each alert entry |
| `--config` | `pipewatch.yaml` | Path to pipewatch config file |

## Payload Format

```json
{
  "count": 2,
  "alerts": [
    {
      "metric": "row_count",
      "status": "critical",
      "source": "postgres",
      "tags": ["env:prod"],
      "value": 0.0
    }
  ]
}
```

## Exit Codes

- `0` — No alerts, or webhook delivered successfully.
- `1` — Webhook request failed (HTTP error or connection error).

## Integration Example

Add to `build_parser` in `cli.py`:

```python
from pipewatch.cli_webhook import add_webhook_subcommand

def build_parser():
    parser = argparse.ArgumentParser(prog="pipewatch")
    sub = parser.add_subparsers(dest="command")
    # ... existing subcommands ...
    add_webhook_subcommand(sub)
    return parser
```

## Notes

- If there are no active alerts, the webhook is **not** called and exit code is `0`.
- Use `--no-source` / `--no-tags` to reduce payload size when the receiver does not need those fields.
- The `WebhookConfig` dataclass can be imported directly for programmatic use.

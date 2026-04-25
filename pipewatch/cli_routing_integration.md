# Alert Routing Integration

The `route` subcommand lets you direct alerts to named channels based on
source, status, or tag rules. Rules are evaluated in order; the first match
wins. Unmatched alerts fall through to `--default-channel`.

## Routing rules file

Create a `routing_rules.json` file:

```json
[
  {"channel": "pagerduty", "sources": ["payments"], "statuses": ["critical"], "tags": []},
  {"channel": "slack-ops",  "sources": [],           "statuses": ["critical"], "tags": []},
  {"channel": "slack-dev",  "sources": [],           "statuses": ["warning"],  "tags": []}
]
```

Each rule supports:

| Field      | Type         | Description                                      |
|------------|--------------|--------------------------------------------------|
| `channel`  | string       | Destination channel name                         |
| `sources`  | list[string] | Match only these sources (empty = all)           |
| `statuses` | list[string] | `"warning"` / `"critical"` (empty = all)         |
| `tags`     | list[string] | All listed tags must be present (empty = all)    |

## CLI usage

```bash
# Use default rules file and default channel
pipewatch route

# Custom rules file
pipewatch route --rules /etc/pipewatch/routes.json

# Override fallback channel
pipewatch route --default-channel email-oncall
```

## Integration with build_parser

```python
from pipewatch.cli_routing import add_routing_subcommand

def build_parser():
    parser = ArgumentParser(prog="pipewatch")
    sub = parser.add_subparsers(dest="subcommand")
    # ... other subcommands ...
    add_routing_subcommand(sub)
    return parser
```

## Exit codes

| Code | Meaning                        |
|------|--------------------------------|
| `0`  | No alerts generated            |
| `1`  | One or more alerts were routed |

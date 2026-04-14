# pipewatch

A lightweight CLI for monitoring and alerting on data pipeline health metrics across multiple sources.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install -e .
```

---

## Usage

Monitor a pipeline by pointing pipewatch at a config file that defines your sources and alert thresholds:

```bash
pipewatch monitor --config pipelines.yaml
```

**Example `pipelines.yaml`:**

```yaml
pipelines:
  - name: orders_etl
    source: postgres
    connection: $DATABASE_URL
    checks:
      - metric: row_count
        threshold: "> 0"
      - metric: freshness
        max_age_minutes: 60

alerts:
  slack_webhook: $SLACK_WEBHOOK_URL
```

Run a one-time health check and print results to stdout:

```bash
pipewatch check --pipeline orders_etl --config pipelines.yaml
```

List all monitored pipelines and their last known status:

```bash
pipewatch status
```

---

## License

MIT © 2024 [Your Name](https://github.com/yourname)
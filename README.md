# Anthropic Model Monitoring on GCP (Vertex AI + Cloud Observability)

Repeatable, version-controllable Cloud Monitoring dashboards for Anthropic Claude
models served through **Vertex AI Model Garden**, deployed with a single script.

```
model-monitoring/
├── deploy.sh                  # idempotent deployment script
├── README.md                  # this file
└── dashboards/
    ├── 00-anthropic-model-usage.json       # at-a-glance usage summary
    ├── 01-fable5-token-usage.json          # Claude Fable 5 — daily token usage
    ├── 02-anthropic-fleet-overview.json    # all Anthropic models — usage overview
    ├── 03-anthropic-latency-performance.json
    ├── 04-anthropic-errors-reliability.json
    ├── 05-anthropic-caching-efficiency.json
    └── 06-anthropic-capacity-quota.json
```

---

## Quick start

```sh
cd model-monitoring
./deploy.sh                      # deploy/update ALL dashboards in current project
./deploy.sh -p my-project-id     # target a specific project
./deploy.sh -d dashboards/01-fable5-token-usage.json   # deploy a single dashboard
./deploy.sh --list               # show what's currently deployed
```

The script is **idempotent**: dashboards are matched by `displayName`. If one
already exists it is updated in place (preserving its URL and any links you've
shared); otherwise it is created. Run it as often as you like — from your
laptop, CI, or a cron job.

**Requirements**

- `gcloud` authenticated (`gcloud auth login`), `python3` on PATH
- IAM: `roles/monitoring.editor` on the target project
- Traffic to an Anthropic model via Vertex AI (metrics appear only after the
  first requests are served)

---

## How the metrics work

All dashboards are built on Vertex AI's **publisher model** metrics, emitted
automatically for partner models (no agent or instrumentation needed):

| Metric (`aiplatform.googleapis.com/publisher/online_serving/…`) | Kind | What it measures |
|---|---|---|
| `token_count` | DELTA | Tokens consumed, broken down by the `type` label |
| `model_invocation_count` | DELTA | Request count, with `response_code`, `method`, `error_category`, token-size buckets |
| `model_invocation_latencies` | DISTRIBUTION | End-to-end request latency (ms) |
| `first_token_latencies` | DISTRIBUTION | Time-to-first-token for streaming (ms) |
| `consumed_throughput` / `consumed_token_throughput` | DELTA | Throughput consumption (provisioned-throughput accounting) |

**Monitored resource:** `aiplatform.googleapis.com/PublisherModel` with labels:

- `publisher` = `anthropic`
- `model_user_id` = the model ID, e.g. **`claude-fable-5`** (verified in this
  project — note there is *no* `@default` suffix here; the version is a separate
  `model_version_id` label)
- `location` = region serving the request (`global` for the global endpoint)

**Token `type` label values** observed for Anthropic models:

| `type` | Meaning | Billing relevance |
|---|---|---|
| `input` | Uncached prompt tokens | Full input price |
| `output` | Generated tokens | Output price (highest per-token cost) |
| `cache_read_input` | Prompt tokens served from prompt cache | ~0.1× input price |
| `cache_write_input` | Tokens written to cache (5-min TTL) | ~1.25× input price |
| `cache_write_1h_input` | Tokens written to cache (1-hour TTL) | ~2× input price |

This is why the dashboards always group by `type` — "total tokens" alone hides
the cost structure entirely.

### Verifying labels in a new project

Before pointing these dashboards at another project, confirm what
`model_user_id` values it emits:

```sh
gcloud monitoring metrics-descriptors list \
  --filter='metric.type=starts_with("aiplatform.googleapis.com/publisher")' 2>/dev/null

# Or look at live series (Metrics Explorer → Vertex AI Publisher Model → Token count)
```

If your project uses versioned IDs (e.g. `claude-fable-5@<version>`), change the
exact-match filters in the JSONs to the regex form:
`resource.label."model_user_id"=monitoring.regex.full_match("claude-fable-5.*")`.

---

## The dashboards

### 00 — Anthropic: Model Usage (at-a-glance summary)
A compact landing page: four scorecards (total tokens, requests, output tokens,
errors — last 24h) plus daily tokens by model, daily tokens by type, and an
hourly usage line. Start here; drill into dashboards 01–06 for detail.

### 01 — Claude Fable 5: Daily Token Usage
The original ask: **total tokens consumed per day for one model**
(`claude-fable-5`).
- Stacked daily bars by token type (input / output / cache read / cache writes)
- Scorecards: total, output-only, and input-only tokens over the last 24h
- Hourly token-rate line chart to spot intraday spikes

*Use for:* daily consumption tracking, budget conversations, spotting runaway
workloads. To clone it for a different model, copy the JSON, change
`displayName` and the `model_user_id` filter.

### 02 — Anthropic Fleet Overview
Everything Anthropic in one place — filters on `publisher="anthropic"` only, so
**new Claude models appear automatically** with zero dashboard changes.
- Daily tokens by model and daily requests by model
- Hourly token rate by model
- Input vs output mix across the fleet
- Consumed throughput by model

*Use for:* comparing model adoption (e.g. how much traffic moved from Opus to
Fable 5), capacity planning, the single bookmark for "how much Claude are we
using?".

### 03 — Latency & Performance
- **Time-to-first-token** p50 / p95 by model — the metric your users actually
  feel in streaming UIs
- **End-to-end latency** p50 / p99 by model — long-tail watching; reasoning
  models can legitimately run minutes on hard tasks, so watch the trend, not
  the absolute number
- Latency distribution heatmap

*Use for:* regression detection after a model swap, validating that
effort/thinking changes had the intended latency effect, SLO discussions.

### 04 — Errors & Reliability
- Requests by response code, errors by `error_category` + code
- Scorecards: successful, failed, and **429-throttled** requests (last 24h)
- Hourly error rate per model

*Use for:* incident triage ("is it us or the platform?"), quota-pressure
detection (429s rising = you're hitting rate limits — request a quota increase
or add backoff), watching 4xx after client deployments.

### 05 — Prompt Caching & Cost Efficiency
Caching is the single biggest cost lever for Claude workloads (cache reads cost
~10% of normal input tokens).
- Daily input-side breakdown: uncached input vs cache read vs cache writes
- Scorecards: cache-read (cheap) vs uncached (full-price) tokens, last 24h
- Cache-hit-ratio proxy: cache_read vs input lines — if the read line isn't
  well above the input line for a chat/agent workload, caching is broken
  (a timestamp in the system prompt, unstable tool ordering, etc.)
- Requests split by `explicit_caching`

*Use for:* verifying `cache_control` actually works after deployments,
quantifying savings, catching silent cache invalidation regressions.

### 06 — Capacity, Quota & Request Shape
- Requests by `request_type` / `shared_request_type` (on-demand vs provisioned)
- Request-shape histograms: input and output token-size buckets — catches
  context-bloat ("why are all requests suddenly in the 100k+ bucket?")
- Consumed token throughput by model
- Requests by API method (`rawPredict` vs `streamRawPredict` — i.e. how much
  traffic streams)

*Use for:* provisioned-throughput sizing, detecting context-window bloat,
confirming streaming adoption.

---

## Alerting (recommended next step)

Dashboards show you the past; alerts catch problems live. Suggested policies
(create under **Monitoring → Alerting**, same filters as the dashboards):

| Alert | Condition (suggested starting point) |
|---|---|
| Daily token budget | `token_count` (model=claude-fable-5) SUM over 1d > your budget |
| Error spike | non-200 `model_invocation_count` SUM over 5m > 10 |
| Throttling | `response_code=429` count > 0 over 15m |
| Latency regression | `model_invocation_latencies` p95 over 10m > 2× normal |
| Cache regression | `cache_read_input` tokens drop to ~0 while `input` stays high |

Example budget alert via gcloud:

```sh
gcloud alpha monitoring policies create \
  --display-name="Fable 5 daily token budget" \
  --condition-display-name="tokens/day > 50M" \
  --condition-filter='metric.type="aiplatform.googleapis.com/publisher/online_serving/token_count" resource.type="aiplatform.googleapis.com/PublisherModel" resource.label."model_user_id"="claude-fable-5"' \
  --condition-threshold-value=50000000 \
  --condition-threshold-duration=0s \
  --aggregation='{"alignmentPeriod":"86400s","perSeriesAligner":"ALIGN_SUM","crossSeriesReducer":"REDUCE_SUM"}' \
  --combiner=OR \
  --notification-channels=CHANNEL_ID
```

---

## Caveats & gotchas

1. **Scope:** these metrics cover Vertex AI traffic only. Usage via the
   first-party Anthropic API does not appear here (track that in the Anthropic
   Console).
2. **Tokens ≠ dollars.** `token_count` mixes token types with very different
   prices (see the type table above). For actual spend use
   **Billing → Reports** filtered to Vertex AI Anthropic SKUs; use dashboard 05
   to understand the *structure* of the cost.
3. **DELTA metrics + daily alignment:** daily totals are aligned to the query
   window, not calendar midnight. Good for trends and budgets; for exact
   calendar-day accounting export to BigQuery via a Monitoring metrics export.
4. **Metric latency:** points can lag ~3–4 minutes behind real traffic. Zeros
   for the most recent minutes are normal.
5. **Empty charts** usually mean a label mismatch — re-run the label
   verification above, or no traffic of that kind (e.g. no provisioned
   throughput → throughput charts stay empty).
6. **Updating dashboards:** edit the JSON and re-run `./deploy.sh`. Avoid
   hand-editing in the Console if you want this folder to remain the source of
   truth (Console edits are overwritten on the next deploy).

---

## Adding a new dashboard

1. Copy an existing JSON in `dashboards/` as a starting point.
2. Give it a **unique `displayName`** (this is the idempotency key).
3. Adjust filters/widgets. Reference: [Dashboard API](https://cloud.google.com/monitoring/api/ref_v3/rest/v1/projects.dashboards).
4. Run `./deploy.sh -d dashboards/your-new-file.json` to test it alone, then
   `./deploy.sh` to deploy everything.

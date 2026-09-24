# Architecture, Metric Schema & FinOps/SRE Playbook

Detailed reference companion to [README.md](../README.md) for the Anthropic Model Monitoring on Vertex AI dashboard suite.

---

## 1. Vertex AI PublisherModel Telemetry Schema & Query Engine

> **MQL Deprecation Compliance ([docs](https://docs.cloud.google.com/stackdriver/docs/deprecations/mql)):** Per Google Cloud Observability guidelines (support for MQL ended July 22, 2025), **zero dashboards in this repository use `timeSeriesQueryLanguage` (MQL)**. All scorecards, ratios, percentiles, and tables use native **`timeSeriesFilter`**, **`timeSeriesFilterRatio`**, and **[PromQL](https://cloud.google.com/monitoring/promql)**-compatible aggregations.

All dashboards query native [Vertex AI metrics](https://cloud.google.com/vertex-ai/docs/general/monitoring-metrics) emitted under `aiplatform.googleapis.com/PublisherModel` (`publisher="anthropic"`):

| Metric (`aiplatform.googleapis.com/publisher/online_serving/…`) | Kind | Key Labels | Official Docs |
|---|---|---|---|
| `token_count` | `DELTA` | `type`, `model_user_id`, `location`, `explicit_caching` | [Vertex AI Metrics](https://cloud.google.com/vertex-ai/docs/general/monitoring-metrics) |
| `model_invocation_count` | `DELTA` | `response_code`, `method`, `error_category`, `input_token_size_bucket` | [Claude on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude) |
| `model_invocation_latencies` | `DISTRIBUTION` | `model_user_id`, `location`, `method` | [Cloud Monitoring Distributions](https://cloud.google.com/monitoring/api/v3/distribution-metrics) |
| `first_token_latencies` | `DISTRIBUTION` | `model_user_id`, `location` | [Streaming Claude](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude#stream) |
| `consumed_throughput` / `consumed_token_throughput` | `DELTA` | `model_user_id`, `location` | [Provisioned Throughput (PTU)](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/overview) |

---

## 2. Prompt Caching FinOps Break-Even Math

Reference: [Anthropic Prompt Caching on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude-prompt-caching)

| Token `type` Label | Pricing Multiplier | Break-Even Threshold (`cache_read / cache_write`) | Remediation if Below Break-Even |
|---|---|---|---|
| `input` | `1.00×` | Baseline (uncached prompt tokens) | Add `cache_control` breakpoints on static prefixes (`>1,024` tokens) |
| `cache_read_input` | `0.10×` | **90% discount** on cached prefix hits | Target **Cache Hit Ratio ≥ 80%** |
| `cache_write_input` (5m TTL) | `1.25×` | **`> 0.28` subsequent reads** (`1.28×` total hits) | Strip dynamic timestamps/UUIDs from system prompts |
| `cache_write_1h_input` (1h TTL) | `2.00×` | **`> 1.11` subsequent reads** (`2.11×` total hits) | Downgrade to 5m TTL if session turns occur >60m apart |
| `output` | Output tier | N/A (generation & reasoning tokens) | Cap `max_tokens` / `thinking.budget_tokens` on `Claude Opus x` / `Claude Fable x` |

---

## 3. SRE Latency & Error Triage Rules

| Signal | Dashboard | Threshold / Symptom | Actionable Triage |
|---|---|---|---|
| **TTFT `p95` > 1,000 ms** | [03 — Latency](../dashboards/03-anthropic-latency-performance.json) | `first_token_latencies` spike | Cold-start or uncached prefill bottleneck; check cache hit rate in [05 — Caching](../dashboards/05-anthropic-caching-efficiency.json) |
| **E2E `p99` > 15s (TTFT < 1s)** | [03 — Latency](../dashboards/03-anthropic-latency-performance.json) | Normal on `Claude Opus x` / `Claude Fable x` | Extended reasoning output; alert on **TTFT `p95`**, not raw `E2E` |
| **HTTP `429` Spike** | [04 — Errors](../dashboards/04-anthropic-errors-reliability.json) | Regional burst quota exhaustion | Route overflow traffic to `global` endpoint or increase [PTU commitment](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/overview) |

---

## 4. Version Lineage (`v1.0.0` → `v3.0.0`)

| Version Directory | Git Tag | Architectural Delta |
|---|---|---|
| [`dashboards/versions/v1.0-original/`](../dashboards/versions/v1.0-original/) | `v1.0.0` | Baseline stacked bar/line charts (`00`–`06`). |
| [`dashboards/versions/v2.0-old/`](../dashboards/versions/v2.0-old/) | `v2.0.0` | Dark header banners, sparklines, single `model_user_id` filter. |
| [`dashboards/versions/v3.1-iter1/`](../dashboards/versions/v3.1-iter1/) | *(Iter 1)* | Multi-dimensional `dashboardFilters` (`location`, `method`, `response_code`) + `timeSeriesFilterRatio` scorecards. |
| [`dashboards/versions/v3.2-iter2/`](../dashboards/versions/v3.2-iter2/) | *(Iter 2)* | Proportional `pieChart` (`DONUT`) shares + Dual-Axis (`Y1`/`Y2`) correlation charts + unified `p50`/`p95`/`p99` SLO curves. |
| [`dashboards/versions/v3.3-final/`](../dashboards/versions/v3.3-final/) | `v3.0.0` | Live `timeSeriesTable` leaderboards (`metricVisualization: "BAR"`) + embedded FinOps/SRE playbooks. |

# Anthropic Model Monitoring on GCP (Vertex AI + Cloud Observability)

![Anthropic Model Observability & FinOps Executive Infographic](images/twg-exec-hero-infographic.png)

## Executive Statement

Zero-instrumentation **FinOps, SRE, and Capacity control plane** for Anthropic models (**`Claude Opus x`**, **`Claude Fable x`**, **`Claude Sonnet x`**, **`Claude Haiku x`**) on [Vertex AI Model Garden](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude), built on native [`PublisherModel` telemetry](https://cloud.google.com/vertex-ai/docs/general/monitoring-metrics) and deployed via a single idempotent command (`./deploy.sh`).

| Operational Blind Spot | Risk if Unmonitored | How This Suite Solves It | Dashboard & Reference Docs |
|---|---|---|---|
| **Silent Prompt Cache Invalidation (FinOps)** | Dynamic prompt prefixes trigger `1.25×` (5m) or `2.00×` (1h) cache write penalties with zero reads — **doubling input spend** instead of saving 90%. | Real-time **Cache Hit Ratio %** and **Read-to-Write Break-Even** scorecards (`>1.28×` for 5m TTL, `>2.11×` for 1h TTL). | [05 — Caching](dashboards/05-anthropic-caching-efficiency.json) · [FinOps Math](docs/ARCHITECTURE_AND_PLAYBOOK.md#2-prompt-caching-finops-break-even-math) · [GCP Caching Docs](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude-prompt-caching) |
| **Reasoning Tail Latency vs. Cold Starts (SRE)** | Extended thinking chains (`Claude Opus x` / `Claude Fable x`) take `15s–45s` `E2E` while `TTFT` stays `<1s`, causing false-positive latency paging. | Decouples **TTFT (`p50`/`p95`)** prefill latency from **E2E (`p50`/`p95`/`p99`)** generation tails via bimodal heatmaps & SLO lines. | [03 — Latency](dashboards/03-anthropic-latency-performance.json) · [SRE Playbook](docs/ARCHITECTURE_AND_PLAYBOOK.md#3-sre-latency--error-triage-rules) · [Streaming Docs](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude#stream) |
| **Regional `HTTP 429` & PTU Skew (Capacity)** | Multi-region traffic spikes exhaust burst quotas (`429`) or under-utilize [Provisioned Throughput (`PTU`)](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/overview). | Dual-Axis **Demand vs. `429` Throttling** overlays, regional Donut shares, and prompt size bucket histograms. | [04 — Errors](dashboards/04-anthropic-errors-reliability.json) · [06 — Capacity](dashboards/06-anthropic-capacity-quota.json) · [PTU Docs](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/overview) |

---

## Architecture & Triage Flow

![Anthropic Model Observability Architecture on Vertex AI](images/twg-telemetry-architecture.png)

![FinOps and SRE Automated Triage Decision Workflow](images/twg-finops-sre-decision-flow.png)

> **Deep-Dive Documentation:** See **[Architecture, Metric Schema & FinOps/SRE Playbook (`docs/ARCHITECTURE_AND_PLAYBOOK.md`)](docs/ARCHITECTURE_AND_PLAYBOOK.md)** for full MQL formulas, pricing multipliers, and version lineage (`v1.0.0` → `v3.0.0`).

---

## Quick Start

```sh
./deploy.sh                                  # Deploy latest (v3.3-final) to active gcloud project
./deploy.sh -c argolis-project --both        # Deploy [v2.0 Old] + v3.3-final side-by-side
./deploy.sh --version old                    # Deploy preserved v2.0-old (or v1.0, v3.1, v3.2, new)
./deploy.sh --validate                       # Validate all 42 JSON dashboards (0 tile overlaps)
```

---

## Dashboard Catalog (`v3.3-final`)

| # | Dashboard JSON | Primary Audience | Key Widgets (`Donut`, `Dual-Axis`, `Table`, `Ratio`) | Live GCP Console (`sa-learning-1`) |
|---|---|---|---|---|
| **00** | [`00-anthropic-model-usage.json`](dashboards/00-anthropic-model-usage.json) | Exec / FinOps | 6 Ratio Scorecards · 3 Share Donuts · Volume vs. Error Dual-Axis · Live Leaderboard | [Open `00` (`v3.3`)](https://console.cloud.google.com/monitoring/dashboards/builder/494f39e1-954a-4dd5-8451-fd3908ad5c09?project=sa-learning-1&duration=P30D) · [[v2.0 Old]](https://console.cloud.google.com/monitoring/dashboards/builder/d105114d-9bad-4995-81e0-3119eeea5e13?project=sa-learning-1&duration=P30D) |
| **01** | [`01-fable5-token-usage.json`](dashboards/01-fable5-token-usage.json) | AI Eng (`Opus x` / `Fable x`) | Cache Hit Ratio % · Token Volume vs. `p95` Latency Dual-Axis · Regional Table | [Open `01` (`v3.3`)](https://console.cloud.google.com/monitoring/dashboards/builder/64a5328f-902f-4ee5-a9ee-a18ffef20cdd?project=sa-learning-1&duration=P30D) · [[v2.0 Old]](https://console.cloud.google.com/monitoring/dashboards/builder/82ab9e73-ae0e-4ef6-bb0c-8ecf20e6cb60?project=sa-learning-1&duration=P30D) |
| **02** | [`02-anthropic-fleet-overview.json`](dashboards/02-anthropic-fleet-overview.json) | Platform / Fleet Leads | **Token Share vs. Request Share Donuts** · Multi-Model PTU & Invocation Matrix | [Open `02` (`v3.3`)](https://console.cloud.google.com/monitoring/dashboards/builder/6d36a847-54e0-4d18-b6e1-698ae75410ad?project=sa-learning-1&duration=P30D) · [[v2.0 Old]](https://console.cloud.google.com/monitoring/dashboards/builder/abdd1b99-c407-4994-a1ee-f238403829d0?project=sa-learning-1&duration=P30D) |
| **03** | [`03-anthropic-latency-performance.json`](dashboards/03-anthropic-latency-performance.json) | SRE / Performance | Unified `p50`/`p95`/`p99` Curves + SLO Lines · **Dual TTFT & E2E Heatmaps** | [Open `03` (`v3.3`)](https://console.cloud.google.com/monitoring/dashboards/builder/d3df09ad-ad8e-4995-b37a-607c70abe68d?project=sa-learning-1&duration=P30D) · [[v2.0 Old]](https://console.cloud.google.com/monitoring/dashboards/builder/4c432e57-a408-45fa-884c-fc44088103ad?project=sa-learning-1&duration=P30D) |
| **04** | [`04-anthropic-errors-reliability.json`](dashboards/04-anthropic-errors-reliability.json) | SRE / On-Call | True Error & `429` Ratios · Regional `429` Donut · Traffic vs. `429` Dual-Axis | [Open `04` (`v3.3`)](https://console.cloud.google.com/monitoring/dashboards/builder/a2a32f88-77ac-433a-a6de-c265503d13c1?project=sa-learning-1&duration=P30D) · [[v2.0 Old]](https://console.cloud.google.com/monitoring/dashboards/builder/6da26801-7092-44b1-a8ae-d4f685974958?project=sa-learning-1&duration=P30D) |
| **05** | [`05-anthropic-caching-efficiency.json`](dashboards/05-anthropic-caching-efficiency.json) | FinOps / Prompt Eng | **True Cache Hit %** · **Read/Write Break-Even Ratio** · Pricing Tier Donuts | [Open `05` (`v3.3`)](https://console.cloud.google.com/monitoring/dashboards/builder/2947cbef-4e26-4df1-93ad-fee37ea9c18e?project=sa-learning-1&duration=P30D) · [[v2.0 Old]](https://console.cloud.google.com/monitoring/dashboards/builder/d6d457e6-f1a6-42e3-b624-f8176bc229de?project=sa-learning-1&duration=P30D) |
| **06** | [`06-anthropic-capacity-quota.json`](dashboards/06-anthropic-capacity-quota.json) | Capacity / Infra | Input/Output Prompt Size Donuts · Shared PayGo vs. PTU Routing · Quota Table | [Open `06` (`v3.3`)](https://console.cloud.google.com/monitoring/dashboards/builder/5fd86181-f1f5-4335-859e-11e613f7b158?project=sa-learning-1&duration=P30D) · [[v2.0 Old]](https://console.cloud.google.com/monitoring/dashboards/builder/fde8d3b7-625b-45e2-b3ee-7c701c5b124b?project=sa-learning-1&duration=P30D) |

---

## Verified 30-Day Telemetry Snapshot (`sa-learning-1`)

| Model Family (`model_user_id`) | `location` | Token `type` | 30-Day Volume | FinOps / SRE Benchmark |
|---|---|---|---:|---|
| **`claude-opus-x` / `claude-fable-x`** | `global` | `cache_read_input` | **39,115,765** | **94.9% Cache Hit Ratio** (`0.10×` cost tier) |
| **`claude-opus-x` / `claude-fable-x`** | `global` | `input` (uncached) | **2,113,023** | **24.6× Read-to-Write Ratio** (vs. `1.28×` 5m break-even) |
| **`claude-opus-x` / `claude-fable-x`** | `global` | `cache_write_input` (5m / 1h) | **2,062,295** | `1,588,561` (5m TTL) + `473,734` (1h TTL) |
| **`claude-opus-x` / `claude-fable-x`** | `global` | `output` | **548,924** | Reasoning + completion tokens |
| **`claude-sonnet-x`** / **`count-tokens`** | `global` | `input` / `output` | **379,508** | Lightweight eval & token-counting API calls |

---

## Cloud Monitoring Screenshots

| Executive Scorecards & Usage (`00`) | Fleet Overview (`02`) | Prompt Caching & FinOps (`05`) |
|---|---|---|
| ![Model Usage](images/model-usage-scorecards.png) | ![Fleet Overview](images/fleet-overview-daily-volume.png) | ![Caching Efficiency](images/caching-cost-efficiency.png) |

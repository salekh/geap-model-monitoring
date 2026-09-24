# Anthropic Model Monitoring on GCP (Vertex AI + Cloud Observability)

![Anthropic Model Observability & FinOps Executive Infographic](images/twg-exec-hero-infographic.png)

## Executive Summary: What Problem Is Being Solved?

Enterprise teams deploying Anthropic Claude models (**`Claude Opus x`**, **`Claude Fable x`**, **`Claude Sonnet x`**, **`Claude Haiku x`**) through **Google Cloud Vertex AI Model Garden** face three operational and financial blind spots out of the box:

1. **Unattributed Token Spend & Silent Prompt Cache Regressions (FinOps)**:
   Anthropic prompt caching reduces input token cost by **90%** (`0.10×` base input price for `cache_read_input`), but populating the cache carries a **`1.25×` (5-minute TTL)** or **`2.00×` (1-hour TTL)** write premium. If a dynamic timestamp, request UUID, or unsorted tool definition is injected near the top of a system prompt, cache writes occur on every turn with zero subsequent reads — **silently doubling (`2.00×`) input token spend instead of saving 90%**. Without real-time tracking of the **True Cache Hit Ratio** and **Cache Read-to-Write Break-Even Ratio** (`>1.28×` reads/write for 5m TTL; `>2.11×` reads/write for 1h TTL), FinOps teams only discover cache invalidation on their monthly invoice.
2. **Reasoning Tail Latency vs. Upstream Cold-Start Degradation (SRE Performance)**:
   Deep-reasoning models (**`Claude Opus x` / `Claude Fable x`**) generate extended chain-of-thought token sequences that naturally extend End-to-End (`E2E`) invocation duration to `15s–45s` on complex tasks while Time-to-First-Token (`TTFT`) remains sub-second (`<1,000 ms`). Traditional single-latency dashboards conflate expected reasoning generation time with upstream prefill bottlenecks or cold-start regressions, triggering false-positive paging alerts.
3. **Regional Quota Exhaustion (`HTTP 429`) & Provisioned Throughput (`PTU`) Skew (Capacity Planning)**:
   Multi-region deployments (`global`, `us-central1`, `europe-west1`) routing across shared Pay-as-You-Go (`PayGo`) endpoints and Provisioned Throughput (`PTU`) reservations suffer localized `HTTP 429` burst throttling and context-window bloat when traffic spikes or prompt size distributions shift intraday.

### How This Suite Solves It

**`geap-model-monitoring`** provides a **zero-instrumentation, version-controlled observability and FinOps control plane** built directly on Vertex AI's native `aiplatform.googleapis.com/PublisherModel` telemetry. With a single idempotent command (`./deploy.sh`), it deploys **7 specialized Google Cloud Monitoring dashboards** featuring:
- **Normalized Server-Side Ratio Scorecards (`timeSeriesFilterRatio`)**: Real-time **Error Rate %**, **HTTP 429 Throttle %**, **True Cache Hit Ratio %**, **Cache Read-to-Write Break-Even Ratio**, and **Avg Tokens / Request**.
- **Proportional Donut (`pieChart`) & Dual-Axis (`Y1`/`Y2`) Correlation Views**: Side-by-side Token Share vs. Request Share Donuts, plus Dual-Axis overlays correlating request demand directly against `HTTP 429` throttling, `p95` latency, and cache write overhead.
- **Bimodal `TTFT` vs. `E2E` Latency Decomposition**: Unified multi-percentile (`p50`, `p95`, `p99`) curves with horizontal SLO target lines and dual distribution heatmaps (`first_token_latencies` vs. `model_invocation_latencies`).
- **Live Tabular Leaderboards (`timeSeriesTable`) & Embedded Playbooks**: Sortable per-model, per-region leaderboards with inline progress bars (`metricVisualization: "BAR"`) paired with FinOps and SRE remediation playbooks.

---

## System Architecture & Automated Triage Workflow

![Anthropic Model Observability Architecture on Vertex AI](images/twg-telemetry-architecture.png)

### FinOps & SRE Signal Decomposition Flow

![FinOps and SRE Automated Triage Decision Workflow](images/twg-finops-sre-decision-flow.png)

---

## Repository Structure

![Model Usage Dashboard — Cloud Monitoring scorecards, daily token consumption by model and type, and invocation breakdown](images/model-usage-scorecards.png)

```
geap-model-monitoring/
├── deploy.sh                        # idempotent multi-version & side-by-side deployment script
├── README.md                        # executive architecture, FinOps math & SRE playbooks
├── scripts/
│   ├── validate_dashboards.py       # 48-column mosaic overlap & schema validator
│   ├── build_v3_1_iter1.py          # Recursive Self-Improvement Iteration 1 builder
│   ├── build_v3_2_iter2.py          # Recursive Self-Improvement Iteration 2 builder
│   └── build_v3_3_final.py          # Recursive Self-Improvement Iteration 3 builder
├── images/                          # architecture diagrams, infographics & Cloud Monitoring screenshots
│   ├── twg-exec-hero-infographic.png
│   ├── twg-telemetry-architecture.png
│   ├── twg-finops-sre-decision-flow.png
│   ├── model-usage-scorecards.png
│   ├── fleet-overview-daily-volume.png
│   ├── caching-cost-efficiency.png
│   └── versions/
│       └── v2.0-old/                # preserved historical v2.0 screenshots
└── dashboards/                      # latest v3.3-final JSON dashboards (default deploy target)
    ├── 00-anthropic-model-usage.json
    ├── 01-fable5-token-usage.json
    ├── 02-anthropic-fleet-overview.json
    ├── 03-anthropic-latency-performance.json
    ├── 04-anthropic-errors-reliability.json
    ├── 05-anthropic-caching-efficiency.json
    ├── 06-anthropic-capacity-quota.json
    └── versions/                    # preserved historical & recursive iteration versions
        ├── v1.0-original/           # Initial baseline (commit 21d0a75 / git tag v1.0.0)
        ├── v2.0-old/                # Previous baseline (commit 5ddb648 / git tag v2.0.0 & old)
        ├── v3.1-iter1/              # Iter 1: Multi-dimensional filters + Ratio scorecards
        ├── v3.2-iter2/              # Iter 2: Donut charts + Dual-Axis overlays + Dual Heatmaps
        └── v3.3-final/              # Iter 3: Tabular leaderboards (BAR) + FinOps/SRE Playbooks
```

---

## Quick start & Multi-Version Deployment

```sh
# Deploy latest (v3.3-final) dashboards to current active gcloud project
./deploy.sh

# Deploy using a specific gcloud configuration (e.g. nexus-project or argolis-project)
./deploy.sh -c nexus-project

# Deploy BOTH preserved Old ([v2.0 Old] ...) and New (v3.3-final) side-by-side in Cloud Monitoring!
./deploy.sh -c nexus-project --both

# Deploy a specific preserved historical or iterative version
./deploy.sh --version old            # deploys v2.0-old
./deploy.sh --version v1.0           # deploys v1.0-original
./deploy.sh --version v3.1           # deploys v3.1-iter1
./deploy.sh --version v3.2           # deploys v3.2-iter2
./deploy.sh --version new            # deploys v3.3-final (default)

# Validate all 42 dashboard JSON files across all versions (0 tile overlaps & strict API schema)
./deploy.sh --validate

# List currently deployed dashboards in target project
./deploy.sh -c nexus-project --list
```

The script is **idempotent**: dashboards are matched by `displayName`. When `--both` (`--side-by-side`) is passed, the script automatically prefixes the preserved old version with `[v2.0 Old] ` and tags its Cloud Monitoring `labels.version="v2-0-old"`, allowing **both the old and new versions to live side-by-side in the Google Cloud Console** without overwriting each other.

---

## Recursive Self-Improvement Lineage & Version Preservation

Every version of the dashboard suite is preserved across three independent layers:
1. **Git Tags**: `v1.0.0` (initial baseline), `v2.0.0` (previous visual baseline), `v3.0.0` (recursively self-improved release).
2. **Filesystem Directories**: `dashboards/versions/<version>/` and `images/versions/v2.0-old/`.
3. **Cloud Monitoring Resource Labels (`labels`)**: Every JSON embeds structured metadata tags (`"publisher": "anthropic"`, `"suite": "geap-model-monitoring"`, `"version": "v3-3-final"`).

| Directory Version | Git Tag | Key Self-Critique & Recursive Upgrades Implemented |
|---|---|---|
| **`v1.0-original`** | `v1.0.0` | Initial baseline 7 dashboards (`00`–`06`) with raw metric counts and basic stacked bar/line charts. |
| **`v2.0-old`** | `v2.0.0` | Added dark header banners, section headers, basic sparklines, and a single `model_user_id` filter (0 filters on Fable 5). |
| **`v3.1-iter1`** | *(Iter 1)* | **Critique:** Single-dimension filtering (`model_user_id`) hid regional 429 quota spikes and version regressions; raw count scorecards fluctuated with diurnal traffic.<br>**Upgrade:** Added multi-dimensional interactive `dashboardFilters` (`location`, `model_version_id`, `method`, `response_code`, `explicit_caching`) to all 7 dashboards; added native `timeSeriesFilterRatio` scorecards (**Error Rate %**, **Cache Hit Ratio %**, **Avg Tokens/Req**, **Streaming %**); added 24h Latency Scorecards to Dashboard 03. |
| **`v3.2-iter2`** | *(Iter 2)* | **Critique:** Stacked bars obscured proportional shares; siloed p50/p95 charts hid tail latency amplification; volume and errors lived on separate charts.<br>**Upgrade:** Added native `pieChart` (**Donut**) visualizations for instant proportional comprehension; added **Dual-Axis (`yAxis Y1` + `y2Axis Y2`)** overlay charts correlating request volume directly against errors, p95 latency, and cache writes; unified multi-percentile (**p50, p95, p99**) latency curves with horizontal SLO reference lines; added **TTFT Distribution Heatmap**. |
| **`v3.3-final`** | `v3.0.0` | **Critique:** Incident responders and FinOps engineers need exact sortable tabular numbers per model/region and mathematical break-even rules right next to charts.<br>**Upgrade:** Added live **Tabular Leaderboards (`timeSeriesTable` with `metricVisualization: "BAR"`)** to all 7 dashboards; embedded **FinOps Cache Break-Even Formulas** and **SRE Incident Triage Playbooks** directly in dashboard tiles. |

---

## How the metrics work

All dashboards are built on Vertex AI's **publisher model** metrics, emitted automatically for partner models (no agent or instrumentation needed):

| Metric (`aiplatform.googleapis.com/publisher/online_serving/…`) | Kind | What it measures |
|---|---|---|
| `token_count` | DELTA | Tokens consumed, broken down by the `type` label |
| `model_invocation_count` | DELTA | Request count, with `response_code`, `method`, `error_category`, token-size buckets |
| `model_invocation_latencies` | DISTRIBUTION | End-to-end request latency (ms) |
| `first_token_latencies` | DISTRIBUTION | Time-to-first-token for streaming (ms) |
| `consumed_throughput` / `consumed_token_throughput` | DELTA | Throughput consumption (provisioned-throughput accounting) |

**Monitored resource:** `aiplatform.googleapis.com/PublisherModel` with labels:
- `publisher` = `anthropic`
- `model_user_id` = the model ID, e.g. **`claude-opus-x`**, **`claude-fable-x`**, **`claude-sonnet-x`**, **`claude-haiku-x`**
- `location` = region serving the request (`global`, `us-central1`, `europe-west1`, etc.)
- `model_version_id` = specific model snapshot/version ID

**Token `type` label values & FinOps Economics:**

| `type` | Meaning | Relative Pricing | FinOps Break-Even Rule |
|---|---|---|---|
| `input` | Uncached prompt tokens | `1.00×` (Full price) | Baseline |
| `output` | Generated tokens | Output price (Highest) | Watch reasoning length on `Claude Opus x` / `Claude Fable x` |
| `cache_read_input` | Prompt tokens served from cache | `~0.10×` input price | **90% discount** |
| `cache_write_input` | Tokens written to cache (5-min TTL) | `~1.25×` input price | Break-even at **>0.28 subsequent reads** (1.28 total hits) |
| `cache_write_1h_input` | Tokens written to cache (1-hour TTL) | `~2.00×` input price | Break-even at **>1.11 subsequent reads** (2.11 total hits) |

---

## The Dashboards (`v3.3-final`)

### 00 — Anthropic: Model Usage (Executive Command Center)
- **6 Executive Scorecards & Ratios (24h)**: Total tokens, Requests, **Avg Tokens / Request Ratio**, Output tokens, Non-200 Errors, and **Error Rate Ratio %**.
- **3 Proportional Donut Visualizations**: Token Share by Model, Token Share by Billing Type, and Request Share by GCP Region (`location`).
- **Dual-Axis Correlation Chart**: Hourly Request Volume (`Y1 Stacked Bar`) overlaid with Non-200 Error Spikes (`Y2 Line`).
- **Live Tabular Leaderboard (`timeSeriesTable`)**: Per-model & token type daily breakdown with inline visual progress bars (`metricVisualization: "BAR"`) + Executive Triage Playbook card.

### 01 — Claude Fable x / Opus x: Daily Token Usage & Performance
Dedicated deep-dive for **`claude-fable-x`** and **`claude-opus-x`** (`monitoring.regex.full_match("claude-(fable|opus)-.*")`):
- **Interactive Filters**: Filter dynamically by `location`, `model_version_id`, `api_method`, and `token_type`.
- **5 Scorecards & Ratios**: Total Fable/Opus tokens, Output tokens, Uncached input tokens, **Cache Hit Ratio %**, and **Avg Tokens / Request**.
- **3 Donut Charts**: Billing Type Share, Serving Region Share, and Streaming vs Batch API Split.
- **Dual-Axis Token vs Latency Correlation**: Hourly Token Generation (`Y1 Stacked Area`) overlaid with **End-to-End p95 Latency (`Y2 Line`)** to see how reasoning depth drives latency.
- **Regional Leaderboard Table**: Sortable token consumption across regions with inline bars.

### 02 — Anthropic Fleet Overview
Compare all active Anthropic models (`claude-opus-x`, `claude-fable-x`, `claude-sonnet-x`, `claude-haiku-x`) side-by-side:
- **Architectural Donut Comparison**: **Fleet Token Share by Model (Donut)** vs **Fleet Request Share by Model (Donut)** side-by-side — immediately highlights why a reasoning model with 31% of requests accounts for 58%+ of token volume.
- **Multi-Model Trends & PTU Utilization**: Daily stacked token/request bars and Provisioned Throughput consumption.
- **Fleet Leaderboard Matrix (`timeSeriesTable`)**: Token and invocation leaderboards grouped by Model, Region, and API Method.

![Fleet Overview — Cloud Monitoring daily token and invocation volume across Anthropic models](images/fleet-overview-daily-volume.png)

### 03 — Latency & Performance SLO Monitor
- **4 Latency Percentile Scorecards (24h)**: **TTFT p50**, **TTFT p95**, **End-to-End Latency p50**, and **End-to-End Latency p99** with color-coded warning and SLO breach thresholds.
- **Unified Multi-Percentile Spread Curves**: Overlays **p50, p95, and p99** on a single chart with horizontal **SLO Target Reference Lines** (`1,000 ms` for TTFT, `10,000 ms` for interactive E2E) to expose tail amplification.
- **Dual Distribution Heatmaps**: Side-by-side **TTFT Distribution Heatmap (`first_token_latencies`)** (revealing cached fast-path vs cold-start bimodal clusters) and **End-to-End Latency Heatmap (`model_invocation_latencies`)**.
- **Latency Leaderboard Table & SRE Guide**: Sortable p95 TTFT and p95 E2E latency by model and region.

### 04 — Errors, Throttling & Reliability Triage
- **5 Reliability Scorecards & Ratios**: Successful 200 OK count, Failed non-200 count, **True Error Rate Ratio %**, Throttled 429 count, and **429 Throttle Ratio %**.
- **3 Error Donut Visualizations**: Non-200 Errors by HTTP Response Code, Errors by Error Category, and **429 Throttling by GCP Region (`location`)**.
- **Dual-Axis Traffic Demand vs 429 Throttling**: Overlays Total Regional Request Demand (`Y1 Bar`) against 429 Quota Exhaustion (`Y2 Line`).
- **Incident Leaderboard Table & SRE Playbook**: Exact failure counts by Model, Region, and Response Code + HTTP error triage rules.

### 05 — Prompt Caching & FinOps Cost Efficiency
- **4 FinOps Scorecards & Ratios**: Cache Read Tokens (90% discount), Uncached Input Tokens (full price), **True Cache Hit Ratio %**, and **Cache Read-to-Write Ratio**.
- **3 Cost Structure Donuts**: Input Token Composition by Pricing Tier (`0.1x` vs `1.0x` vs `1.25x` vs `2.0x`), Cache Read Savings by Model, and Explicit Caching Adoption Share.
- **Dual-Axis Cache Read Savings (`Y1 Area`) vs Cache Write Overhead (`Y2 Line`)**: Ensures cache reads stay well above writes.
- **FinOps Break-Even Formula Card & Leaderboard Table**: Mathematical break-even thresholds (`>1.28` reads/write for 5m TTL, `>2.11` reads/write for 1h TTL) and silent cache invalidation diagnostics.

![Caching & Cost Efficiency — Cloud Monitoring dashboard showing cache read vs uncached input token volume and efficiency](images/caching-cost-efficiency.png)

### 06 — Capacity, Quota & Request Shape
- **4 Capacity Scorecards**: Total Requests, Consumed Token Throughput, Streaming Method Ratio %, and Avg Output Tokens / Request.
- **3 Context Window & Routing Donuts**: Input Prompt Size Bucket Share, Output Token Size Bucket Share, and Shared vs Provisioned Routing Share.
- **Context-Bloat Histograms & Leaderboard Table**: Intraday prompt size bucket shifts and per-model capacity matrix.

---

## Live GCP Deployments & Verified 30-Day Telemetry (`argolis-project` / `sa-learning-1`)

Both `v3.3-final` (7 dashboards) and preserved `[v2.0 Old]` (7 dashboards) are deployed side-by-side in:
- **`argolis-project` (`sa-learning-1`)**: `https://console.cloud.google.com/monitoring/dashboards?project=sa-learning-1`
- **`nexus-project` (`sa-nexus-gcp-4-sandbox-183936`)**: `https://console.cloud.google.com/monitoring/dashboards?project=sa-nexus-gcp-4-sandbox-183936`

### Direct Links (`sa-learning-1` — Last 30 Days `P30D`)

| Dashboard (`v3.3-final`) | Preserved `[v2.0 Old]` Counterpart |
|---|---|
| [Anthropic - Model Usage](https://console.cloud.google.com/monitoring/dashboards/builder/494f39e1-954a-4dd5-8451-fd3908ad5c09?project=sa-learning-1&duration=P30D) | [[v2.0 Old] Anthropic - Model Usage](https://console.cloud.google.com/monitoring/dashboards/builder/d105114d-9bad-4995-81e0-3119eeea5e13?project=sa-learning-1&duration=P30D) |
| [Claude Fable x / Opus x - Daily Token Usage](https://console.cloud.google.com/monitoring/dashboards/builder/64a5328f-902f-4ee5-a9ee-a18ffef20cdd?project=sa-learning-1&duration=P30D) | [[v2.0 Old] Claude Fable x / Opus x - Daily Token Usage](https://console.cloud.google.com/monitoring/dashboards/builder/82ab9e73-ae0e-4ef6-bb0c-8ecf20e6cb60?project=sa-learning-1&duration=P30D) |
| [Anthropic Models - Fleet Overview (All Models)](https://console.cloud.google.com/monitoring/dashboards/builder/6d36a847-54e0-4d18-b6e1-698ae75410ad?project=sa-learning-1&duration=P30D) | [[v2.0 Old] Anthropic Models - Fleet Overview (All Models)](https://console.cloud.google.com/monitoring/dashboards/builder/abdd1b99-c407-4994-a1ee-f238403829d0?project=sa-learning-1&duration=P30D) |
| [Anthropic Models - Latency & Performance](https://console.cloud.google.com/monitoring/dashboards/builder/d3df09ad-ad8e-4995-b37a-607c70abe68d?project=sa-learning-1&duration=P30D) | [[v2.0 Old] Anthropic Models - Latency & Performance](https://console.cloud.google.com/monitoring/dashboards/builder/4c432e57-a408-45fa-884c-fc44088103ad?project=sa-learning-1&duration=P30D) |
| [Anthropic Models - Errors & Reliability](https://console.cloud.google.com/monitoring/dashboards/builder/a2a32f88-77ac-433a-a6de-c265503d13c1?project=sa-learning-1&duration=P30D) | [[v2.0 Old] Anthropic Models - Errors & Reliability](https://console.cloud.google.com/monitoring/dashboards/builder/6da26801-7092-44b1-a8ae-d4f685974958?project=sa-learning-1&duration=P30D) |
| [Anthropic Models - Prompt Caching & Cost Efficiency](https://console.cloud.google.com/monitoring/dashboards/builder/2947cbef-4e26-4df1-93ad-fee37ea9c18e?project=sa-learning-1&duration=P30D) | [[v2.0 Old] Anthropic Models - Prompt Caching & Cost Efficiency](https://console.cloud.google.com/monitoring/dashboards/builder/d6d457e6-f1a6-42e3-b624-f8176bc229de?project=sa-learning-1&duration=P30D) |
| [Anthropic Models - Capacity, Quota & Request Shape](https://console.cloud.google.com/monitoring/dashboards/builder/5fd86181-f1f5-4335-859e-11e613f7b158?project=sa-learning-1&duration=P30D) | [[v2.0 Old] Anthropic Models - Capacity, Quota & Request Shape](https://console.cloud.google.com/monitoring/dashboards/builder/fde8d3b7-625b-45e2-b3ee-7c701c5b124b?project=sa-learning-1&duration=P30D) |

### Verified 30-Day Anthropic Telemetry Summary (`sa-learning-1`)

| Model Family (`model_user_id`) | `location` | Token `type` | 30-Day Token Count | Key FinOps / SRE Metric |
|---|---|---|---:|---|
| **`claude-opus-x` / `claude-fable-x`** | `global` | `cache_read_input` | **39,115,765** | **94.9% Cache Hit Ratio** (`cache_read / (cache_read + input)`) |
| **`claude-opus-x` / `claude-fable-x`** | `global` | `input` (uncached) | **2,113,023** | **24.6× Cache Read-to-Write Ratio** (well above `1.28×` 5m & `2.11×` 1h break-even) |
| **`claude-opus-x` / `claude-fable-x`** | `global` | `cache_write_input` (5m TTL) | **1,588,561** | Standard 5-minute TTL prompt cache population |
| **`claude-opus-x` / `claude-fable-x`** | `global` | `cache_write_1h_input` (1h TTL) | **473,734** | Extended 1-hour TTL prompt cache population |
| **`claude-opus-x` / `claude-fable-x`** | `global` | `output` | **548,924** | Total generated completion & reasoning tokens |
| **`claude-sonnet-x`** | `global` | `input` / `output` | **1,163** / **49** | Lightweight evaluation invocations |
| **`count-tokens`** | `global` | `input` | **378,296** | Pre-flight token counting API requests |

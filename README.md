# Anthropic Model Monitoring on GCP (Vertex AI + Cloud Observability)

![Model Usage Dashboard — v3.3-final executive view showing 64.8M tokens, normalized ratios, Donut shares, Dual-Axis Volume vs Error correlation, and Live Tabular Leaderboard](images/model-usage-scorecards.png)

Repeatable, version-controllable, and **recursively self-improved** Google Cloud Monitoring dashboards for Anthropic Claude models served through **Vertex AI Model Garden**, deployed with a single idempotent script.

```
geap-model-monitoring/
├── deploy.sh                        # idempotent multi-version & side-by-side deployment script
├── dashboard-studio.html            # standalone interactive HTML5 version explorer & incident simulator
├── README.md                        # documentation & FinOps/SRE playbooks
├── scripts/
│   ├── validate_dashboards.py       # 48-column mosaic overlap & schema validator
│   ├── generate_screenshots.py      # 2x Retina Cloud Monitoring UI screenshot renderer
│   ├── build_v3_1_iter1.py          # Recursive Self-Improvement Iteration 1 builder
│   ├── build_v3_2_iter2.py          # Recursive Self-Improvement Iteration 2 builder
│   └── build_v3_3_final.py          # Recursive Self-Improvement Iteration 3 builder
├── images/                          # latest v3.3-final dashboard screenshots
│   ├── model-usage-scorecards.png
│   ├── fleet-overview-daily-volume.png
│   ├── latency-performance-slos.png
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
1. **Git Tags**: `v1.0.0`, `v2.0.0`, `old`, `v3.1.0-iter1`, `v3.2.0-iter2`, `v3.3.0-final`, `v3.0.0`, `new`.
2. **Filesystem Directories**: `dashboards/versions/<version>/` and `images/versions/v2.0-old/`.
3. **Cloud Monitoring Resource Labels (`labels`)**: Every JSON embeds structured metadata tags (`"publisher": "anthropic"`, `"suite": "geap-model-monitoring"`, `"version": "v3-3-final"`).

| Version Tag | Key Self-Critique & Recursive Upgrades Implemented |
|---|---|
| **`v1.0-original`** (`v1.0.0`) | Initial baseline 7 dashboards (`00`–`06`) with raw metric counts and basic stacked bar/line charts. |
| **`v2.0-old`** (`v2.0.0` / `old`) | Added dark header banners, section headers, basic sparklines, and a single `model_user_id` filter (0 filters on Fable 5). |
| **`v3.1-iter1`** (`v3.1.0-iter1`) | **Critique:** Single-dimension filtering (`model_user_id`) hid regional 429 quota spikes and version regressions; raw count scorecards fluctuated with diurnal traffic.<br>**Upgrade:** Added multi-dimensional interactive `dashboardFilters` (`location`, `model_version_id`, `method`, `response_code`, `explicit_caching`) to all 7 dashboards; added native `timeSeriesFilterRatio` scorecards (**Error Rate %**, **Cache Hit Ratio %**, **Avg Tokens/Req**, **Streaming %**); added 24h Latency Scorecards to Dashboard 03. |
| **`v3.2-iter2`** (`v3.2.0-iter2`) | **Critique:** Stacked bars obscured proportional shares; siloed p50/p95 charts hid tail latency amplification; volume and errors lived on separate charts.<br>**Upgrade:** Added native `pieChart` (**Donut**) visualizations for instant proportional comprehension; added **Dual-Axis (`yAxis Y1` + `y2Axis Y2`)** overlay charts correlating request volume directly against errors, p95 latency, and cache writes; unified multi-percentile (**p50, p95, p99**) latency curves with horizontal SLO reference lines; added **TTFT Distribution Heatmap**. |
| **`v3.3-final`** (`v3.3.0-final` / `new`) | **Critique:** Incident responders and FinOps engineers need exact sortable tabular numbers per model/region and mathematical break-even rules right next to charts.<br>**Upgrade:** Added live **Tabular Leaderboards (`timeSeriesTable` with `metricVisualization: "BAR"`)** to all 7 dashboards; embedded **FinOps Cache Break-Even Formulas** and **SRE Incident Triage Playbooks** directly in dashboard tiles. |

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
- `model_user_id` = the model ID, e.g. **`claude-fable-5`**
- `location` = region serving the request (`global`, `us-central1`, `europe-west1`, etc.)
- `model_version_id` = specific model snapshot/version ID

**Token `type` label values & FinOps Economics:**

| `type` | Meaning | Relative Pricing | FinOps Break-Even Rule |
|---|---|---|---|
| `input` | Uncached prompt tokens | `1.00×` (Full price) | Baseline |
| `output` | Generated tokens | Output price (Highest) | Watch reasoning length on Fable 5 |
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

### 01 — Claude Fable 5: Daily Token Usage & Performance
Dedicated deep-dive for **`claude-fable-5`**:
- **Interactive Filters**: Filter Fable 5 dynamically by `location`, `model_version_id`, `api_method`, and `token_type`.
- **5 Scorecards & Ratios**: Total Fable 5 tokens, Output tokens, Uncached input tokens, **Fable 5 Cache Hit Ratio %**, and **Avg Tokens / Request**.
- **3 Donut Charts**: Billing Type Share, Serving Region Share, and Streaming vs Batch API Split.
- **Dual-Axis Token vs Latency Correlation**: Hourly Fable 5 Token Generation (`Y1 Stacked Area`) overlaid with **End-to-End p95 Latency (`Y2 Line`)** to see how reasoning depth drives latency.
- **Regional Leaderboard Table**: Sortable token consumption across regions with inline bars.

### 02 — Anthropic Fleet Overview
Compare all active Anthropic models (`claude-fable-5`, `claude-opus-4`, `claude-sonnet-4`) side-by-side:
- **Architectural Donut Comparison**: **Fleet Token Share by Model (Donut)** vs **Fleet Request Share by Model (Donut)** side-by-side — immediately highlights why a reasoning model with 31% of requests accounts for 58%+ of token volume.
- **Multi-Model Trends & PTU Utilization**: Daily stacked token/request bars and Provisioned Throughput consumption.
- **Fleet Leaderboard Matrix (`timeSeriesTable`)**: Token and invocation leaderboards grouped by Model, Region, and API Method.

![Fleet Overview — v3.3-final showing Token Share vs Request Share Donut comparison, Multi-Model trends, and Leaderboard Matrix](images/fleet-overview-daily-volume.png)

### 03 — Latency & Performance SLO Monitor
- **4 Latency Percentile Scorecards (24h)**: **TTFT p50**, **TTFT p95**, **End-to-End Latency p50**, and **End-to-End Latency p99** with color-coded warning and SLO breach thresholds.
- **Unified Multi-Percentile Spread Curves**: Overlays **p50, p95, and p99** on a single chart with horizontal **SLO Target Reference Lines** (`1,000 ms` for TTFT, `10,000 ms` for interactive E2E) to expose tail amplification.
- **Dual Distribution Heatmaps**: Side-by-side **TTFT Distribution Heatmap (`first_token_latencies`)** (revealing cached fast-path vs cold-start bimodal clusters) and **End-to-End Latency Heatmap (`model_invocation_latencies`)**.
- **Latency Leaderboard Table & SRE Guide**: Sortable p95 TTFT and p95 E2E latency by model and region.

![Latency & Performance — v3.3-final showing SLO scorecards, unified multi-percentile curves with horizontal SLO lines, and Latency Leaderboard](images/latency-performance-slos.png)

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

![Caching & Cost Efficiency — v3.3-final showing True Cache Hit Ratio, Cost Structure Donuts, Dual-Axis Read vs Write chart, and FinOps Break-Even Formula](images/caching-cost-efficiency.png)

### 06 — Capacity, Quota & Request Shape
- **4 Capacity Scorecards**: Total Requests, Consumed Token Throughput, Streaming Method Ratio %, and Avg Output Tokens / Request.
- **3 Context Window & Routing Donuts**: Input Prompt Size Bucket Share, Output Token Size Bucket Share, and Shared vs Provisioned Routing Share.
- **Context-Bloat Histograms & Leaderboard Table**: Intraday prompt size bucket shifts and per-model capacity matrix.

---

## Interactive Web Dashboard Studio (`dashboard-studio.html`)

Open `dashboard-studio.html` in any browser to launch the standalone **Cloud Monitoring Dashboard Studio & Version Explorer**:
- Switch live between **all 5 preserved versions** (`v1.0-original`, `v2.0-old`, `v3.1-iter1`, `v3.2-iter2`, `v3.3-final`).
- Toggle **Side-by-Side Diff Mode (`⇄ Compare Old v2.0 vs New v3.3`)** to audit every architectural improvement.
- Test interactive filters (`model_id`, `location`) and simulate production incidents (**Regional 429 Quota Spike**, **Silent Cache Invalidation Regression**, **Fable 5 Deep Reasoning Tail Latency**).

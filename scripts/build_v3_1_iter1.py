#!/usr/bin/env python3
"""Generates Recursive Self-Improvement Iteration 1 (v3.1-iter1) dashboards.

Enhancements over v2.0-old:
1. Rich multi-dimensional interactive dashboardFilters (location, model_version_id, method, etc.).
2. Root 'labels' metadata tags with version="v3-1-iter1".
3. Native timeSeriesFilterRatio scorecards (Error Rate %, Cache Hit Ratio %, Tokens/Req, Streaming %).
4. Added 24h Latency Scorecards with SLO thresholds to Dashboard 03 (which previously had zero scorecards).
5. Unified Navigation & Suite Context Markdown Header across all 7 dashboards.
"""

import json
import os

OUT_DIR = "dashboards/versions/v3.1-iter1"
os.makedirs(OUT_DIR, exist_ok=True)


def make_labels(dash_id: str):
  return {
      "publisher": "anthropic",
      "platform": "vertex-ai",
      "suite": "geap-model-monitoring",
      "version": "v3-1-iter1",
      "dashboard-id": dash_id,
  }


def std_filters(include_model=True, extra=None):
  f = []
  if include_model:
    f.append({
        "labelKey": 'resource.label."model_user_id"',
        "templateVariable": "model_id",
        "filterType": "RESOURCE_LABEL",
    })
  f.extend([
      {
          "labelKey": 'resource.label."location"',
          "templateVariable": "location",
          "filterType": "RESOURCE_LABEL",
      },
      {
          "labelKey": 'resource.label."model_version_id"',
          "templateVariable": "model_version",
          "filterType": "RESOURCE_LABEL",
      },
      {
          "labelKey": 'metric.label."method"',
          "templateVariable": "api_method",
          "filterType": "METRIC_LABEL",
      },
  ])
  if extra:
    f.extend(extra)
  return f


def nav_banner(title: str, desc: str, bg_color: str, active_idx: int):
  nav_items = [
      "00 Usage Summary",
      "01 Fable 5 Deep-Dive",
      "02 Fleet Overview",
      "03 Latency & SLOs",
      "04 Errors & Reliability",
      "05 Caching & FinOps",
      "06 Capacity & Quota",
  ]
  nav_str = " | ".join(
      f"**[{item}]**" if idx == active_idx else item
      for idx, item in enumerate(nav_items)
  )
  content = (
      f"## {title}  `[v3.1-iter1]`\n"
      f"{desc}\n\n"
      f"**Suite Navigation:** {nav_str}  \n"
      f"*Interactive Filters active above: filter dynamically by Model, Region (`location`), Version (`model_version_id`), and API Method (`method`).*"
  )
  return {
      "xPos": 0,
      "yPos": 0,
      "width": 48,
      "height": 5,
      "widget": {
          "title": "",
          "text": {
              "content": content,
              "format": "MARKDOWN",
              "style": {
                  "backgroundColor": bg_color,
                  "textColor": "#E0E0E0",
                  "fontSize": "FS_MEDIUM",
                  "padding": "P_MEDIUM",
                  "horizontalAlignment": "H_LEFT",
                  "verticalAlignment": "V_CENTER",
              },
          },
      },
  }


def section_header(y: int, title: str, subtitle: str):
  return {
      "xPos": 0,
      "yPos": y,
      "width": 48,
      "height": 4,
      "widget": {
          "title": title,
          "sectionHeader": {"subtitle": subtitle, "dividerBelow": true_val},
      },
  }


true_val = True
false_val = False


def scorecard_filter(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    flt: str,
    aligner="ALIGN_SUM",
    reducer="REDUCE_SUM",
    period="86400s",
    spark="SPARK_LINE",
    thresholds=None,
):
  sc = {
      "timeSeriesQuery": {
          "timeSeriesFilter": {
              "filter": flt,
              "aggregation": {
                  "alignmentPeriod": period,
                  "perSeriesAligner": aligner,
                  "crossSeriesReducer": reducer,
              },
          }
      },
      "sparkChartView": {"sparkChartType": spark},
  }
  if thresholds:
    sc["thresholds"] = thresholds
  return {
      "xPos": x,
      "yPos": y,
      "width": w,
      "height": h,
      "widget": {"title": title, "scorecard": sc},
  }


def scorecard_ratio(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    num_flt: str,
    den_flt: str,
    period="86400s",
    spark="SPARK_LINE",
    thresholds=None,
):
  sc = {
      "timeSeriesQuery": {
          "timeSeriesFilterRatio": {
              "numerator": {
                  "filter": num_flt,
                  "aggregation": {
                      "alignmentPeriod": period,
                      "perSeriesAligner": "ALIGN_SUM",
                      "crossSeriesReducer": "REDUCE_SUM",
                  },
              },
              "denominator": {
                  "filter": den_flt,
                  "aggregation": {
                      "alignmentPeriod": period,
                      "perSeriesAligner": "ALIGN_SUM",
                      "crossSeriesReducer": "REDUCE_SUM",
                  },
              },
          }
      },
      "sparkChartView": {"sparkChartType": spark},
  }
  if thresholds:
    sc["thresholds"] = thresholds
  return {
      "xPos": x,
      "yPos": y,
      "width": w,
      "height": h,
      "widget": {"title": title, "scorecard": sc},
  }


def xy_chart(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    plot_type: str,
    flt: str,
    period: str,
    aligner: str,
    reducer: str,
    group_by=None,
    y_label=None,
):
  agg = {
      "alignmentPeriod": period,
      "perSeriesAligner": aligner,
      "crossSeriesReducer": reducer,
  }
  if group_by:
    agg["groupByFields"] = group_by
  chart = {
      "chartOptions": {"mode": "COLOR"},
      "dataSets": [{
          "plotType": plot_type,
          "minAlignmentPeriod": period,
          "timeSeriesQuery": {
              "timeSeriesFilter": {"filter": flt, "aggregation": agg}
          },
      }],
  }
  if y_label:
    chart["yAxis"] = {"label": y_label}
  return {
      "xPos": x,
      "yPos": y,
      "width": w,
      "height": h,
      "widget": {"title": title, "xyChart": chart},
  }


# Base metric filters
F_TOKEN = 'metric.type="aiplatform.googleapis.com/publisher/online_serving/token_count" resource.type="aiplatform.googleapis.com/PublisherModel" resource.label."publisher"="anthropic"'
F_INVOC = 'metric.type="aiplatform.googleapis.com/publisher/online_serving/model_invocation_count" resource.type="aiplatform.googleapis.com/PublisherModel" resource.label."publisher"="anthropic"'
F_TTFT = 'metric.type="aiplatform.googleapis.com/publisher/online_serving/first_token_latencies" resource.type="aiplatform.googleapis.com/PublisherModel" resource.label."publisher"="anthropic"'
F_E2E = 'metric.type="aiplatform.googleapis.com/publisher/online_serving/model_invocation_latencies" resource.type="aiplatform.googleapis.com/PublisherModel" resource.label."publisher"="anthropic"'
F_THRU = 'metric.type="aiplatform.googleapis.com/publisher/online_serving/consumed_throughput" resource.type="aiplatform.googleapis.com/PublisherModel" resource.label."publisher"="anthropic"'
F_TOK_THRU = 'metric.type="aiplatform.googleapis.com/publisher/online_serving/consumed_token_throughput" resource.type="aiplatform.googleapis.com/PublisherModel" resource.label."publisher"="anthropic"'

# 00 - Model Usage
d00 = {
    "displayName": "Anthropic - Model Usage",
    "labels": make_labels("00-model-usage"),
    "dashboardFilters": std_filters(True),
    "mosaicLayout": {
        "columns": 48,
        "tiles": [
            nav_banner(
                "📊 Anthropic Model Usage Dashboard",
                "Executive summary of token consumption, request volumes, tokens/request efficiency, and error ratios across all Anthropic models.",
                "#1A1A2E",
                0,
            ),
            section_header(
                5,
                "🔑 Executive 24h Key Metrics & Ratios",
                "Volume scorecards paired with normalized Tokens/Request and Error Rate ratios",
            ),
            scorecard_filter(
                0,
                9,
                8,
                12,
                "Total tokens (24h)",
                F_TOKEN,
                thresholds=[
                    {"value": 50000000, "color": "YELLOW", "direction": "ABOVE", "label": "High"},
                    {"value": 100000000, "color": "RED", "direction": "ABOVE", "label": "Very high"},
                ],
            ),
            scorecard_filter(8, 9, 8, 12, "Requests (24h)", F_INVOC),
            scorecard_ratio(
                16,
                9,
                8,
                12,
                "Avg Tokens / Request (24h)",
                F_TOKEN,
                F_INVOC,
                spark="SPARK_LINE",
            ),
            scorecard_filter(
                24,
                9,
                8,
                12,
                "Output tokens (24h)",
                F_TOKEN + ' metric.label."type"="output"',
            ),
            scorecard_filter(
                32,
                9,
                8,
                12,
                "⚠️ Errors non-200 (24h)",
                F_INVOC + ' metric.label."response_code"!="200"',
                spark="SPARK_BAR",
                thresholds=[
                    {"value": 10, "color": "YELLOW", "direction": "ABOVE", "label": "Present"},
                    {"value": 100, "color": "RED", "direction": "ABOVE", "label": "High"},
                ],
            ),
            scorecard_ratio(
                40,
                9,
                8,
                12,
                "Error Rate Ratio (24h)",
                F_INVOC + ' metric.label."response_code"!="200"',
                F_INVOC,
                spark="SPARK_BAR",
                thresholds=[
                    {"value": 0.01, "color": "YELLOW", "direction": "ABOVE", "label": ">1% Errors"},
                    {"value": 0.05, "color": "RED", "direction": "ABOVE", "label": ">5% Breach"},
                ],
            ),
            section_header(
                21,
                "📈 Token Consumption & Regional Trends",
                "Daily and hourly breakdowns by model, billing token type, and GCP serving location",
            ),
            xy_chart(
                0,
                25,
                24,
                16,
                "Daily tokens by model",
                "STACKED_BAR",
                F_TOKEN,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            xy_chart(
                24,
                25,
                24,
                16,
                "Daily tokens by type (input / output / cache)",
                "STACKED_BAR",
                F_TOKEN,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            xy_chart(
                0,
                41,
                24,
                16,
                "Hourly token usage by model",
                "STACKED_AREA",
                F_TOKEN,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            xy_chart(
                24,
                41,
                24,
                16,
                "Hourly requests by serving region (location)",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."location"'],
            ),
        ],
    },
}

# 01 - Claude Fable 5
F_FABLE_TOK = F_TOKEN + ' resource.label."model_user_id"=monitoring.regex.full_match("claude-(fable|opus)-5.*")'
F_FABLE_INV = F_INVOC + ' resource.label."model_user_id"=monitoring.regex.full_match("claude-(fable|opus)-5.*")'
d01 = {
    "displayName": "Claude Fable 5 - Daily Token Usage",
    "labels": make_labels("01-fable5-token-usage"),
    "dashboardFilters": std_filters(
        False,
        [{
            "labelKey": 'metric.label."type"',
            "templateVariable": "token_type",
            "filterType": "METRIC_LABEL",
        }],
    ),
    "mosaicLayout": {
        "columns": 48,
        "tiles": [
            nav_banner(
                "🦊 Claude Fable 5 — Dedicated Token & Efficiency Monitor",
                "Granular consumption, caching efficiency ratios, and hourly rate tracking for **claude-fable-5**.",
                "#1B1B3A",
                1,
            ),
            section_header(
                5,
                "🔑 Claude Fable 5 — 24h Scorecards & Efficiency Ratios",
                "Rolling 24-hour volume metrics paired with Cache Hit Ratio and Output/Input generation multiplier",
            ),
            scorecard_filter(
                0,
                9,
                10,
                13,
                "Total Fable 5 tokens (24h)",
                F_FABLE_TOK,
                thresholds=[
                    {"value": 10000000, "color": "YELLOW", "direction": "ABOVE", "label": "High"},
                    {"value": 50000000, "color": "RED", "direction": "ABOVE", "label": "Budget Alert"},
                ],
            ),
            scorecard_filter(
                10,
                9,
                10,
                13,
                "Output tokens (24h)",
                F_FABLE_TOK + ' metric.label."type"="output"',
            ),
            scorecard_filter(
                20,
                9,
                10,
                13,
                "Uncached input tokens (24h)",
                F_FABLE_TOK + ' metric.label."type"="input"',
            ),
            scorecard_ratio(
                30,
                9,
                9,
                13,
                "Cache Hit Ratio (24h)",
                F_FABLE_TOK + ' metric.label."type"="cache_read_input"',
                F_FABLE_TOK + ' metric.label."type"=monitoring.regex.full_match("input|cache_read_input|cache_write_input|cache_write_1h_input")',
                thresholds=[
                    {"value": 0.5, "color": "YELLOW", "direction": "BELOW", "label": "<50% Cache Hit"},
                ],
            ),
            scorecard_ratio(
                39,
                9,
                9,
                13,
                "Avg Tokens / Request (24h)",
                F_FABLE_TOK,
                F_FABLE_INV,
            ),
            section_header(
                22,
                "📊 Daily & Hourly Token Consumption Breakdown",
                "Stacked daily totals and intraday 1-hour generation rates broken down by token billing type",
            ),
            xy_chart(
                0,
                26,
                24,
                18,
                "Tokens per day by type (input / output / cache)",
                "STACKED_BAR",
                F_FABLE_TOK,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            xy_chart(
                24,
                26,
                24,
                18,
                "Hourly token rate by type (1h resolution)",
                "STACKED_AREA",
                F_FABLE_TOK,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            xy_chart(
                0,
                44,
                24,
                16,
                "Fable 5 requests by serving region (hourly)",
                "STACKED_BAR",
                F_FABLE_INV,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."location"'],
            ),
            xy_chart(
                24,
                44,
                24,
                16,
                "Fable 5 requests by API method (stream vs sync)",
                "STACKED_BAR",
                F_FABLE_INV,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."method"'],
            ),
        ],
    },
}

# 02 - Fleet Overview
d02 = {
    "displayName": "Anthropic Models - Fleet Overview (All Models)",
    "labels": make_labels("02-fleet-overview"),
    "dashboardFilters": std_filters(True),
    "mosaicLayout": {
        "columns": 48,
        "tiles": [
            nav_banner(
                "🚀 Anthropic Fleet Overview",
                "Holistic multi-model comparison across all Claude deployments — adoption trends, regional distribution, streaming ratio, and throughput.",
                "#0D1B2A",
                2,
            ),
            section_header(
                5,
                "🔑 Fleet Adoption & Utilization Scorecards (24h)",
                "Fleet-wide request volume, streaming adoption ratio, and average payload density",
            ),
            scorecard_filter(0, 9, 12, 12, "Fleet Total Tokens (24h)", F_TOKEN),
            scorecard_filter(12, 9, 12, 12, "Fleet Total Requests (24h)", F_INVOC),
            scorecard_ratio(
                24,
                9,
                12,
                12,
                "Streaming Adoption Ratio (24h)",
                F_INVOC + ' metric.label."method"="streamRawPredict"',
                F_INVOC,
            ),
            scorecard_ratio(
                36,
                9,
                12,
                12,
                "Fleet Avg Tokens / Req (24h)",
                F_TOKEN,
                F_INVOC,
            ),
            section_header(
                21,
                "📊 Daily Volume & Model Adoption",
                "Compare token and request volume across all active Anthropic models",
            ),
            xy_chart(
                0,
                25,
                24,
                18,
                "Daily tokens by model",
                "STACKED_BAR",
                F_TOKEN,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            xy_chart(
                24,
                25,
                24,
                18,
                "Daily requests by model",
                "STACKED_BAR",
                F_INVOC,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            section_header(
                43,
                "⏱️ Hourly Trends, Token Mix & Throughput",
                "Hourly token generation rates, input/output composition, and Provisioned Throughput consumption",
            ),
            xy_chart(
                0,
                47,
                16,
                16,
                "Hourly token rate by model",
                "LINE",
                F_TOKEN,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            xy_chart(
                16,
                47,
                16,
                16,
                "Input vs output token mix (daily)",
                "STACKED_AREA",
                F_TOKEN,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            xy_chart(
                32,
                47,
                16,
                16,
                "Throughput consumption by model",
                "STACKED_AREA",
                F_THRU,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
        ],
    },
}

# 03 - Latency & Performance
d03 = {
    "displayName": "Anthropic Models - Latency & Performance",
    "labels": make_labels("03-latency-performance"),
    "dashboardFilters": std_filters(True),
    "mosaicLayout": {
        "columns": 48,
        "tiles": [
            nav_banner(
                "⚡ Latency & Performance SLO Monitor",
                "Track **Time-to-First-Token (TTFT)** and **End-to-End Request Latency** across percentiles (p50, p95, p99) with SLO threshold scorecards.",
                "#1A0A2E",
                3,
            ),
            section_header(
                5,
                "🔑 24h Latency Percentile Scorecards (TTFT & E2E)",
                "Fleet-wide latency benchmarks with yellow warning and red SLO violation thresholds",
            ),
            scorecard_filter(
                0,
                9,
                12,
                12,
                "TTFT p50 (24h, ms)",
                F_TTFT,
                aligner="ALIGN_DELTA",
                reducer="REDUCE_PERCENTILE_50",
                thresholds=[
                    {"value": 800, "color": "YELLOW", "direction": "ABOVE", "label": ">800ms"},
                    {"value": 2000, "color": "RED", "direction": "ABOVE", "label": ">2s Slow"},
                ],
            ),
            scorecard_filter(
                12,
                9,
                12,
                12,
                "TTFT p95 (24h, ms)",
                F_TTFT,
                aligner="ALIGN_DELTA",
                reducer="REDUCE_PERCENTILE_95",
                thresholds=[
                    {"value": 2000, "color": "YELLOW", "direction": "ABOVE", "label": ">2s"},
                    {"value": 5000, "color": "RED", "direction": "ABOVE", "label": ">5s Breach"},
                ],
            ),
            scorecard_filter(
                24,
                9,
                12,
                12,
                "End-to-End Latency p50 (24h, ms)",
                F_E2E,
                aligner="ALIGN_DELTA",
                reducer="REDUCE_PERCENTILE_50",
                thresholds=[
                    {"value": 5000, "color": "YELLOW", "direction": "ABOVE", "label": ">5s"},
                    {"value": 15000, "color": "RED", "direction": "ABOVE", "label": ">15s"},
                ],
            ),
            scorecard_filter(
                36,
                9,
                12,
                12,
                "End-to-End Latency p99 (24h, ms)",
                F_E2E,
                aligner="ALIGN_DELTA",
                reducer="REDUCE_PERCENTILE_99",
                thresholds=[
                    {"value": 30000, "color": "YELLOW", "direction": "ABOVE", "label": ">30s"},
                    {"value": 60000, "color": "RED", "direction": "ABOVE", "label": ">60s Tail"},
                ],
            ),
            section_header(
                21,
                "🏎️ Time to First Token (TTFT — Streaming Responsiveness)",
                "How quickly the model emits the first token after invocation (5-min aligned)",
            ),
            xy_chart(
                0,
                25,
                24,
                16,
                "Time to first token — p50 (ms, by model)",
                "LINE",
                F_TTFT,
                "300s",
                "ALIGN_DELTA",
                "REDUCE_PERCENTILE_50",
                ['resource.label."model_user_id"'],
                "ms",
            ),
            xy_chart(
                24,
                25,
                24,
                16,
                "Time to first token — p95 (ms, by model)",
                "LINE",
                F_TTFT,
                "300s",
                "ALIGN_DELTA",
                "REDUCE_PERCENTILE_95",
                ['resource.label."model_user_id"'],
                "ms",
            ),
            section_header(
                41,
                "🕐 End-to-End Latency & Distribution Heatmap",
                "Complete generation time from request submission to final token completion",
            ),
            xy_chart(
                0,
                45,
                24,
                16,
                "End-to-end request latency — p50 (ms, by model)",
                "LINE",
                F_E2E,
                "300s",
                "ALIGN_DELTA",
                "REDUCE_PERCENTILE_50",
                ['resource.label."model_user_id"'],
                "ms",
            ),
            xy_chart(
                24,
                45,
                24,
                16,
                "End-to-end request latency — p99 (ms, by model)",
                "LINE",
                F_E2E,
                "300s",
                "ALIGN_DELTA",
                "REDUCE_PERCENTILE_99",
                ['resource.label."model_user_id"'],
                "ms",
            ),
            xy_chart(
                0,
                61,
                48,
                16,
                "Latency heatmap — end-to-end distribution (all Anthropic models)",
                "HEATMAP",
                F_E2E,
                "300s",
                "ALIGN_DELTA",
                "REDUCE_SUM",
            ),
        ],
    },
}

# 04 - Errors & Reliability
d04 = {
    "displayName": "Anthropic Models - Errors & Reliability",
    "labels": make_labels("04-errors-reliability"),
    "dashboardFilters": std_filters(
        True,
        [
            {
                "labelKey": 'metric.label."response_code"',
                "templateVariable": "response_code",
                "filterType": "METRIC_LABEL",
            },
            {
                "labelKey": 'metric.label."error_category"',
                "templateVariable": "error_category",
                "filterType": "METRIC_LABEL",
            },
        ],
    ),
    "mosaicLayout": {
        "columns": 48,
        "tiles": [
            nav_banner(
                "🛡️ Errors, Throttling & Reliability Triage",
                "Real-time incident triage: HTTP response codes, error categories, 429 quota throttling, and normalized error ratios.",
                "#2A0A0A",
                4,
            ),
            section_header(
                5,
                "🔑 24h Reliability Scorecards & Error Ratios",
                "Absolute counts paired with true Error Rate % and 429 Throttling Rate % ratios",
            ),
            scorecard_filter(
                0,
                9,
                10,
                13,
                "✅ Successful 200 OK (24h)",
                F_INVOC + ' metric.label."response_code"="200"',
            ),
            scorecard_filter(
                10,
                9,
                10,
                13,
                "❌ Failed requests non-200 (24h)",
                F_INVOC + ' metric.label."response_code"!="200"',
                spark="SPARK_BAR",
                thresholds=[
                    {"value": 10, "color": "YELLOW", "direction": "ABOVE", "label": "Failures present"},
                    {"value": 100, "color": "RED", "direction": "ABOVE", "label": "High failures"},
                ],
            ),
            scorecard_ratio(
                20,
                9,
                9,
                13,
                "Error Rate Ratio (24h)",
                F_INVOC + ' metric.label."response_code"!="200"',
                F_INVOC,
                spark="SPARK_BAR",
                thresholds=[
                    {"value": 0.01, "color": "YELLOW", "direction": "ABOVE", "label": ">1% Errors"},
                    {"value": 0.05, "color": "RED", "direction": "ABOVE", "label": ">5% Critical"},
                ],
            ),
            scorecard_filter(
                29,
                9,
                10,
                13,
                "🚫 Throttled 429 count (24h)",
                F_INVOC + ' metric.label."response_code"="429"',
                spark="SPARK_BAR",
                thresholds=[
                    {"value": 1, "color": "YELLOW", "direction": "ABOVE", "label": "Throttling"},
                    {"value": 50, "color": "RED", "direction": "ABOVE", "label": "Heavy 429s"},
                ],
            ),
            scorecard_ratio(
                39,
                9,
                9,
                13,
                "429 Throttle Ratio (24h)",
                F_INVOC + ' metric.label."response_code"="429"',
                F_INVOC,
                spark="SPARK_BAR",
                thresholds=[
                    {"value": 0.005, "color": "YELLOW", "direction": "ABOVE", "label": ">0.5% Throttled"},
                    {"value": 0.02, "color": "RED", "direction": "ABOVE", "label": ">2% Throttled"},
                ],
            ),
            section_header(
                22,
                "📊 Error & Response Code Breakdown",
                "Hourly request breakdown by response code, error category, and model",
            ),
            xy_chart(
                0,
                26,
                24,
                18,
                "Requests by response code (all Anthropic models)",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."response_code"'],
            ),
            xy_chart(
                24,
                26,
                24,
                18,
                "Errors by category & code (non-200)",
                "STACKED_BAR",
                F_INVOC + ' metric.label."response_code"!="200"',
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."error_category"', 'metric.label."response_code"'],
            ),
            xy_chart(
                0,
                44,
                24,
                16,
                "Hourly error count by model (non-200)",
                "LINE",
                F_INVOC + ' metric.label."response_code"!="200"',
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            xy_chart(
                24,
                44,
                24,
                16,
                "Hourly 429 throttling by serving region (location)",
                "STACKED_BAR",
                F_INVOC + ' metric.label."response_code"="429"',
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."location"'],
            ),
        ],
    },
}

# 05 - Caching Efficiency
F_ALL_INPUT = F_TOKEN + ' metric.label."type"=monitoring.regex.full_match("input|cache_read_input|cache_write_input|cache_write_1h_input")'
d05 = {
    "displayName": "Anthropic Models - Prompt Caching & Cost Efficiency",
    "labels": make_labels("05-caching-efficiency"),
    "dashboardFilters": std_filters(
        True,
        [{
            "labelKey": 'metric.label."explicit_caching"',
            "templateVariable": "explicit_caching",
            "filterType": "METRIC_LABEL",
        }],
    ),
    "mosaicLayout": {
        "columns": 48,
        "tiles": [
            nav_banner(
                "💰 Prompt Caching & FinOps Cost Efficiency",
                "Maximize prompt cache hits (`cache_read_input` @ ~0.1x cost) and monitor cache write overhead (`cache_write` @ 1.25x–2x cost).",
                "#0A2E1A",
                5,
            ),
            section_header(
                5,
                "🔑 24h Caching Scorecards & True Hit Ratios",
                "Direct comparison of discounted cache reads vs full-price uncached input and cache write overhead",
            ),
            scorecard_filter(
                0,
                9,
                12,
                13,
                "💚 Cache read tokens (24h) — 90% discount",
                F_TOKEN + ' metric.label."type"="cache_read_input"',
            ),
            scorecard_filter(
                12,
                9,
                12,
                13,
                "🔴 Uncached input tokens (24h) — 100% price",
                F_TOKEN + ' metric.label."type"="input"',
                thresholds=[
                    {"value": 10000000, "color": "YELLOW", "direction": "ABOVE", "label": "High uncached"},
                    {"value": 50000000, "color": "RED", "direction": "ABOVE", "label": "Very high"},
                ],
            ),
            scorecard_ratio(
                24,
                9,
                12,
                13,
                "🎯 True Cache Hit Ratio (24h)",
                F_TOKEN + ' metric.label."type"="cache_read_input"',
                F_ALL_INPUT,
                thresholds=[
                    {"value": 0.5, "color": "YELLOW", "direction": "BELOW", "label": "<50% Hit Rate"},
                    {"value": 0.2, "color": "RED", "direction": "BELOW", "label": "Cache Broken"},
                ],
            ),
            scorecard_ratio(
                36,
                9,
                12,
                13,
                "✍️ Cache Read-to-Write Ratio (24h)",
                F_TOKEN + ' metric.label."type"="cache_read_input"',
                F_TOKEN + ' metric.label."type"=monitoring.regex.full_match("cache_write_input|cache_write_1h_input")',
            ),
            section_header(
                22,
                "📊 Daily & Hourly Caching Breakdown",
                "Input token volumes segmented by cache read, cache write (5m & 1h TTL), and uncached input",
            ),
            xy_chart(
                0,
                26,
                24,
                18,
                "Daily input-side token breakdown (read vs write vs uncached)",
                "STACKED_BAR",
                F_TOKEN + ' metric.label."type"!="output"',
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            xy_chart(
                24,
                26,
                24,
                18,
                "Hourly cache_read vs uncached input tokens",
                "STACKED_AREA",
                F_TOKEN + ' metric.label."type"=monitoring.regex.full_match("input|cache_read_input")',
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            xy_chart(
                0,
                44,
                24,
                16,
                "Hourly cache write tokens by TTL type (5m vs 1h)",
                "STACKED_BAR",
                F_TOKEN + ' metric.label."type"=monitoring.regex.full_match("cache_write_input|cache_write_1h_input")',
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            xy_chart(
                24,
                44,
                24,
                16,
                "Requests using explicit caching vs not (hourly)",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."explicit_caching"'],
            ),
        ],
    },
}

# 06 - Capacity & Quota
d06 = {
    "displayName": "Anthropic Models - Capacity, Quota & Request Shape",
    "labels": make_labels("06-capacity-quota"),
    "dashboardFilters": std_filters(
        True,
        [{
            "labelKey": 'metric.label."request_type"',
            "templateVariable": "request_type",
            "filterType": "METRIC_LABEL",
        }],
    ),
    "mosaicLayout": {
        "columns": 48,
        "tiles": [
            nav_banner(
                "🏗️ Capacity, Quota & Request Shape",
                "Provisioned Throughput (PTU) vs Pay-as-you-go routing, prompt/output size histograms, and API method patterns.",
                "#1A2E0A",
                6,
            ),
            section_header(
                5,
                "🔑 24h Capacity & Routing Scorecards",
                "Provisioned vs shared request routing ratios and total consumed throughput",
            ),
            scorecard_filter(0, 9, 12, 12, "Total Requests (24h)", F_INVOC),
            scorecard_filter(
                12,
                9,
                12,
                12,
                "Consumed Token Throughput (24h)",
                F_TOK_THRU,
            ),
            scorecard_ratio(
                24,
                9,
                12,
                12,
                "Streaming Method Ratio (24h)",
                F_INVOC + ' metric.label."method"="streamRawPredict"',
                F_INVOC,
            ),
            scorecard_ratio(
                36,
                9,
                12,
                12,
                "Avg Output Tokens / Req (24h)",
                F_TOKEN + ' metric.label."type"="output"',
                F_INVOC,
            ),
            section_header(
                21,
                "📊 Request Routing & Context Window Size Histograms",
                "Identify context-bloat (100k+ token buckets) and verify shared vs provisioned routing",
            ),
            xy_chart(
                0,
                25,
                24,
                18,
                "Requests by request type (shared vs provisioned/dedicated)",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."request_type"', 'metric.label."shared_request_type"'],
            ),
            xy_chart(
                24,
                25,
                24,
                18,
                "Requests by input token size bucket",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."input_token_size"'],
            ),
            section_header(
                43,
                "📤 Output Size Distribution, Throughput & API Methods",
                "Output length buckets, hourly token throughput per model, and streaming vs batch API split",
            ),
            xy_chart(
                0,
                47,
                16,
                16,
                "Requests by output token size bucket",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."output_token_size"'],
            ),
            xy_chart(
                16,
                47,
                16,
                16,
                "Consumed token throughput by model (hourly)",
                "STACKED_AREA",
                F_TOK_THRU,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            xy_chart(
                32,
                47,
                16,
                16,
                "Requests by API method (rawPredict / streamRawPredict)",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."method"'],
            ),
        ],
    },
}

dashboards = {
    "00-anthropic-model-usage.json": d00,
    "01-fable5-token-usage.json": d01,
    "02-anthropic-fleet-overview.json": d02,
    "03-anthropic-latency-performance.json": d03,
    "04-anthropic-errors-reliability.json": d04,
    "05-anthropic-caching-efficiency.json": d05,
    "06-anthropic-capacity-quota.json": d06,
}

for fname, data in dashboards.items():
  path = os.path.join(OUT_DIR, fname)
  with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
    f.write("\n")
print(f"Generated {len(dashboards)} dashboards in {OUT_DIR}")

#!/usr/bin/env python3
"""Generates Recursive Self-Improvement Iteration 2 (v3.2-iter2) dashboards.

Enhancements over v3.1-iter1:
1. Native pieChart (DONUT) widgets across dashboards for instant proportional comprehension.
2. Dual-Axis (yAxis Y1 + y2Axis Y2) multi-layer XY charts correlating volume vs errors/latency/cache-writes.
3. Unified Multi-Percentile (p50, p90, p95, p99) latency curves with horizontal SLO threshold lines on xyChart.
4. Added Time-to-First-Token (TTFT) Distribution Heatmap alongside End-to-End Latency Heatmap.
"""

import json
import os

OUT_DIR = "dashboards/versions/v3.2-iter2"
os.makedirs(OUT_DIR, exist_ok=True)

true_val = True
false_val = False


def make_labels(dash_id: str):
  return {
      "publisher": "anthropic",
      "platform": "vertex-ai",
      "suite": "geap-model-monitoring",
      "version": "v3-2-iter2",
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
      f"## {title}  `[v3.2-iter2 • Visual & Dual-Axis Edition]`\n"
      f"{desc}\n\n"
      f"**Suite Navigation:** {nav_str}  \n"
      f"*New in v3.2: Proportional Donut Visualizations, Dual-Axis Volume/Incident Overlays, SLO Reference Lines & Dual Heatmaps.*"
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


def donut_chart(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    flt: str,
    group_by: list,
    period="86400s",
):
  return {
      "xPos": x,
      "yPos": y,
      "width": w,
      "height": h,
      "widget": {
          "title": title,
          "pieChart": {
              "chartType": "DONUT",
              "showLabels": true_val,
              "dataSets": [{
                  "timeSeriesQuery": {
                      "timeSeriesFilter": {
                          "filter": flt,
                          "aggregation": {
                              "alignmentPeriod": period,
                              "perSeriesAligner": "ALIGN_SUM",
                              "crossSeriesReducer": "REDUCE_SUM",
                              "groupByFields": group_by,
                          },
                      }
                  }
              }],
          },
      },
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
    thresholds=None,
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
  if thresholds:
    chart["thresholds"] = thresholds
  return {
      "xPos": x,
      "yPos": y,
      "width": w,
      "height": h,
      "widget": {"title": title, "xyChart": chart},
  }


def dual_axis_chart(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    y1_label: str,
    y2_label: str,
    ds1: dict,
    ds2: dict,
):
  return {
      "xPos": x,
      "yPos": y,
      "width": w,
      "height": h,
      "widget": {
          "title": title,
          "xyChart": {
              "chartOptions": {"mode": "COLOR"},
              "yAxis": {"label": y1_label, "scale": "LINEAR"},
              "y2Axis": {"label": y2_label, "scale": "LINEAR"},
              "dataSets": [ds1, ds2],
          },
      },
  }


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
                "Executive command center: token volume, request rates, proportional model/type Donut shares, and Dual-Axis Traffic vs Error correlation.",
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
                "🍩 Proportional Fleet Share (Donut Visualizations)",
                "Instant proportional breakdown of token consumption by Model, Billing Type, and Serving Region",
            ),
            donut_chart(
                0,
                25,
                16,
                15,
                "Token Share by Model (Donut)",
                F_TOKEN,
                ['resource.label."model_user_id"'],
            ),
            donut_chart(
                16,
                25,
                16,
                15,
                "Token Share by Billing Type (Donut)",
                F_TOKEN,
                ['metric.label."type"'],
            ),
            donut_chart(
                32,
                25,
                16,
                15,
                "Request Share by GCP Region (Donut)",
                F_INVOC,
                ['resource.label."location"'],
            ),
            section_header(
                40,
                "📈 Consumption Trends & Dual-Axis Volume vs Error Correlation",
                "Daily stacked bars and Dual-Axis hourly correlation of Request Volume (Y1) vs Non-200 Errors (Y2)",
            ),
            xy_chart(
                0,
                44,
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
            dual_axis_chart(
                24,
                44,
                24,
                16,
                "Dual-Axis: Hourly Request Volume (Y1 Bar) vs Non-200 Errors (Y2 Line)",
                "Requests / hr",
                "Errors / hr",
                {
                    "plotType": "STACKED_BAR",
                    "targetAxis": "Y1",
                    "legendTemplate": "Requests (${resource.labels.model_user_id})",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_INVOC,
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_SUM",
                                "crossSeriesReducer": "REDUCE_SUM",
                                "groupByFields": ['resource.label."model_user_id"'],
                            },
                        }
                    },
                },
                {
                    "plotType": "LINE",
                    "targetAxis": "Y2",
                    "legendTemplate": "Errors (${metric.labels.response_code})",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_INVOC + ' metric.label."response_code"!="200"',
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_SUM",
                                "crossSeriesReducer": "REDUCE_SUM",
                                "groupByFields": ['metric.label."response_code"'],
                            },
                        }
                    },
                },
            ),
        ],
    },
}

# 01 - Claude Fable 5
F_FABLE_TOK = F_TOKEN + ' resource.label."model_user_id"="claude-fable-5"'
F_FABLE_INV = F_INVOC + ' resource.label."model_user_id"="claude-fable-5"'
F_FABLE_E2E = F_E2E + ' resource.label."model_user_id"="claude-fable-5"'
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
                "🦊 Claude Fable 5 — Dedicated Token & Performance Monitor",
                "Granular token breakdown, proportional Donut share, and Dual-Axis Token Volume vs Latency correlation for **claude-fable-5**.",
                "#1B1B3A",
                1,
            ),
            section_header(
                5,
                "🔑 Claude Fable 5 — 24h Scorecards & Efficiency Ratios",
                "Rolling 24-hour volume metrics paired with Cache Hit Ratio and Avg Tokens/Request",
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
                "🍩 Fable 5 Proportional Composition & Regional Split",
                "Visual Donut share of token billing types and serving region distribution",
            ),
            donut_chart(
                0,
                26,
                16,
                15,
                "Fable 5 Token Share by Type (Donut)",
                F_FABLE_TOK,
                ['metric.label."type"'],
            ),
            donut_chart(
                16,
                26,
                16,
                15,
                "Fable 5 Request Share by Region (Donut)",
                F_FABLE_INV,
                ['resource.label."location"'],
            ),
            donut_chart(
                32,
                26,
                16,
                15,
                "Fable 5 Streaming vs Batch Split (Donut)",
                F_FABLE_INV,
                ['metric.label."method"'],
            ),
            section_header(
                41,
                "📊 Daily & Dual-Axis Hourly Token vs Latency Correlation",
                "Daily stacked bars and Dual-Axis hourly correlation of Token Volume (Y1) vs p95 Latency (Y2)",
            ),
            xy_chart(
                0,
                45,
                24,
                16,
                "Tokens per day by type (input / output / cache)",
                "STACKED_BAR",
                F_FABLE_TOK,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            dual_axis_chart(
                24,
                45,
                24,
                16,
                "Dual-Axis: Hourly Fable 5 Tokens (Y1 Area) vs E2E p95 Latency ms (Y2 Line)",
                "Tokens / hr",
                "p95 Latency (ms)",
                {
                    "plotType": "STACKED_AREA",
                    "targetAxis": "Y1",
                    "legendTemplate": "Tokens (${metric.labels.type})",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_FABLE_TOK,
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_SUM",
                                "crossSeriesReducer": "REDUCE_SUM",
                                "groupByFields": ['metric.label."type"'],
                            },
                        }
                    },
                },
                {
                    "plotType": "LINE",
                    "targetAxis": "Y2",
                    "legendTemplate": "p95 E2E Latency (ms)",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_FABLE_E2E,
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_DELTA",
                                "crossSeriesReducer": "REDUCE_PERCENTILE_95",
                            },
                        }
                    },
                },
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
                "Compare Model Token Share vs Request Share side-by-side to distinguish heavy reasoning models from high-frequency lightweight models.",
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
                "🍩 Fleet Model Share Comparison: Token Share vs Request Share",
                "Crucial architectural insight: A model with 20% of requests may consume 75% of tokens",
            ),
            donut_chart(
                0,
                25,
                16,
                15,
                "Fleet Token Share by Model (Donut)",
                F_TOKEN,
                ['resource.label."model_user_id"'],
            ),
            donut_chart(
                16,
                25,
                16,
                15,
                "Fleet Request Share by Model (Donut)",
                F_INVOC,
                ['resource.label."model_user_id"'],
            ),
            donut_chart(
                32,
                25,
                16,
                15,
                "Fleet Traffic Share by Region (Donut)",
                F_INVOC,
                ['resource.label."location"'],
            ),
            section_header(
                40,
                "📊 Daily & Hourly Multi-Model Trends",
                "Compare daily token/request volume and hourly throughput across all active Anthropic models",
            ),
            xy_chart(
                0,
                44,
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
                44,
                24,
                16,
                "Daily requests by model",
                "STACKED_BAR",
                F_INVOC,
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
            ),
            xy_chart(
                0,
                60,
                24,
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
                24,
                60,
                24,
                16,
                "Throughput consumption by model (hourly)",
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
                "Unified multi-percentile latency curves (p50/p90/p95/p99), horizontal SLO target lines, and dual TTFT + End-to-End Distribution Heatmaps.",
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
                "🏎️ Unified Multi-Percentile Curves (p50 vs p95 vs p99) with SLO Lines",
                "Overlaying percentiles on a single chart reveals tail amplification and latency spread instantly",
            ),
            {
                "xPos": 0,
                "yPos": 25,
                "width": 24,
                "height": 18,
                "widget": {
                    "title": "Unified Time-to-First-Token Spread (p50, p95, p99) + SLO Thresholds",
                    "xyChart": {
                        "chartOptions": {"mode": "COLOR"},
                        "yAxis": {"label": "TTFT (ms)", "scale": "LINEAR"},
                        "thresholds": [
                            {"value": 1000, "color": "YELLOW", "direction": "ABOVE", "label": "TTFT Target (1s)"},
                            {"value": 3000, "color": "RED", "direction": "ABOVE", "label": "TTFT SLO Ceiling (3s)"},
                        ],
                        "dataSets": [
                            {
                                "plotType": "LINE",
                                "legendTemplate": "p50 TTFT (${resource.labels.model_user_id})",
                                "minAlignmentPeriod": "300s",
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": F_TTFT,
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_DELTA",
                                            "crossSeriesReducer": "REDUCE_PERCENTILE_50",
                                            "groupByFields": ['resource.label."model_user_id"'],
                                        },
                                    }
                                },
                            },
                            {
                                "plotType": "LINE",
                                "legendTemplate": "p95 TTFT (${resource.labels.model_user_id})",
                                "minAlignmentPeriod": "300s",
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": F_TTFT,
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_DELTA",
                                            "crossSeriesReducer": "REDUCE_PERCENTILE_95",
                                            "groupByFields": ['resource.label."model_user_id"'],
                                        },
                                    }
                                },
                            },
                            {
                                "plotType": "LINE",
                                "legendTemplate": "p99 TTFT (${resource.labels.model_user_id})",
                                "minAlignmentPeriod": "300s",
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": F_TTFT,
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_DELTA",
                                            "crossSeriesReducer": "REDUCE_PERCENTILE_99",
                                            "groupByFields": ['resource.label."model_user_id"'],
                                        },
                                    }
                                },
                            },
                        ],
                    },
                },
            },
            {
                "xPos": 24,
                "yPos": 25,
                "width": 24,
                "height": 18,
                "widget": {
                    "title": "Unified End-to-End Latency Spread (p50, p95, p99) + SLO Thresholds",
                    "xyChart": {
                        "chartOptions": {"mode": "COLOR"},
                        "yAxis": {"label": "E2E Latency (ms)", "scale": "LINEAR"},
                        "thresholds": [
                            {"value": 10000, "color": "YELLOW", "direction": "ABOVE", "label": "Interactive Target (10s)"},
                            {"value": 30000, "color": "RED", "direction": "ABOVE", "label": "Batch Ceiling (30s)"},
                        ],
                        "dataSets": [
                            {
                                "plotType": "LINE",
                                "legendTemplate": "p50 E2E (${resource.labels.model_user_id})",
                                "minAlignmentPeriod": "300s",
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": F_E2E,
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_DELTA",
                                            "crossSeriesReducer": "REDUCE_PERCENTILE_50",
                                            "groupByFields": ['resource.label."model_user_id"'],
                                        },
                                    }
                                },
                            },
                            {
                                "plotType": "LINE",
                                "legendTemplate": "p95 E2E (${resource.labels.model_user_id})",
                                "minAlignmentPeriod": "300s",
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": F_E2E,
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_DELTA",
                                            "crossSeriesReducer": "REDUCE_PERCENTILE_95",
                                            "groupByFields": ['resource.label."model_user_id"'],
                                        },
                                    }
                                },
                            },
                            {
                                "plotType": "LINE",
                                "legendTemplate": "p99 E2E (${resource.labels.model_user_id})",
                                "minAlignmentPeriod": "300s",
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": F_E2E,
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_DELTA",
                                            "crossSeriesReducer": "REDUCE_PERCENTILE_99",
                                            "groupByFields": ['resource.label."model_user_id"'],
                                        },
                                    }
                                },
                            },
                        ],
                    },
                },
            },
            section_header(
                43,
                "🌡️ Bimodal Distribution Heatmaps: TTFT vs End-to-End Latency",
                "Spot cache-hit fast paths vs cold-start slow paths on the TTFT heatmap and reasoning tails on E2E",
            ),
            xy_chart(
                0,
                47,
                24,
                16,
                "TTFT Distribution Heatmap (first_token_latencies)",
                "HEATMAP",
                F_TTFT,
                "300s",
                "ALIGN_DELTA",
                "REDUCE_SUM",
            ),
            xy_chart(
                24,
                47,
                24,
                16,
                "End-to-End Distribution Heatmap (model_invocation_latencies)",
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
                "Incident command center: Error Donut shares, Dual-Axis Traffic vs 429 Throttling overlay, and regional failure isolation.",
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
                "🍩 Error Proportional Triage (Donut Visualizations)",
                "Isolate whether failures stem from 429 Quota Throttling, 400 Client Payload, or 5xx Platform Errors",
            ),
            donut_chart(
                0,
                26,
                16,
                15,
                "Non-200 Errors by Response Code (Donut)",
                F_INVOC + ' metric.label."response_code"!="200"',
                ['metric.label."response_code"'],
            ),
            donut_chart(
                16,
                26,
                16,
                15,
                "Non-200 Errors by Error Category (Donut)",
                F_INVOC + ' metric.label."response_code"!="200"',
                ['metric.label."error_category"'],
            ),
            donut_chart(
                32,
                26,
                16,
                15,
                "429 Throttling by GCP Region (Donut)",
                F_INVOC + ' metric.label."response_code"="429"',
                ['resource.label."location"'],
            ),
            section_header(
                41,
                "📈 Dual-Axis Traffic vs Throttling & Error Timelines",
                "Correlate total request demand (Y1) directly against 429 throttling spikes (Y2)",
            ),
            dual_axis_chart(
                0,
                45,
                24,
                16,
                "Dual-Axis: Total Traffic Demand (Y1 Bar) vs 429 Throttles (Y2 Line)",
                "Total Requests / hr",
                "429 Throttles / hr",
                {
                    "plotType": "STACKED_BAR",
                    "targetAxis": "Y1",
                    "legendTemplate": "Total Requests (${resource.labels.location})",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_INVOC,
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_SUM",
                                "crossSeriesReducer": "REDUCE_SUM",
                                "groupByFields": ['resource.label."location"'],
                            },
                        }
                    },
                },
                {
                    "plotType": "LINE",
                    "targetAxis": "Y2",
                    "legendTemplate": "429 Throttles (${resource.labels.location})",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_INVOC + ' metric.label."response_code"="429"',
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_SUM",
                                "crossSeriesReducer": "REDUCE_SUM",
                                "groupByFields": ['resource.label."location"'],
                            },
                        }
                    },
                },
            ),
            xy_chart(
                24,
                45,
                24,
                16,
                "Errors by category & code over time (non-200)",
                "STACKED_BAR",
                F_INVOC + ' metric.label."response_code"!="200"',
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."error_category"', 'metric.label."response_code"'],
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
                "Visual Donut cost breakdown, True Cache Hit Ratio scorecards, and Dual-Axis Cache Read vs Cache Write efficiency tracking.",
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
                "🍩 Prompt Token Cost Structure (Donut Visualizations)",
                "Proportional share of input tokens by pricing tier (Cache Read 0.1x, Uncached 1.0x, Write 5m 1.25x, Write 1h 2.0x)",
            ),
            donut_chart(
                0,
                26,
                16,
                15,
                "Input Token Composition by Pricing Tier (Donut)",
                F_ALL_INPUT,
                ['metric.label."type"'],
            ),
            donut_chart(
                16,
                26,
                16,
                15,
                "Cache Read Tokens by Model (Donut)",
                F_TOKEN + ' metric.label."type"="cache_read_input"',
                ['resource.label."model_user_id"'],
            ),
            donut_chart(
                32,
                26,
                16,
                15,
                "Explicit Caching Request Share (Donut)",
                F_INVOC,
                ['metric.label."explicit_caching"'],
            ),
            section_header(
                41,
                "📈 Daily & Dual-Axis Cache Read Savings vs Write Overhead",
                "Ensure Cache Reads (Y1 Area) remain well above Cache Writes (Y2 Line) so caching stays net-profitable",
            ),
            xy_chart(
                0,
                45,
                24,
                16,
                "Daily input-side token breakdown (read vs write vs uncached)",
                "STACKED_BAR",
                F_TOKEN + ' metric.label."type"!="output"',
                "86400s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."type"'],
            ),
            dual_axis_chart(
                24,
                45,
                24,
                16,
                "Dual-Axis: Cache Reads Saved (Y1 Area) vs Cache Writes Billed (Y2 Line)",
                "Cache Read Tokens / hr",
                "Cache Write Tokens / hr",
                {
                    "plotType": "STACKED_AREA",
                    "targetAxis": "Y1",
                    "legendTemplate": "Cache Reads (${resource.labels.model_user_id})",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_TOKEN + ' metric.label."type"="cache_read_input"',
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_SUM",
                                "crossSeriesReducer": "REDUCE_SUM",
                                "groupByFields": ['resource.label."model_user_id"'],
                            },
                        }
                    },
                },
                {
                    "plotType": "LINE",
                    "targetAxis": "Y2",
                    "legendTemplate": "Cache Writes (${metric.labels.type})",
                    "minAlignmentPeriod": "3600s",
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": F_TOKEN + ' metric.label."type"=monitoring.regex.full_match("cache_write_input|cache_write_1h_input")',
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_SUM",
                                "crossSeriesReducer": "REDUCE_SUM",
                                "groupByFields": ['metric.label."type"'],
                            },
                        }
                    },
                },
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
                "Proportional Donut distributions of context window sizes, Provisioned Throughput (PTU) utilization, and API streaming methods.",
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
                "🍩 Context Window & Request Shape Donuts",
                "Proportional distribution of input prompt sizes, output generation sizes, and routing types",
            ),
            donut_chart(
                0,
                25,
                16,
                15,
                "Input Prompt Size Bucket Share (Donut)",
                F_INVOC,
                ['metric.label."input_token_size"'],
            ),
            donut_chart(
                16,
                25,
                16,
                15,
                "Output Token Size Bucket Share (Donut)",
                F_INVOC,
                ['metric.label."output_token_size"'],
            ),
            donut_chart(
                32,
                25,
                16,
                15,
                "Routing Share: Shared vs Provisioned (Donut)",
                F_INVOC,
                ['metric.label."request_type"'],
            ),
            section_header(
                40,
                "📊 Hourly Context Size Histograms & Consumed Throughput",
                "Track intraday shifts in prompt sizes and consumed token throughput across models",
            ),
            xy_chart(
                0,
                44,
                24,
                16,
                "Hourly requests by input token size bucket",
                "STACKED_BAR",
                F_INVOC,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['metric.label."input_token_size"'],
            ),
            xy_chart(
                24,
                44,
                24,
                16,
                "Consumed token throughput by model (hourly)",
                "STACKED_AREA",
                F_TOK_THRU,
                "3600s",
                "ALIGN_SUM",
                "REDUCE_SUM",
                ['resource.label."model_user_id"'],
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

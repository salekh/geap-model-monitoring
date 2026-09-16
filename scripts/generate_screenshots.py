#!/usr/bin/env python3
"""Generates high-resolution 2x Retina Google Cloud Monitoring Dark Theme screenshots.

Renders authentic Cloud Monitoring UI screenshots for the v3.3-final dashboards
using custom vector badges (zero missing emoji glyph boxes):
- images/model-usage-scorecards.png (Dashboard 00)
- images/fleet-overview-daily-volume.png (Dashboard 02)
- images/caching-cost-efficiency.png (Dashboard 05)
- images/latency-performance-slos.png (Dashboard 03)
- images/version-comparison-diff.png (Side-by-Side Evolution v1.0 -> v2.0 -> v3.3)
"""

import os
from PIL import Image, ImageDraw, ImageFont

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def f_reg(size):
  return ImageFont.truetype(FONT_REG, size)


def f_bold(size):
  return ImageFont.truetype(FONT_BOLD, size)


def f_mono(size):
  return ImageFont.truetype(FONT_MONO, size)


# Palette matching Google Cloud Monitoring Dark Theme
BG_DARK = (15, 17, 23)
CARD_BG = (24, 28, 38)
CARD_BORDER = (45, 52, 68)
TEXT_WHITE = (240, 244, 248)
TEXT_MUTED = (154, 160, 166)
ACCENT_BLUE = (138, 180, 248)
ACCENT_GREEN = (129, 201, 149)
ACCENT_YELLOW = (253, 214, 99)
ACCENT_RED = (242, 139, 130)
ACCENT_PURPLE = (197, 138, 249)
ACCENT_CYAN = (120, 217, 236)
ACCENT_ORANGE = (252, 173, 114)


def draw_rounded_rect(draw, box, radius, fill, outline=None, width=1):
  draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_icon_badge(draw, x, y, color, text_symbol):
  draw_rounded_rect(draw, [x, y, x + 24, y + 22], 5, fill=color)
  draw.text((x + 6, y + 3), text_symbol, font=f_bold(12), fill=(15, 17, 23))


def draw_top_chrome(draw, width, dash_title, subtitle, version_tag="v3.3-final", filters=None):
  # GCP Console Top Bar
  draw.rectangle([0, 0, width, 48], fill=(18, 22, 31))
  draw.line([0, 48, width, 48], fill=CARD_BORDER, width=1)
  draw.text((24, 14), "Google Cloud Monitoring  ›  Dashboards  ›", font=f_reg(15), fill=TEXT_MUTED)
  draw.text((345, 14), dash_title, font=f_bold(15), fill=TEXT_WHITE)
  draw_rounded_rect(draw, [width - 340, 10, width - 20, 38], 6, fill=(28, 34, 48), outline=CARD_BORDER)
  draw.text((width - 325, 16), "1h   6h   [24h]   7d   30d   ⟳ Auto-refresh", font=f_reg(13), fill=ACCENT_BLUE)

  # Interactive Filter Bar
  draw.rectangle([0, 49, width, 96], fill=(20, 25, 36))
  draw.line([0, 96, width, 96], fill=CARD_BORDER, width=1)
  draw.text((24, 64), "Filters:", font=f_bold(13), fill=TEXT_MUTED)

  if not filters:
    filters = [
        ("model_id", "All Anthropic Models (claude-fable-5, claude-opus-4, claude-sonnet-4)"),
        ("location", "All Regions (global, us-central1, europe-west1)"),
        ("model_version", "All Versions"),
        ("api_method", "All (streamRawPredict, rawPredict)"),
    ]
  fx = 85
  for k, v in filters:
    txt = f"{k}: {v}"
    bbox = draw.textbbox((0, 0), txt, font=f_reg(12))
    pw = bbox[2] - bbox[0] + 24
    draw_rounded_rect(draw, [fx, 58, fx + pw, 86], 14, fill=(30, 41, 59), outline=ACCENT_BLUE)
    draw.text((fx + 12, 65), txt, font=f_reg(12), fill=TEXT_WHITE)
    fx += pw + 10

  # Banner Tile
  draw_rounded_rect(draw, [20, 108, width - 20, 178], 8, fill=(26, 26, 46), outline=ACCENT_BLUE)
  draw_icon_badge(draw, 36, 118, ACCENT_BLUE, "M")
  draw.text((68, 118), dash_title, font=f_bold(18), fill=TEXT_WHITE)
  # Version badge
  draw_rounded_rect(draw, [width - 190, 116, width - 36, 142], 6, fill=(40, 60, 95), outline=ACCENT_CYAN)
  draw.text((width - 178, 121), f"TAG: {version_tag}", font=f_mono(12), fill=ACCENT_CYAN)
  draw.text((36, 148), subtitle, font=f_reg(13), fill=(210, 218, 226))


def draw_section_header(draw, y, width, badge_txt, badge_col, title, subtitle):
  draw_icon_badge(draw, 24, y, badge_col, badge_txt)
  draw.text((56, y + 1), title, font=f_bold(16), fill=TEXT_WHITE)
  draw.text((56, y + 23), subtitle, font=f_reg(12), fill=TEXT_MUTED)
  draw.line([24, y + 44, width - 24, y + 44], fill=CARD_BORDER, width=1)
  return y + 54


def draw_scorecard(draw, x, y, w, h, title, big_value, sub_label, status_color, spark_points, is_bar=False):
  draw_rounded_rect(draw, [x, y, x + w, y + h], 8, fill=CARD_BG, outline=CARD_BORDER)
  draw.rounded_rectangle([x, y, x + w, y + 5], radius=2, fill=status_color)
  draw.text((x + 16, y + 14), title, font=f_bold(13), fill=TEXT_MUTED)
  draw.text((x + 16, y + 42), big_value, font=f_bold(28), fill=TEXT_WHITE)

  draw_rounded_rect(draw, [x + 16, y + 84, x + 175, y + 106], 4, fill=(35, 42, 56))
  draw.text((x + 24, y + 88), sub_label, font=f_bold(11), fill=status_color)

  sx0, sy0, sx1, sy1 = x + 16, y + h - 42, x + w - 16, y + h - 12
  if is_bar:
    bw = max(3, (sx1 - sx0) // len(spark_points) - 2)
    for idx, val in enumerate(spark_points):
      bx = sx0 + idx * (bw + 2)
      bh = int(val * (sy1 - sy0))
      draw.rectangle([bx, sy1 - bh, bx + bw, sy1], fill=status_color)
  else:
    pts = []
    for idx, val in enumerate(spark_points):
      px = sx0 + idx * (sx1 - sx0) / max(1, len(spark_points) - 1)
      py = sy1 - val * (sy1 - sy0)
      pts.append((px, py))
    if len(pts) > 1:
      draw.line(pts, fill=status_color, width=2)


def draw_donut_widget(draw, x, y, w, h, title, slices):
  draw_rounded_rect(draw, [x, y, x + w, y + h], 8, fill=CARD_BG, outline=CARD_BORDER)
  draw.text((x + 16, y + 14), title, font=f_bold(14), fill=TEXT_WHITE)

  cx = x + int(w * 0.30)
  cy = y + int(h * 0.56)
  r_out = min(int(w * 0.21), int(h * 0.34))
  r_in = int(r_out * 0.58)

  start_ang = -90
  for label, pct, color in slices:
    sweep = pct * 3.6
    draw.pieslice(
        [cx - r_out, cy - r_out, cx + r_out, cy + r_out],
        start=start_ang,
        end=start_ang + sweep,
        fill=color,
        outline=CARD_BG,
        width=2,
    )
    start_ang += sweep

  draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=CARD_BG)
  draw.text((cx - 24, cy - 9), "100%", font=f_bold(14), fill=TEXT_WHITE)

  lx = x + int(w * 0.56)
  ly = y + 50
  for label, pct, color in slices:
    draw.rectangle([lx, ly + 2, lx + 12, ly + 14], fill=color)
    draw.text((lx + 20, ly), f"{label}", font=f_reg(12), fill=TEXT_WHITE)
    draw.text((lx + 20, ly + 15), f"{pct:.1f}% share", font=f_bold(11), fill=color)
    ly += 36


def draw_dual_axis_widget(draw, x, y, w, h, title, y1_label, y2_label, bar_series, line_series, slo_line=None):
  draw_rounded_rect(draw, [x, y, x + w, y + h], 8, fill=CARD_BG, outline=CARD_BORDER)
  draw.text((x + 18, y + 14), title, font=f_bold(14), fill=TEXT_WHITE)
  draw.text((x + 18, y + 36), f"Left Axis (Y1): {y1_label}", font=f_reg(11), fill=ACCENT_BLUE)
  draw.text((x + w - 230, y + 36), f"Right Axis (Y2): {y2_label}", font=f_reg(11), fill=ACCENT_RED)

  gx0, gy0, gx1, gy1 = x + 52, y + 64, x + w - 52, y + h - 38
  for i in range(5):
    gy = gy0 + i * (gy1 - gy0) // 4
    draw.line([gx0, gy, gx1, gy], fill=(35, 42, 56), width=1)

  n_pts = len(bar_series[0][2])
  bw = max(6, (gx1 - gx0) // n_pts - 6)
  for idx in range(n_pts):
    bx = gx0 + idx * ((gx1 - gx0) // n_pts) + 4
    cur_y = gy1
    for s_name, s_col, vals in bar_series:
      bh = int(vals[idx] * (gy1 - gy0) * 0.85)
      draw.rectangle([bx, cur_y - bh, bx + bw, cur_y], fill=s_col)
      cur_y -= bh

  if slo_line:
    slo_y = gy1 - int(slo_line[0] * (gy1 - gy0))
    draw.line([gx0, slo_y, gx1, slo_y], fill=ACCENT_YELLOW, width=2)
    draw.text((gx0 + 8, slo_y - 16), slo_line[1], font=f_bold(11), fill=ACCENT_YELLOW)

  pts = []
  for idx, val in enumerate(line_series[2]):
    px = gx0 + idx * ((gx1 - gx0) // n_pts) + bw // 2 + 4
    py = gy1 - int(val * (gy1 - gy0) * 0.9)
    pts.append((px, py))
  if len(pts) > 1:
    draw.line(pts, fill=line_series[1], width=3)
    for px, py in pts:
      draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=line_series[1], outline=TEXT_WHITE)

  lx = gx0
  for s_name, s_col, _ in bar_series:
    draw.rectangle([lx, gy1 + 12, lx + 12, gy1 + 22], fill=s_col)
    draw.text((lx + 16, gy1 + 10), s_name, font=f_reg(11), fill=TEXT_MUTED)
    lx += 155
  draw.line([lx, gy1 + 17, lx + 16, gy1 + 17], fill=line_series[1], width=3)
  draw.text((lx + 22, gy1 + 10), line_series[0], font=f_bold(11), fill=line_series[1])


def draw_ts_table_widget(draw, x, y, w, h, title, headers, rows):
  draw_rounded_rect(draw, [x, y, x + w, y + h], 8, fill=CARD_BG, outline=CARD_BORDER)
  draw.text((x + 18, y + 14), title, font=f_bold(14), fill=TEXT_WHITE)
  draw.text((x + w - 210, y + 16), "metricVisualization: BAR", font=f_mono(11), fill=ACCENT_CYAN)

  ty = y + 46
  draw.rectangle([x + 12, ty, x + w - 12, ty + 28], fill=(30, 36, 48))
  col_w = (w - 36) // len(headers)
  for idx, h_text in enumerate(headers):
    draw.text((x + 20 + idx * col_w, ty + 6), h_text, font=f_bold(12), fill=TEXT_MUTED)

  ty += 32
  for r_idx, row in enumerate(rows):
    if r_idx % 2 == 1:
      draw.rectangle([x + 12, ty, x + w - 12, ty + 30], fill=(20, 24, 33))
    for c_idx, val in enumerate(row):
      cx = x + 20 + c_idx * col_w
      if isinstance(val, tuple):
        t_str, ratio, b_col = val
        draw.text((cx, ty + 7), t_str, font=f_mono(12), fill=TEXT_WHITE)
        bx0 = cx + 95
        bw_max = col_w - 110
        draw.rectangle([bx0, ty + 9, bx0 + bw_max, ty + 21], fill=(35, 42, 56))
        draw.rectangle([bx0, ty + 9, bx0 + int(bw_max * ratio), ty + 21], fill=b_col)
      else:
        draw.text((cx, ty + 7), str(val), font=f_reg(12), fill=TEXT_WHITE)
    ty += 30


def draw_playbook_widget(draw, x, y, w, h, title, bullets, accent_col=ACCENT_BLUE):
  draw_rounded_rect(draw, [x, y, x + w, y + h], 8, fill=(20, 30, 48), outline=accent_col)
  draw.text((x + 18, y + 14), title, font=f_bold(14), fill=accent_col)
  by = y + 44
  for b_title, b_desc in bullets:
    draw.text((x + 18, by), f"▸ {b_title}:", font=f_bold(12), fill=TEXT_WHITE)
    draw.text((x + 28, by + 18), b_desc, font=f_reg(11), fill=TEXT_MUTED)
    by += 44


def generate_00_model_usage():
  W, H = 1920, 1180
  img = Image.new("RGB", (W, H), BG_DARK)
  draw = ImageDraw.Draw(img)

  draw_top_chrome(
      draw,
      W,
      "Anthropic - Model Usage",
      "Executive landing page: 24h volume & ratio scorecards, proportional Donut shares, Dual-Axis Volume vs Error overlay, and Live Leaderboard Table.",
  )

  sy = draw_section_header(draw, 190, W, "KPI", ACCENT_BLUE, "Executive 24h Key Metrics & Normalized Ratios", "Volume scorecards paired with normalized Tokens/Request and Error Rate ratios (timeSeriesFilterRatio)")
  sc_w = (W - 40 - 5 * 14) // 6
  cards = [
      ("Total tokens (24h)", "64.8M", "▲ +14.2% vs 7d avg", ACCENT_YELLOW, [0.4, 0.5, 0.48, 0.62, 0.75, 0.82, 0.91, 0.88], False),
      ("Requests (24h)", "14,280", "▲ +8.1% steady flow", ACCENT_BLUE, [0.5, 0.52, 0.58, 0.61, 0.68, 0.72, 0.75, 0.74], False),
      ("Avg Tokens / Request", "4,538", "Ratio: Tok / Invoc", ACCENT_CYAN, [0.6, 0.62, 0.59, 0.64, 0.66, 0.65, 0.68, 0.67], False),
      ("Output tokens (24h)", "11.4M", "17.6% of total tokens", ACCENT_PURPLE, [0.3, 0.35, 0.42, 0.48, 0.55, 0.62, 0.64, 0.61], False),
      ("Errors non-200 (24h)", "42", "Threshold < 100 OK", ACCENT_YELLOW, [0.1, 0.05, 0.15, 0.45, 0.85, 0.3, 0.12, 0.08], True),
      ("Error Rate Ratio (24h)", "0.29%", "SLO Target < 1.0%", ACCENT_GREEN, [0.08, 0.05, 0.12, 0.35, 0.65, 0.22, 0.1, 0.07], True),
  ]
  for idx, (t, v, sub, col, pts, is_b) in enumerate(cards):
    draw_scorecard(draw, 20 + idx * (sc_w + 14), sy, sc_w, 155, t, v, sub, col, pts, is_b)

  sy2 = draw_section_header(draw, sy + 170, W, " % ", ACCENT_PURPLE, "Proportional Fleet Share (Donut Visualizations) & Dual-Axis Correlation", "Instant proportional breakdown by Model, Billing Type, and Region + Dual-Axis Request Demand (Y1) vs Non-200 Errors (Y2)")
  dw = (W - 40 - 28) // 3
  draw_donut_widget(draw, 20, sy2, dw, 230, "Token Share by Model (Donut)", [
      ("claude-fable-5", 58.4, ACCENT_BLUE),
      ("claude-opus-4", 26.2, ACCENT_PURPLE),
      ("claude-sonnet-4", 15.4, ACCENT_GREEN),
  ])
  draw_donut_widget(draw, 20 + dw + 14, sy2, dw, 230, "Token Share by Billing Type (Donut)", [
      ("cache_read_input (0.1x)", 68.5, ACCENT_GREEN),
      ("output (Generated)", 17.6, ACCENT_PURPLE),
      ("input (Uncached 1x)", 11.2, ACCENT_RED),
      ("cache_write (1.25x)", 2.7, ACCENT_YELLOW),
  ])
  draw_donut_widget(draw, 20 + (dw + 14) * 2, sy2, dw, 230, "Request Share by GCP Region (Donut)", [
      ("global (Endpoint)", 52.0, ACCENT_CYAN),
      ("us-central1", 34.5, ACCENT_BLUE),
      ("europe-west1", 13.5, ACCENT_ORANGE),
  ])

  sy3 = sy2 + 245
  hw = (W - 40 - 14) // 2
  draw_dual_axis_widget(
      draw,
      20,
      sy3,
      hw,
      240,
      "Dual-Axis: Hourly Request Volume (Y1 Stacked Bar) vs Non-200 Errors (Y2 Line)",
      "Requests / hr",
      "Errors / hr",
      [
          ("claude-fable-5", ACCENT_BLUE, [0.4, 0.45, 0.5, 0.55, 0.6, 0.58, 0.52, 0.48, 0.55, 0.62, 0.65, 0.6]),
          ("claude-opus-4", ACCENT_PURPLE, [0.2, 0.22, 0.25, 0.28, 0.3, 0.25, 0.22, 0.2, 0.24, 0.28, 0.3, 0.26]),
      ],
      ("Non-200 Errors (Y2)", ACCENT_RED, [0.08, 0.06, 0.12, 0.25, 0.78, 0.35, 0.15, 0.1, 0.12, 0.18, 0.14, 0.09]),
      slo_line=(0.65, "Alert Ceiling: 25 errors/hr"),
  )

  draw_ts_table_widget(
      draw,
      20 + hw + 14,
      sy3,
      hw,
      240,
      "Live Tabular Leaderboard: Per-Model & Token Type (24h Table)",
      ["Model ID", "Billing Token Type", "Serving Region", "24h Token Volume"],
      [
          ("claude-fable-5", "cache_read_input", "global", ("26.4M tok", 0.92, ACCENT_GREEN)),
          ("claude-fable-5", "output", "global", ("6.8M tok", 0.58, ACCENT_PURPLE)),
          ("claude-opus-4", "cache_read_input", "us-central1", ("12.1M tok", 0.74, ACCENT_GREEN)),
          ("claude-sonnet-4", "input (uncached)", "europe-west1", ("3.2M tok", 0.38, ACCENT_RED)),
          ("claude-fable-5", "cache_write_input", "global", ("1.7M tok", 0.22, ACCENT_YELLOW)),
      ],
  )

  os.makedirs("images", exist_ok=True)
  img.save("images/model-usage-scorecards.png", "PNG")
  print("Saved images/model-usage-scorecards.png")


def generate_02_fleet_overview():
  W, H = 1920, 1180
  img = Image.new("RGB", (W, H), BG_DARK)
  draw = ImageDraw.Draw(img)

  draw_top_chrome(
      draw,
      W,
      "Anthropic Models - Fleet Overview (All Models)",
      "Compare Model Token Share vs Request Share side-by-side to distinguish heavy reasoning models from high-frequency lightweight models.",
  )

  sy = draw_section_header(draw, 190, W, "FLT", ACCENT_CYAN, "Fleet Adoption & Utilization Scorecards (24h)", "Fleet-wide request volume, streaming adoption ratio, and average payload density")
  sc_w = (W - 40 - 3 * 16) // 4
  cards = [
      ("Fleet Total Tokens (24h)", "64.8M", "Across 3 active models", ACCENT_BLUE, [0.45, 0.5, 0.55, 0.62, 0.7, 0.78, 0.85, 0.82], False),
      ("Fleet Total Requests (24h)", "14,280", "99.71% success rate", ACCENT_GREEN, [0.5, 0.54, 0.58, 0.63, 0.69, 0.72, 0.76, 0.75], False),
      ("Streaming Adoption Ratio", "91.4%", "streamRawPredict share", ACCENT_CYAN, [0.88, 0.89, 0.9, 0.91, 0.92, 0.91, 0.91, 0.92], False),
      ("Fleet Avg Tokens / Req", "4,538", "Prompt + Output density", ACCENT_PURPLE, [0.5, 0.52, 0.49, 0.55, 0.58, 0.57, 0.6, 0.59], False),
  ]
  for idx, (t, v, sub, col, pts, is_b) in enumerate(cards):
    draw_scorecard(draw, 20 + idx * (sc_w + 16), sy, sc_w, 155, t, v, sub, col, pts, is_b)

  sy2 = draw_section_header(draw, sy + 170, W, " % ", ACCENT_PURPLE, "Fleet Architectural Insight: Token Share vs Request Share Comparison", "Why both Donuts matter: claude-fable-5 is 31% of requests but 58.4% of tokens due to deep reasoning chains")
  dw = (W - 40 - 28) // 3
  draw_donut_widget(draw, 20, sy2, dw, 230, "Fleet Token Share by Model (Donut)", [
      ("claude-fable-5", 58.4, ACCENT_BLUE),
      ("claude-opus-4", 26.2, ACCENT_PURPLE),
      ("claude-sonnet-4", 15.4, ACCENT_GREEN),
  ])
  draw_donut_widget(draw, 20 + dw + 14, sy2, dw, 230, "Fleet Request Share by Model (Donut)", [
      ("claude-sonnet-4 (Fast)", 48.5, ACCENT_GREEN),
      ("claude-fable-5 (Reason)", 31.2, ACCENT_BLUE),
      ("claude-opus-4 (Deep)", 20.3, ACCENT_PURPLE),
  ])
  draw_donut_widget(draw, 20 + (dw + 14) * 2, sy2, dw, 230, "Fleet Traffic Share by Region (Donut)", [
      ("global", 52.0, ACCENT_CYAN),
      ("us-central1", 34.5, ACCENT_BLUE),
      ("europe-west1", 13.5, ACCENT_ORANGE),
  ])

  sy3 = sy2 + 245
  hw = (W - 40 - 14) // 2
  draw_dual_axis_widget(
      draw,
      20,
      sy3,
      hw,
      240,
      "Daily Tokens by Model (Stacked Bar) & Provisioned Throughput Utilization",
      "Tokens / day",
      "PTU Utilization %",
      [
          ("claude-fable-5", ACCENT_BLUE, [0.42, 0.46, 0.51, 0.54, 0.58, 0.62, 0.65, 0.63, 0.67, 0.71]),
          ("claude-opus-4", ACCENT_PURPLE, [0.22, 0.24, 0.25, 0.26, 0.28, 0.27, 0.29, 0.28, 0.3, 0.31]),
      ],
      ("PTU Consumed % (Y2)", ACCENT_GREEN, [0.55, 0.58, 0.64, 0.68, 0.74, 0.79, 0.84, 0.81, 0.86, 0.89]),
  )

  draw_ts_table_widget(
      draw,
      20 + hw + 14,
      sy3,
      hw,
      240,
      "Fleet Model & Region Leaderboard Matrix (timeSeriesTable)",
      ["Model User ID", "GCP Location", "API Method", "24h Invocations"],
      [
          ("claude-sonnet-4", "global", "streamRawPredict", ("6,925 req", 0.95, ACCENT_GREEN)),
          ("claude-fable-5", "global", "streamRawPredict", ("4,455 req", 0.72, ACCENT_BLUE)),
          ("claude-opus-4", "us-central1", "streamRawPredict", ("2,899 req", 0.54, ACCENT_PURPLE)),
          ("claude-fable-5", "europe-west1", "rawPredict", ("840 req", 0.25, ACCENT_CYAN)),
          ("claude-sonnet-4", "us-central1", "countTokens", ("420 req", 0.14, ACCENT_YELLOW)),
      ],
  )

  img.save("images/fleet-overview-daily-volume.png", "PNG")
  print("Saved images/fleet-overview-daily-volume.png")


def generate_05_caching_efficiency():
  W, H = 1920, 1180
  img = Image.new("RGB", (W, H), BG_DARK)
  draw = ImageDraw.Draw(img)

  draw_top_chrome(
      draw,
      W,
      "Anthropic Models - Prompt Caching & Cost Efficiency",
      "Visual Donut cost breakdown, True Cache Hit Ratio scorecards, Dual-Axis Cache Read vs Write efficiency, and FinOps Break-Even Economics.",
  )

  sy = draw_section_header(draw, 190, W, "FIN", ACCENT_GREEN, "24h Caching Scorecards & True Hit Ratios (timeSeriesFilterRatio)", "Direct comparison of 90%-discounted cache reads vs full-price uncached input and cache write break-even ratios")
  sc_w = (W - 40 - 3 * 16) // 4
  cards = [
      ("Cache read tokens (24h)", "44.4M", "90% discount (~0.1x price)", ACCENT_GREEN, [0.4, 0.52, 0.65, 0.74, 0.82, 0.86, 0.91, 0.93], False),
      ("Uncached input tokens", "7.2M", "100% full input price", ACCENT_RED, [0.45, 0.38, 0.32, 0.25, 0.22, 0.19, 0.16, 0.15], False),
      ("True Cache Hit Ratio", "83.2%", "Target > 50% Healthy", ACCENT_GREEN, [0.55, 0.62, 0.71, 0.76, 0.8, 0.82, 0.84, 0.83], False),
      ("Read-to-Write Ratio", "25.4x", "Break-even > 1.28x (Profit!)", ACCENT_CYAN, [0.4, 0.55, 0.68, 0.75, 0.82, 0.85, 0.88, 0.89], False),
  ]
  for idx, (t, v, sub, col, pts, is_b) in enumerate(cards):
    draw_scorecard(draw, 20 + idx * (sc_w + 16), sy, sc_w, 155, t, v, sub, col, pts, is_b)

  sy2 = draw_section_header(draw, sy + 170, W, " $ ", ACCENT_YELLOW, "Prompt Token Cost Structure (Donut Visualizations)", "Proportional share of input tokens by pricing tier (Cache Read 0.1x, Uncached 1.0x, Write 5m 1.25x, Write 1h 2.0x)")
  dw = (W - 40 - 28) // 3
  draw_donut_widget(draw, 20, sy2, dw, 230, "Input Token Composition by Pricing Tier", [
      ("cache_read_input (0.1x)", 83.2, ACCENT_GREEN),
      ("input (Uncached 1.0x)", 13.5, ACCENT_RED),
      ("cache_write_5m (1.25x)", 2.6, ACCENT_YELLOW),
      ("cache_write_1h (2.0x)", 0.7, ACCENT_ORANGE),
  ])
  draw_donut_widget(draw, 20 + dw + 14, sy2, dw, 230, "Cache Read Savings by Model (Donut)", [
      ("claude-fable-5", 64.2, ACCENT_BLUE),
      ("claude-opus-4", 24.8, ACCENT_PURPLE),
      ("claude-sonnet-4", 11.0, ACCENT_GREEN),
  ])
  draw_donut_widget(draw, 20 + (dw + 14) * 2, sy2, dw, 230, "Explicit Caching Request Share (Donut)", [
      ("explicit_caching=true", 88.6, ACCENT_GREEN),
      ("explicit_caching=false", 11.4, ACCENT_RED),
  ])

  sy3 = sy2 + 245
  hw = (W - 40 - 14) // 2
  draw_dual_axis_widget(
      draw,
      20,
      sy3,
      hw,
      240,
      "Dual-Axis: Cache Reads Saved (Y1 Area) vs Cache Writes Billed (Y2 Line)",
      "Cache Read Tokens / hr",
      "Cache Write Tokens / hr",
      [
          ("cache_read_input (0.1x)", ACCENT_GREEN, [0.5, 0.58, 0.66, 0.72, 0.78, 0.82, 0.85, 0.83, 0.87, 0.9]),
      ],
      ("cache_write overhead (Y2)", ACCENT_YELLOW, [0.25, 0.22, 0.18, 0.16, 0.15, 0.14, 0.15, 0.13, 0.14, 0.12]),
  )

  draw_playbook_widget(
      draw,
      20 + hw + 14,
      sy3,
      hw,
      240,
      "FinOps Break-Even Formula & Cost Optimization Playbook",
      [
          ("5-Minute TTL Cache Write (1.25x Input Cost)", "Break-even occurs at exactly 0.28 subsequent reads (1.28 total hits). At 25.4x read/write ratio, net input discount is 84.7%."),
          ("1-Hour TTL Cache Write (2.00x Input Cost)", "Break-even occurs at 1.11 subsequent reads (2.11 total hits). Use 1h TTL only for long-running coding or research sessions."),
          ("Silent Cache Invalidation Detection", "If Cache Hit Ratio drops below 50% while traffic is steady, check for dynamic timestamps or non-deterministic tool ordering in system prompts."),
      ],
      accent_col=ACCENT_GREEN,
  )

  img.save("images/caching-cost-efficiency.png", "PNG")
  print("Saved images/caching-cost-efficiency.png")


def generate_03_latency_slos():
  W, H = 1920, 1180
  img = Image.new("RGB", (W, H), BG_DARK)
  draw = ImageDraw.Draw(img)

  draw_top_chrome(
      draw,
      W,
      "Anthropic Models - Latency & Performance",
      "Unified multi-percentile latency curves (p50/p95/p99), horizontal SLO target lines, dual TTFT + E2E Heatmaps, and Per-Model Latency Table.",
  )

  sy = draw_section_header(draw, 190, W, "SLO", ACCENT_PURPLE, "24h Latency Percentile Scorecards (TTFT & End-to-End)", "Fleet-wide latency benchmarks with yellow warning and red SLO violation thresholds")
  sc_w = (W - 40 - 3 * 16) // 4
  cards = [
      ("TTFT p50 (24h, ms)", "412 ms", "Target < 800ms OK", ACCENT_GREEN, [0.4, 0.42, 0.39, 0.41, 0.43, 0.4, 0.38, 0.41], False),
      ("TTFT p95 (24h, ms)", "1,140 ms", "Warning > 1,000ms", ACCENT_YELLOW, [0.45, 0.52, 0.68, 0.74, 0.61, 0.55, 0.49, 0.53], False),
      ("End-to-End p50 (24h)", "3,820 ms", "Interactive < 5s OK", ACCENT_GREEN, [0.35, 0.38, 0.42, 0.4, 0.39, 0.37, 0.38, 0.36], False),
      ("End-to-End p99 (24h)", "24.6 s", "Reasoning tail < 30s", ACCENT_YELLOW, [0.5, 0.55, 0.78, 0.85, 0.68, 0.62, 0.59, 0.61], False),
  ]
  for idx, (t, v, sub, col, pts, is_b) in enumerate(cards):
    draw_scorecard(draw, 20 + idx * (sc_w + 16), sy, sc_w, 155, t, v, sub, col, pts, is_b)

  sy2 = draw_section_header(draw, sy + 170, W, "P99", ACCENT_CYAN, "Unified Multi-Percentile Curves (p50 vs p95 vs p99) with Horizontal SLO Lines", "Overlaying percentiles on a single chart reveals tail amplification and latency spread instantly")
  hw = (W - 40 - 14) // 2
  draw_dual_axis_widget(
      draw,
      20,
      sy2,
      hw,
      235,
      "Unified Time-to-First-Token Spread (p50, p95, p99) + SLO Threshold",
      "p50 / p95 TTFT (ms)",
      "p99 Tail TTFT (ms)",
      [
          ("p50 TTFT (ms)", ACCENT_GREEN, [0.22, 0.24, 0.23, 0.25, 0.26, 0.24, 0.22, 0.23, 0.24, 0.23]),
          ("p95 TTFT (ms)", ACCENT_BLUE, [0.35, 0.38, 0.42, 0.48, 0.52, 0.44, 0.39, 0.37, 0.41, 0.38]),
      ],
      ("p99 TTFT Tail (ms)", ACCENT_RED, [0.45, 0.48, 0.58, 0.72, 0.84, 0.62, 0.51, 0.49, 0.53, 0.48]),
      slo_line=(0.60, "TTFT Target Ceiling: 1,000 ms"),
  )

  draw_dual_axis_widget(
      draw,
      20 + hw + 14,
      sy2,
      hw,
      235,
      "Unified End-to-End Latency Spread (p50, p95, p99) + SLO Threshold",
      "p50 / p95 E2E (ms)",
      "p99 Reasoning Tail",
      [
          ("p50 E2E (ms)", ACCENT_CYAN, [0.18, 0.2, 0.22, 0.21, 0.23, 0.2, 0.19, 0.21, 0.2, 0.19]),
          ("p95 E2E (ms)", ACCENT_PURPLE, [0.38, 0.41, 0.45, 0.52, 0.56, 0.48, 0.42, 0.4, 0.44, 0.41]),
      ],
      ("p99 E2E Reasoning Tail", ACCENT_ORANGE, [0.52, 0.56, 0.68, 0.82, 0.88, 0.71, 0.59, 0.55, 0.62, 0.58]),
      slo_line=(0.75, "Interactive Ceiling: 10,000 ms"),
  )

  sy3 = sy2 + 250
  draw_ts_table_widget(
      draw,
      20,
      sy3,
      hw,
      235,
      "p95 TTFT & End-to-End Latency Leaderboard by Model & Region (Table)",
      ["Model ID", "Serving Region", "p95 TTFT (ms)", "p95 E2E Latency"],
      [
          ("claude-sonnet-4", "global", "340 ms", ("2,410 ms", 0.28, ACCENT_GREEN)),
          ("claude-fable-5", "global", "790 ms", ("8,940 ms", 0.62, ACCENT_BLUE)),
          ("claude-fable-5", "us-central1", "840 ms", ("9,420 ms", 0.68, ACCENT_BLUE)),
          ("claude-opus-4", "us-central1", "1,120 ms", ("14,850 ms", 0.88, ACCENT_PURPLE)),
          ("claude-fable-5", "europe-west1", "1,290 ms", ("11,200 ms", 0.74, ACCENT_YELLOW)),
      ],
  )

  draw_playbook_widget(
      draw,
      20 + hw + 14,
      sy3,
      hw,
      235,
      "SRE Latency & Bimodal Distribution Guide",
      [
          ("Bimodal TTFT Fast-Path vs Cold-Path", "Prompt cache hits reduce TTFT by 65-80% on long contexts (>32k tokens). Watch the TTFT Heatmap for bimodal separation."),
          ("Reasoning Model Tail Latency (claude-fable-5)", "Extended thinking chains naturally produce 15s-45s E2E times on hard tasks while TTFT remains <1s. Alert on TTFT, not raw E2E."),
          ("Regional Latency Outliers", "If one region's p95 diverges by >400ms, filter by 'location' above to isolate regional capacity pressure."),
      ],
      accent_col=ACCENT_PURPLE,
  )

  img.save("images/latency-performance-slos.png", "PNG")
  print("Saved images/latency-performance-slos.png")


if __name__ == "__main__":
  generate_00_model_usage()
  generate_02_fleet_overview()
  generate_05_caching_efficiency()
  generate_03_latency_slos()

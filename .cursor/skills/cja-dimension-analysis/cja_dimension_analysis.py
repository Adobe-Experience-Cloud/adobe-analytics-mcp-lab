#!/usr/bin/env python3
"""
CJA Dimension Analysis Script v1.0
====================================

Analyzes CJA dimension data collected by the cja-dimension-analysis skill.
Performs cardinality classification, skew/distribution analysis, trend detection,
anomaly detection (z-score), data quality scoring, comparisons, and forecasting.
Generates both JSON results and comprehensive reports (markdown or HTML).

This script is called by the cja-dimension-analysis skill after data collection phases.

Usage:
    python3 cja_dimension_analysis.py <analysis_json> <data_view_name> <data_view_id> \
        [output_dir] [--format=markdown|html] [--keep-analyses=N]

Arguments:
    analysis_json    - Path to JSON file with dimension data collected by SKILL.md workflow
    data_view_name   - Name of the data view being analyzed
    data_view_id     - ID of the data view being analyzed
    output_dir       - (Optional) Directory for output files (default: current directory)
    --format=FORMAT  - (Optional) Output format: 'markdown' or 'html' (default: html)
    --keep-analyses=N - (Optional) Keep N recent analyses, delete older ones (default: 5)

Output Files:
    - dimension_analysis_results_YYYY-MM-DD_HH-MM.json: Raw analysis data
    - DIMENSION_ANALYSIS_REPORT_YYYY-MM-DD_HH-MM.md or .html: Comprehensive report

Expected input JSON structure (collected by SKILL.md workflow):
{
  "analysis_metadata": {
    "data_view_name": "...",
    "data_view_id": "...",
    "date_range": "...",
    "analyses_run": ["cardinality", "distribution", "trends", "anomalies", "errors"],
    "generated_at": "ISO8601"
  },
  "dimensions": [
    {
      "id": "variables/page",
      "name": "Page",
      "cardinality": {"uniqueValueCount": 1500, "level": "HIGH"},
      "distribution": {"gini": 0.72, "skewLabel": "High skew", "topValues": [...]},
      "trends": {"period1": "...", "period2": "...", "changes": [...], "newValues": [], "disappearedValues": []},
      "anomalies": [...],
      "errors": {"errorPatterns": [...], "missingDataPct": 3.2}
    }
  ],
  "comparisons": [...],
  "summary": {}
}

Version: 1.0.0
Last Updated: March 13, 2026
"""

import json
import sys
import os
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Cardinality helpers
# ---------------------------------------------------------------------------

CARDINALITY_LEVELS = [
    ("VERY_HIGH", 10000),
    ("HIGH",      1000),
    ("MEDIUM",    100),
    ("LOW",       0),
]

CARDINALITY_BADGES = {
    "LOW":       ("🟢", "Low", "< 100 unique values — fast queries"),
    "MEDIUM":    ("🟡", "Medium", "100–1,000 unique values"),
    "HIGH":      ("🟠", "High", "1,000–10,000 unique values — monitor query performance"),
    "VERY_HIGH": ("🔴", "Very High", "> 10,000 unique values — can slow queries"),
}


def classify_cardinality(count: int) -> str:
    for level, threshold in CARDINALITY_LEVELS:
        if count > threshold:
            return level
    return "LOW"


# ---------------------------------------------------------------------------
# Distribution / skew helpers
# ---------------------------------------------------------------------------

def compute_gini(values: list[float]) -> float:
    """Compute Gini coefficient for a list of non-negative values."""
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumulative = 0.0
    for i, v in enumerate(sorted_vals):
        cumulative += (2 * (i + 1) - n - 1) * v
    total = sum(sorted_vals)
    return cumulative / (n * total) if total else 0.0


def classify_skew(top1_pct: float, top5_pct: float, top10_pct: float) -> str:
    if top1_pct >= 50:
        return "Extreme skew"
    if top1_pct >= 30:
        return "High skew"
    if top10_pct < 50:
        return "Long tail"
    return "Moderate"


def enrich_distribution(dim_data: dict) -> dict:
    """Compute derived distribution metrics from raw topValues list."""
    dist = dim_data.get("distribution", {})
    top_values = dist.get("topValues", [])
    if not top_values:
        return dim_data

    metrics = [float(v.get("metric", 0)) for v in top_values]
    total = sum(metrics)
    if total == 0:
        return dim_data

    for i, v in enumerate(top_values):
        v["pct"] = round(metrics[i] / total * 100, 2)
        v["cumulative"] = round(sum(metrics[: i + 1]) / total * 100, 2)

    top1_pct = metrics[0] / total * 100 if metrics else 0
    top5_pct = sum(metrics[:5]) / total * 100 if len(metrics) >= 5 else sum(metrics) / total * 100
    top10_pct = sum(metrics[:10]) / total * 100 if len(metrics) >= 10 else sum(metrics) / total * 100

    dist["top1Pct"] = round(top1_pct, 2)
    dist["top5Pct"] = round(top5_pct, 2)
    dist["top10Pct"] = round(top10_pct, 2)
    dist["gini"] = round(compute_gini(metrics), 3)
    dist["skewLabel"] = classify_skew(top1_pct, top5_pct, top10_pct)
    dim_data["distribution"] = dist
    return dim_data


# ---------------------------------------------------------------------------
# Anomaly detection (z-score)
# ---------------------------------------------------------------------------

def detect_anomalies_zscore(time_series: list[dict], threshold: float = 2.0) -> list[dict]:
    """Detect anomalies in a time series using z-score method."""
    if len(time_series) < 3:
        return []

    values = [float(p.get("metric", 0)) for p in time_series]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance) if variance > 0 else 0

    anomalies = []
    for i, (point, val) in enumerate(zip(time_series, values)):
        if std == 0:
            continue
        z = abs(val - mean) / std
        if z > threshold:
            atype = "spike" if val > mean else "drop"
            anomalies.append({
                "date": point.get("date", f"period_{i}"),
                "value": val,
                "mean": round(mean, 2),
                "zScore": round(z, 2),
                "type": atype,
            })
    return anomalies


# ---------------------------------------------------------------------------
# Linear regression / forecasting
# ---------------------------------------------------------------------------

def linear_regression(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """Simple linear regression. Returns (slope, intercept, r_squared)."""
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, sum_y / n, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    # R²
    y_mean = sum_y / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return round(slope, 4), round(intercept, 4), round(max(0, min(1, r2)), 4)


def classify_forecast(slope: float, r2: float, mean: float) -> dict:
    """Classify forecast trend and confidence."""
    if r2 >= 0.7:
        confidence = "High"
    elif r2 >= 0.4:
        confidence = "Medium"
    else:
        confidence = "Low"

    if mean == 0:
        direction = "Flat"
    elif slope > mean * 0.05:
        direction = "Upward"
    elif slope < -mean * 0.05:
        direction = "Downward"
    else:
        direction = "Flat"

    return {"direction": direction, "confidence": confidence}


# ---------------------------------------------------------------------------
# Data quality scoring
# ---------------------------------------------------------------------------

def score_data_quality(error_data: dict) -> tuple[str, str]:
    """Return (severity, label) based on missing data percentage."""
    pct = error_data.get("missingDataPct", 0)
    if pct >= 20:
        return "critical", f"⛔ Critical ({pct:.1f}% missing)"
    elif pct >= 5:
        return "warning", f"⚠️ Warning ({pct:.1f}% missing)"
    else:
        return "ok", f"✅ OK ({pct:.1f}% missing)"


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def analyze(raw: dict) -> dict:
    """Run all analysis enrichments on the raw input data."""
    metadata = raw.get("analysis_metadata", {})
    dimensions = raw.get("dimensions", [])

    enriched_dims = []
    summary = {
        "totalDimensions": len(dimensions),
        "cardinalityBreakdown": defaultdict(int),
        "skewBreakdown": defaultdict(int),
        "totalAnomalies": 0,
        "criticalDataQualityCount": 0,
        "warningDataQualityCount": 0,
        "highCardinalityCount": 0,
    }

    for dim in dimensions:
        # Cardinality
        card = dim.get("cardinality", {})
        count = card.get("uniqueValueCount", 0)
        card["level"] = classify_cardinality(count)
        card["badge"] = CARDINALITY_BADGES.get(card["level"], ("⚪", "Unknown", ""))
        dim["cardinality"] = card

        level = card["level"]
        summary["cardinalityBreakdown"][level] += 1
        if level in ("HIGH", "VERY_HIGH"):
            summary["highCardinalityCount"] += 1

        # Distribution enrichment
        dim = enrich_distribution(dim)
        skew_label = dim.get("distribution", {}).get("skewLabel", "Unknown")
        summary["skewBreakdown"][skew_label] += 1

        # Anomaly count
        anomalies = dim.get("anomalies", [])
        summary["totalAnomalies"] += len(anomalies)

        # Data quality
        errors = dim.get("errors", {})
        severity, label = score_data_quality(errors)
        errors["severity"] = severity
        errors["severityLabel"] = label
        dim["errors"] = errors
        if severity == "critical":
            summary["criticalDataQualityCount"] += 1
        elif severity == "warning":
            summary["warningDataQualityCount"] += 1

        enriched_dims.append(dim)

    summary["cardinalityBreakdown"] = dict(summary["cardinalityBreakdown"])
    summary["skewBreakdown"] = dict(summary["skewBreakdown"])

    return {
        "analysis_metadata": metadata,
        "dimensions": enriched_dims,
        "comparisons": raw.get("comparisons", []),
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def generate_markdown(data: dict, data_view_name: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = data.get("analysis_metadata", {})
    dims = data.get("dimensions", [])
    summary = data.get("summary", {})

    lines = [
        f"# CJA Dimension Analysis Report",
        f"**Data View**: {data_view_name}",
        f"**Date Range**: {meta.get('date_range', 'N/A')}",
        f"**Generated**: {now}",
        f"**Dimensions Analyzed**: {summary.get('totalDimensions', 0)}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Dimensions | {summary.get('totalDimensions', 0)} |",
        f"| High / Very High Cardinality | {summary.get('highCardinalityCount', 0)} |",
        f"| Total Anomalies Detected | {summary.get('totalAnomalies', 0)} |",
        f"| Critical Data Quality Issues | {summary.get('criticalDataQualityCount', 0)} |",
        f"| Warning Data Quality Issues | {summary.get('warningDataQualityCount', 0)} |",
        "",
        "### Cardinality Breakdown",
        "",
    ]

    card_bd = summary.get("cardinalityBreakdown", {})
    for level in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]:
        badge_info = CARDINALITY_BADGES.get(level, ("⚪", level, ""))
        lines.append(f"- {badge_info[0]} **{badge_info[1]}**: {card_bd.get(level, 0)} dimensions — {badge_info[2]}")
    lines.append("")

    for dim in dims:
        name = dim.get("name", dim.get("id", "Unknown"))
        dim_id = dim.get("id", "")
        lines += [
            f"---",
            f"",
            f"## {name}",
            f"**ID**: `{dim_id}`",
            "",
        ]

        # Cardinality
        card = dim.get("cardinality", {})
        badge = card.get("badge", ("⚪", "Unknown", ""))
        lines += [
            f"### Cardinality",
            f"- **Unique Values**: {card.get('uniqueValueCount', 'N/A'):,}",
            f"- **Level**: {badge[0]} {badge[1]} — {badge[2]}",
            "",
        ]

        # Distribution
        dist = dim.get("distribution", {})
        if dist:
            lines += [
                f"### Distribution & Skew",
                f"- **Skew**: {dist.get('skewLabel', 'N/A')}",
                f"- **Gini Coefficient**: {dist.get('gini', 'N/A')}",
                f"- **Top 1 value share**: {dist.get('top1Pct', 0):.1f}%",
                f"- **Top 5 value share**: {dist.get('top5Pct', 0):.1f}%",
                f"- **Top 10 value share**: {dist.get('top10Pct', 0):.1f}%",
                "",
            ]
            top_values = dist.get("topValues", [])[:10]
            if top_values:
                lines += [
                    "| Rank | Value | Metric | % of Total | Cumulative % |",
                    "|------|-------|--------|------------|--------------|",
                ]
                for i, v in enumerate(top_values):
                    lines.append(
                        f"| {i+1} | {v.get('value', 'N/A')} | "
                        f"{v.get('metric', 0):,.0f} | {v.get('pct', 0):.1f}% | "
                        f"{v.get('cumulative', 0):.1f}% |"
                    )
                lines.append("")

        # Trends
        trends = dim.get("trends", {})
        if trends:
            new_vals = trends.get("newValues", [])
            gone_vals = trends.get("disappearedValues", [])
            changes = trends.get("changes", [])
            lines += [
                f"### Trends",
                f"- **Period 1**: {trends.get('period1', 'N/A')}",
                f"- **Period 2**: {trends.get('period2', 'N/A')}",
                f"- **New values**: {len(new_vals)}",
                f"- **Disappeared values**: {len(gone_vals)}",
                "",
            ]
            growing = [c for c in changes if c.get("badge") == "🟢 Growing"]
            declining = [c for c in changes if c.get("badge") == "🔴 Declining"]
            if growing:
                lines.append(f"**Top Growing Values**: {', '.join(c.get('value','') for c in growing[:5])}")
            if declining:
                lines.append(f"**Top Declining Values**: {', '.join(c.get('value','') for c in declining[:5])}")
            lines.append("")

        # Anomalies
        anomalies = dim.get("anomalies", [])
        if anomalies:
            lines += [
                f"### Anomalies ({len(anomalies)} detected)",
                "",
                "| Type | Value/Date | Z-Score | Magnitude |",
                "|------|-----------|---------|-----------|",
            ]
            for a in anomalies[:10]:
                lines.append(
                    f"| {a.get('type', 'N/A')} | {a.get('date', a.get('value', 'N/A'))} | "
                    f"{a.get('zScore', 'N/A')} | {a.get('value', 'N/A')} |"
                )
            lines.append("")

        # Data quality
        errors = dim.get("errors", {})
        if errors:
            lines += [
                f"### Data Quality",
                f"- **Status**: {errors.get('severityLabel', 'N/A')}",
                f"- **Missing data**: {errors.get('missingDataPct', 0):.1f}%",
            ]
            patterns = errors.get("errorPatterns", [])
            if patterns:
                lines.append("")
                lines.append("| Error Pattern | Count | % of Total |")
                lines.append("|--------------|-------|------------|")
                for p in patterns:
                    lines.append(
                        f"| `{p.get('pattern', 'N/A')}` | {p.get('count', 0):,} | {p.get('pct', 0):.1f}% |"
                    )
            lines.append("")

        # Forecasts
        forecasts = dim.get("forecasts", [])
        if forecasts:
            lines += [
                f"### Forecasts",
                "",
                "| Value | Direction | Confidence | Trend |",
                "|-------|-----------|------------|-------|",
            ]
            for f in forecasts[:5]:
                lines.append(
                    f"| {f.get('value', 'N/A')} | {f.get('direction', 'N/A')} | "
                    f"{f.get('confidence', 'N/A')} | slope={f.get('slope', 0):.4f} |"
                )
            lines.append("")

    lines += [
        "---",
        "",
        "## Recommendations",
        "",
    ]

    # Generate recommendations based on findings
    recs = []
    for dim in dims:
        name = dim.get("name", dim.get("id", "Unknown"))
        card = dim.get("cardinality", {})
        if card.get("level") in ("HIGH", "VERY_HIGH"):
            recs.append(
                f"🟠 **{name}** — High cardinality ({card.get('uniqueValueCount',0):,} values). "
                f"Consider whether all values are necessary; high cardinality can slow queries."
            )
        errors = dim.get("errors", {})
        if errors.get("severity") == "critical":
            recs.append(
                f"⛔ **{name}** — Critical data quality ({errors.get('missingDataPct',0):.1f}% missing). "
                f"Review data collection for this dimension."
            )
        elif errors.get("severity") == "warning":
            recs.append(
                f"⚠️ **{name}** — Data quality warning ({errors.get('missingDataPct',0):.1f}% missing)."
            )
        if len(dim.get("anomalies", [])) > 0:
            recs.append(
                f"🔍 **{name}** — {len(dim.get('anomalies', []))} anomalies detected. "
                f"Review for data spikes or drops."
            )

    if recs:
        for r in recs:
            lines.append(f"- {r}")
    else:
        lines.append("No critical recommendations — dimensions look healthy.")

    lines += ["", "---", "", "*Generated by cja-dimension-analysis skill*"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------------

def generate_html(data: dict, data_view_name: str, data_view_id: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = data.get("analysis_metadata", {})
    dims = data.get("dimensions", [])
    summary = data.get("summary", {})

    dims_json = json.dumps(dims, default=str)
    summary_json = json.dumps(summary, default=str)

    card_bd = summary.get("cardinalityBreakdown", {})
    card_labels = json.dumps(list(card_bd.keys()))
    card_values = json.dumps(list(card_bd.values()))

    skew_bd = summary.get("skewBreakdown", {})
    skew_labels = json.dumps(list(skew_bd.keys()))
    skew_values = json.dumps(list(skew_bd.values()))

    nav_items = "".join(
        f'<li><a href="#dim-{i}" class="nav-link">{d.get("name", d.get("id",""))}</a></li>'
        for i, d in enumerate(dims)
    )

    dim_sections = ""
    for i, dim in enumerate(dims):
        name = dim.get("name", dim.get("id", "Unknown"))
        dim_id = dim.get("id", "")

        card = dim.get("cardinality", {})
        card_count = card.get("uniqueValueCount", 0)
        card_level = card.get("level", "UNKNOWN")
        badge_info = CARDINALITY_BADGES.get(card_level, ("⚪", card_level, ""))
        card_color = {"LOW": "#22c55e", "MEDIUM": "#eab308", "HIGH": "#f97316", "VERY_HIGH": "#ef4444"}.get(card_level, "#6b7280")

        dist = dim.get("distribution", {})
        top_values = dist.get("topValues", [])[:10]
        tv_labels = json.dumps([v.get("value", "N/A") for v in top_values])
        tv_values = json.dumps([v.get("metric", 0) for v in top_values])

        errors = dim.get("errors", {})
        err_severity_color = {"ok": "#22c55e", "warning": "#eab308", "critical": "#ef4444"}.get(
            errors.get("severity", "ok"), "#6b7280"
        )

        anomalies = dim.get("anomalies", [])
        anomaly_rows = "".join(
            f"<tr><td>{a.get('type','N/A')}</td><td>{a.get('date', a.get('value','N/A'))}</td>"
            f"<td>{a.get('zScore','N/A')}</td></tr>"
            for a in anomalies[:5]
        )

        dist_table_rows = "".join(
            f"<tr><td>{j+1}</td><td>{v.get('value','N/A')}</td>"
            f"<td>{v.get('metric',0):,.0f}</td>"
            f"<td>{v.get('pct',0):.1f}%</td>"
            f"<td>{v.get('cumulative',0):.1f}%</td></tr>"
            for j, v in enumerate(top_values)
        )

        forecasts = dim.get("forecasts", [])
        forecast_rows = "".join(
            f"<tr><td>{f.get('value','N/A')}</td><td>{f.get('direction','N/A')}</td>"
            f"<td>{f.get('confidence','N/A')}</td></tr>"
            for f in forecasts[:5]
        )

        dim_sections += f"""
        <section id="dim-{i}" class="dim-section">
          <div class="dim-header">
            <h2>{name}</h2>
            <code class="dim-id">{dim_id}</code>
          </div>
          <div class="cards-row">
            <div class="card">
              <div class="card-label">Cardinality</div>
              <div class="card-value" style="color:{card_color}">{badge_info[0]} {badge_info[1]}</div>
              <div class="card-sub">{card_count:,} unique values</div>
            </div>
            <div class="card">
              <div class="card-label">Skew</div>
              <div class="card-value">{dist.get('skewLabel','N/A')}</div>
              <div class="card-sub">Gini: {dist.get('gini','N/A')}</div>
            </div>
            <div class="card">
              <div class="card-label">Data Quality</div>
              <div class="card-value" style="color:{err_severity_color}">{errors.get('severityLabel','N/A')}</div>
              <div class="card-sub">{errors.get('missingDataPct',0):.1f}% missing</div>
            </div>
            <div class="card">
              <div class="card-label">Anomalies</div>
              <div class="card-value">{len(anomalies)}</div>
              <div class="card-sub">detected</div>
            </div>
          </div>

          <details open class="dim-detail">
            <summary>Top Values Distribution</summary>
            <canvas id="chart-{i}" width="600" height="200"></canvas>
            <script>
              (function(){{
                var ctx = document.getElementById('chart-{i}').getContext('2d');
                new Chart(ctx, {{
                  type: 'bar',
                  data: {{
                    labels: {tv_labels},
                    datasets: [{{ label: 'Metric', data: {tv_values},
                      backgroundColor: 'rgba(67,97,238,0.7)', borderColor: 'rgba(67,97,238,1)',
                      borderWidth: 1 }}]
                  }},
                  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
                    scales: {{ y: {{ beginAtZero: true }} }} }}
                }});
              }})();
            </script>
            <table class="data-table">
              <tr><th>#</th><th>Value</th><th>Metric</th><th>% of Total</th><th>Cumulative</th></tr>
              {dist_table_rows}
            </table>
          </details>

          {'<details class="dim-detail"><summary>Anomalies (' + str(len(anomalies)) + ')</summary><table class="data-table"><tr><th>Type</th><th>Date/Value</th><th>Z-Score</th></tr>' + anomaly_rows + '</table></details>' if anomalies else ''}

          {'<details class="dim-detail"><summary>Forecasts (' + str(len(forecasts)) + ' values)</summary><table class="data-table"><tr><th>Value</th><th>Direction</th><th>Confidence</th></tr>' + forecast_rows + '</table></details>' if forecasts else ''}
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CJA Dimension Analysis — {data_view_name}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --accent: #4361ee;
      --accent-light: rgba(67,97,238,0.08);
      --bg: #f8f9fa;
      --card-bg: #ffffff;
      --border: #e9ecef;
      --text: #1a1a2e;
      --text-muted: #6c757d;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: var(--bg); color: var(--text); line-height: 1.6; }}
    header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      color: white; padding: 2rem;
    }}
    header h1 {{ font-size: 1.8rem; font-weight: 700; }}
    header p {{ opacity: 0.9; font-size: 0.9rem; margin-top: 0.25rem; }}
    .layout {{ display: flex; min-height: calc(100vh - 120px); }}
    nav {{
      width: 220px; min-width: 220px; background: var(--card-bg);
      border-right: 1px solid var(--border); padding: 1rem;
      position: sticky; top: 0; height: 100vh; overflow-y: auto;
    }}
    nav h3 {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted);
              margin-bottom: 0.5rem; letter-spacing: 0.05em; }}
    nav ul {{ list-style: none; }}
    nav .nav-link {{ display: block; padding: 0.35rem 0.5rem; color: var(--text);
                    text-decoration: none; font-size: 0.85rem; border-radius: 4px; }}
    nav .nav-link:hover {{ background: var(--accent-light); color: var(--accent); }}
    main {{ flex: 1; padding: 2rem; max-width: 1000px; }}
    .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                      gap: 1rem; margin-bottom: 2rem; }}
    .card {{
      background: var(--card-bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 1rem; text-align: center;
    }}
    .card-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;
                   letter-spacing: 0.05em; margin-bottom: 0.25rem; }}
    .card-value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
    .card-sub {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 0.15rem; }}
    .cards-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                  gap: 0.75rem; margin: 1rem 0; }}
    .dim-section {{ background: var(--card-bg); border: 1px solid var(--border);
                    border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }}
    .dim-header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }}
    .dim-header h2 {{ font-size: 1.2rem; font-weight: 600; }}
    .dim-id {{ font-size: 0.8rem; color: var(--text-muted); background: var(--bg);
               padding: 0.2rem 0.5rem; border-radius: 4px; }}
    details.dim-detail {{ margin-top: 1rem; border: 1px solid var(--border); border-radius: 6px; }}
    details.dim-detail summary {{
      padding: 0.75rem 1rem; cursor: pointer; font-weight: 600;
      font-size: 0.9rem; background: var(--bg); border-radius: 6px;
    }}
    details.dim-detail[open] summary {{ border-bottom: 1px solid var(--border); border-radius: 6px 6px 0 0; }}
    details.dim-detail > *:not(summary) {{ padding: 1rem; }}
    .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 0.75rem; }}
    .data-table th {{ background: var(--bg); padding: 0.5rem; text-align: left;
                      border-bottom: 2px solid var(--border); font-weight: 600; }}
    .data-table td {{ padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--border); }}
    .data-table tr:hover td {{ background: var(--accent-light); }}
    footer {{ text-align: center; padding: 1rem; color: var(--text-muted); font-size: 0.8rem;
              border-top: 1px solid var(--border); }}
    a {{ scroll-behavior: smooth; }}
  </style>
</head>
<body>
  <header>
    <h1>📊 CJA Dimension Analysis</h1>
    <p>Data View: {data_view_name} &nbsp;|&nbsp; {meta.get('date_range','N/A')} &nbsp;|&nbsp; Generated: {now}</p>
  </header>
  <div class="layout">
    <nav>
      <h3>Dimensions</h3>
      <ul>{nav_items}</ul>
    </nav>
    <main>
      <section id="summary">
        <h2 style="margin-bottom:1rem">Executive Summary</h2>
        <div class="summary-cards">
          <div class="card">
            <div class="card-label">Dimensions</div>
            <div class="card-value">{summary.get('totalDimensions',0)}</div>
            <div class="card-sub">analyzed</div>
          </div>
          <div class="card">
            <div class="card-label">High Cardinality</div>
            <div class="card-value" style="color:#f97316">{summary.get('highCardinalityCount',0)}</div>
            <div class="card-sub">HIGH or VERY HIGH</div>
          </div>
          <div class="card">
            <div class="card-label">Anomalies</div>
            <div class="card-value" style="color:var(--accent)">{summary.get('totalAnomalies',0)}</div>
            <div class="card-sub">detected</div>
          </div>
          <div class="card">
            <div class="card-label">Critical DQ</div>
            <div class="card-value" style="color:#ef4444">{summary.get('criticalDataQualityCount',0)}</div>
            <div class="card-sub">data quality issues</div>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem">
          <div style="background:white;border:1px solid var(--border);border-radius:8px;padding:1rem">
            <h3 style="font-size:0.9rem;margin-bottom:0.5rem">Cardinality Distribution</h3>
            <canvas id="chart-cardinality" width="300" height="200"></canvas>
          </div>
          <div style="background:white;border:1px solid var(--border);border-radius:8px;padding:1rem">
            <h3 style="font-size:0.9rem;margin-bottom:0.5rem">Skew Distribution</h3>
            <canvas id="chart-skew" width="300" height="200"></canvas>
          </div>
        </div>
        <script>
          new Chart(document.getElementById('chart-cardinality'), {{
            type: 'doughnut',
            data: {{
              labels: {card_labels},
              datasets: [{{ data: {card_values},
                backgroundColor: ['#22c55e','#eab308','#f97316','#ef4444'] }}]
            }},
            options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
          }});
          new Chart(document.getElementById('chart-skew'), {{
            type: 'doughnut',
            data: {{
              labels: {skew_labels},
              datasets: [{{ data: {skew_values},
                backgroundColor: ['#2ec4b6','#4361ee','#7209b7','#ff9f1c','#e71d36'] }}]
            }},
            options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
          }});
        </script>
      </section>
      {dim_sections}
    </main>
  </div>
  <footer>Generated by cja-dimension-analysis skill &nbsp;|&nbsp; CJA MCP Lab</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# File management helpers
# ---------------------------------------------------------------------------

def cleanup_old_files(output_dir: Path, prefix: str, keep: int):
    if keep == 0:
        return
    files = sorted(output_dir.glob(f"{prefix}*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_file in files[keep:]:
        try:
            old_file.unlink()
            print(f"  🗑️  Removed old file: {old_file.name}")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    analysis_json_path = sys.argv[1]
    data_view_name = sys.argv[2]
    data_view_id = sys.argv[3]

    output_dir = Path(".")
    fmt = "html"
    keep_analyses = 5

    for arg in sys.argv[4:]:
        if arg.startswith("--format="):
            fmt = arg.split("=", 1)[1].lower()
        elif arg.startswith("--keep-analyses="):
            keep_analyses = int(arg.split("=", 1)[1])
        elif not arg.startswith("--"):
            output_dir = Path(arg)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🔍 CJA Dimension Analysis")
    print(f"   Data View: {data_view_name}")
    print(f"   Input:     {analysis_json_path}")
    print(f"   Output:    {output_dir} ({fmt})")
    print()

    # Load raw data
    print("📂 Loading analysis data...")
    with open(analysis_json_path) as f:
        raw = json.load(f)

    # Run analysis enrichment
    print("⚙️  Running analysis pipeline...")
    enriched = analyze(raw)

    # Timestamp for output files
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Save enriched JSON
    json_path = output_dir / f"dimension_analysis_results_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(enriched, f, indent=2, default=str)
    print(f"✅ Analysis JSON saved: {json_path} ({json_path.stat().st_size:,} bytes)")

    # Generate report
    print(f"📝 Generating {fmt.upper()} report...")
    if fmt == "markdown":
        report_content = generate_markdown(enriched, data_view_name)
        report_ext = "md"
        report_prefix = "DIMENSION_ANALYSIS_REPORT_"
    else:
        report_content = generate_html(enriched, data_view_name, data_view_id)
        report_ext = "html"
        report_prefix = "DIMENSION_ANALYSIS_REPORT_"

    report_path = output_dir / f"{report_prefix}{ts}.{report_ext}"
    with open(report_path, "w") as f:
        f.write(report_content)
    print(f"✅ Report saved: {report_path} ({report_path.stat().st_size:,} bytes)")

    # Cleanup old files
    if keep_analyses > 0:
        print(f"\n🧹 Cleaning up old analysis files (keeping {keep_analyses} most recent)...")
        cleanup_old_files(output_dir, "dimension_analysis_results_", keep_analyses)
        cleanup_old_files(output_dir, report_prefix, keep_analyses)

    # Summary
    summary = enriched.get("summary", {})
    dims = enriched.get("dimensions", [])
    print(f"\n{'='*50}")
    print(f"📊 Analysis complete — {data_view_name}")
    print(f"   Dimensions analyzed:   {summary.get('totalDimensions', 0)}")
    print(f"   High cardinality:      {summary.get('highCardinalityCount', 0)}")
    print(f"   Total anomalies:       {summary.get('totalAnomalies', 0)}")
    print(f"   Critical DQ issues:    {summary.get('criticalDataQualityCount', 0)}")
    print(f"   Warning DQ issues:     {summary.get('warningDataQualityCount', 0)}")
    print(f"{'='*50}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

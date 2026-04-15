# cja-dimension-analysis — Developer Notes

Comprehensive dimension analysis skill for CJA. Analyzes cardinality, distribution/skew,
trends, anomalies, data quality, comparisons, and forecasting for one or more dimensions.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Main skill definition — phased workflow, trigger phrases, guardrails |
| `cja_dimension_analysis.py` | Primary analysis + report generation script |
| `analysis_report_gen.py` | Standalone HTML report generator (regenerate from existing JSON) |
| `output/` | Generated reports and analysis JSON files (auto-created) |

---

## How It Works

The SKILL.md directs data collection via CJA MCP tool calls (Phases 0–7). Collected data is
saved to a JSON file, then the Python script reads it and generates the report.

```
SKILL.md (Cursor/Claude) collects data via MCP tools
    │
    ▼
dimension_analysis_results_YYYY-MM-DD_HH-MM.json   ← raw collected data
    │
    ▼
cja_dimension_analysis.py   ← enriches + generates report
    │
    ├── DIMENSION_ANALYSIS_REPORT_YYYY-MM-DD_HH-MM.html   (default)
    └── DIMENSION_ANALYSIS_REPORT_YYYY-MM-DD_HH-MM.md     (--format=markdown)
```

---

## Running the Script

```bash
# HTML report (default)
python3 cja_dimension_analysis.py \
  ./output/dimension_analysis_results_2026-03-13_10-00.json \
  "My Data View" \
  "dv_abc123" \
  ./output \
  --format=html \
  --keep-analyses=5

# Markdown report
python3 cja_dimension_analysis.py \
  ./output/dimension_analysis_results_2026-03-13_10-00.json \
  "My Data View" \
  "dv_abc123" \
  ./output \
  --format=markdown

# Regenerate HTML from existing results (without re-running analysis)
python3 analysis_report_gen.py ./output/dimension_analysis_results_2026-03-13_10-00.json ./output
```

---

## Input JSON Structure

The input JSON is produced by the SKILL.md workflow (Claude collecting data via MCP tools).
Structure:

```json
{
  "analysis_metadata": {
    "data_view_name": "Adobe Store Prod",
    "data_view_id": "dv_abc123",
    "date_range": "Last 90 days",
    "analyses_run": ["cardinality", "distribution", "trends", "anomalies", "errors"],
    "generated_at": "2026-03-13T10:00:00Z"
  },
  "dimensions": [
    {
      "id": "variables/page",
      "name": "Page",
      "cardinality": {
        "uniqueValueCount": 1500
      },
      "distribution": {
        "topValues": [
          {"value": "Home", "metric": 5000},
          {"value": "Product Detail", "metric": 3200}
        ]
      },
      "trends": {
        "period1": "Last 45 days",
        "period2": "Previous 45 days",
        "newValues": ["New Page A"],
        "disappearedValues": [],
        "changes": [
          {"value": "Home", "p1Metric": 4500, "p2Metric": 5000, "pctChange": 11.1, "badge": "🟢 Growing"}
        ]
      },
      "anomalies": [
        {"date": "2026-02-14", "value": "Home", "type": "spike", "magnitude": 9500, "zScore": 3.2}
      ],
      "errors": {
        "errorPatterns": [
          {"pattern": "Unspecified", "count": 450, "pct": 9.0}
        ],
        "missingDataPct": 9.0
      },
      "forecasts": [
        {"value": "Home", "slope": 12.5, "r2": 0.82, "direction": "Upward", "confidence": "High"}
      ]
    }
  ],
  "comparisons": [],
  "summary": {}
}
```

All fields in each dimension section are optional — the script handles missing data gracefully.

---

## Cardinality Classification

| Level | Threshold | Recommendation |
|-------|-----------|----------------|
| LOW | < 100 | No action needed |
| MEDIUM | 100–1,000 | Normal; monitor growth |
| HIGH | 1,000–10,000 | Flag for performance review |
| VERY_HIGH | > 10,000 | Can slow queries; consider value reduction |

---

## Skew Classification

| Label | Condition |
|-------|-----------|
| Extreme skew | Top 1 value > 50% of total metric |
| High skew | Top 1 value > 30% of total metric |
| Moderate | Middle distribution |
| Long tail | Top 10 values < 50% of total metric |

---

## Data Quality Severity

| Severity | Threshold |
|----------|-----------|
| ✅ OK | < 5% missing |
| ⚠️ Warning | 5–20% missing |
| ⛔ Critical | > 20% missing |

---

## Customization

**Anomaly sensitivity** — the z-score threshold (default: 2.0) can be adjusted in the
SKILL.md Phase 4 instructions. Lower = more sensitive (more alerts); higher = fewer alerts.

**Cardinality thresholds** — update `CARDINALITY_LEVELS` in `cja_dimension_analysis.py`
if your org uses different thresholds for HIGH/VERY HIGH classification.

**Keeping old reports** — default is 5 most recent. Use `--keep-analyses=0` to keep all.

---

## Architecture Notes

- The script is intentionally self-contained (no external dependencies beyond stdlib).
- Chart.js is loaded from CDN in HTML output; if CDN is unavailable, charts won't render
  but the data tables will still show.
- For very large dimension sets (> 50), consider running in batches and merging results.
- The script re-runs enrichment on the input JSON even if the skill already computed
  some values — this ensures consistency and allows re-running on raw data.

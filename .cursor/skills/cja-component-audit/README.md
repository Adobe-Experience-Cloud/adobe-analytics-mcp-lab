# cja-component-audit — Developer Notes

Multi-type CJA component audit skill. Audits segments, calculated metrics, and optionally
dimensions and metrics — covering usage classification, duplicate detection, cross-type
dependencies, ownership analysis, and health scoring.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Main skill definition — phased workflow, trigger phrases, guardrails |
| `cja_component_audit.py` | Primary audit + report generation script |
| `audit_report_gen.py` | Standalone HTML report regenerator |
| `output/` | Generated audit reports and JSON files (auto-created) |

---

## How It Works

The SKILL.md directs data collection via CJA MCP tool calls (Phases 0–6). Collected data is
saved as JSON inventory files, then the Python script reads them and generates the report.

```
SKILL.md (Cursor/Claude) collects data via MCP tools
    │
    ├── output/segments_inventory.json         ← from findSegments
    ├── output/calcmetrics_inventory.json      ← from findCalculatedMetrics
    ├── output/dimensions_inventory.json       ← optional
    ├── output/metrics_inventory.json          ← optional
    ├── output/usage_segment.json              ← from listComponentUsage
    ├── output/usage_calculatedMetric.json     ← from listComponentUsage
    ├── output/usage_dimension.json            ← optional
    └── output/usage_metric.json               ← optional
    │
    ▼
cja_component_audit.py  ←  reads inventory files, runs analysis
    │
    ├── component_audit_results_YYYY-MM-DD_HH-MM.json   (raw data)
    └── COMPONENT_AUDIT_REPORT_YYYY-MM-DD_HH-MM.html    (or .md)
```

---

## Running the Script

```bash
# HTML report (default)
python3 cja_component_audit.py \
  ./output \
  "Adobe Store Prod" \
  "dv_abc123" \
  ./output \
  --format=html \
  --keep-audits=5

# Markdown report
python3 cja_component_audit.py \
  ./output \
  "Adobe Store Prod" \
  "dv_abc123" \
  ./output \
  --format=markdown

# Regenerate HTML from existing audit results
python3 audit_report_gen.py ./output/component_audit_results_2026-03-13_10-00.json ./output
```

---

## Input File Structures

### segments_inventory.json / calcmetrics_inventory.json

Arrays of component objects from `findSegments` / `findCalculatedMetrics` with expansions:

```json
[
  {
    "id": "s12345_abc",
    "name": "Mobile Users",
    "ownerFullName": "Jane Smith",
    "modified": "2025-09-15T12:00:00Z",
    "createdDate": "2024-01-10T08:00:00Z",
    "recentRecordedAccess": "2025-11-20T14:00:00Z",
    "usageSummary": {
      "usedInProjects": 5,
      "usedInSegments": 2,
      "usedInCalculatedMetrics": 1
    },
    "definition": { ... },
    "tags": ["mobile", "audience"],
    "isDeleted": false
  }
]
```

### usage_segment.json / usage_calculatedMetric.json

Arrays from `listComponentUsage`:

```json
[
  { "componentId": "s12345_abc", "componentType": "segment", "count": 42 }
]
```

---

## Usage Classification

| Bucket | Criteria |
|--------|----------|
| **Active** | In `listComponentUsage` results OR `recentRecordedAccess` within 90 days OR non-zero `usageSummary` |
| **Stale** | Last accessed 90–365 days ago AND not in usage results |
| **Unused** | Never accessed OR > 365 days AND zero usage references |

---

## Health Score Formula

Per component type (0–100):
- Active ratio (0–50): `activeCount / totalCount * 50`
- Duplicate penalty (0–30): `max(0, 30 - duplicateGroups * 3)`
- Unused penalty (0–20): `20 * (1 - unusedPct / 100)`

Overall score: weighted average (segments + calcMetrics weighted 2×, dimensions + metrics 1×).

---

## Duplicate Detection

**Calculated Metrics** — formula structure comparison:
- Serializes the `formula` object (sorted keys) as a signature
- Groups calc metrics with identical formula structures

**All Types** — name similarity:
- Lowercases and strips punctuation from names
- Groups components with identical normalized names
- Presented as "review candidates" — not assumed to be true duplicates

For **deep segment duplicate detection** (4-tier logical canonicalization), escalate to
`cja-segment-audit`. The component audit detects segment duplicates at a lightweight level
and will recommend escalating when complex segment situations are found.

---

## Relationship with cja-segment-audit

| Aspect | cja-component-audit | cja-segment-audit |
|--------|--------------------|--------------------|
| Scope | Multiple component types | Segments only |
| Segment depth | Lightweight (name similarity) | Full 4-tier logical canonicalization |
| Cross-type dependencies | ✅ Yes | ❌ No |
| Ownership analysis | ✅ Yes | ❌ No |
| Best for | "How healthy are all my components?" | "Find all logically equivalent segments" |

---

## Customization

**Usage thresholds** — edit `THRESHOLD_90` and `THRESHOLD_365` in `cja_component_audit.py`
to adjust Active/Stale/Unused cutoffs.

**Health score weights** — edit the `weights` dict in `run_audit()` to change how component
types are weighted in the overall health score.

**Keeping old reports** — default is 5 most recent. Use `--keep-audits=0` to keep all.

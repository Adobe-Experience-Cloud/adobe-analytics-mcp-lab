---
name: cja-component-audit
description: >
  Full audit of CJA components across multiple types: segments, calculated metrics, and
  optionally dimensions and metrics. Use this skill whenever the user asks to audit, review,
  or assess the health of their CJA components. Also trigger when someone says "component
  health check", "which components are unused", "find duplicate calculated metrics",
  "component hygiene", "component governance", "clean up my components", "component bloat",
  "unused segments and calc metrics", "archival candidates", "component audit report",
  "generate component dashboard", or any variation of a multi-type component review.
  Produces an actionable HTML dashboard or markdown report. Strictly report-only — never
  deletes, modifies, or archives anything. Works with the CJA MCP server.
---
# CJA Component Audit

Audit your CJA component library across segments, calculated metrics, and optionally
dimensions and metrics. Produces a concrete, actionable report covering usage classification,
duplicate/near-duplicate detection, cross-type dependencies, ownership analysis, health
scoring, and consolidation recommendations.

## Why This Matters

Component libraries grow unchecked across teams and campaigns. The result: a segment picker
filled with hundreds of filters nobody uses, calculated metrics that are near-identical copies
of each other, and no one knows who owns what. This audit gives teams a clear picture of what
they have, what they can clean up, and what needs attention — all without touching anything.

## Workflow

Execute these phases in order. Each phase feeds the next.

### Phase 0 — Setup

1. Call `findDataViews` to list available data views. If the user hasn't specified one,
   ask which data view to audit. Set it with `setDefaultSessionDataViewId`.
2. Ask which component types to include:
   - **Default**: segments + calculated metrics (always included)
   - **Optional**: dimensions, metrics (add for broader cross-type dependency mapping)
3. Note the data view ID — you'll need it for subsequent calls.

### Phase 1 — Inventory

Pull the full component list per type with rich metadata:

**Segments:**
```
findSegments(
  limit: 1000,
  page: 0,
  expansions: "ownerFullName,modified,isDeleted,componentType,compatibility,definition,
               dataId,dataName,tags,usageSummary,usageSummaryWithRelevancyScore,
               createdDate,recentRecordedAccess"
)
```

**Calculated Metrics:**
```
findCalculatedMetrics(
  limit: 1000,
  page: 0,
  expansions: "ownerFullName,modified,isDeleted,definition,dataId,dataName,tags,
               usageSummary,usageSummaryWithRelevancyScore,createdDate,recentRecordedAccess"
)
```

**Dimensions (if requested):**
```
findDimensions(limit: 1000)  →  metadata only (no definitions, but usage data available)
```

**Metrics (if requested):**
```
findMetrics(limit: 1000)  →  metadata only
```

Paginate if `totalPages > 1`. Filter out any component where `isDeleted` is true.

For each component, extract and store:
- `id`, `name`, `description`, `ownerFullName`
- `modified`, `createdDate`, `recentRecordedAccess`
- `usageSummary` — references in projects, other segments, calculated metrics
- `definition` — the JSON logic (segments and calculated metrics only)
- `tags`

Save inventory to JSON files (one per component type) in `.cursor/skills/cja-component-audit/output/`:
`segments_inventory.json`, `calcmetrics_inventory.json`, etc.

### Phase 2 — Usage Analysis

1. For each component type, call `listComponentUsage(componentType: "<type>")`:
   - `"segment"`, `"calculatedMetric"`, `"dimension"`, `"metric"`
   - Returns a ranked list of components by usage across all reports.
2. Cross-reference with the inventory from Phase 1.
3. Classify each component into usage buckets:

| Bucket | Criteria |
|--------|----------|
| **Active** | In `listComponentUsage` results OR `recentRecordedAccess` within 90 days OR meaningful `usageSummary` counts |
| **Stale** | Last accessed 90–365 days ago AND not in usage results |
| **Unused** | Never accessed OR last accessed > 365 days ago AND zero usage references |

4. Save usage data: `usage_<type>.json`

### Phase 3 — Duplicate & Similarity Detection

**For Segments** — 4-tier approach (same as `cja-segment-audit`):
1. **Logical canonicalization**: normalize definitions using De Morgan's law, double-negation
   elimination, operator consolidation, redundancy removal
2. **Cosmetic normalization**: strip descriptions, sort commutative predicates, normalize keys
3. **Structural fingerprinting**: extract function/dimension/event signatures
4. **Similarity scoring**: 0.0–1.0 weighted structural similarity with diff explanations
   for pairs scoring >= 0.70

> If a segment situation looks complex, recommend the user also run `cja-segment-audit`
> for deeper segment-specific analysis with the full canonicalization engine.

**For Calculated Metrics** — adapted definition comparison:
1. Extract formula structure: functions used, metrics/dimensions referenced, nesting depth
2. Compare formula structure across all calculated metrics
3. Flag pairs with identical or very similar formulas (same functions, same referenced components)
4. Use `listSimilarTo` for API-driven similarity on top calculated metrics

**For All Types** — name-based similarity:
1. Lowercase and strip punctuation from all names
2. Flag near-identical names (e.g., "Mobile Users" vs "Mobile users" vs "mobile_users")
3. Present as "similar name groups" for manual review — don't assume they're duplicates

**Step E — API-driven similarity:**
For the top 10–15 most-used components per type, call:
```
listSimilarTo(componentId: id, componentType: "<type>")
```
Cross-reference API similarity findings with definition-based findings to strengthen confidence.

Save to JSON: `{dimensionId, similarPairs: [...], exactDuplicateGroups: [...], nameSimilarGroups: [...]}`

### Phase 4 — Cross-Type Dependencies & Co-Usage

1. **Extract dependencies from definitions**:
   - For each segment: which dimensions and metrics does its definition reference?
   - For each calculated metric: which metrics, dimensions, and segments does it reference?
   - Build a dependency map: `component → [referenced_components]`

2. **Flag orphaned dependencies**: a component that references another component which is
   itself Unused or not found in the inventory (may indicate stale references).

3. **Call `listFrequentlyUsedWith`** for the top 5–10 components per type:
   ```
   listFrequentlyUsedWith(componentId: id, componentType: "<type>")
   ```
   Reveals which dimensions, metrics, and other components are commonly paired together.
   Surface "always together" pairs as merge candidates.

Save: `{dependencies: {componentId: [deps]}, orphaned: [...], coUsage: [...]}`

### Phase 5 — Ownership & Distribution Analysis

1. **Aggregate ownership across all component types**:
   - Count: how many components each `ownerFullName` has created
   - Identify: owners with the most Unused components (cleanup conversation targets)
   - Flag: components with no owner or "Unknown" owner

2. **Component type distribution**:
   - Ratio of segments to calculated metrics
   - Distribution of Active / Stale / Unused across each type
   - Flag if any type has > 50% Unused (high bloat signal)

3. **Single-owner risk**: components owned by one person with high Active usage and no tags
   (knowledge transfer risk).

Save: `{ownershipStats: {...}, typeDistribution: {...}}`

### Phase 6 — Health Scoring & Recommendations

**Per-type health score** (0–100):
- Active % contribution: `activeCount / totalCount * 50`
- Duplicate penalty: `-5 per duplicate group found`
- Error penalty: `-10 if any type has > 50% unused`
- Naming consistency bonus: `+10 if < 5% name similarity pairs`

**Overall health score**: weighted average across types (segments and calc metrics weighted 2×,
dimensions and metrics weighted 1× if included).

**Recommendations** (categorized):
- 🗑️ **Delete**: Unused, zero dependencies, no meaningful purpose (explain based on age and owner)
- 🔗 **Merge**: Duplicate groups — recommend which to keep (prefer most-used, most recently
  modified, best named)
- ✏️ **Rename**: Confusing or ambiguous names — suggest clearer convention
- 📦 **Archive Review**: Stale but possibly seasonal (e.g., last used 10 months ago)
- 🏷️ **Tag**: Components lacking categorization that would benefit from tags

Each recommendation includes: **what**, **why**, **impact** (High/Medium/Low), **effort** (Quick/Moderate).

Prioritize: quick wins (Delete: unused, no deps) first, then bigger cleanup tasks (Merge groups).

### Phase 7 — Report Generation

After all phases complete:

1. Save all collected data to a consolidated JSON file:
   `component_audit_results_YYYY-MM-DD_HH-MM.json`
   (in `.cursor/skills/cja-component-audit/output/`)

2. Run the Python report generator:
   ```bash
   python3 .cursor/skills/cja-component-audit/cja_component_audit.py \
     <inventory_dir> \
     "<data_view_name>" \
     "<data_view_id>" \
     [output_directory] \
     [--format=html|markdown] \
     [--keep-audits=N]
   ```

   **Options:**
   - `--format=html` (default): Interactive HTML dashboard
   - `--format=markdown`: Comprehensive text-based report
   - `--keep-audits=N` (default: 5): Auto-cleanup of old audit files

3. The report structure:
   - **Executive Summary**: overall health score, total components per type, component counts
     by bucket (Active/Stale/Unused), top issues
   - **Per-Type Breakdown**: for each component type — usage distribution, top 10 by usage,
     unused list, health score
   - **Duplicates & Near-Duplicates**: grouped by type, each group with recommendation
   - **Cross-Type Dependencies**: dependency map, orphaned references, co-usage highlights
   - **Ownership Distribution**: top owners by count, owners with most unused components
   - **Recommendations**: prioritized action list with what/why/impact/effort
   - **Next Steps**: concrete actions in priority order

4. Present the report path to the user and summarize the top 3–5 findings.

## CJA MCP Tools Used

| Tool | Phase | Purpose |
|------|-------|---------|
| `findDataViews` | 0 | List available data views |
| `setDefaultSessionDataViewId` | 0 | Set active data view |
| `findSegments` | 1 | Pull full segment inventory with metadata |
| `findCalculatedMetrics` | 1 | Pull full calculated metric inventory |
| `findDimensions` | 1 | Pull dimension inventory (optional) |
| `findMetrics` | 1 | Pull metric inventory (optional) |
| `describeSegment` | 3 | Get segment definition for duplicate comparison |
| `describeCalculatedMetric` | 3 | Get calc metric definition for duplicate comparison |
| `describeDimension` | 4 | Get dimension metadata for cross-type mapping |
| `describeMetric` | 4 | Get metric metadata for cross-type mapping |
| `listComponentUsage` | 2 | Usage ranking per component type |
| `listSimilarTo` | 3 | API-driven similarity per component |
| `listFrequentlyUsedWith` | 4 | Co-usage patterns for merge candidates |

## Relationship with cja-segment-audit

This skill audits **all component types** at breadth. For **deep segment-only analysis**
with full 4-tier logical canonicalization (De Morgan's law, operator consolidation, etc.),
use `cja-segment-audit` instead. The component audit includes segment duplicate detection
at a reasonable depth, and will recommend escalating to `cja-segment-audit` when it finds
complex or large segment duplicate situations.

## Important Guardrails

- **Strictly report-only**: Never delete, modify, archive, or rename anything automatically.
  Present findings and let the user decide.
- If segment count is very large (> 300), focus duplicate detection on segments older than
  1 year plus all segments with zero usage. Note that full analysis requires more passes.
- If `listComponentUsage` or `listSimilarTo` returns limited results, note this and rely
  more heavily on definition comparison and access dates.
- Always include owner names in recommendations — cleanup is a team coordination task.
- A typical audit takes several minutes for a large org. Update the user as phases complete:
  "Phase 1 complete — 247 segments, 89 calculated metrics inventoried. Running Phase 2..."

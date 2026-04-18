---
name: cja-component-audit
author: Rene Muniz <muniz@adobe.com>
description: >
  Full audit of CJA components across multiple types: segments, calculated metrics, and
  optionally dimensions and metrics. Use this skill whenever the user asks to audit, review,
  or assess the health of their CJA components. Also trigger when someone says "component
  health check", "which components are unused", "find duplicate calculated metrics",
  "component hygiene", "component governance", "clean up my components", "component bloat",
  "unused segments and calc metrics", "archival candidates", "component audit report",
  "generate component dashboard", or any variation of a multi-type component review.
  Produces an actionable HTML dashboard. Strictly report-only — never
  deletes, modifies, or archives anything. Works with the CJA MCP server.
metadata:
  author: adobe
  version: "1.0"
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

Save inventory to JSON files (one per component type) in `/tmp/cja-component-audit/`:
`segments_inventory.json`, `calcmetrics_inventory.json`, etc.

### Phase 2 — Usage Analysis

1. For each component type, call `listComponentUsage(componentType: "<type>")`:
   - `"segment"`, `"calculatedMetric"`, `"dimension"`, `"metric"`
   - Returns a ranked list of components by usage across all reports.
2. Cross-reference with the inventory from Phase 1.
3. Classify each component into usage buckets using this **strict, consistent definition**:

| Bucket | Criteria |
|--------|----------|
| **Active** | Appears in `listComponentUsage` results **AND/OR** has non-zero `usageSummary` counts (referenced in projects, other segments, or calculated metrics) |
| **Stale** | NOT in `listComponentUsage` AND zero `usageSummary` counts BUT `recentRecordedAccess` within the last 365 days |
| **Unused** | NOT in `listComponentUsage` AND zero `usageSummary` counts AND no `recentRecordedAccess` within 365 days |

**IMPORTANT — `recentRecordedAccess` alone must NOT classify a component as Active.** Opening
a component in the UI counts as an access but does not mean it is used in reports. Only
`listComponentUsage` results and non-zero `usageSummary` counts indicate real usage.
Use this same definition consistently in both the health score calculation and the Score
Breakdown box — they must not contradict each other.

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

**Recommendations — rules-based, not narrative-driven**

Generate recommendations mechanically from the data using these exact rules. Do not
improvise or invent recommendations beyond what the data triggers. Every recommendation
must cite the specific count or component names that triggered it.

| Rule | Trigger | Recommendation text |
|------|---------|-------------------|
| **R1 — Delete unused segments** | `unusedSegments > 0` | "Delete {N} unused segments: [list names]. These have zero report usage and zero usageSummary references. Effort: Quick." |
| **R2 — Delete unused calc metrics** | `unusedCalcMetrics > 0` | "Delete {N} unused calculated metrics: [list names]. Zero report usage confirmed. Effort: Quick." |
| **R3 — Merge segment duplicates** | `segDupGroups > 0` | "Merge {N} segment duplicate groups. For each group keep the most recently modified copy and retire the rest: [list group names and copy counts]. Effort: Moderate." |
| **R4 — Merge calc metric duplicates** | `cmDupGroups > 0` | "Merge {N} calculated metric duplicate groups: [list names]. Keep the most-used copy. Effort: Moderate." |
| **R5 — Tag untagged segments** | `segZeroTags / totalSegs > 0.5` | "Add tags to {N}/{total} segments that have no tags. Tagging enables governance and discoverability. Effort: Moderate." |
| **R6 — Tag untagged calc metrics** | `cmZeroTags / totalCM > 0.5` | "Add tags to {N}/{total} calculated metrics that have no tags. Effort: Moderate." |
| **R7 — Resolve unknown ownership** | `unknownOwner / total > 0.5` | "{N}/{total} components have no owner. Assign ownership in the CJA UI to enable team cleanup coordination. Effort: Moderate." |
| **R8 — Investigate mystery high-use** | `mysterySegs > 0 OR mysteryCMs > 0` | "{N} components show high workspace usage but are not visible to this account. Verify with a CJA admin that these components are still valid and accessible to the team. Effort: Quick." |
| **R9 — Stale review** | `staleSegments > 0 OR staleCalcMetrics > 0` | "Review {N} stale components last accessed 90–365 days ago: [list names]. Archive or delete if no longer needed. Effort: Low." |

Rules fire in priority order R1 → R9. Skip any rule whose trigger condition is false.
Each recommendation must include: the triggering count, component names (or top 5 if list is long),
impact (High/Medium/Low), and effort (Quick/Moderate/Low).

**Author and date context — required in all component listings**

Whenever listing individual components anywhere in the report (duplicate groups, unused lists,
stale lists, recommendations, ownership tables) always include the following alongside the name:
- **Owner** (`ownerFullName`, or "Unknown" if absent)
- **Created** (`createdDate`, formatted as `MMM D, YYYY`)
- **Last modified** (`modified`, formatted as `MMM D, YYYY`)

This gives users the context they need to act: who to contact, how old the component is, and
whether it was recently touched. Format as a compact table or inline — e.g.:

| Name | Owner | Created | Last Modified |
|------|-------|---------|---------------|
| Cart Abandoners - Last 30 Days | Jane Smith | Jan 5, 2024 | Mar 12, 2025 |

If `ownerFullName` is null or empty, display "Unknown owner" — never omit the column.

### Phase 7 — Report Generation

After all phases complete:

1. Save all collected data to a consolidated JSON file:
   `component_audit_results_YYYY-MM-DD_HH-MM.json`
   (in a temp output directory, e.g. `/tmp/cja-component-audit/`)

2. Run the Python script to produce the analysis results JSON:
   ```bash
   python3 scripts/cja_component_audit.py \
     <inventory_dir> \
     "<data_view_name>" \
     "<data_view_id>" \
     [output_directory]
   ```

   > **Important:** The Python script performs the data analysis (usage classification,
   > duplicate detection, health scoring) and writes a results JSON file. **Do not use
   > the Python script's HTML output as the report.** Generate the HTML report yourself
   > using the required templates defined below — this ensures the correct layout,
   > two-box summary, and style are always produced consistently.

3. The report structure:
   - **Executive Summary**: two side-by-side boxes (health score card + score breakdown) — see
     required layout below, followed by KPI stat cards and critical alerts
   - **Per-Type Breakdown**: for each component type — usage distribution, top 10 by usage,
     unused list, health score
   - **Duplicates & Near-Duplicates**: grouped by type, each group with recommendation
   - **Cross-Type Dependencies**: dependency map, orphaned references, co-usage highlights
   - **Ownership Distribution**: top owners by count, owners with most unused components
   - **Recommendations**: prioritized action list with what/why/impact/effort
   - **Next Steps**: concrete actions in priority order

### Required Summary Section — Two-Box Layout

The Executive Summary **must always** open with two side-by-side boxes. This layout is
mandatory — do not replace it with a plain alert banner or simple KPI cards.

**Status color mapping** (apply to health score card background and circle):

| Score | Label | Card background | Border / circle color |
|-------|-------|-----------------|----------------------|
| 80–100 | 🟢 Excellent | `#D4F0E8` | `#12805C` |
| 60–79  | 🟡 Good | `#FEF3E2` | `#DA7B11` |
| 40–59  | 🟠 Fair | `#FFF0E6` | `#E07B39` |
| 0–39   | 🔴 Needs Improvement | `#FDECEA` | `#D7373F` |

**Required HTML — paste this block immediately after the `<div class="container">` opening tag:**

```html
<!-- ═══ SUMMARY: Two-box layout — MANDATORY ═══ -->
<div id="summary" style="display:flex; gap:20px; align-items:flex-start; margin-bottom:28px; flex-wrap:wrap;">

  <!-- LEFT: Health Score Card -->
  <div style="flex:1; min-width:300px; background:{STATUS_BG}; border:2px solid {STATUS_COLOR};
              border-radius:12px; padding:28px; box-shadow:0 2px 8px rgba(0,0,0,.07);">
    <div style="display:flex; gap:20px; align-items:flex-start; margin-bottom:20px;">
      <!-- Score circle -->
      <div style="background:{STATUS_COLOR}; color:#fff; width:84px; height:84px; border-radius:50%;
                  display:flex; flex-direction:column; align-items:center; justify-content:center;
                  flex-shrink:0; font-weight:800;">
        <span style="font-size:28px; line-height:1;">{OVERALL_SCORE}</span>
        <span style="font-size:11px; opacity:.8;">/ 100</span>
      </div>
      <!-- Status + narrative -->
      <div>
        <div style="font-size:20px; font-weight:700; color:{STATUS_COLOR}; margin-bottom:8px;">
          {STATUS_ICON} {STATUS_LABEL}
        </div>
        <p style="font-size:13px; line-height:1.6; color:#2C2C2C;">{NARRATIVE_TEXT}</p>
      </div>
    </div>
    <!-- Per-type sub-scores -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px;">
      <div style="background:#fff; border-radius:8px; padding:12px 14px;">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#6E6E6E; margin-bottom:4px;">Segments</div>
        <div style="font-size:22px; font-weight:800; color:#2C2C2C;">{SEG_SCORE}</div>
        <div style="font-size:11px; color:#6E6E6E;">/ 100 &middot; {SEG_STATUS_ICON} {SEG_STATUS_LABEL}</div>
      </div>
      <div style="background:#fff; border-radius:8px; padding:12px 14px;">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#6E6E6E; margin-bottom:4px;">Calc Metrics</div>
        <div style="font-size:22px; font-weight:800; color:#2C2C2C;">{CM_SCORE}</div>
        <div style="font-size:11px; color:#6E6E6E;">/ 100 &middot; {CM_STATUS_ICON} {CM_STATUS_LABEL}</div>
      </div>
      <!-- Add more sub-cards if additional component types were audited -->
    </div>
  </div>

  <!-- RIGHT: Score Breakdown — exact rows and colors are MANDATORY -->
  <!-- min-width:360px keeps labels on one line — do not reduce -->
  <div style="flex:0 0 360px; min-width:360px; background:#fff; border-radius:12px; padding:28px;
              box-shadow:0 2px 8px rgba(0,0,0,.07);">
    <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.8px;
                color:#6E6E6E; margin-bottom:16px;">Score Breakdown</div>
    <table style="width:100%; border-collapse:collapse; font-size:13px;">
      <!--
        Color rules (apply to the right-hand value cell):
          Active counts   → bold #2C2C2C (dark, not colored — being active is neutral/good)
          Duplicate groups > 0 → #D7373F (red)
          Zero-tags counts    → #D7373F (red) when all or nearly all are untagged
          Approved calc metrics = 0 → #D7373F (red)
          Unknown-owner high  → #DA7B11 (orange)
      -->

      <!-- Row 1: Active segments — use bold dark, NOT red -->
      <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Active segments</td>
        <td style="text-align:right; font-weight:700; color:#2C2C2C; white-space:nowrap;">
          {ACTIVE_SEGS} / {TOTAL_SEGS} ({SEG_ACTIVE_PCT}%)</td>
      </tr>
      <!-- Row 2: Active custom calc metrics — use bold dark, NOT red -->
      <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Active custom calc metrics</td>
        <td style="text-align:right; font-weight:700; color:#2C2C2C; white-space:nowrap;">
          {ACTIVE_CM} / {TOTAL_CM} ({CM_ACTIVE_PCT}%)</td>
      </tr>
      <!-- Row 3: Segment duplicate groups — red if > 0 -->
      <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Segment duplicate groups</td>
        <td style="text-align:right; font-weight:700; color:#D7373F; white-space:nowrap;">
          {SEG_DUP_GROUPS} groups</td>
      </tr>
      <!-- Row 4: Calc metric duplicate groups — orange if > 0 -->
      <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Calc metric duplicate groups</td>
        <td style="text-align:right; font-weight:700; color:#DA7B11; white-space:nowrap;">
          {CM_DUP_GROUPS} group ({CM_DUP_COPIES} copies)</td>
      </tr>
      <!-- Row 5: Segments with zero tags — red -->
      <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Segments with zero tags</td>
        <td style="text-align:right; font-weight:700; color:#D7373F; white-space:nowrap;">
          {SEG_ZERO_TAGS} / {TOTAL_SEGS}</td>
      </tr>
      <!-- Row 6: Calc metrics with zero tags — red -->
      <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Calc metrics with zero tags</td>
        <td style="text-align:right; font-weight:700; color:#D7373F; white-space:nowrap;">
          {CM_ZERO_TAGS} / {TOTAL_CM}</td>
      </tr>
      <!-- Row 7: Approved calc metrics — red if 0 -->
      <tr style="border-bottom:1px solid #f0f0f0;">
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Approved calc metrics</td>
        <td style="text-align:right; font-weight:700; color:#D7373F; white-space:nowrap;">
          {APPROVED_CM} / {TOTAL_CM}</td>
      </tr>
      <!-- Row 8: Unknown-owner components — orange if high -->
      <tr>
        <td style="padding:9px 0; color:#2C2C2C; white-space:nowrap;">Unknown-owner components</td>
        <td style="text-align:right; font-weight:700; color:#DA7B11; white-space:nowrap;">
          {UNKNOWN_OWNER} / {TOTAL_COMPONENTS}</td>
      </tr>
    </table>
  </div>

</div>
<!-- ═══ END two-box layout ═══ -->
```

After the two-box layout, continue with the KPI stat cards grid and critical alert banners.

4. Open with `open <output_directory>/COMPONENT_AUDIT_REPORT_YYYY-MM-DD_HH-MM.html`
5. Present the report path to the user and summarize the top 3–5 findings.

### Required HTML Style — Header, Nav & Theme

The HTML report **must** use a light theme with a dark-to-blue gradient header and white nav bar.
Do **not** use a dark background, dark cards, or a purple gradient. Do **not** left-align the header text.

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       background: #F5F5F5; color: #2C2C2C; }
header { background: linear-gradient(135deg, #1B1B1B 0%, #1473E6 100%);
         color: white; padding: 36px 32px; text-align: center; width: 100%; }
header h1 { font-size: 26px; font-weight: 700; }
header p  { opacity: 0.85; margin-top: 6px; font-size: 14px; }
nav { position: sticky; top: 0; background: #fff;
      border-bottom: 1px solid #dfe6e9; display: flex; gap: 4px;
      padding: 0 24px; z-index: 100; }
nav a { display: block; padding: 13px 16px; font-size: 13px;
        font-weight: 600; color: #1473E6; text-decoration: none; }
nav a:hover { background: #EAF3FF; border-radius: 4px; }
.container { max-width: 1100px; margin: 0 auto; padding: 28px 20px; }
.kpi-card { background: #fff; border-radius: 12px; padding: 22px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,.07); }
.section  { background: #fff; border-radius: 10px; margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,.07); overflow: hidden; }
```

**Correct HTML structure:**
```html
<header>
  <h1>CJA Component Audit Report</h1>
  <p>Data View: {DATA_VIEW_NAME} ({DATA_VIEW_ID}) &middot; Audit Date: {DATE} &middot; Total Components: {COUNT}</p>
</header>
<nav>
  <a href="#summary">Summary</a>
  <a href="#segments">Segments</a>
  <a href="#calc-metrics">Calc Metrics</a>
  <a href="#duplicates">Duplicates</a>
  <a href="#ownership">Ownership</a>
  <a href="#recommendations">Recommendations</a>
  <a href="#next-steps">Next Steps</a>
</nav>
```

**Section titles — no phase prefix**: Section headings in the HTML report must **not** include
the phase number. Use the plain section name only:
- ✅ "Usage Analysis" — not "Phase 2 — Usage Analysis"
- ✅ "Duplicate & Similarity Groups" — not "Phase 3 — Duplicate & Similarity Groups"
- ✅ "Ownership Distribution" — not "Phase 5 — Ownership & Distribution Analysis"

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

## Example Interaction

> "Can you do a full component audit of our CJA setup — segments and calculated metrics?"

1. **Setup:** Call `findDataViews`, present available data views, user selects one. Call `setDefaultSessionDataViewId`.
2. **Inventory:** Fetch all segments with `findSegments` (expansions: ownerFullName, modified, usageSummary, recentRecordedAccess, tags). Fetch all calculated metrics with `findCalculatedMetrics`. Announce: "Found 87 segments and 34 calculated metrics."
3. **Usage:** Call `listComponentUsage` for both types. Classify each component as Active / Stale / Unused. Announce tier counts.
4. **Duplicates:** Run name-similarity grouping. Call `listSimilarTo` for unused + stale + top 15 active of each type. Report: "Found 6 duplicate groups across both types."
5. **Report:** Run `python3 scripts/cja_component_audit.py /tmp/cja-component-audit/ "Prod DV" "dv_abc123" /tmp/cja-component-audit/` to produce the analysis JSON. Generate the HTML report from the templates in this skill and write to `/tmp/cja-component-audit/COMPONENT_AUDIT_REPORT_2026-04-17_14-32.html`. Open it. Summarize: "Your library has 121 components. 31 unused, 6 duplicate groups detected, combined health score 61/100. Recommended actions: delete 24 items, merge 4 groups, add tags to 18."

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

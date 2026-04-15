---
name: cja-component-find-replace
description: >
  Find all CJA projects that reference a specific component (dimension, metric, segment,
  calculated metric, or audience) and optionally replace it with a different component.
  Use this skill whenever the user asks "find where this component is used",
  "which projects use this dimension", "replace this metric in all projects",
  "component impact analysis", "swap out this segment across projects",
  "find and replace component", "how many projects use X", "migrate this component",
  "retire this metric", or any variation of component discovery and replacement across projects.
  Works with the CJA MCP server. Safe test-first approach for replacements.
---
# CJA Component Find & Replace

Find every project that references a specific CJA component and, when needed, safely replace
it with a different one. This skill is useful for impact analysis before retiring a component,
migrating to updated components, and understanding cross-project dependencies.

## Why This Matters

Components get renamed, deprecated, or superseded over time. Before you retire a dimension or
metric, you need to know which projects would break. Before you merge two segments, you need to
know which projects reference each one. This skill answers those questions — and when you're
ready to act, it handles the replacement for you.

## Workflow

### Phase 0 — Setup

Ask the user for:

1. **Component to find** — name or component ID (e.g., `variables/page`, `metrics/revenue`,
   a segment name like "Mobile Users")
2. **Component type** — `dimension`, `metric`, `segment`, `calculatedMetric`, or `audience`
3. **Data view scope** (optional) — leave blank to search all accessible data views

If the user provides a data view, call `setDefaultSessionDataViewId` to scope subsequent calls.

### Phase 1 — Locate & Verify

Find and confirm the exact component before searching for it across projects.

**For dimensions:**
```
findDimensions(search: "<name>")  →  get candidates
describeDimension(dimensionId)    →  confirm ID, name, data view
```

**For metrics:**
```
findMetrics(search: "<name>")     →  get candidates
describeMetric(metricId)          →  confirm ID, name, data view
```

**For segments:**
```
findSegments(search: "<name>")    →  get candidates
describeSegment(id, expansions: "usedIn,uses,definition")
```

**For calculated metrics:**
```
findCalculatedMetrics(search: "<name>")
describeCalculatedMetric(id, expansions: "usedIn,uses,definition")
```

**For audiences:**
```
findAudiences(search: "<name>")
describeAudience(id, expansions: "usedIn,uses,definition")
```

If multiple components match the search, list all candidates and ask the user to confirm which
one they mean. Show: ID, name, description, data view.

### Phase 2 — Find References

How you find references depends on component type:

**Segments, Calculated Metrics, Audiences** — use native `usedIn` expansion:
The `describe*` call in Phase 1 already returns `usedIn` — extract the project list directly.
These component types have built-in cross-reference data; no need to scan project definitions.

**Dimensions and Metrics** — scan project definitions:

1. **Get the project list** via `findProjects`:
   ```
   findProjects(expansions: "dataId,dataName,name,id,ownerFullName,modified")
   ```
   > ⚠️ **Known limitation**: `findProjects` only returns projects accessible to the current
   > user (not all org projects). For a full org-wide search, the user needs to run the
   > `fetch_all_projects.py` / `fetch_all_projects.ps1` workaround scripts (see
   > `UC-013-Component-Find-and-Replace/` folder) and provide the resulting JSON file.
   > If the user asks for "all projects" or "all org projects", explain this limitation and
   > offer both options.

2. **Scan each project**: call `describeProject(id, expansions: "definition")` and search
   the definition JSON for the component ID (both full and short form). Process in batches
   for large project lists.

3. Collect matches: project name, owner, last modified date, project ID.

### Phase 3 — Results Report

Present findings in a clear table:

```
Component:      [Display Name]
Component ID:   [Full ID]
Type:           [dimension | metric | segment | calculatedMetric | audience]
Data View:      [Name, or "All data views"]
Projects Found: [count]

| Project Name | Owner | Last Modified | Project ID |
|--------------|-------|---------------|------------|
| ...          | ...   | YYYY-MM-DD    | ...        |
(sorted by Last Modified descending)

⚠️ Results include only projects accessible to the current user.
   For all org projects, use the workaround scripts in UC-013-Component-Find-and-Replace/.
```

If zero projects reference the component, say so clearly — this is useful information
(e.g., "safe to retire — no projects depend on it").

Ask: "Would you like to replace this component with a different one?"

### Phase 4 — Replace (optional, user-initiated)

Only proceed if the user explicitly requests replacement.

**4.1 — Get the replacement component**

Ask for:
- Replacement component name or ID
- Must be the **same type** as the original (dimension→dimension, metric→metric, etc.)
  If the user provides a different type, reject it clearly and explain why.

Look up and verify the replacement component using the same approach as Phase 1.

**4.2 — Confirm the replacement plan**

Present a clear summary before touching anything:

```
REPLACEMENT PLAN
────────────────────────────────────────────
Replace:  [old name]  ([old ID])
With:     [new name]  ([new ID])
Type:     [component type]
Projects: [count] projects will be modified

[list all project names]

⚠️ This will modify project definitions.
   Changes affect all reports and panels using this component in those projects.

Proceed? (yes / no)
```

Wait for explicit confirmation before making any changes.

**4.3 — Test on one project first**

Select the project that was modified least recently as the test subject.

1. Call `describeProject(id, expansions: "definition")` to get the full definition.
2. Replace all occurrences of the old component ID with the new component ID
   (exact string match, case-sensitive).
3. Call `upsertProject` with the modified definition.
4. Report the result:
   ```
   TEST COMPLETE: [project name]
   Replaced [N] occurrence(s) of [old ID] → [new ID]

   Please verify this project in the CJA interface before continuing.
   Proceed with remaining [X] projects? (yes / no)
   ```

Only continue to the remaining projects after the user confirms the test project looks correct.

**4.4 — Batch the remaining projects**

Process remaining projects, replacing the component ID in each definition.
For each project, report: success / failure / occurrences replaced.

If a project update fails, pause and ask the user: retry / skip / stop all.

### Phase 5 — Audit Trail

After all replacements (or after find-only), offer to generate a log:

```
REPLACEMENT LOG — [date]
────────────────────────────────────────────
Component replaced: [old name] → [new name]
Total projects processed: [N]
Successful: [N]
Failed: [N]

| Project | Occurrences Replaced | Status |
|---------|---------------------|--------|
| ...     | ...                 | ✅ / ❌ |
```

## CJA MCP Tools Used

| Tool | Phase | Purpose |
|------|-------|---------|
| `findDataViews` | 0 | List data views for scope selection |
| `setDefaultSessionDataViewId` | 0 | Scope session to a specific data view |
| `findDimensions` | 1 | Search for dimensions by name |
| `findMetrics` | 1 | Search for metrics by name |
| `findSegments` | 1 | Search for segments by name |
| `findCalculatedMetrics` | 1 | Search for calculated metrics |
| `findAudiences` | 1 | Search for audiences |
| `describeDimension` | 1 | Get dimension ID and metadata |
| `describeMetric` | 1 | Get metric ID and metadata |
| `describeSegment` | 1–2 | Get segment details + usedIn expansion |
| `describeCalculatedMetric` | 1–2 | Get calc metric details + usedIn expansion |
| `describeAudience` | 1–2 | Get audience details + usedIn expansion |
| `findProjects` | 2 | List accessible projects |
| `describeProject` | 2, 4 | Get project definition for scanning and modification |
| `upsertProject` | 4 | Save modified project definition |

## Key Design Decisions

**Type safety**: Replacements are always same-type. A dimension can only be replaced by a
dimension, a segment by a segment. If the user tries to replace across types, explain clearly
that this would break the project definition.

**Test-first always**: Never batch-replace without first testing on one project and getting
explicit user confirmation. One bad replacement in a test project is recoverable; a bad batch
is not.

**`usedIn` shortcut**: For segments, calculated metrics, and audiences, the CJA API's `usedIn`
expansion returns project references without scanning. This is much faster than scanning project
definitions and should always be used when available.

**Org-wide projects**: `findProjects` only returns user-accessible projects. Documenting this
limitation clearly is important so users know the result may not be exhaustive.

## Important Guardrails

- Never replace components without explicit step-by-step user confirmation.
- Always test on one project and pause for validation before proceeding to batch replacement.
- If a replacement component is not found or is wrong type, stop and clarify before proceeding.
- If the user says "just find, don't replace", never attempt any modifications.
- Report failures clearly and give the user control over whether to retry or stop.

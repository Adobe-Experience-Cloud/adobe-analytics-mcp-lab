---
name: cja-dimension-survey
description: >
  CJA dimension survey from usage-ranked dimensions and metrics (standard metrics only; no calculated metrics, no segments in usage lists). Hardcodes Events as metrics/occurrences and All Data as segment All_Visits. After qualification, groups ordered lexicographically by component id; panel/subpanel titles use friendly names; grid subpanel descriptions are stringified Quill (Y/Z from dimension id). 3x3 grid clones scripts/subPanel_snippet_trimmed.json (trimmed genericSubPanel+FreeformReportlet). runReport under All_Visits for metric zero vs non-zero. Final panel: three text reportlets plus one non-zero-metrics table. User supplies N and/or M (single number applies to both). Prompt for data view unless already established.
---

# CJA Dimension Survey

Build a CJA Workspace project that:

1. Takes **usage-ranked dimensions** and **usage-ranked standard metrics** (counts **N** / **M** from the user—see below), after exclusions.
2. **Classifies each study dimension** with **`runReport`** using **only** the hardcoded **`metrics/occurrences`** (Events) on the column axis.
3. Places **only** dimensions with **two or more** distinct usable row values onto **3×3** freeform table panels; **each grid table** uses **only** **`metrics/occurrences`** in the column tree.
4. Runs **separate `runReport` call(s)** with **`All_Visits`** (All Data) on the **row** side and **all qualified study metrics** on the **column** side (split across multiple requests if payload or limits require), to label each qualified metric **zero** vs **non-zero**.
5. Closes with a **final panel** containing:
   - **Three** `TextReportlet` subpanels (Quill Delta in `textContent`): dimensions **no usable data**, dimensions **single usable value**, and **metrics with value 0** under All Data.
   - **One** freeform table: **every non-zero qualified metric as a row**, **All Data** as the **column** context (same segment semantics as the qualification pass; one column of values under All Data—see layout notes below).

Use [`cja-project-builder`](../cja-project-builder/SKILL.md) for v96 structure and patterns. Use [`CJA_PROJECT_PRE_UPSERT_CHECKLIST.md`](../cja-project-builder/CJA_PROJECT_PRE_UPSERT_CHECKLIST.md): **`TextReportlet.textContent`** and **dimension grid `subPanels[].description`** must be **stringified Quill Delta** (not plain text).

Do not auto-invoke unless the user explicitly asks for dimension coverage, a dimension survey, or similar bulk dimension work.

---

## Hardcoded metric and segment (do not resolve via MCP)

Use these **fixed** component ids for this skill unless the user explicitly overrides scope:

| Role | Id | Notes |
| ---- | -- | ----- |
| **Events (occurrences)** | **`metrics/occurrences`** | **Always** use this id for dimension classification `runReport`, for **every** 3×3 grid `columnTree` Events column, and anywhere this skill calls for Events. Do not substitute another metric id from `findMetrics` for these steps. |
| **All Data** | **`All_Visits`** | **Always** use this id for the built-in **All Data** / all-visits segment in **`runReport`** (metric zero vs non-zero pass) and when wiring the **All Data** column or panel segment for the final non-zero-metrics table. **Do not** call **`findSegments`** just to discover All Data for this skill. |

If `runReport` or Workspace JSON in your environment requires a **`segments/`** prefix on segment ids, use the form your MCP contract expects (e.g. `segments/All_Visits`) while keeping the same built-in target; otherwise use **`All_Visits`** as returned by your tooling.

---

## When to use

User explicitly asks for dimension coverage, which dimensions have data, a usage-based survey, or similar—when this **Events-only** classification and **metric zero / non-zero** pass fit the goal.

---

## Data view (no silent default)

- **Unless a data view is already established** in the conversation (user named one, picked one from a short list you showed, or prior context clearly fixes `dataViewId` for this task), **prompt the user to choose** after **`findDataViews`** (paginate as needed).
- **Do not** assume, auto-select, or hardcode a demo or “first” data view.

---

## Counts **N** and **M** (and single-number rule)

After exclusions:

- **`dimensionCount` (N)** and **`metricCount` (M)** come from the user.
- If the user gives **only one** number (either N or M, not both), use **that same integer for both** N and M.
- If both are missing, **ask**; do not invent counts.

**Usage lists — types allowed**

- Call **`listComponentUsage`** only with `componentType: "dimension"` and **`componentType: "metric"`**.
- **Do not** pull or merge **`calculatedMetric`** or **`segment`** lists for this skill’s candidate sets.

---

## Date range

- Default: **last 30 days** for the whole project (classification, grid tables, metric qualification, and summary table), expressed with the same **inline panel date** shape you use elsewhere for “rolling last 30 days” (for example the `td-29d/td+1d`-style preset in lab starters—match [`cja-project-builder`](../cja-project-builder/SKILL.md) unless the user specifies a different window).

---

## Exclusions (before taking top N / top M)

**Dimensions**

- Skip IDs starting with `variables/daterange`
- Skip IDs starting with `variables/timepart`
- Skip dimensions that error in classification

**Metrics**

- Use **standard metrics only** from the **`metric`** usage list (already excludes calculated metrics by source).
- Skip metrics that error or are unusable for reporting in this data view.

---

## Dimension classification (`runReport`)

For **each** of the **N** study dimensions:

- **Rows:** that dimension
- **Columns:** **only** **`metrics/occurrences`** (hardcoded; display name **Events** in `columnTree` / `__metaData__` as usual)
- **Date range:** project default (last 30 days unless the user changed it)
- **Row cap:** high enough to count distinct usable labels (e.g. top **50** rows unless the user specifies otherwise)

Normalize **No value** / **No Value** (and equivalent sentinels) as **not** usable.

| Group | Rule | On 3×3 grid |
| ----- | ---- | ----------- |
| **No data** | Zero usable row values | No |
| **One element** | Exactly one usable value (No value may appear as an extra row) | No |
| **All others** | Two or more usable values | Yes |

Errors: default **omit from grid** and mention in the **no data** text block if the user should know.

---

## Ordering and naming (after qualification)

### Lexicographic order by component **id**

Once **qualified groups** are known (dimension buckets and metric zero / non-zero sets), **sort each group** in **lexicographic order on the full component id string** (plain Unicode string sort of the id as returned by MCP—**not** the friendly display name). Use this order **before**:

- emitting dimensions or metrics into **text reportlets** (line order in Quill),
- assigning **All others** dimensions to **3×3** slots (row-major within each panel: slots `0 … 8`, then the next panel),
- building rows for the **non-zero metrics** summary table.

**Groups to sort independently:**

| Group | Sort key |
| ----- | -------- |
| **No data** dimensions | `dimension.id` |
| **One element** dimensions | `dimension.id` |
| **All others** dimensions | `dimension.id` |
| **Zero** metrics (All Data pass) | `metric.id` |
| **Non-zero** metrics (All Data pass) | `metric.id` |

Classification **`runReport`** calls may run in any order; only **published** lists and **Workspace layout** use these sorted sequences.

### Friendly **name** (for titles only)

For **panel titles** and **dimension subpanel titles**, **friendly name** means the CJA/Workspace **human-facing title** for that component id—resolve with **`describeDimension`** (dimensions) or **`describeMetric`** (metrics) when needed, or reuse an authoritative **`name`** field from the same discovery response if it already matches what Workspace shows. **Do not** use friendly names for **lexicographic ordering**; ordering is always by **id**.

### Panel titles — dimension table panels (`panels[].name`)

For **each** panel that contains a block of dimension freeform tables (up to nine per panel):

**`panels[].name`** = **`<<friendly name of first dimension in panel>> - <<friendly name of last dimension in panel>>`**

- **First** / **last** = the dimensions in that panel with the **smallest** and **largest** **id** in that panel’s chunk (because the chunk is filled from the **id-sorted All others** list).
- Use the **friendly name** rule above for both ends. If a panel has **only one** dimension, use **`<<friendly name>> - <<friendly name>>`** (same name twice) or a single name—**pick one convention per project** and stay consistent.

### Dimension subpanel titles and descriptions (`subPanels[]` on the grid)

| JSON field | Value |
| ---------- | ----- |
| **`name`** | **`<<friendly name of dimension>>`** for that subpanel’s row dimension (friendly name rule above). |
| **`description`** | **Stringified Quill Delta** (see [`CJA_PROJECT_PRE_UPSERT_CHECKLIST.md`](../cja-project-builder/CJA_PROJECT_PRE_UPSERT_CHECKLIST.md)) built from the row dimension’s **component id** using **Dimension id → subpanel description (Quill)** below. |

#### Dimension id → subpanel description (Quill)

Start from the dimension’s full **`dimension.id`** string (e.g. `variables/abc123def456...rest.path`).

1. Remove the leading prefix **`variables/`** if present.
2. If the string **starts with** a **24-character alphanumeric** token **immediately before** the **first** `.`, replace **only that token** with **`...`** plus the token’s **last 4 characters** (e.g. `abc123def456789012345678` → `...5678`). Alphanumeric = ASCII letters and digits.
3. Split on the **final** `.` in the string:
   - **`Y`**: substring from the start **through** that final `.` **inclusive**
   - **`Z`**: everything **after** that final `.`  
   If there is **no** `.` in the string after step 2, set **`Z`** to **`""`** and **`Y`** to the whole processed string.

Build a **Quill Delta** object with this exact shape (substitute your computed **`Y`** and **`Z`** string values; escape newlines and quotes for JSON as usual):

```json
{"ops":[{"insert":"<Y>\n"},{"attributes":{"italic":true},"insert":"<Z>"},{"insert":"\n"}]}
```

Build the Delta **as a JSON object in memory** (substitute real **`Y`** / **`Z`** strings into `insert` values), then set **`subPanels[].description`** to **`JSON.stringify`** of that object so **`Y` / `Z`** metacharacters are escaped correctly inside the outer `upsertProject` JSON (same pattern as other stringified Quill fields in [`CJA_PROJECT_PRE_UPSERT_CHECKLIST.md`](../cja-project-builder/CJA_PROJECT_PRE_UPSERT_CHECKLIST.md)).

---

## Metric zero / non-zero pass (`runReport`, separate from dimensions)

- **Purpose:** for the **same qualified metric IDs** (top **M** after exclusions), determine **which metrics are zero** vs **non-zero** under **All Data**.
- **Report shape:** **`All_Visits`** (All Data) on the **row** axis (only that segment row), **all qualified metrics** on the **column** axis—so each metric gets one cell. Use the hardcoded segment id from **Hardcoded metric and segment** above.
- If **M** or API limits make one request impractical, **split** into multiple `runReport` calls (disjoint metric subsets) and **merge** results before building summaries.

---

## 3×3 dimension grid — static subpanel template (no live lookup)

The grid uses **one fixed `genericSubPanel` + `FreeformReportlet` shape** for every dimension cell. **Do not** improvise alternate freeform layouts, omit fields, or merge with unrelated `describeProject` fragments for these tables.

**Project-level**

- Set **`definition.viewDensity`** to **`"compact"`** (exception to the generic builder rule about leaving `viewDensity` unset).
- **`definition.version`:** follow [`cja-project-builder`](../cja-project-builder/SKILL.md) and bundled `projectSchema_v96.json` for the org’s supported Workspace definition version.

**What may change per dimension cell (only these content fields)**

| Field | Where | Rule |
| ----- | ----- | ---- |
| **Subpanel title** | `subPanels[].name` | **`<<friendly name of dimension>>`** per **Ordering and naming** (resolve via `describeDimension` or equivalent). |
| **Description** | `subPanels[].description` | **Stringified Quill Delta** from **Dimension id → subpanel description (Quill)** in **Ordering and naming**. |
| **Dimension id** | `subPanels[].reportlet.freeformTable.dimensionSettings[0].dimension.id` | The row dimension component id. **`__metaData__.name`** on that entity may stay **`""`** in the freeform payload; the **subpanel `name`** carries the friendly title. |

**What must change per cell for uniqueness (structure unchanged)**

Use **[`scripts/subPanel_snippet_trimmed.json`](scripts/subPanel_snippet_trimmed.json)** (next to the builder in **`scripts/`**)—a trimmed **`genericSubPanel` + `FreeformReportlet`** with only the nodes needed for upsert, not a full Workspace export. Do not hand-author a different freeform shape for these cells. **[`scripts/build_dimension_survey_project.py`](scripts/build_dimension_survey_project.py)** deep-clones it by default; **`--cell-template`** may point at another file that uses the **same `<<<PLACEHOLDER>>>`** pattern (for example a maintained fork of the snippet).

Every string value that is exactly **`<<<PLACEHOLDER>>>`** is replaced for each clone. **Guids** → new RFC4122-style UUID strings. **`<<<X>>>`**, **`<<<Y>>>`**, and **`<<<VISUALIZATION_INDEX>>>`** must become **JSON numbers** (floats/ints), not quoted strings, before `upsertProject`.

| Placeholder | Role |
| ----------- | ---- |
| `<<<SUBPANEL_GUID>>>` | `subPanels[].id` |
| `<<<COLUMN_GUID>>>` | `columnTree.id` (root) |
| `<<<METRIC_COLUMN_GUID>>>` | Events column node `id` **and** `freeformTable.sort.columnId` (same value) |
| `<<<DIMENSION_GUID>>>` | `freeformTable.dimensionSettings[0].id` |
| `<<<SUBPANEL_NAME>>>` | Friendly title (`subPanels[].name` and reportlet display name in snippet) |
| `<<<SUBPANEL_DESCRIPTION_QUILL>>>` | Stringified Quill for `subPanels[].description` |
| `<<<DIMENSION_COMPONENT_ID>>>` | Row dimension id on `dimensionSettings[0].dimension.id` |
| `<<<DIMENSION_COMPONENT_NAME>>>` | Usually **`""`** on the dimension entity; friendly title stays on **`name`** |
| `<<<X>>>`, `<<<Y>>>` | Slot **`position.x`** / **`position.y`** (see slot table) |
| `<<<VISUALIZATION_INDEX>>>` | Slot **`visualizationIndex`** (integer **0–8**) |

**What changes per cell for layout (fixed 3×3 map)**

Set **`position.x`**, **`position.y`**, **`swatchColor`**, and **`visualizationIndex`** from the slot index `slot` **0–8** (row-major: left→right, top→bottom within the panel):

| `slot` | `position.x` | `position.y` | `swatchColor` | `visualizationIndex` |
| -----: | -----------: | -----------: | -------------- | --------------------: |
| 0 | 0 | 0 | `#E8871A` | 0 |
| 1 | 33.33 | 0 | `#5144D3` | 1 |
| 2 | 66.66 | 0 | `#47E26F` | 2 |
| 3 | 0 | 325 | `#DA3490` | 3 |
| 4 | 33.33 | 325 | `#2780EB` | 4 |
| 5 | 66.66 | 325 | `#DFBF03` | 5 |
| 6 | 0 | 650 | `#00C0C7` | 6 |
| 7 | 33.33 | 650 | `#9089FA` | 7 |
| 8 | 66.66 | 650 | `#6F38B1` | 8 |

Always keep **`position.autoSize`:** **`false`**, **`fixedHeight`:** **`325`**, **`autoHeight`:** **`325`**, **`width`:** **`33.33`**.

**`upsertProject` assembly**

1. Deep-clone **[`scripts/subPanel_snippet_trimmed.json`](scripts/subPanel_snippet_trimmed.json)** (or the same-shape file passed as **`--cell-template`** to the builder) for each dimension that belongs on the grid.
2. Apply the **content** table (friendly **`name`**, **`description`** = Quill from **Dimension id → subpanel description (Quill)**, **`dimension.id`**) and the **slot** table (position + swatch + `visualizationIndex`). Dimension cells must follow the **id-sorted All others** order so slot `0` is the lexicographically smallest id in that panel chunk.
3. Replace **snippet placeholders** with new ids and values per clone; ensure **`x` / `y` / `visualizationIndex`** are numeric.
4. Wrap clones in `panels[].subPanels[]` (and panel ids / dates / `reportSuite`) per [`cja-project-builder`](../cja-project-builder/SKILL.md). Do not hand-author a different freeform shape for these cells.

### Canonical `genericSubPanel` object (dimension freeform cell)

The machine-readable shape lives in **[`scripts/subPanel_snippet_trimmed.json`](scripts/subPanel_snippet_trimmed.json)** in **`scripts/`**—**do not** duplicate full cell JSON in this markdown.

**[`scripts/build_dimension_survey_project.py`](scripts/build_dimension_survey_project.py)** deep-clones that file for each grid cell (substitutions + slot geometry; coerces **`x` / `y` / `visualizationIndex`** to numbers). **`--cell-template`** may point at another JSON file with the **same placeholder contract** if you maintain a forked snippet.

When executing the skill, **do not** query CJA for a **“temporary grid sample”** or other template project—clone and bind **this JSON** (or your fork) only.

---

## Final summary panel (not a 3×3 grid)

Single closing panel **after** all 3×3 table panels. Lay out subpanels in a sensible vertical flow (e.g. three text blocks then the metrics table, or widths that match your panel geometry).

1. **Text — dimensions, no usable data** (Quill Delta). List dimensions in **lexicographic id order** (see **Ordering and naming**).
2. **Text — dimensions, single usable value** (list each dimension and its single non–No value label when known). Dimensions appear in **lexicographic id order**.
3. **Text — metrics with value 0** (from the All Data / metrics qualification pass; list clearly, **lexicographic metric id order**).
4. **Freeform table — non-zero metrics only:** **each qualifying metric as a row** in **lexicographic metric id order**, with **`All_Visits`** as the **All Data** segment context for the numeric column (same semantics as the metric qualification `runReport`). Implement with the same segment + table pattern as that pass, or **`advancedSettings.rows`** / builder-approved “metrics as rows” pattern from [`cja-project-builder`](../cja-project-builder/SKILL.md).

**`TextReportlet.textContent`:** stringified Quill only—no raw HTML/Markdown.

---

## Optional helper: config-driven `projectBody` JSON

After qualification and naming, you may emit a **small JSON config** (no Adobe calls) and run the generic builder next to this skill:

- **Grid cell JSON:** [`scripts/subPanel_snippet_trimmed.json`](scripts/subPanel_snippet_trimmed.json); optional **`--cell-template`** path to another file with the same **`<<<PLACEHOLDER>>>`** pattern
- **Script:** [`scripts/build_dimension_survey_project.py`](scripts/build_dimension_survey_project.py)
- **Example config:** [`scripts/example_survey_config.json`](scripts/example_survey_config.json)
- **Pinned lab fixture (N=M=10, snippet):** [`scripts/snippet_survey_lab_fixture_n10_m10.json`](scripts/snippet_survey_lab_fixture_n10_m10.json) — org-specific `dataViewId` / component ids; copy and edit for your data view. Built body: [`scripts/snippet_survey_lab_fixture_projectBody.min.json`](scripts/snippet_survey_lab_fixture_projectBody.min.json)

```bash
python scripts/build_dimension_survey_project.py --config your_survey.json --out projectBody.json
python scripts/build_dimension_survey_project.py --config your_survey.json --minify --out projectBody.min.json
python scripts/build_dimension_survey_project.py --config scripts/snippet_survey_lab_fixture_n10_m10.json --minify --out scripts/snippet_survey_lab_fixture_projectBody.min.json
python scripts/build_dimension_survey_project.py --config your_survey.json --cell-template path/to/your_snippet_fork.json --out projectBody.json
```

**Required config keys:** `dataViewId`, `dataViewName`, `counts` (`n`, `m`), `gridDimensions` (array of `{ "id", "friendlyName" }`, **at most 9** per panel—split into multiple panels manually if you have more), `summary` with `noDataDimensions` (array of `{ "id", "friendlyName" }`), `singleValueNote` (string), `zeroMetrics` (array of `{ "id" }`), `nonZeroMetrics` (array of `{ "id", "name" }`, non-empty; the script **sorts** these rows by metric id before building the table).

**Optional:** `projectName` (default `Top {n} / {m} components in {dataViewName}`), `projectDescription`, `dateRangeDefinition` (default `td-29d/td+1d`), `definitionVersion`, `summaryPanelTitle`, `dimensionPanelTitle`, `allDataSegmentId` / `allDataSegmentDisplayName` (defaults **`All_Visits`** / **All Data**).

Grid **subpanel height** and **slot `y`** offsets match this skill (**325** px row height; second row **y = 325**, third **y = 650**).

---

## Workflow

1. **Data view:** if not already established, **`findDataViews`**, show choices, **wait for user selection**.
2. **Counts:** resolve **N** and **M** (single supplied number → both N and M).
3. **`listComponentUsage`:** `dimension` and **`metric` only** → exclusions → top **N** dimensions, top **M** metrics.
4. **Dimension classification:** per-dimension **`runReport`** with **Events only** on columns → three groups.
5. **Metric qualification:** **`runReport`(s)** with **`All_Visits`** row + **all M metrics** on columns → zero vs non-zero lists.
6. **Order and name:** apply **Ordering and naming** — sort each qualified group by **id**; resolve **friendly names** for panel and subpanel titles; set **`panels[].name`** for each dimension-table panel; set each grid subpanel’s **`name`** and stringified-Quill **`description`** per **Dimension id → subpanel description (Quill)**.
7. **Build** 3×3 panels (**All others** only) by cloning **[`scripts/subPanel_snippet_trimmed.json`](scripts/subPanel_snippet_trimmed.json)** per cell (fresh ids; numeric **`x` / `y` / `visualizationIndex`**; slot **`swatchColor`**; friendly **`name`**, **`description`**, **`dimension.id`** per cell in **sorted** order).
8. **Build** final panel: **three** text reportlets + **one** non-zero-metrics table (lists / rows in **id** order per step 6).
9. **`upsertProject`**; use [`large-json-workflow`](../large-json-workflow/SKILL.md) when needed. Return the Workspace link.

---

## Tool notes

- **`listComponentUsage`:** `dataViewId`; **never** `calculatedMetric` or `segment` for candidate lists in this skill.
- **`runReport`:** dimension passes use **`metrics/occurrences`** only on columns; metric pass uses **`All_Visits`** on rows + full qualified metric set on columns (chunk if needed).
- **`describeDimension`** / **`describeMetric`:** use when building **friendly** panel and subpanel **titles** (and any optional display labels), not for ordering.
- **`searchDimensionItems`:** optional if classification rows are ambiguous.

---

## Guardrails

- No **calculated metrics** and no **segments** in the **usage-based** N/M candidate lists.
- Do not put **No data** or **One element** dimensions on the **3×3** grid.
- **3×3** applies only to **dimension** table panels; the final panel mixes **three** texts + **one** table.
- Do not default a **data view** without user confirmation (unless already established in-session as above).
- Do **not** query CJA for **“temporary grid sample”** (or any named template project) while executing this skill; dimension grid cells **must** follow **[`scripts/subPanel_snippet_trimmed.json`](scripts/subPanel_snippet_trimmed.json)** (or a fork with the **same** placeholder-driven shape via **`--cell-template`**)—no alternate freeform layouts for those cells.
- Do **not** call **`findSegments`** solely to resolve **All Data**; use **`All_Visits`** per **Hardcoded metric and segment**.

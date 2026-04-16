---
name: cja-component-visualizer
description: >
  CJA Workspace component co-usage network (D3): usage-weighted nodes and co-usage edges from listComponentUsage + listFrequentlyUsedWith. Use when the user wants a component relationship map, co-usage visualization, or “which components appear together” graph for their data view. Always drive builds from the user’s org/session, chosen data view, and explicit preferences (volume/threshold).
---

# CJA component network (visualizer)

Produce an **interactive component map** for **the user’s** Customer Journey Analytics data view: nodes are dimensions, metrics, calculated metrics, and segments; links encode **co-usage** (MCP **`listFrequentlyUsedWith`**) and node size can reflect **`listComponentUsage`** counts.

This skill is **context-first**: resolve **which data view** and **how much graph** the user wants before calling APIs.

---

## When to use

The user asks for things like:

- component co-usage / relationship / dependency map  
- “what’s used with what” in Workspace for **their** data view  
- a network or force graph of CJA components  
- emitting HTML/JS for **their** org from fresh MCP pulls  

---

## Non-negotiables

1. **Data view** — Use the user’s **`dataViewId`** (and IMS org implied by their MCP session). If they do not supply an id, use MCP **`findDataViews`** (or equivalent listing) and have them **pick one**.  
2. **Preferences** — Ask (or infer clearly from their message) how they want **volume / thresholds**:  
   - **Universe**: e.g. all usage rows after exclusions, **above mean** per type, **mean + 1 SD**, **top N per component type**, or a **hard cap** on total nodes.  
   - **Edges**: prefer real **`listFrequentlyUsedWith`** co-usage; if that is blocked, document fallback (e.g. **`proxy_edges`** in `scripts/component_network_lib.py`) and set expectations (“synthetic proximity,” not co-usage).  
   - **Exclusions**: default noise filter is `EXCLUDE` / `should_exclude` in `scripts/component_network_lib.py`; adjust only if the user asks.  
3. **Secrets** — Never commit bearer tokens, raw MCP dumps with secrets, or customer identifiers the user did not agree to store.  

---

## Run artifacts (`outputs/`)

HTML/JS (and optional JSON sidecars) from MCP-backed builds go under **`outputs/`** at the skill root. That directory is **gitignored** at the repo level (see root `.gitignore`). **Do not commit** contents.

After saving **`outputs/mcp_run_bundle.json`** (usage + FUW from MCP):

`python scripts/build_network_to_outputs.py`

Optional: `--max-nodes N`, `--input path/to/bundle.json`, `--run-label "My label"`, **`outputs/display_names.json`** (see workflow step 6).

---

## Agent workflow (user-driven build)

1. **Confirm target** — Data view name + **`dataViewId`** from the user or from **`findDataViews`** + user confirmation.  
2. **Confirm graph policy** — Selection rule (above mean / +1 SD / top-N / cap), edge source (FUW vs proxy), and whether to tweak **`EXCLUDE`**.  
3. **Usage** — Call **`listComponentUsage`** once per type: `dimension`, `metric`, `calculatedMetric`, `segment` with the chosen **`dataViewId`**. Normalize to rows `(componentId, componentType, usageCount)`; drop rows where `should_exclude(componentId)` unless the user opts out.  
4. **Selection** — Apply `select_above_mean`, `select_1sd`, or a user-defined rule; enforce any **max node** cap last so the graph stays readable.  
5. **Co-usage** — For each seed in the selected universe (and any extra seeds the user cares about), call **`listFrequentlyUsedWith`** with **`dataViewId`**. For **metric** and **dimension** seeds, use **`componentId` with literal `%252F` instead of `/`** where your MCP layer still 404s on slash ids (see **`MCP_BUG_REPORT.md`**). Merge bidirectional pairs into undirected edges; keep **`count`** as weight. Restrict targets to types you want in the graph (dimension, metric, calculatedMetric, segment).  
6. **Labels (friendly titles, not raw ids)** — For each selected component id, resolve a **display title** and pass it into **`build_nodes(..., display_names=...)`** (`scripts/component_network_lib.py` maps `name` in the emitted JS). Use CJA MCP:  
   - **Dimensions** — `describeDimension` with `dataViewId` and `dimensionId` **without** the `variables/` prefix (see MCP tool description). Use the response **`name`**.  
   - **Metrics** — `describeMetric` with `metricId` **without** the `metrics/` prefix. Use **`name`**.  
   - **Calculated metrics** — `describeCalculatedMetric` with full calculated metric id; **`expansions`** is required (e.g. `dataName` or `dataName,definition`). Use **`name`**.  
   - **Segments** — `describeSegment` with segment id; **`expansions`** is required (e.g. `dataName`). Use **`name`** (human label).  
   Build a JSON map **`fullComponentId` → `title`** and save it as **`outputs/display_names.json`** (gitignored). **`scripts/build_network_to_outputs.py`** merges that file (and optional `displayNames` on the bundle, and `--display-names`). Helpers: `scripts/component_display_names.py`. Skip auto-merge with **`--skip-display-names`** if you only want raw ids.  
7. **Emit artifacts** — Save the bundle JSON with **`dataViewId`**, **`dataViewLabel`**, **`usage`**, and **`fuw`**, then run **`python scripts/build_network_to_outputs.py`**. The writer uses **`synthetic_sample/component_network_top100.html`** as the HTML shell (string replacements only).  
8. **Handoff** — Tell the user how to open the HTML locally and what selection/edge rules were used.  

Reuse **`scripts/component_network_lib.py`** for math and node shaping.

Long-form replication (token copy, network tab, etc.) remains in **`AGENT_REPLICATION_GUIDE.md`**.

---

## Related files

| File | Role |
|------|------|
| `scripts/component_network_lib.py` | Shared selection, exclusions, `proxy_edges`, `build_nodes`, `count_types` (no embedded data view). |
| `MCP_BUG_REPORT.md` | `%252F` encoding for FUW seeds. |
| `AGENT_REPLICATION_GUIDE.md` | Detailed replication and API steps. |
| `VISUALIZATION_NOTES.md` | Layout, quintile tiers, UX; not read by build scripts. |
| `outputs/` | Gitignored folder for local HTML/JS run outputs. |
| `scripts/build_network_to_outputs.py` | Reads MCP bundle JSON → writes HTML/JS under **`outputs/`**. |
| `scripts/component_display_names.py` | Parse/merge display-name overlays (no MCP calls). |
| `synthetic_sample/component_network_top100.html` | HTML shell template for emitted pages. |

---

## Do not

- Ship a “plan” that hard-codes one data view for all users.  
- Use **`listSimilarTo`** as a stand-in for co-usage unless the user explicitly asks for similarity rather than co-usage.  

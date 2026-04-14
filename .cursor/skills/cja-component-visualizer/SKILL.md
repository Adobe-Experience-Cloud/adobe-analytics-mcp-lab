---
name: cja-component-visualizer
description: >
  CJA Workspace component co-usage network (D3): usage-weighted nodes and co-usage edges from listComponentUsage + listFrequentlyUsedWith. Use when the user wants a component relationship map, co-usage visualization, or “which components appear together” graph for their data view. Always drive builds from the user’s org/session and chosen data view plus explicit preferences (volume/threshold); never assume an example snapshot data view. Optional demo_example bundle is a fake-dataset preview only.
---

# CJA component network (visualizer)

Produce an **interactive component map** for **the user’s** Customer Journey Analytics data view: nodes are dimensions, metrics, calculated metrics, and segments; links encode **co-usage** (MCP **`listFrequentlyUsedWith`**) and node size can reflect **`listComponentUsage`** counts.

This skill is meant to be **shared**. Treat every run as **context-first**: resolve **which data view** and **how much graph** the user wants before calling APIs. **Do not** follow a fixed plan tied to a specific production or example snapshot data view.

---

## When to use

The user asks for things like:

- component co-usage / relationship / dependency map  
- “what’s used with what” in Workspace for **their** data view  
- a network or force graph of CJA components  
- regenerating or extending the bundled HTML/JS pattern for **their** org  

---

## Non-negotiables

1. **Data view** — Use the user’s **`dataViewId`** (and IMS org implied by their MCP session). If they do not supply an id, use MCP **`findDataViews`** (or equivalent listing) and have them **pick one**. Never default to the bundled id in **`demo_example/demo_example_snapshot.py`** for a real deliverable.  
2. **Preferences** — Ask (or infer clearly from their message) how they want **volume / thresholds**:  
   - **Universe**: e.g. all usage rows after exclusions, **above mean** per type, **mean + 1 SD**, **top N per component type**, or a **hard cap** on total nodes.  
   - **Edges**: prefer real **`listFrequentlyUsedWith`** co-usage; if that is blocked, document fallback (e.g. **`proxy_edges`** in `scripts/component_network_lib.py`) and set expectations (“synthetic proximity,” not co-usage).  
   - **Exclusions**: default noise filter is `EXCLUDE` / `should_exclude` in `scripts/component_network_lib.py`; adjust only if the user asks.  
3. **Secrets** — Never commit bearer tokens, raw MCP dumps with secrets, or customer identifiers the user did not agree to store.  

---

## Optional preview (not the default workflow)

**`demo_example/`** is a **frozen fake-dataset example** so anyone can open a finished-looking HTML/JS pair **without** credentials. Use it only to answer “what does the output look like?” — not as the template for **their** data view.

- Open: `demo_example/component_network_demo_example.html` (with `visualization_data_demo_example.js` beside it).  
- Regenerate that preview: `python demo_example/build_demo_example.py` from the skill folder (reads `demo_example/demo_example_snapshot.py` only).  

---

## Run artifacts (`outputs/`)

Ephemeral HTML/JS (and optional JSON sidecars) from **MCP-backed** or **scratch** builds go under **`outputs/`** at the skill root. That directory is **gitignored** at the repo level (see root `.gitignore`) so Cursor/OneDrive sync and git stays clean. **Do not commit** contents.

Example (local check using the lab snapshot module, not a substitute for live MCP):

`python scripts/build_network_to_outputs.py --preset lab-snapshot --max-nodes 85`

MCP-backed bundle + optional **`outputs/display_names.json`** (see **Agent workflow** step 6):

`python scripts/build_network_to_outputs.py --preset mcp-json`

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
   Build a JSON map **`fullComponentId` → `title`** and save it as **`outputs/display_names.json`** (gitignored). **`scripts/build_network_to_outputs.py`** auto-merges that file (and optional `displayNames` on the bundle, and `--display-names`) when using **`--preset mcp-json`**. Helpers: `scripts/component_display_names.py`. Skip auto-merge with **`--skip-display-names`** if you only want raw ids.  
7. **Emit artifacts** — Write `visualization_data_<label>.js` (`nodes` + `apiConnections` in the same shape as the samples) and either copy **`synthetic_sample/component_network_top100.html`** as a base and swap the `<script src=...>` or follow the string-replace approach in **`demo_example/build_demo_example.py`**. Prefer writing under **`outputs/`** for one-off runs so files stay out of git (see **Run artifacts** above).  
8. **Handoff** — Tell the user how to open the HTML locally and what selection/edge rules were used.  

Reuse **`scripts/component_network_lib.py`** for math and node shaping; add a **small** runner script or one-off code path that passes **live MCP rows**, not `demo_example/demo_example_snapshot.py`.

Long-form replication (token copy, network tab, etc.) remains in **`AGENT_REPLICATION_GUIDE.md`**.

---

## Related files

| File | Role |
|------|------|
| `scripts/component_network_lib.py` | Shared selection, exclusions, `proxy_edges`, `build_nodes`, `count_types` (no embedded data view). |
| `demo_example/demo_example_snapshot.py` | **Example only** — frozen fake-dataset usage + FUW for the static preview. |
| `demo_example/build_demo_example.py` | Regenerates the static **`demo_example/`** bundle from the snapshot only. |
| `MCP_BUG_REPORT.md` | `%252F` encoding for FUW seeds. |
| `AGENT_REPLICATION_GUIDE.md` | Detailed replication and API steps. |
| `VISUALIZATION_NOTES.md` | Layout, quintile tiers, UX; not read by build scripts. |
| `outputs/` | Gitignored folder for local HTML/JS run outputs (see **Run artifacts**). |
| `scripts/build_network_to_outputs.py` | Writer into **`outputs/`** (`lab-snapshot` or `mcp-json` preset; merges display titles). |
| `scripts/component_display_names.py` | Parse/merge display-name overlays (no MCP calls). |

---

## Do not

- Ship a “plan” that hard-codes one data view for all users.  
- Present **`demo_example/`** as if it were their org’s graph without labeling it as the fake-dataset preview.  
- Use **`listSimilarTo`** as a stand-in for co-usage unless the user explicitly asks for similarity rather than co-usage.  

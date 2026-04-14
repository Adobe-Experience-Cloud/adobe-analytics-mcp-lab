# CJA component network (visualizer skill)

Interactive **D3** layouts that show **which CJA components tend to appear together** in Workspace projects, plus optional **usage** sizing on nodes.

For **shared / multi-tenant** use, start with **`SKILL.md`**: pick the **user’s data view**, confirm **thresholds and graph size**, then pull live usage and co-usage for that view.

## Quick start (sample bundle)

1. **Optional fake-dataset preview (no build):** open **`demo_example/component_network_demo_example.html`** in a browser (same folder as `visualization_data_demo_example.js`) to see **one** finished-looking result — not your data view.  
2. **Synthetic pipeline samples:** open **`synthetic_sample/component_network_above_mean.html`** or **`synthetic_sample/component_network_top100.html`** with their matching `visualization_data_*.js` in the same folder (built by PowerShell under **`scripts/`**).
3. Use **Fit All**, pan/zoom, and **Separation** to explore.

The **`demo_example/`** bundle is a **frozen fake-dataset example** (`demo_example/demo_example_snapshot.py`: usage + co-usage). **`synthetic_sample/`** holds the **synthetic** lab graph (`connections_sample_raw.json`), HTML templates, and generated `visualization_data_*.js` for layout and script testing.

## Regenerate sample JS (PowerShell)

From this directory (skill root):

```powershell
.\scripts\build_1sd_outliers.ps1; .\scripts\generate_1sd_viz.ps1
.\scripts\build_above_mean.ps1; .\scripts\generate_above_mean_viz.ps1
```

Friendly labels for the sample ids live in **`synthetic_sample/component_display_names.json`**.

## Fake-dataset static demo (regenerate preview snapshot only)

Run **`python demo_example/build_demo_example.py`** (or **`python scripts/component_network_lib.py`**, same output) from this folder. That refreshes files inside **`demo_example/`** from **`demo_example/demo_example_snapshot.py`** only (illustrative ids and labels). Open the HTML locally; no MCP required to view. Real user builds follow **`SKILL.md`** with their **`dataViewId`**.

## MCP data for graph edges

- **`listComponentUsage`** — usage counts per component type.
- **`listFrequentlyUsedWith`** — co-usage edges; for **metrics** and **dimensions**, pass **`componentId` with a literal `%252F` in place of each `/`** (example: `metrics%252Foccurrences`). Plain slash ids often **404** on MCP. See **`MCP_BUG_REPORT.md`** for the encoding matrix.

**`listSimilarTo`** is **not** part of this skill’s workflow (similarity links are omitted).

## Documentation

See **`SKILL.md`** (agent workflow), **`START_HERE.md`**, **`AGENT_REPLICATION_GUIDE.md`**, **`PROJECT_SUMMARY.md`**, and **`VISUALIZATION_NOTES.md`** (layout, tiers, UX) for structure, replication, and file roles.

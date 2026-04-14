# CJA component network visualization — start here

## What this is

An interactive **D3.js** network: **nodes** are CJA components (dimensions, metrics, calculated metrics, segments). **Links** represent **co-usage strength** (from your own `connections_*.json` export, or from MCP **`listFrequentlyUsedWith`** when you build that export).

**Agents:** the canonical, shareable workflow is **`SKILL.md`** — always use the **user’s data view** and their **volume/threshold** preferences. Nothing in this folder should be read as “the” data view for every run.

This skill also ships with **samples**: a frozen **fake-dataset** demo preview and **small synthetic graphs** so you can open HTML locally without production credentials.

---

## File guide

### View the sample

- **`SKILL.md`** — **primary** instructions for user-context builds (data view + preferences → visualization map)  
- **`demo_example/component_network_demo_example.html`** + **`demo_example/visualization_data_demo_example.js`** — **optional fake-dataset preview** (what a finished bundle can look like; open locally; no build step)
- **`synthetic_sample/component_network_above_mean.html`** + **`synthetic_sample/visualization_data_above_mean.js`** — synthetic PowerShell pipeline sample
- **`synthetic_sample/component_network_top100.html`** + **`synthetic_sample/visualization_data_top10pct.js`** — synthetic “mean + 1 SD” sample (legacy filename)

### Understand behavior

- **`README.md`** — quick start  
- **`VISUALIZATION_NOTES.md`** — layout (three-zone), separation toggle, quintile link tiers, UX/interaction, how to read the graph, future ideas (not used by builds)  
- **`MCP_BUG_REPORT.md`** — MCP **`listFrequentlyUsedWith`** `%252F` workaround; why **`listSimilarTo`** is out of scope  

### Replicate for your org

1. Follow **`AGENT_REPLICATION_GUIDE.md`**.  
2. You need: a **bearer token**, your **IMS org id**, and a **data view id** (values come from your environment — do not commit them).  
3. Prefer **`listComponentUsage`** (MCP) for usage lists. **Co-usage edges:** use MCP **`listFrequentlyUsedWith`** with **`componentId` using a literal `%252F` in place of each `/`** for metrics and dimensions (canonical `metrics/foo` still tends to **404** on MCP). **Similarity** (`listSimilarTo`) is **not** used in this skill. Encoding details: **`MCP_BUG_REPORT.md`**.

### Fake-dataset demo bundle (regenerate preview only)

- **`demo_example/build_demo_example.py`** — refreshes the **`demo_example/`** HTML/JS from **`demo_example/demo_example_snapshot.py`** (frozen fake-dataset usage + **listFrequentlyUsedWith**). Not a substitute for a user-driven build.
- **`scripts/component_network_lib.py`** — shared helpers only; its **`main()`** delegates to **`demo_example/build_demo_example.py`** for that preview.

---

## Regenerate sample data (PowerShell)

```powershell
cd .cursor\skills\cja-component-visualizer
.\scripts\build_1sd_outliers.ps1; .\scripts\generate_1sd_viz.ps1
.\scripts\build_above_mean.ps1; .\scripts\generate_above_mean_viz.ps1
```

Source graph: **`synthetic_sample/connections_sample_raw.json`**. Display names: **`synthetic_sample/component_display_names.json`**.

---

## Interaction cheat sheet

- **Hover a node** — highlights its incident links; others dim.  
- **Pan / zoom** — drag background; scroll to zoom.  
- **Fit All / Reset** — viewport controls.  
- **Separation** — toggles the three-zone horizontal bias.

---

## Agent task (generic)

> Follow **`SKILL.md`**: confirm **my** `dataViewId` and graph preferences (volume/threshold), then pull usage, pull or approximate co-usage, exclude standard time/person noise fields, dedupe bidirectional edges, resolve display names, emit `visualization_data*.js` + self-contained `component_network*.html` with quintile link tiers. Use **`AGENT_REPLICATION_GUIDE.md`** for long-form replication detail.

The user supplies **token**, **org**, and **data view**; keep those out of git.

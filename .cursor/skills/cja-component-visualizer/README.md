# CJA component network (visualizer skill)

Interactive **D3** layout: **which CJA components tend to appear together** in Workspace (co-usage from MCP **`listFrequentlyUsedWith`**), with node size from **`listComponentUsage`**.

Start with **`SKILL.md`**: confirm the **user’s data view**, **thresholds**, and **graph size**, pull usage and co-usage from MCP, save a bundle JSON, then run the builder below.

## Build from MCP data

1. Save **`listComponentUsage`** + **`listFrequentlyUsedWith`** (plus `dataViewId` / label) as **`outputs/mcp_run_bundle.json`** — shape expected by **`scripts/build_network_to_outputs.py`** (see **`SKILL.md`** / **`AGENT_REPLICATION_GUIDE.md`**).
2. From the skill root:

```bash
python scripts/build_network_to_outputs.py
python scripts/build_network_to_outputs.py --max-nodes 30
python scripts/build_network_to_outputs.py --input outputs/my_bundle.json
```

3. Open the generated **`outputs/component_network_run_n*.html`** next to its **`visualization_data_run_n*.js`**.

Optional: **`outputs/display_names.json`** for friendly titles (merged automatically unless **`--skip-display-names`**).

## MCP edges

- **`listFrequentlyUsedWith`** — for **metrics** and **dimensions**, some gateways need **`componentId` with literal `%252F` in place of each `/`**. See **`MCP_BUG_REPORT.md`**.

**`listSimilarTo`** is not part of this skill’s workflow.

## Documentation

**`SKILL.md`**, **`START_HERE.md`**, **`AGENT_REPLICATION_GUIDE.md`**, **`PROJECT_SUMMARY.md`**, **`VISUALIZATION_NOTES.md`**.

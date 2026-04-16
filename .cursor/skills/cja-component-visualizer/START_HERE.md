# CJA component network visualization — start here

## What this is

An interactive **D3.js** network: **nodes** are CJA components (dimensions, metrics, calculated metrics, segments). **Links** are **co-usage** from MCP **`listFrequentlyUsedWith`** (and usage sizing from **`listComponentUsage`**).

**Agents:** follow **`SKILL.md`** — always the **user’s data view** and their **volume/threshold** preferences.

---

## Build a fresh graph

1. **`SKILL.md`** — full MCP workflow (usage, FUW, display names, bundle JSON).  
2. **`AGENT_REPLICATION_GUIDE.md`** — replication detail (token, org, data view; keep secrets out of git).  
3. **`scripts/build_network_to_outputs.py`** — reads **`outputs/mcp_run_bundle.json`** (or **`--input`**) and writes HTML + JS under **`outputs/`**.

```bash
cd .cursor\skills\cja-component-visualizer
python scripts\build_network_to_outputs.py --max-nodes 30
```

4. **`MCP_BUG_REPORT.md`** — **`listFrequentlyUsedWith`** `%252F` workaround.

**`scripts/component_network_lib.py`** is a **library** only; run **`build_network_to_outputs.py`** to emit files.

---

## Interaction (in the generated HTML)

- **Hover a node** — highlights incident links.  
- **Pan / zoom** — drag background; scroll to zoom.  
- **Fit All / Reset** — viewport controls.  
- **Separation** — three-zone horizontal bias toggle.

---

## Agent task (generic)

> Follow **`SKILL.md`**: confirm **my** `dataViewId` and graph preferences, pull usage and co-usage from MCP, build the bundle, run **`python scripts/build_network_to_outputs.py`**, hand off the **`outputs/`** HTML + JS.

The user supplies **token**, **org**, and **data view**; keep those out of git.

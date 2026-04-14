# Component visualizer skill — summary

This folder holds a **D3.js** force-directed **component network** pattern for Customer Journey Analytics: nodes are dimensions, metrics, calculated metrics, and segments; edges are co-usage strengths (from your own exported `connections_*.json`, typically produced via MCP **`listFrequentlyUsedWith`**).

## Bundled assets

| Asset | Role |
|--------|------|
| `scripts/*.ps1` | Synthetic pipeline: selection + `visualization_data_*.js` generation |
| `scripts/component_network_lib.py` | Shared Python helpers for real or demo builds |
| `synthetic_sample/connections_sample_raw.json` | Tiny **synthetic** edge list for local testing |
| `synthetic_sample/component_display_names.json` | Friendly labels for sample component ids |
| `synthetic_sample/*.html` + matching `visualization_data_*.js` | Synthetic “mean + 1 SD” / “above mean” samples |
| `demo_example/component_network_demo_example.html` + `visualization_data_demo_example.js` | **Optional fake-dataset preview** (open in browser; no MCP to view) |
| `SKILL.md` | **Primary** agent workflow: user data view + preferences → map |
| `demo_example/demo_example_snapshot.py` | Frozen fake-dataset usage + FUW for preview only |
| `demo_example/build_demo_example.py` | Regenerate the **`demo_example/`** bundle from the snapshot (uses `synthetic_sample/component_network_top100.html` as HTML template) |

Do **not** commit production tokens or bearer strings in graph exports.

## Docs index

- `SKILL.md` — user-context workflow (data view + thresholds)  
- `START_HERE.md` — orientation and file map  
- `AGENT_REPLICATION_GUIDE.md` — end-to-end replication for **your** data view  
- `VISUALIZATION_NOTES.md` — consolidated UI/design/UX notes (not used by builds)  
- `MCP_BUG_REPORT.md` — MCP `listFrequentlyUsedWith` encoding (`%252F`); `listSimilarTo` out of scope  

**Folders:** `scripts/` (Python + PowerShell builders), `synthetic_sample/` (checked-in synthetic graph + templates), `demo_example/` (fake-dataset browser preview), `outputs/` (**gitignored** — local run HTML/JS).

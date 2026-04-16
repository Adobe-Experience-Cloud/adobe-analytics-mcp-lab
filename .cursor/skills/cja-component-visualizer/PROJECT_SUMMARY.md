# Component visualizer skill — summary

**D3.js** force-directed **component network** for Customer Journey Analytics: nodes are dimensions, metrics, calculated metrics, and segments; edges are co-usage from MCP **`listFrequentlyUsedWith`** (bundle JSON → **`build_network_to_outputs.py`**).

## Bundled pieces

| Piece | Role |
|--------|------|
| `scripts/component_network_lib.py` | Selection, exclusions, `proxy_edges`, `build_nodes` |
| `scripts/build_network_to_outputs.py` | MCP bundle JSON → **`outputs/`** HTML + JS |
| `scripts/component_display_names.py` | Merge display-name overlays |
| `synthetic_sample/component_network_top100.html` | HTML shell template for emitted pages |
| `SKILL.md` | Primary agent workflow |

Do **not** commit production tokens or raw MCP exports with secrets.

## Docs

- `SKILL.md` — workflow  
- `START_HERE.md` — orientation  
- `AGENT_REPLICATION_GUIDE.md` — replication  
- `VISUALIZATION_NOTES.md` — UX / layout notes  
- `MCP_BUG_REPORT.md` — FUW `%252F` encoding  

**Folders:** `scripts/`, `synthetic_sample/` (template + legacy synthetic assets), `outputs/` (**gitignored**).

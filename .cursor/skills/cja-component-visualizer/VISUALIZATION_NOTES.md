# Visualization notes (design & UX)

Single reference for **layout, tiers, interaction, and how to read** the component-network HTML/JS in this skill. Builds and scripts do **not** read this file; it is for humans and agents editing or explaining the UI.

---

## Table of contents

1. [Three-zone spatial layout](#three-zone-spatial-layout)
2. [Spatial separation (toggle & forces)](#spatial-separation-toggle--forces)
3. [Dynamic tier system (quintiles)](#dynamic-tier-system-quintiles)
4. [UX and interaction](#ux-and-interaction)
5. [Reading a component network](#reading-a-component-network)
6. [Future ideas](#future-ideas)

---

## Three-zone spatial layout

The component network visualization uses a **three-zone spatial layout** so types are easier to scan.

### Zones (left → right)

#### 1. Metrics and calculated metrics (left, ~20% width)

- **Color:** Metrics use one accent; calculated metrics use another (see HTML legend).
- **Examples:** Orders, revenue, session counts, derived rates (labels depend on your data view).

#### 2. Dimensions (center, ~50% width)

- **Color:** Dimension accent.
- **Examples:** Page, campaign, channel, product attributes — whatever appears in your `nodes` data.

#### 3. Segments (right, ~80% width)

- **Color:** Segment accent.
- **Examples:** Registered visitors, campaign filters, high-value audiences — from your segment definitions.

### Force simulation

The D3 layout combines:

- **Link force** — distance/strength from co-usage tier  
- **Many-body charge** — repulsion so labels stay readable  
- **Weak Y pull** — slight vertical centering  
- **X bias** — pushes each type toward its column  

Toggle **Separation** in the UI to reduce or disable the horizontal bias.

### Reference implementation

See **`synthetic_sample/component_network_*.html`** in this skill.

---

## Spatial separation (toggle & forces)

*Note: This section includes an earlier two-column write-up alongside toggle behavior. Where it conflicts with the [three-zone layout](#three-zone-spatial-layout) section, treat **three-zone** as the canonical model for current `component_network_*.html`.*

### Overview

The visualization includes spatial organization so **metrics** are separated from **dimensions / calculated metrics**, making component types easier to see at a glance.

### Layout organization (two-column description)

#### Left zone (35% of canvas)

**METRICS** — example counts and names from a sample dataset (your graph will differ).

#### Right zone (65% of canvas)

**DIMENSIONS & CALC METRICS** — dimensions and calculated metrics from the same illustrative split.

### Visual indicators

- **Separator line**: Dashed vertical line dividing zones (when that layout variant is used).
- **Zone labels** at the top.
- **Color coding** (see HTML legend): metrics, dimensions, calc metrics use distinct accents.

### Enhanced spacing

Example parameter shifts used when tuning dense graphs (values are illustrative; inspect current HTML/JS for live numbers):

| Parameter | Direction of change |
|-----------|---------------------|
| Link distance (strong vs weak tiers) | Wider spacing for readability |
| Charge strength | Stronger repulsion |
| Collision buffer | Larger padding |
| Link strength | Weaker links for distant tiers |

### Toggle control

**Separation: ON/OFF**

- Near **Fit All** / **Reset View** in the header.
- **ON:** Spatial separation forces apply (type-based horizontal bias).
- **OFF:** Components arrange from connection forces only.

### Drag behavior

- Lower **alpha** on restart for smoother dragging.
- Nodes can stay pinned after drag; double-click node or background to unpin and let the simulation resume.

### Force simulation (example)

```javascript
.force("x", d3.forceX()
    .x(d => d.type === "metric" ? width * 0.35 : width * 0.65)
    .strength(0.3))  // 0.3 when ON, 0 when OFF
.force("y", d3.forceY(height / 2).strength(0.1))
```

The X-axis force pulls nodes toward their zones while strong co-usage can still pull groups toward the middle.

### When to use separation ON vs OFF

- **ON:** Initial exploration, teaching, finding a component by type.
- **OFF:** Emphasizing pure connection clusters and cross-type bridges.

### Cross-zone connections

Links that span zones highlight **metric–dimension** (and similar) pairings. High co-usage tiers pull nodes toward a natural **bridge** region.

### Navigation tips

1. **Pan** — drag empty space  
2. **Zoom** — scroll or pinch  
3. **Fit All** — entire network in view  
4. **Reset View** — default zoom/center  
5. **Drag nodes** — manual layout  
6. **Toggle separation** — alternate layout emphasis  

---

## Dynamic tier system (quintiles)

### Overview

Connection tiers are calculated **dynamically** from the distribution of co-usage **counts** in the loaded graph, not from fixed numeric cutoffs. Relative strength stays meaningful across different datasets.

### How it works

#### Quintile calculation

Connections are grouped into **5 tiers** (quintiles) along the range from minimum to maximum count:

```
Range = Maximum Count - Minimum Count
Percentile = (Connection Count - Minimum Count) / Range

Tier 5 (Top 20%):    Percentile >= 0.8   [Strongest connections]
Tier 4 (60-80%):     Percentile >= 0.6
Tier 3 (40-60%):     Percentile >= 0.4   [Middle/average]
Tier 2 (20-40%):     Percentile >= 0.2
Tier 1 (Bottom 20%): Percentile < 0.2    [Weakest connections]
```

#### Why quintiles?

- **Adaptive** — scales with your data  
- **Balanced** — each tier is ~20% of the strength range  
- **Comparative** — emphasizes relative importance  
- **Consistent** — five visual tiers even when raw counts are skewed  

### Visual representation

#### Tier styling (typical mapping)

| Tier | Color | Width | Shadow | Meaning |
|------|-------|-------|--------|---------|
| 5 | Bright green (#22c55e) | 5px | Yes (green glow) | Top 20% — strongest |
| 4 | Lime (#84cc16) | 4px | Yes (lime glow) | 60–80% |
| 3 | Yellow (#eab308) | 3px | No | 40–60% |
| 2 | Orange (#f97316) | 2.5px | No | 20–40% |
| 1 | Gray (#cbd5e0) | 1.5px | No | Bottom 20% |

#### Hover (when implemented on links)

Design intent: wider stroke, glow, and labels showing **raw count**; **node hover** may highlight incident links instead of requiring hover on thin lines.

### Tooltip information

Typical content:

- **Connection** — source ↔ target names  
- **Co-usage count** — raw value (e.g. “52 times”)  
- **Strength** — tier label (e.g. “Tier 5”)  

### Example distribution

Thresholds are **recomputed on load** from `apiConnections`. Any numeric example (min/max counts) is illustrative only.

### Advantages over static thresholds

**Older static approach:** fixed cutoffs could leave most edges in one tier. **Quintile approach:** spreads edges across tiers using the actual min/max range.

### Technical implementation (sketch)

```javascript
const maxCount = Math.max(...apiConnections.map(c => c.count));
const minCount = Math.min(...apiConnections.map(c => c.count));
const range = maxCount - minCount;

const percentile = (conn.count - minCount) / range;
if (percentile >= 0.8) tier = 'tier-5';
else if (percentile >= 0.6) tier = 'tier-4';
else if (percentile >= 0.4) tier = 'tier-3';
else if (percentile >= 0.2) tier = 'tier-2';
else tier = 'tier-1';
```

### Use in analysis

- Strongest patterns — top quintile  
- Communities — many high-tier links inside a group  
- Anomalies — single very strong cross-cluster link  
- Relative ranking — even when absolute counts are small  

---

## UX and interaction

### Enhanced node labels (readability)

- **Color** — darker charcoal for text  
- **Weight** — semi-bold  
- **Size** — slightly larger than default  

### Smart tooltip positioning

Algorithm keeps tooltips inside the viewport and flips side when near edges (right/left/top/bottom).

### Interaction model (node-centric)

Many builds use **node-focused** interaction:

- Hover a **node** — enlarge slightly, tooltip, connected links highlighted and widened, unconnected links dimmed, link count labels on connected edges.  
- Default — full node opacity; links at a fixed baseline opacity; link labels hidden until focus.  

*(Some iterations removed direct link hover to avoid fighting thin hit targets; behavior matches the HTML you ship.)*

### Visual hierarchy

- **Type colors** — see legend in HTML (metrics / dimensions / calc metrics / segments).  
- **Connection tiers** — quintile colors and widths (see [Dynamic tier system](#dynamic-tier-system-quintiles)).  
- **Node size** — often scaled from usage in the payload.  

### Keyboard-free navigation

Pan, zoom, hover, drag, **Fit All**, **Reset View**, **Separation** — all pointer-driven.

### Performance

Short transitions, collision handling, SVG rendering; heavy effects (e.g. glow) may be limited to top tiers.

### Accessibility (design intent)

High-contrast labels, redundant encoding (size/position plus color), predictable hover/dim pattern, legend + stats panel for context.

### Edge cases called out in UX work

Viewport edge tooltips, zoom/pan during hover, resize, dense vs sparse graphs, isolated nodes.

### Incorporated feedback (checklist)

Examples of themes addressed in iterations: spatial separation, spacing, display names, noise exclusions, dynamic tiers, hover focus, label contrast, tooltip placement, node-first interaction.

### Additional UI ideas (not necessarily implemented)

- Search / filter by name  
- Highlight by business category  
- Path tracing between two nodes  
- Export PNG/SVG  
- Side-by-side comparison of two datasets  
- Time-filtered usage  
- Community detection  
- Drill-down to Workspace usage  

---

## Reading a component network

### What the graph encodes

- **Nodes** — dimensions, metrics, calculated metrics, and segments from your `visualization_data*.js` payload. **Size** usually reflects a **usage** or **strength** score you chose when building the file.  
- **Links** — **co-usage** or another **pairwise score** you defined when building the graph. Thickness/color tiers are **quintiles** on that score within the current graph (see [Dynamic tier system](#dynamic-tier-system-quintiles)).  

### Density

**Density** = actual edges divided by the maximum possible undirected edges among the selected nodes. Low density is normal when analysts use different slices of the same large catalog.

### Interpreting clusters

Tight clusters often imply a **shared reporting workflow**. Long bridges suggest **cross-workflow** pairings that are still strong in your export.

### Files in this skill

Outputs follow naming conventions (`outputs/visualization_data_run_n*.js` from **`build_network_to_outputs.py`**, plus older `synthetic_sample/visualization_data_*.js` if present). Counts and labels always come from the **generated JS** next to each HTML file.

---

## Future ideas

### Skill roadmap

**Project nodes at the rim** — Optionally add **workspace project** nodes on the perimeter, linked to components that appear in those projects. *Considerations:* rotating project ids, stale filters, cap degree to avoid star graphs.

**Edge bundling or hive plot** — For very dense `apiConnections`, bundling parallel edges or an auxiliary hive/matrix view.

**Automated refresh** — Scheduled MCP re-runs and regeneration of exports + viz scripts (keep tokens and sensitive exports out of git).

### From UX exploration

See also the bullet list under **Additional UI ideas** in [UX and interaction](#ux-and-interaction).

---

*This file replaces: `THREE_ZONE_LAYOUT.md`, `SPATIAL_SEPARATION_FEATURE.md`, `DYNAMIC_TIER_SYSTEM.md`, `UX_IMPROVEMENTS_SUMMARY.md`, `FINAL_NETWORK_SUMMARY.md`, and `FUTURE_IDEAS.md`.*

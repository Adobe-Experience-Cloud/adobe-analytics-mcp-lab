# CJA Component Network Visualization - Agent Replication Guide

## Overview

This guide enables any agent to recreate the CJA Component Network Visualization for any organization and data view. The visualization shows how CJA components (dimensions, metrics, calculated metrics, segments) are used together in workspace projects.

### Before you start (shared skill)

Read **`SKILL.md`** first. The **default** path is **user-context driven**: confirm the user’s **`dataViewId`** (or list data views and let them choose) and their **preferences** for how many components and which threshold (for example above-mean vs mean + 1 SD vs top-N). Do **not** assume a specific example snapshot data view for deliverables.

The **`demo_example/`** HTML/JS pair is an **optional preview** of what a finished bundle looks like (frozen fake-dataset example), not the template graph for every org.

## What This Creates

The PowerShell samples in this folder historically produced **two** threshold examples on synthetic data:

1. **Statistical Outliers (Mean + 1.0 SD)**: ~16 components - only the true statistical standouts (~7% of components)
2. **Above Mean**: ~37 components - broader view of high-usage components (~17% of components)

For **live** MCP builds, match the user’s requested policy (which may differ from both).

Both visualizations feature:
- **Three-zone spatial layout**: Metrics/Calc Metrics (left), Dimensions (center), Segments (right)
- **Node sizing by actual project usage**: Larger nodes = more frequently used
- **Connection strength visualization**: Color-coded by co-occurrence frequency (quintile-based tiers)
- **Interactive controls**: Pan, zoom, spatial separation toggle, hover tooltips

## Prerequisites

### Required User Information
1. **OAuth Bearer Token**: User must provide a fresh token for CJA API authentication
2. **Data View ID**: Target data view (e.g., `dv_XXXXXXXXXXXXXXXXXXXX`)

**Note**: The Org ID is automatically determined from your CJA MCP authentication. As long as your MCP connection and web CJA login are authenticated to the same organization, you only need to specify the Data View ID.

### How to Obtain Your OAuth Bearer Token

The easiest way to get your CJA authentication token is through your browser's developer tools:

#### Step-by-Step Instructions

1. **Open CJA** in your browser and navigate to Analysis Workspace

2. **Open Developer Tools**:
   - **Windows/Linux**: Press `Ctrl + Shift + I`
   - **Mac**: Press `Cmd + Option + I`
   - Or right-click anywhere and select "Inspect"

3. **Go to the Network tab** in Developer Tools

4. **Filter for API calls**:
   - In the filter box, type: `appsvc`
   - This will show only CJA API requests

5. **Trigger an API call**:
   - Go to a blank workspace
   - Drag any dimension into a freeform table
   - You'll see network requests appear

6. **Find a "ranked" request** (or any `metrics?locale=` or `ranked?locale=` request)

7. **Copy the Authorization token** (two methods):

   **Method 1 - Copy All Headers** (Easiest):
   - Right-click on the request
   - Select **"Copy"** → **"Copy as PowerShell"** (or similar option)
   - Paste the entire output into Cursor
   - The agent will automatically extract the Bearer token

   **Method 2 - Copy Just the Token**:
   - Click on the request to open the details panel
   - Click the **"Headers"** tab
   - Scroll to the **"Request Headers"** section
   - Find the **"Authorization"** header
   - Copy the entire value (starts with `Bearer eyJ...`)
   - Paste just this token value when prompted

#### Token Validity

- Tokens typically expire after **24 hours**
- If you get authentication errors, get a fresh token using the steps above
- The token is specific to your Adobe account and org

#### Finding Your Data View ID

Once you have the token, the agent can list available data views for you using the CJA API. Alternatively:
- In CJA, go to **Components** → **Data Views**
- Click on your target data view
- The Data View ID appears in the URL: `dataview/dv_XXXXXXXXXXXXXXXXXXXX`

### Tools Needed
- CJA MCP tools (`user-CJA-*` functions)
- PowerShell for data processing
- File system access for JSON storage

## Step-by-Step Replication Process

### Phase 1: Data Collection

#### 1.1 Identify Most-Used Components

Use `user-CJA-listComponentUsage` to find the most frequently used components:

```javascript
// Call for each component type
user-CJA-listComponentUsage({ componentType: 'dimension' })
user-CJA-listComponentUsage({ componentType: 'metric' })
user-CJA-listComponentUsage({ componentType: 'calculatedMetric' })
user-CJA-listComponentUsage({ componentType: 'segment' })
```

**Note**: If MCP tools time out or return empty, retry with fewer components, confirm **`dataViewId`**, refresh the session token, and verify **`listFrequentlyUsedWith`** uses literal **`%252F`** for slashy metric/dimension ids (see **`MCP_BUG_REPORT.md`**).

#### 1.2 Fetch "Frequently Used With" Relationships

For each component from step 1.1, call:

```javascript
user-CJA-listFrequentlyUsedWith({
    componentId: <component_id>,
    componentType: <type>,
    dataViewId: <data_view_id>
})
```

**Critical — `listFrequentlyUsedWith`:** pass **`componentId` as a single string** where each `/` is replaced by the literal sequence **`%252F`** (for example `metrics%252Foccurrences`, `variables%252Fdaterangeday`). Canonical ids with a plain `/` often return **404** from MCP; `%2F` only is typically **invalid**. This skill does **not** use **`listSimilarTo`** (similarity edges). See **`MCP_BUG_REPORT.md`** for the encoding matrix.

**Save all raw responses** to `connections_raw.json` with this structure:
```json
[
  {
    "Source": "variables/eVar1",
    "Target": "metrics/visits",
    "Count": 286
  }
]
```

Where `Count` = number of projects where these components appear together.

### Phase 2: Component Selection

Create two selection strategies:

#### 2.1 Statistical Outliers (Mean + 1.0 SD)

For each component category:
1. Calculate mean usage: `mean = Σ(usage) / n`
2. Calculate standard deviation: `σ = √(Σ(x - mean)² / n)`
3. Select components where `usage > mean + (1.0 * σ)`

**PowerShell implementation**: See `scripts/build_1sd_outliers.ps1`

**Standard fields to exclude**:
- `metrics/visits`, `metrics/visitors`, `metrics/occurrences`, `metrics/bounces`
- `metrics/timespent*`, `metrics/event*`
- `variables/daterange*`, `variables/day`, `variables/week`, `variables/month`, etc.
- `variables/adobe_personid`, `variables/personid`, `variables/timestamp`

**Typical results**: 12-20 components (0-2 dominant segments, 2-4 dimensions, 3-4 metrics, 6-8 calc metrics)

#### 2.2 Above Mean

For each component category:
1. Calculate mean usage
2. Select all components where `usage > mean`

**PowerShell implementation**: See `scripts/build_above_mean.ps1`

**Typical results**: 35-40 components (14 segments, 6 dimensions, 6 metrics, 11 calc metrics)

### Phase 3: Network Building

#### 3.1 Filter Connections

From `connections_raw.json`:
1. Keep only connections where **both** Source and Target are in the selected components list
2. Deduplicate bidirectional connections:
   - If both `A→B` and `B→A` exist, keep only the one with higher `Count`
   - Store using a normalized key: `min(A,B)|max(A,B)`

#### 3.2 Calculate Network Metrics

```
nodes = selected components
edges = deduplicated connections
density = (actual_edges / max_possible_edges) * 100
  where max_possible_edges = (n * (n-1)) / 2
```

### Phase 4: Fetch Component Names

For all selected components, fetch display names:

```javascript
// Dimensions
user-CJA-describeDimension({ 
    dimensionId: <id_without_variables_prefix> 
})

// Metrics  
user-CJA-describeMetric({ 
    metricId: <id_without_metrics_prefix> 
})

// Calculated Metrics
user-CJA-describeCalculatedMetric({ 
    id: <full_id>,
    expansions: "definition"
})

// Segments
user-CJA-describeSegment({ 
    segmentId: <full_id>,
    expansions: "name,description"
})
```

**Store in a lookup map** for the generation phase.

### Phase 5: Generate Visualization Data

Create JavaScript data files with this structure:

```javascript
// visualization_data_top10pct.js (for 1SD outliers)
const nodes = [
    {
        id: "n1",                    // Simple sequential ID
        fullId: "variables/eVar1",   // Original CJA ID
        name: "Custom Dimension 1",  // Display name
        type: "dimension",           // dimension|metric|calculatedMetric|segment
        usage: 15250                 // Total co-occurrence count from raw data
    }
    // ... more nodes
];

const apiConnections = [
    {
        source: "n1",     // References node.id
        target: "n3",
        count: 286        // Number of projects with this pair
    }
    // ... more connections
];
```

**PowerShell implementation**: See `scripts/generate_1sd_viz.ps1` and `scripts/generate_above_mean_viz.ps1`

**Key requirements**:
- `usage` must come from the **full raw dataset**, not just filtered network
- IDs must be simplified (`n1`, `n2`, etc.) for D3.js performance
- Store connection `count` for tier calculation in the visualization

### Phase 6: Create HTML Visualizations

Copy the template structure from `synthetic_sample/component_network_top100.html` and update:

1. **Title**: Update to reflect selection method
2. **Script source**: Point to the correct data file
3. **Header stats**: Update component counts per type
4. **Legend**: Update counts in parentheses

**Two final files** (in this skill they live under **`synthetic_sample/`**):
- `synthetic_sample/component_network_top100.html` → 1SD statistical outliers (16 components)
- `synthetic_sample/component_network_above_mean.html` → Above mean (37 components)

### Phase 7: Verify and Test

1. Open each HTML file in a modern browser (Chrome, Firefox, Edge)
2. Verify:
   - All nodes render with circles and labels
   - Node sizes vary by usage (largest = highest usage)
   - Hover shows full component details
   - Separation toggle works (adjusts zone spacing)
   - Connections show color gradients (green=rare → red=frequent)
   - Pan and zoom respond smoothly

## File Structure (Final State)

```
cja-component-visualizer/
├── SKILL.md, README.md, START_HERE.md, PROJECT_SUMMARY.md, …
├── scripts/
│   ├── component_network_lib.py           # Shared Python helpers (real + demo builds)
│   ├── build_1sd_outliers.ps1            # Step 2a: synthetic 1SD selection
│   ├── build_above_mean.ps1              # Step 2b: synthetic above-mean selection
│   ├── generate_1sd_viz.ps1             # Step 3a: emit JS for 1SD graph
│   ├── generate_above_mean_viz.ps1      # Step 3b: emit JS for above-mean graph
│   └── analyze_statistical_outliers.ps1
├── synthetic_sample/
│   ├── connections_sample_raw.json       # Tiny synthetic edge list (not MCP)
│   ├── component_display_names.json
│   ├── visualization_data_top10pct.js
│   ├── visualization_data_above_mean.js
│   ├── component_network_top100.html
│   └── component_network_above_mean.html
├── demo_example/                         # Fake-dataset static preview + builder
└── …
```

For **your** org, keep raw MCP exports (e.g. `connections_raw.json`) **outside** git; the layout above matches this skill’s **checked-in** samples.

## Example Statistical Findings

### Typical Distribution Patterns

**Segment Distribution**: Often highly right-skewed
- A few segments may dominate usage (e.g., visitor/customer filters)
- Most segments have lower usage counts
- Mean + 1.0 SD typically identifies 1-3 dominant segments

**Dimension Distribution**: More balanced
- Page-related dimensions often have high usage
- Custom dimensions vary by organization

**Metric Distribution**: 
- Core event metrics typically stand out
- Custom events depend on implementation

**Calculated Metric Distribution**:
- Usually lower usage than base metrics
- Performance rates and ratios common

### Network Density Patterns

| Selection Method | Typical Components | Typical Density | Interpretation |
|------------------|-------------------|-----------------|----------------|
| Mean + 1.5 SD | 10-15 | 20-25% | Ultra-focused, highest connectivity |
| **Mean + 1.0 SD** | **15-20** | **25-30%** | **Optimal: Best balance** |
| Above Mean | 35-40 | 15-20% | Moderate breadth, still interpretable |
| Top Quartile (Q3) | 50-60 | 10-15% | Getting cluttered |
| Above Median | 100-110 | 3-5% | Too sparse for meaningful patterns |

**Recommendation**: Mean + 1.0 SD provides the best balance of focus and comprehensiveness.

## Troubleshooting

### Issue: MCP Tools Return Empty Results

**Things to check**:

1. For **metrics** and **dimensions**, `componentId` must use literal **`%252F`** instead of `/` in **`listFrequentlyUsedWith`** (see **`MCP_BUG_REPORT.md`**).
2. Confirm **`dataViewId`** matches the org your MCP session is using.
3. Reduce batch size or retry timeouts; save MCP output to JSON as you go.

### Issue: Token Expires During Long MCP Sessions

**Solution**: 
1. Fetch all connections in one session (typically 10-20 minutes)
2. Save raw data to JSON immediately
3. All subsequent processing works offline from the saved data

### Issue: Component Names Missing

**Solution**:
- Some components may not have public names in the API
- Display as `[Unknown: <id_prefix>]` in the visualization
- Usually indicates internal/system components

### Issue: Empty Visualization Canvas

**Problem**: Variable name mismatch between data file and HTML
**Solution**: Ensure data file exports `const nodes` and `const apiConnections` (not `vizData.nodes`)

## MCP tools (reference)

| Goal | MCP tool | Notes |
|------|-----------|--------|
| Usage by type | `user-CJA-listComponentUsage` | `componentType`: `dimension`, `metric`, `calculatedMetric`, `segment` |
| Co-usage edges | `user-CJA-listFrequentlyUsedWith` | For metrics/dimensions, `componentId` must use literal **`%252F`** instead of `/` (see **`MCP_BUG_REPORT.md`**) |
| Display names | `user-CJA-describeDimension`, `describeMetric`, `describeCalculatedMetric`, `describeSegment` | As needed for labels |

**`listSimilarTo`** is intentionally **not** used in this skill workflow.

## Customization Options

### Adjust Statistical Threshold

Modify the standard deviation multiplier in `build_*sd_outliers.ps1`:

```powershell
$threshold = $mean + (1.5 * $stdDev)  # More restrictive (fewer components)
$threshold = $mean + (0.75 * $stdDev) # Less restrictive (more components)
```

### Change Excluded Standard Fields

Edit the `$excludePatterns` array to match your org's naming conventions:

```powershell
$excludePatterns = @(
    '^metrics/visits$',
    '^metrics/custom_*',  # Add custom patterns
    '^variables/prop*'    # Exclude props if needed
)
```

### Modify Visualization Colors

In the HTML file, update the color scale:

```javascript
const colorScale = d3.scaleOrdinal()
    .domain(['dimension', 'metric', 'calculatedMetric', 'segment'])
    .range(['#48bb78', '#f56565', '#9f7aea', '#ed8936']);
```

## Success Criteria

A successful replication should produce:

✅ Two HTML files that open without errors  
✅ All nodes visible with circles and labels  
✅ Node sizes proportional to actual usage  
✅ Connections color-coded by frequency  
✅ Hover tooltips showing full component details  
✅ Three-zone layout with clear spatial separation  
✅ Smooth pan/zoom interactions  
✅ Separation toggle adjusting zone spacing  
✅ Network density between 15-30% for optimal interpretation  

## Performance Notes

- **Raw data fetch**: 10-20 minutes (depends on component count and MCP latency)
- **Processing time**: < 2 minutes for filtering, deduplication, and statistical analysis
- **Name fetching**: ~1 second per component (batch in parallel when possible)
- **Visualization generation**: < 5 seconds per variant
- **Browser rendering**: Instant for networks up to 100 nodes; smooth for up to 200

## Methodology

This approach uses statistical analysis to identify genuinely high-usage components rather than arbitrary percentage cutoffs. The Mean + 1.0 SD threshold successfully filters noise while identifying components that truly stand out in usage patterns. This is particularly effective for segment selection, where distributions are often highly skewed.

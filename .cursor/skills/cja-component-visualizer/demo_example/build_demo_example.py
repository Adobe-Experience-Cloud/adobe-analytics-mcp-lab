"""
Regenerate the **optional static preview** in this folder only.

Uses ``demo_example_snapshot.py`` in this folder (same directory as this script; frozen **fake-dataset** example).
The shared skill workflow for real users is **user-context driven** — see ``../SKILL.md``.

Run from the skill root (``cja-component-visualizer``)::

    python demo_example/build_demo_example.py

Or from this folder::

    python build_demo_example.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
for _p in (ROOT, DEMO, SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import component_network_lib as lab
import demo_example_snapshot as snap

OUT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "synthetic_sample" / "component_network_top100.html"


def filtered_rows() -> list[tuple[str, str, int]]:
    return [(c, t, u) for c, t, u in snap.USAGE_ROWS if not lab.should_exclude(c)]


def merge_fuw_edges(universe: set[str]) -> list[dict]:
    allowed = {"dimension", "metric", "calculatedMetric", "segment"}
    best: dict[tuple[str, str], int] = {}
    for seed, items in snap.FUW_COUSAGE.items():
        if seed not in universe:
            continue
        for it in items:
            tid = it["componentId"]
            if not tid or tid == "undefined" or "undefined" in tid:
                continue
            if it["componentType"] not in allowed:
                continue
            if tid not in universe:
                continue
            a, b = sorted((seed, tid))
            best[(a, b)] = max(best.get((a, b), 0), int(it["count"]))
    return [{"source": a, "target": b, "count": cnt} for (a, b), cnt in sorted(best.items())]


def to_js(
    selected: list[str],
    rows: list[tuple[str, str, int]],
    edges: list[dict],
) -> str:
    umap = {c: u for c, t, u in rows}
    nodes, id_map = lab.build_nodes(selected, umap, rows, snap.DISPLAY_NAMES)
    api = []
    for e in edges:
        s = id_map.get(e["source"])
        t = id_map.get(e["target"])
        if s and t:
            api.append({"source": s, "target": t, "count": e["count"]})

    dim = sum(1 for n in nodes if n["type"] == "dimension")
    met = sum(1 for n in nodes if n["type"] == "metric")
    calc = sum(1 for n in nodes if n["type"] == "calculatedMetric")
    seg = sum(1 for n in nodes if n["type"] == "segment")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    header = (
        "// Demo example — static preview only (see SKILL.md for user-driven builds)\n"
        f"// Generated: {ts}\n"
        f"// Data view: {snap.DATA_VIEW_DISPLAY_NAME} ({snap.DATA_VIEW_ID})\n"
        f"// Components: {len(nodes)} ({met} metrics, {dim} dimensions, {calc} calc metrics, {seg} segments)\n"
        f"// Connections: {len(api)} co-usage pairs (MCP listFrequentlyUsedWith; metric/dimension seeds use %252F)\n"
        "// Selection: all filtered top-usage components (standard time/person noise excluded)\n"
        "// Snapshot: demo_example/demo_example_snapshot.py (fake dataset); not a template for other orgs\n"
    )
    return (
        header
        + "const nodes = "
        + json.dumps(nodes, separators=(",", ":"))
        + ";\nconst apiConnections = "
        + json.dumps(api, separators=(",", ":"))
        + ";\n"
    )


def build_html_demo(title: str, subtitle_html: str, selected: list[str], rows: list[tuple[str, str, int]]) -> str:
    raw = TEMPLATE.read_text(encoding="utf-8")
    ct = lab.count_types(selected, rows)
    total = len(selected)
    raw = raw.replace(
        '<script src="visualization_data_top10pct.js"></script>',
        '<script src="visualization_data_demo_example.js"></script>',
    )
    raw = raw.replace(
        "<title>CJA Component Network - Statistical Outliers</title>",
        f"<title>{title}</title>",
    )
    raw = raw.replace(
        "<h1>Sample lab — Component network (mean + 1 SD)</h1>",
        f"<h1>{title}</h1>",
    )
    raw = raw.replace(
        """                <div class="subtitle">
                    <strong>Counts from data:</strong> see legend after load • Three-zone layout<br/>
                    <em style="font-size: 0.9em; color: #a0aec0;">Synthetic <code>synthetic_sample/connections_sample_raw.json</code>; regenerate with <code>scripts/build_1sd_outliers.ps1</code> + <code>scripts/generate_1sd_viz.ps1</code></em>
                </div>""",
        f'                <div class="subtitle">\n                    {subtitle_html}\n                </div>',
    )
    raw = raw.replace(
        """                    <span>Metrics</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #48bb78;"></div>
                    <span>Dimensions</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #9f7aea;"></div>
                    <span>Calc metrics</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ed8936;"></div>
                    <span>Segments</span>""",
        f"""                    <span>Metrics ({ct["metric"]})</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #48bb78;"></div>
                    <span>Dimensions ({ct["dimension"]})</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #9f7aea;"></div>
                    <span>Calc metrics ({ct["calculatedMetric"]})</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ed8936;"></div>
                    <span>Segments ({ct["segment"]})</span>""",
    )
    raw = raw.replace(
        """                <div class="stat-item">Data: <span class="stat-value">Synthetic lab sample (no production DV)</span></div>
                <div class="stat-item">Components: <span class="stat-value">(from JS)</span></div>""",
        f"""                <div class="stat-item">Data View: <span class="stat-value">{snap.DATA_VIEW_DISPLAY_NAME} ({snap.DATA_VIEW_ID})</span></div>
                <div class="stat-item">Components: <span class="stat-value">{total}</span></div>""",
    )
    return raw


def main() -> None:
    rows = filtered_rows()
    universe = {c for c, _, _ in rows}
    all_edges = merge_fuw_edges(universe)
    selected = [c for c, _, _ in rows]
    sel_set = set(selected)
    edges = [e for e in all_edges if e["source"] in sel_set and e["target"] in sel_set]

    OUT.mkdir(parents=True, exist_ok=True)
    js = to_js(selected, rows, edges)
    (OUT / "visualization_data_demo_example.js").write_text(js, encoding="utf-8")

    ct = lab.count_types(selected, rows)
    refresh = (
        "<code>python demo_example/build_demo_example.py</code> "
        "(from the skill folder) or <code>python build_demo_example.py</code> (from <code>demo_example/</code>)"
    )
    sub = (
        f"<strong>{len(selected)} components:</strong> {ct['metric']} metrics | {ct['dimension']} dimensions | "
        f"{ct['calculatedMetric']} calc metrics | {ct['segment']} segments • <strong>{len(edges)}</strong> co-usage links • three-zone layout<br/>"
        f'<em style="font-size: 0.9em; color: #a0aec0;">Preview only. Real builds use the user&apos;s data view — see <code>SKILL.md</code>. Refresh: {refresh}.</em>'
    )
    html = build_html_demo("Demo example — component network (fake dataset)", sub, selected, rows)
    (OUT / "component_network_demo_example.html").write_text(html, encoding="utf-8")

    readme = (
        "Demo example (static preview only)\n"
        "====================================\n\n"
        "This folder is a frozen fake-dataset example for preview — not your org's data view.\n"
        "For real builds, see SKILL.md in the parent folder.\n\n"
        "Open component_network_demo_example.html in a browser (same folder as visualization_data_demo_example.js).\n"
        "No MCP or Python required to view.\n\n"
        "Regenerate (from the skill folder, cja-component-visualizer):\n"
        "  python demo_example/build_demo_example.py\n\n"
        "Or cd into this folder and run:\n"
        "  python build_demo_example.py\n"
    )
    (OUT / "README.txt").write_text(readme, encoding="utf-8")

    print(f"Wrote {OUT / 'component_network_demo_example.html'}")
    print(f"Wrote {OUT / 'visualization_data_demo_example.js'} ({len(selected)} nodes, {len(edges)} edges)")


if __name__ == "__main__":
    main()

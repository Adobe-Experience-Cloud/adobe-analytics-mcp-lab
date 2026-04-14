"""
Write a component-network HTML + JS pair under ``outputs/`` (gitignored).

Typical use: after pulling ``listComponentUsage`` + ``listFrequentlyUsedWith`` via MCP,
save a JSON bundle under ``outputs/`` (gitignored), e.g. ``outputs/mcp_run_bundle.json``, and build
with ``--preset mcp-json``. Also supports ``--preset lab-snapshot`` for a local pipeline check when
MCP is unavailable (uses ``demo_example/demo_example_snapshot.py``).

Run from skill root::

    python scripts/build_network_to_outputs.py --preset lab-snapshot --max-nodes 85

    python scripts/build_network_to_outputs.py --preset mcp-json
    python scripts/build_network_to_outputs.py --preset mcp-json --input outputs/my_bundle.json

Optional friendly node labels: save ``outputs/display_names.json`` (flat id -> title map from
``describeDimension`` / ``describeMetric`` / ``describeCalculatedMetric`` / ``describeSegment``),
or add a ``displayNames`` object on the bundle. Merge order: bundle ``displayNames``, then
``outputs/display_names.json`` if present, then ``--display-names`` file. Use
``--skip-display-names`` to ignore the default ``outputs/display_names.json``.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DEMO = ROOT / "demo_example"


def _bootstrap_path() -> None:
    import sys

    for p in (ROOT, SCRIPTS, DEMO):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)


def merge_fuw_edges(
    universe: set[str],
    fuw: dict[str, list[dict]],
) -> list[dict]:
    allowed = {"dimension", "metric", "calculatedMetric", "segment"}
    best: dict[tuple[str, str], int] = {}
    for seed, items in fuw.items():
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
    *,
    data_view_id: str,
    data_view_label: str,
    selected: list[str],
    rows: list[tuple[str, str, int]],
    edges: list[dict],
    display_names: dict[str, str],
    selection_note: str,
) -> str:
    import component_network_lib as lab

    umap = {c: u for c, t, u in rows}
    nodes, id_map = lab.build_nodes(selected, umap, rows, display_names)
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
        "// outputs/ — local run (gitignored). Do not commit.\n"
        f"// Generated: {ts}\n"
        f"// Data view: {data_view_label} ({data_view_id})\n"
        f"// Components: {len(nodes)} ({met} metrics, {dim} dimensions, {calc} calc metrics, {seg} segments)\n"
        f"// Connections: {len(api)} co-usage pairs\n"
        f"// Selection: {selection_note}\n"
    )
    return (
        header
        + "const nodes = "
        + json.dumps(nodes, separators=(",", ":"))
        + ";\nconst apiConnections = "
        + json.dumps(api, separators=(",", ":"))
        + ";\n"
    )


def build_html(
    *,
    template_path: Path,
    title: str,
    subtitle_html: str,
    selected: list[str],
    rows: list[tuple[str, str, int]],
    data_view_id: str,
    data_view_label: str,
    js_name: str,
) -> str:
    import component_network_lib as lab

    raw = template_path.read_text(encoding="utf-8")
    ct = lab.count_types(selected, rows)
    total = len(selected)
    raw = raw.replace(
        '<script src="visualization_data_top10pct.js"></script>',
        f'<script src="{js_name}"></script>',
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
        f"""                <div class="stat-item">Data View: <span class="stat-value">{data_view_label} ({data_view_id})</span></div>
                <div class="stat-item">Components: <span class="stat-value">{total}</span></div>""",
    )
    return raw


def run_lab_snapshot(*, max_nodes: int, run_label: str) -> None:
    _bootstrap_path()
    import component_network_lib as lab
    import demo_example_snapshot as snap

    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows_all = [(c, t, u) for c, t, u in snap.USAGE_ROWS if not lab.should_exclude(c)]
    rows_sorted = sorted(rows_all, key=lambda x: -x[2])
    rows = rows_sorted[: max(1, max_nodes)]
    selected = [c for c, _, _ in rows]
    universe = set(selected)
    all_edges = merge_fuw_edges(universe, snap.FUW_COUSAGE)
    sel_set = set(selected)
    edges = [e for e in all_edges if e["source"] in sel_set and e["target"] in sel_set]

    dv_id = snap.DATA_VIEW_ID
    dv_label = run_label
    sel_note = (
        f"default EXCLUDE filter; all filtered components by usage, capped at {max_nodes} nodes "
        f"(digestibility cap; {len(rows)} after cap)"
    )

    js_name = "visualization_data_run.js"
    js = to_js(
        data_view_id=dv_id,
        data_view_label=dv_label,
        selected=selected,
        rows=rows,
        edges=edges,
        display_names=snap.DISPLAY_NAMES,
        selection_note=sel_note,
    )
    (out_dir / js_name).write_text(js, encoding="utf-8")

    ct = lab.count_types(selected, rows)
    sub = (
        f"<strong>{len(selected)} components:</strong> {ct['metric']} metrics | {ct['dimension']} dimensions | "
        f"{ct['calculatedMetric']} calc metrics | {ct['segment']} segments • <strong>{len(edges)}</strong> co-usage links • three-zone layout<br/>"
        "<em style=\"font-size: 0.9em; color: #a0aec0;\">Written to <code>outputs/</code> (gitignored). "
        "Open <code>component_network_run.html</code> beside the JS file. For live MCP pulls, use the same "
        "<code>dataViewId</code> with fresh <code>listComponentUsage</code> / <code>listFrequentlyUsedWith</code>.</em>"
    )
    template = ROOT / "synthetic_sample" / "component_network_top100.html"
    html = build_html(
        template_path=template,
        title=f"Component network — {run_label}",
        subtitle_html=sub,
        selected=selected,
        rows=rows,
        data_view_id=dv_id,
        data_view_label=dv_label,
        js_name=js_name,
    )
    (out_dir / "component_network_run.html").write_text(html, encoding="utf-8")

    manifest = {
        "run_label": run_label,
        "dataViewId": dv_id,
        "preset": "lab-snapshot",
        "max_nodes": max_nodes,
        "nodes_written": len(selected),
        "edges_written": len(edges),
        "note": "CJA MCP was not used in this agent session; data came from demo_example_snapshot.py for pipeline validation.",
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    print(f"Wrote {out_dir / 'component_network_run.html'}")
    print(f"Wrote {out_dir / js_name}")


def _resolve_display_names_for_run(
    raw: dict,
    *,
    explicit_path: Path | None,
    skip_default_file: bool,
) -> tuple[dict[str, str], list[str]]:
    _bootstrap_path()
    import component_display_names as dn

    parts: list[dict[str, str]] = [dn.overlay_from_bundle(raw)]
    sources: list[str] = []
    if raw.get("displayNames"):
        sources.append("bundle.displayNames")

    default_fp = ROOT / "outputs" / "display_names.json"
    if not skip_default_file and default_fp.is_file():
        parts.append(dn.load_display_names_file(default_fp))
        sources.append(str(default_fp))

    if explicit_path is not None:
        if explicit_path.is_file():
            parts.append(dn.load_display_names_file(explicit_path))
            sources.append(str(explicit_path))
        else:
            print(f"Warning: --display-names file not found, skipping: {explicit_path}")

    merged = dn.merge_display_names(*parts)
    return merged, sources


def run_mcp_json(
    *,
    bundle_path: Path,
    max_nodes: int,
    run_label: str | None,
    display_names_path: Path | None,
    skip_default_display_names: bool,
) -> None:
    _bootstrap_path()
    import component_network_lib as lab

    raw = json.loads(bundle_path.read_text(encoding="utf-8"))
    dv_id = str(raw["dataViewId"])
    dv_label = run_label or str(raw.get("dataViewLabel") or dv_id)
    usage_list = raw["usage"]
    fuw = {str(k): list(v) for k, v in raw["fuw"].items()}

    rows_all: list[tuple[str, str, int]] = []
    for row in usage_list:
        cid = str(row["componentId"])
        typ = str(row["componentType"])
        cnt = int(row["count"])
        rows_all.append((cid, typ, cnt))

    rows_filtered = [(c, t, u) for c, t, u in rows_all if not lab.should_exclude(c)]
    rows_sorted = sorted(rows_filtered, key=lambda x: -x[2])
    cap = max(1, max_nodes)
    rows = rows_sorted[:cap]
    selected = [c for c, _, _ in rows]
    universe = set(selected)
    all_edges = merge_fuw_edges(universe, fuw)
    sel_set = set(selected)
    edges = [e for e in all_edges if e["source"] in sel_set and e["target"] in sel_set]

    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    display_names, dn_sources = _resolve_display_names_for_run(
        raw,
        explicit_path=display_names_path,
        skip_default_file=skip_default_display_names,
    )
    sel_note = (
        f"MCP bundle {bundle_path.name}; default EXCLUDE filter; components by usage "
        f"(capped at {cap} nodes; {len(rows)} after cap)"
    )
    if display_names:
        sel_note += f"; friendly labels for {len(display_names)} ids"
        if dn_sources:
            sel_note += f" ({', '.join(dn_sources)})"

    js_name = "visualization_data_run.js"
    js = to_js(
        data_view_id=dv_id,
        data_view_label=dv_label,
        selected=selected,
        rows=rows,
        edges=edges,
        display_names=display_names,
        selection_note=sel_note,
    )
    (out_dir / js_name).write_text(js, encoding="utf-8")

    ct = lab.count_types(selected, rows)
    sub = (
        f"<strong>{len(selected)} components:</strong> {ct['metric']} metrics | {ct['dimension']} dimensions | "
        f"{ct['calculatedMetric']} calc metrics | {ct['segment']} segments • <strong>{len(edges)}</strong> co-usage links • three-zone layout<br/>"
        "<em style=\"font-size: 0.9em; color: #a0aec0;\">Written to <code>outputs/</code> (gitignored). "
        "Open <code>component_network_run.html</code> beside the JS file. Regenerate from MCP export via "
        "<code>--preset mcp-json</code>.</em>"
    )
    template = ROOT / "synthetic_sample" / "component_network_top100.html"
    html = build_html(
        template_path=template,
        title=f"Component network — {dv_label}",
        subtitle_html=sub,
        selected=selected,
        rows=rows,
        data_view_id=dv_id,
        data_view_label=dv_label,
        js_name=js_name,
    )
    (out_dir / "component_network_run.html").write_text(html, encoding="utf-8")

    manifest = {
        "run_label": dv_label,
        "dataViewId": dv_id,
        "preset": "mcp-json",
        "bundle": str(bundle_path.resolve()),
        "max_nodes": cap,
        "nodes_written": len(selected),
        "edges_written": len(edges),
        "displayNamesResolved": len(display_names),
        "displayNamesSources": dn_sources,
        "note": "Built from listComponentUsage + listFrequentlyUsedWith saved as JSON (CJA MCP).",
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"Wrote {out_dir / 'component_network_run.html'}")
    print(f"Wrote {out_dir / js_name}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--preset",
        choices=("lab-snapshot", "mcp-json"),
        default="lab-snapshot",
        help="lab-snapshot: demo_example_snapshot; mcp-json: usage+fuw bundle from CJA MCP export",
    )
    p.add_argument("--max-nodes", type=int, default=85, help="Hard cap on nodes (digestibility)")
    p.add_argument(
        "--run-label",
        default="L611 lab (snapshot-backed run)",
        help="Display label for data view line / title (lab-snapshot default; mcp-json overrides with bundle unless set)",
    )
    p.add_argument(
        "--input",
        type=Path,
        help="For mcp-json: path to bundle JSON (default: outputs/mcp_run_bundle.json under skill root; gitignored)",
    )
    p.add_argument(
        "--display-names",
        type=Path,
        default=None,
        help="Optional JSON map id->title; merged last over bundle and outputs/display_names.json",
    )
    p.add_argument(
        "--skip-display-names",
        action="store_true",
        help="Do not auto-load outputs/display_names.json (still use bundle.displayNames if set)",
    )
    args = p.parse_args()
    if args.preset == "lab-snapshot":
        run_lab_snapshot(max_nodes=args.max_nodes, run_label=args.run_label)
    elif args.preset == "mcp-json":
        out_dir = ROOT / "outputs"
        bundle = args.input or (out_dir / "mcp_run_bundle.json")
        if not bundle.is_file():
            raise SystemExit(
                f"Bundle not found: {bundle}\n"
                "Save listComponentUsage + listFrequentlyUsedWith results as JSON there, "
                "or pass --input path/to/bundle.json (keep run-specific files out of scripts/)."
            )
        label = None if args.run_label == "L611 lab (snapshot-backed run)" else args.run_label
        run_mcp_json(
            bundle_path=bundle,
            max_nodes=args.max_nodes,
            run_label=label,
            display_names_path=args.display_names,
            skip_default_display_names=args.skip_display_names,
        )


if __name__ == "__main__":
    main()

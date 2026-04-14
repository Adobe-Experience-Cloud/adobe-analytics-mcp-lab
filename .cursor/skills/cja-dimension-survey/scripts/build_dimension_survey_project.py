"""
Build a CJA Workspace project body (JSON) for the cja-dimension-survey skill.

Reads a survey config JSON (see example_survey_config.json). Writes UTF-8 JSON
to --out or stdout. Not tied to any data view; all ids and copy come from config.

Grid cells use **[`subPanel_snippet_trimmed.json`](subPanel_snippet_trimmed.json)** next to this script:
placeholders ``<<<KEY>>>`` are replaced per cell (``X``, ``Y``, ``VISUALIZATION_INDEX`` must be
numeric). Optional ``--cell-template`` may point at another JSON file with the **same** placeholder
pattern (forked snippet); do not use a different freeform shape.
Grid geometry: row height 325px, 3×3 slot map; summary table uses All_Visits (configurable).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROW_HEIGHT = 325

SLOTS = [
    (0, 0, 0, "#E8871A"),
    (1, 33.33, 0, "#5144D3"),
    (2, 66.66, 0, "#47E26F"),
    (3, 0, ROW_HEIGHT, "#DA3490"),
    (4, 33.33, ROW_HEIGHT, "#2780EB"),
    (5, 66.66, ROW_HEIGHT, "#DFBF03"),
    (6, 0, 2 * ROW_HEIGHT, "#00C0C7"),
    (7, 33.33, 2 * ROW_HEIGHT, "#9089FA"),
    (8, 66.66, 2 * ROW_HEIGHT, "#6F38B1"),
]


def new_id() -> str:
    return str(uuid.uuid4()).upper()


def quill_delta_for_dimension_id(dim_id: str) -> str:
    """Skill: strip variables/, token collapse, Y/Z split, Quill ops — return JSON string."""
    s = dim_id
    if s.startswith("variables/"):
        s = s[len("variables/") :]
    m = re.match(r"^([A-Za-z0-9]{24})\.(.*)$", s)
    if m:
        tok, rest = m.group(1), m.group(2)
        s = "..." + tok[-4:] + "." + rest
    li = s.rfind(".")
    if li == -1:
        y, z = s, ""
    else:
        y, z = s[: li + 1], s[li + 1 :]
    delta = {
        "ops": [
            {"insert": y + "\n"},
            {"attributes": {"italic": True}, "insert": z},
            {"insert": "\n"},
        ]
    }
    return json.dumps(delta, separators=(",", ":"))


def quill_plain(text: str) -> str:
    return json.dumps({"ops": [{"insert": text}]}, separators=(",", ":"))


_SKILL_DIR = Path(__file__).resolve().parent.parent
_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_SNIPPET_PATH = _SCRIPT_DIR / "subPanel_snippet_trimmed.json"
_template_base_cache: dict[str, dict[str, Any]] = {}


def _template_base(path: Path) -> dict[str, Any]:
    key = str(path.resolve())
    if key not in _template_base_cache:
        _template_base_cache[key] = json.loads(path.read_text(encoding="utf-8"))
    return _template_base_cache[key]


def _clone_cell_template(path: Path) -> dict[str, Any]:
    return copy.deepcopy(_template_base(path))


def _apply_angle_placeholders(obj: Any, repl: dict[str, Any]) -> None:
    """Replace string values that are exactly <<<KEY>>> (entire string)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("<<<") and v.endswith(">>>") and len(v) > 6:
                inner = v[3:-3]
                if inner in repl:
                    obj[k] = repl[inner]
                else:
                    raise ValueError(f"Unknown placeholder {v!r} in cell template {k!r}")
            else:
                _apply_angle_placeholders(v, repl)
    elif isinstance(obj, list):
        for item in obj:
            _apply_angle_placeholders(item, repl)


def _normalize_snippet_grid_cell(cell: dict[str, Any], swatch: str) -> None:
    """Fill fields the trimmed snippet omits but Workspace often expects."""
    cell.setdefault("linkedSourceId", "")
    cell.setdefault("isQuickInsightsSubPanel", False)
    cell["swatchColor"] = swatch
    rr = cell["reportlet"]
    rr.setdefault("type", "FreeformReportlet")
    rr.setdefault(
        "intelligentCaptions",
        {"captions": [], "hasLoaded": False, "hiddenCaptions": [], "isExpanded": False},
    )
    ct = rr["columnTree"]
    ct.setdefault("_computedValues", [])
    ct.setdefault("name", "")
    for node in ct.get("nodes", []):
        node.setdefault("_computedValues", [])
        node.setdefault("selectionCoordinates", [])
        node.setdefault("nodes", [])
        node.setdefault(
            "dataSettings",
            {
                "advancedItemLimit": 5,
                "advancedItemSearch": {"alwaysExcludedItems": [], "operator": "AND", "rules": []},
            },
        )
    ft = rr["freeformTable"]
    ft.setdefault("alignDatesForTimeDimension", True)
    ft.setdefault("breakdowns", [])
    ft.setdefault("hyperlinks", [])
    ft.setdefault("parentItemIds", [])
    ft.setdefault("selectionCoordinates", [])
    ft.setdefault("staticRows", [])
    ft.setdefault("staticSearch", {"alwaysExcludedItems": [], "operator": "AND", "rules": []})
    ft.setdefault("statistics", {"functions": [], "ignoreZeros": True})
    ft["sort"].setdefault("advancedSortRules", [])
    for ds in ft.get("dimensionSettings", []):
        ds.setdefault("search", {"alwaysExcludedItems": [], "operator": "AND", "rules": []})


def freeform_cell(
    dim_id: str,
    friendly: str,
    slot: int,
    cell_template_path: Path,
) -> dict[str, Any]:
    """Build one grid cell from ``subPanel_snippet_trimmed.json`` (or same-shape ``--cell-template``)."""
    _slot, x, y, swatch = SLOTS[slot]
    cell = _clone_cell_template(cell_template_path)
    sp_id = new_id()
    ct_root = new_id()
    col_events = new_id()
    dim_set = new_id()
    ph: dict[str, Any] = {
        "SUBPANEL_DESCRIPTION_QUILL": quill_delta_for_dimension_id(dim_id),
        "SUBPANEL_GUID": sp_id,
        "SUBPANEL_NAME": friendly,
        "X": float(x),
        "Y": float(y),
        "COLUMN_GUID": ct_root,
        "METRIC_COLUMN_GUID": col_events,
        "DIMENSION_COMPONENT_ID": dim_id,
        "DIMENSION_COMPONENT_NAME": "",
        "DIMENSION_GUID": dim_set,
        "VISUALIZATION_INDEX": int(slot),
    }
    _apply_angle_placeholders(cell, ph)
    _normalize_snippet_grid_cell(cell, swatch)
    cell["position"]["autoHeight"] = ROW_HEIGHT
    cell["position"]["fixedHeight"] = ROW_HEIGHT
    return cell


def text_subpanel(title: str, quill_json_str: str, y: int, viz: int) -> dict:
    sp_id = new_id()
    return {
        "id": sp_id,
        "name": title,
        "type": "genericSubPanel",
        "linkedSourceId": "",
        "collapsed": False,
        "description": "",
        "isQuickInsightsSubPanel": False,
        "position": {"x": 0, "y": y, "width": 100, "autoSize": True, "autoHeight": 120},
        "visible": True,
        "visualizationIndex": viz,
        "reportlet": {
            "type": "TextReportlet",
            "name": title,
            "textContent": quill_json_str,
            "hideTitle": False,
            "showAnnotations": True,
            "showControls": True,
        },
    }


def metrics_static_table(
    metric_rows: list[tuple[str, str]],
    segment_id: str,
    segment_display_name: str,
    y: int,
    viz: int,
) -> dict:
    """metric_rows: (metric_id, display_name) sorted by id."""
    sp_id = new_id()
    col_id = new_id()
    static_rows = []
    for mid, mname in metric_rows:
        static_rows.append(
            {
                "id": new_id(),
                "dataSettings": {
                    "advancedItemLimit": 5,
                    "advancedItemSearch": {"alwaysExcludedItems": [], "operator": "AND", "rules": []},
                },
                "component": {
                    "id": mid,
                    "__entity__": True,
                    "type": "Metric",
                    "__metaData__": {"name": mname},
                },
            }
        )
    return {
        "id": sp_id,
        "name": "Non-zero metrics (All Data)",
        "type": "genericSubPanel",
        "linkedSourceId": "",
        "collapsed": False,
        "description": "",
        "isQuickInsightsSubPanel": False,
        "position": {"x": 0, "y": y, "width": 100, "autoSize": True, "autoHeight": 360},
        "visible": True,
        "visualizationIndex": viz,
        "reportlet": {
            "type": "FreeformReportlet",
            "name": "Non-zero metrics",
            "hideTitle": False,
            "showAnnotations": True,
            "showControls": True,
            "isConfigVisible": True,
            "isReadOnly": False,
            "columnTree": {
                "id": new_id(),
                "_computedValues": [],
                "visible": True,
                "name": "",
                "nodes": [
                    {
                        "id": col_id,
                        "_computedValues": [],
                        "visible": True,
                        "component": {
                            "id": segment_id,
                            "__entity__": True,
                            "type": "Segment",
                            "__metaData__": {"name": segment_display_name},
                        },
                        "name": segment_display_name,
                        "nodes": [],
                    }
                ],
            },
            "freeformTable": {
                "alignDatesForTimeDimension": True,
                "breakdowns": [],
                "collapsed": False,
                "columnWidths": [35, 65],
                "dimensionSettings": [],
                "hyperlinks": [],
                "pagination": {"currentPage": 0, "viewBy": 50},
                "parentItemIds": [],
                "selectionCoordinates": [],
                "settings": {
                    "breakdownByPosition": False,
                    "rowBasedPercentages": False,
                    "showThumbnails": False,
                    "totalsType": "allVisits",
                },
                "sort": {"asc": True, "columnId": "", "labelColumn": True},
                "staticRows": static_rows,
                "staticSearch": {"alwaysExcludedItems": [], "operator": "AND", "rules": []},
                "statistics": {"functions": [], "ignoreZeros": True},
            },
            "intelligentCaptions": {
                "captions": [],
                "hasLoaded": False,
                "hiddenCaptions": [],
                "isExpanded": False,
            },
        },
    }


def _require(d: dict[str, Any], key: str, ctx: str) -> Any:
    if key not in d:
        raise ValueError(f"{ctx}: missing required key {key!r}")
    return d[key]


def load_and_validate(raw: dict[str, Any]) -> dict[str, Any]:
    data_view_id = str(_require(raw, "dataViewId", "root"))
    data_view_name = str(_require(raw, "dataViewName", "root"))
    counts = _require(raw, "counts", "root")
    n = int(_require(counts, "n", "counts"))
    m = int(_require(counts, "m", "counts"))
    grid = _require(raw, "gridDimensions", "root")
    if not isinstance(grid, list) or not grid:
        raise ValueError("gridDimensions must be a non-empty array")
    if len(grid) > 9:
        raise ValueError("gridDimensions: at most 9 rows for one 3×3 panel (split panels in config if needed)")
    for i, row in enumerate(grid):
        if not isinstance(row, dict):
            raise ValueError(f"gridDimensions[{i}] must be an object")
        _require(row, "id", f"gridDimensions[{i}]")
        _require(row, "friendlyName", f"gridDimensions[{i}]")
    summary = _require(raw, "summary", "root")
    _require(summary, "noDataDimensions", "summary")
    _require(summary, "singleValueNote", "summary")
    _require(summary, "zeroMetrics", "summary")
    _require(summary, "nonZeroMetrics", "summary")
    if not isinstance(summary["nonZeroMetrics"], list) or not summary["nonZeroMetrics"]:
        raise ValueError("summary.nonZeroMetrics must be a non-empty array")
    return raw


def format_no_data_lines(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Dimensions — no usable data (id order)\n(none)\n"
    lines = ["Dimensions — no usable data (id order)"]
    for r in sorted(rows, key=lambda x: str(x["id"])):
        mid = str(r["id"])
        name = str(r.get("friendlyName", "")).strip()
        if name:
            lines.append(f"• {mid} — {name}")
        else:
            lines.append(f"• {mid}")
    return "\n".join(lines) + "\n"


def format_zero_metrics_lines(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Metrics — zero under All Data (id order)\n(none)\n"
    lines = ["Metrics — zero under All Data (id order)"]
    for r in sorted(rows, key=lambda x: str(x["id"])):
        lines.append(f"• {r['id']}")
    return "\n".join(lines) + "\n"


def resolve_cell_template_path(p: Path | None) -> Path:
    if p is None:
        return _DEFAULT_SNIPPET_PATH.resolve()
    if p.is_file():
        return p.resolve()
    cand_script = _SCRIPT_DIR / p
    if cand_script.is_file():
        return cand_script.resolve()
    cand_skill = _SKILL_DIR / p
    if cand_skill.is_file():
        return cand_skill.resolve()
    raise FileNotFoundError(f"Cell template not found: {p}")


def build_project_body(cfg: dict[str, Any], cell_template_path: Path) -> dict[str, Any]:
    cfg = load_and_validate(cfg)
    data_view_id = str(cfg["dataViewId"])
    data_view_name = str(cfg["dataViewName"])
    n, m = int(cfg["counts"]["n"]), int(cfg["counts"]["m"])
    project_name = str(
        cfg.get("projectName") or f"Top {n} / {m} components in {data_view_name}"
    )
    project_description = str(
        cfg.get(
            "projectDescription",
            "cja-dimension-survey: usage-ranked slice, Events classification, All_Visits metric pass.",
        )
    )
    date_def = str(cfg.get("dateRangeDefinition", "td-29d/td+1d"))
    definition_version = str(cfg.get("definitionVersion", "96"))
    summary_title = str(cfg.get("summaryPanelTitle", "Summary — lists & non-zero metrics"))
    segment_id = str(cfg.get("allDataSegmentId", "All_Visits"))
    segment_name = str(cfg.get("allDataSegmentDisplayName", "All Data"))

    grid_dims: list[tuple[str, str]] = [
        (str(r["id"]), str(r["friendlyName"])) for r in cfg["gridDimensions"]
    ]
    panel_title = str(cfg.get("dimensionPanelTitle") or f"{grid_dims[0][1]} - {grid_dims[-1][1]}")

    summary = cfg["summary"]
    no_data_lines = format_no_data_lines(summary["noDataDimensions"])
    one_el = "Dimensions — single usable value\n" + str(summary["singleValueNote"]).strip() + "\n"
    zero_m = format_zero_metrics_lines(summary["zeroMetrics"])
    non_zero: list[tuple[str, str]] = [
        (str(r["id"]), str(r["name"])) for r in summary["nonZeroMetrics"]
    ]
    non_zero.sort(key=lambda t: t[0])

    grid_subpanels = [
        freeform_cell(d, f, i, cell_template_path) for i, (d, f) in enumerate(grid_dims)
    ]
    summary_subpanels = [
        text_subpanel("Text — dimensions, no usable data", quill_plain(no_data_lines), 0, 0),
        text_subpanel("Text — dimensions, single value", quill_plain(one_el), 125, 1),
        text_subpanel("Text — metrics with value 0", quill_plain(zero_m), 250, 2),
        metrics_static_table(non_zero, segment_id, segment_name, 380, 3),
    ]

    ws_id = new_id()
    panel_grid_id = new_id()
    panel_summary_id = new_id()

    date_ent = {"__entity__": True, "type": "DateRange", "__metaData__": {"definition": date_def}}
    rs_ent = {
        "__entity__": True,
        "id": data_view_id,
        "type": "ReportSuite",
        "__metaData__": {"name": data_view_name, "rsid": data_view_id},
    }

    def panel(pid: str, name: str, subs: list) -> dict:
        return {
            "id": pid,
            "name": name,
            "type": "panel",
            "collapsed": False,
            "datesAreRelativeToPanel": False,
            "description": "",
            "position": {"autoSize": True, "width": 100, "x": 0, "y": 0},
            "dateRange": date_ent,
            "reportSuite": rs_ent,
            "segmentGroups": [],
            "subPanels": subs,
        }

    definition = {
        "version": definition_version,
        "viewDensity": "compact",
        "currentWorkspaceIndex": 0,
        "workspaces": [
            {
                "id": ws_id,
                "name": "",
                "panels": [
                    panel(panel_grid_id, panel_title, grid_subpanels),
                    panel(panel_summary_id, summary_title, summary_subpanels),
                ],
            }
        ],
    }

    return {
        "type": "project",
        "name": project_name,
        "description": project_description,
        "dataId": data_view_id,
        "definition": definition,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Build dimension-survey project JSON from config.")
    ap.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to survey JSON (see example_survey_config.json next to this script).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write project body JSON here; default is stdout.",
    )
    ap.add_argument("--minify", action="store_true", help="Single-line JSON (smaller, for MCP).")
    ap.add_argument(
        "--cell-template",
        type=Path,
        default=None,
        help=(
            "Grid subpanel JSON using the same <<<PLACEHOLDER>>> pattern as "
            "subPanel_snippet_trimmed.json. Default: scripts/subPanel_snippet_trimmed.json beside this script."
        ),
    )
    args = ap.parse_args()

    raw = json.loads(args.config.read_text(encoding="utf-8"))
    cell_tp = resolve_cell_template_path(args.cell_template)
    body = build_project_body(raw, cell_tp)

    if args.minify:
        text = json.dumps(body, ensure_ascii=False, separators=(",", ":")) + "\n"
    else:
        text = json.dumps(body, ensure_ascii=False, indent=2) + "\n"

    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()

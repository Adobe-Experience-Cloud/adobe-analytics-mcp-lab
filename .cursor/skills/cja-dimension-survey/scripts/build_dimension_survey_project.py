"""Build a dimension-only CJA Workspace survey project body from a survey config.

Read `example_survey_config.json` for the expected config shape. The builder
deep-clones `subPanel_snippet_trimmed.json` by default; `--cell-template` may
point at another JSON file with the same `<<<KEY>>>` placeholder contract.
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


def freeform_cell(dim_id: str, friendly: str, slot: int, cell_template_path: Path) -> dict[str, Any]:
    _slot, x, y, swatch = SLOTS[slot]
    cell = _clone_cell_template(cell_template_path)
    sp_id = new_id()
    ct_root = new_id()
    col_events = new_id()
    dim_set = new_id()
    placeholders: dict[str, Any] = {
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
    _apply_angle_placeholders(cell, placeholders)
    _normalize_snippet_grid_cell(cell, swatch)
    cell["position"]["autoHeight"] = ROW_HEIGHT
    cell["position"]["fixedHeight"] = ROW_HEIGHT
    return cell


def text_subpanel(title: str, quill_json_str: str, auto_height: int = 280) -> dict[str, Any]:
    sp_id = new_id()
    return {
        "id": sp_id,
        "name": title,
        "type": "genericSubPanel",
        "linkedSourceId": "",
        "collapsed": False,
        "description": "",
        "isQuickInsightsSubPanel": False,
        "position": {"x": 0, "y": 0, "width": 100, "autoSize": True, "autoHeight": auto_height},
        "visible": True,
        "visualizationIndex": 0,
        "reportlet": {
            "type": "TextReportlet",
            "name": title,
            "textContent": quill_json_str,
            "hideTitle": False,
            "showAnnotations": True,
            "showControls": True,
        },
    }


def _require(d: dict[str, Any], key: str, ctx: str) -> Any:
    if key not in d:
        raise ValueError(f"{ctx}: missing required key {key!r}")
    return d[key]


def load_and_validate(raw: dict[str, Any]) -> dict[str, Any]:
    _require(raw, "dataViewId", "root")
    _require(raw, "dataViewName", "root")
    counts = _require(raw, "counts", "root")
    _require(counts, "n", "counts")

    grid = _require(raw, "gridDimensions", "root")
    if not isinstance(grid, list) or not grid:
        raise ValueError("gridDimensions must be a non-empty array")
    if len(grid) > 9 * 20:
        raise ValueError("gridDimensions: cap 20 panels x 9 cells")
    for i, row in enumerate(grid):
        if not isinstance(row, dict):
            raise ValueError(f"gridDimensions[{i}] must be an object")
        _require(row, "id", f"gridDimensions[{i}]")
        _require(row, "friendlyName", f"gridDimensions[{i}]")

    summary = _require(raw, "summary", "root")
    no_data = _require(summary, "noDataDimensions", "summary")
    single_value = _require(summary, "singleValueDimensions", "summary")
    if not isinstance(no_data, list):
        raise ValueError("summary.noDataDimensions must be an array")
    if not isinstance(single_value, list):
        raise ValueError("summary.singleValueDimensions must be an array")
    return raw


def format_dimension_lines(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [title]
    if not rows:
        lines.append("(none)")
        return lines
    for row in sorted(rows, key=lambda x: str(x["id"])):
        dim_id = str(row["id"])
        name = str(row.get("friendlyName", "")).strip()
        lines.append(f"- {dim_id}" if not name else f"- {dim_id} - {name}")
    return lines


def summary_text(no_data_rows: list[dict[str, Any]], single_value_rows: list[dict[str, Any]]) -> str:
    lines = ["Reviewed dimensions summary", ""]
    lines.extend(format_dimension_lines("No usable data", no_data_rows))
    lines.append("")
    lines.extend(format_dimension_lines("Single usable value", single_value_rows))
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
    n = int(cfg["counts"]["n"])
    project_name = str(cfg.get("projectName") or f"Dimension survey - top {n} in {data_view_name}")
    project_description = str(
        cfg.get(
            "projectDescription",
            "cja-dimension-survey: dimensions only, Events classification, summary of reviewed dimensions.",
        )
    )
    date_def = str(cfg.get("dateRangeDefinition", "td-29d/td+1d"))
    definition_version = str(cfg.get("definitionVersion", "96"))
    summary_title = str(cfg.get("summaryPanelTitle", "Summary - reviewed dimensions"))

    grid_dims: list[tuple[str, str]] = [
        (str(r["id"]), str(r["friendlyName"])) for r in cfg["gridDimensions"]
    ]
    dimension_panel_title_override = cfg.get("dimensionPanelTitle")

    summary_cfg = cfg["summary"]
    summary_subpanels = [
        text_subpanel(
            "Reviewed dimensions",
            quill_plain(
                summary_text(
                    summary_cfg["noDataDimensions"],
                    summary_cfg["singleValueDimensions"],
                )
            ),
        )
    ]

    def grid_chunks(dims: list[tuple[str, str]], size: int = 9) -> list[list[tuple[str, str]]]:
        return [dims[i : i + size] for i in range(0, len(dims), size)]

    grid_panels: list[tuple[str, str, list[dict[str, Any]]]] = []
    chunks = grid_chunks(grid_dims, 9)
    for ci, chunk in enumerate(chunks):
        subs = [freeform_cell(dim_id, friendly, i, cell_template_path) for i, (dim_id, friendly) in enumerate(chunk)]
        if dimension_panel_title_override and len(chunks) == 1:
            title = str(dimension_panel_title_override)
        elif dimension_panel_title_override and len(chunks) > 1:
            title = f"{dimension_panel_title_override} (part {ci + 1}/{len(chunks)})"
        else:
            title = f"{chunk[0][1]} - {chunk[-1][1]}"
        grid_panels.append((new_id(), title, subs))

    date_ent = {"__entity__": True, "type": "DateRange", "__metaData__": {"definition": date_def}}
    rs_ent = {
        "__entity__": True,
        "id": data_view_id,
        "type": "ReportSuite",
        "__metaData__": {"name": data_view_name, "rsid": data_view_id},
    }

    def panel(pid: str, name: str, subs: list[dict[str, Any]]) -> dict[str, Any]:
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

    workspace_panels = [panel(pid, name, subs) for pid, name, subs in grid_panels]
    workspace_panels.append(panel(new_id(), summary_title, summary_subpanels))

    definition = {
        "version": definition_version,
        "currentWorkspaceIndex": 0,
        "workspaces": [
            {
                "id": new_id(),
                "name": "",
                "panels": workspace_panels,
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
    parser = argparse.ArgumentParser(description="Build dimension-survey project JSON from config.")
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to survey JSON (see example_survey_config.json next to this script).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write project body JSON here; default is stdout.",
    )
    parser.add_argument("--minify", action="store_true", help="Single-line JSON for MCP.")
    parser.add_argument(
        "--cell-template",
        type=Path,
        default=None,
        help=(
            "Grid subpanel JSON using the same <<<PLACEHOLDER>>> pattern as "
            "subPanel_snippet_trimmed.json. Default: scripts/subPanel_snippet_trimmed.json beside this script."
        ),
    )
    args = parser.parse_args()

    raw = json.loads(args.config.read_text(encoding="utf-8"))
    cell_template = resolve_cell_template_path(args.cell_template)
    body = build_project_body(raw, cell_template)

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

"""
Shared helpers for CJA **component network** builds — **any** data view.

This module lives under ``scripts/``; the skill root is the parent directory.
Selection math, default exclusions, proxy edges, and node shaping are data-view
agnostic. **Do not** embed a specific ``dataViewId`` or usage data here.
"""
from __future__ import annotations

import math
import sys
import re
from pathlib import Path
from statistics import mean, pstdev

DIR = Path(__file__).resolve().parent

EXCLUDE = [
    r"^metrics/visits$",
    r"^metrics/visitors$",
    r"^metrics/occurrences$",
    r"^metrics/bounces$",
    r"^metrics/timespent",
    r"^metrics/event",
    r"^variables/daterange",
    r"^variables/day$",
    r"^variables/week$",
    r"^variables/month$",
    r"^variables/quarter$",
    r"^variables/year$",
    r"^variables/hour$",
    r"^variables/minute$",
    r"^variables/adobe_personid$",
    r"^variables/personid",
    r"^variables/timestamp",
]


def should_exclude(cid: str) -> bool:
    return any(re.match(p, cid) for p in EXCLUDE)


def select_above_mean(rows: list[tuple[str, str, int]]) -> list[str]:
    out: list[str] = []
    for typ in ("dimension", "metric", "calculatedMetric", "segment"):
        xs = [u for c, t, u in rows if t == typ]
        if not xs:
            continue
        m = mean(xs)
        out.extend(c for c, t, u in rows if t == typ and u > m)
    return out


def select_1sd(rows: list[tuple[str, str, int]]) -> list[str]:
    out: list[str] = []
    for typ in ("dimension", "metric", "calculatedMetric", "segment"):
        xs = [u for c, t, u in rows if t == typ]
        if len(xs) < 2:
            out.extend(c for c, t, u in rows if t == typ)
            continue
        m = mean(xs)
        sd = pstdev(xs)
        th = m + sd
        out.extend(c for c, t, u in rows if t == typ and u > th)
    return out


def usage_map(rows: list[tuple[str, str, int]]) -> dict[str, int]:
    return {c: u for c, t, u in rows}


def proxy_edges(selected: list[str], usage: dict[str, int], k: int = 4) -> list[dict]:
    """Undirected unique edges when co-usage is unavailable; sqrt(usage_i*usage_j), top-k."""
    sel = list(selected)
    best: dict[tuple[str, str], int] = {}

    for i in sel:
        ui = usage.get(i, 1)
        scored = []
        for j in sel:
            if j == i:
                continue
            uj = usage.get(j, 1)
            scored.append((int(math.sqrt(ui * uj)), j))
        scored.sort(key=lambda x: -x[0])
        for score, j in scored[:k]:
            a, b = sorted((i, j))
            key = (a, b)
            best[key] = max(best.get(key, 0), score)

    return [{"source": a, "target": b, "count": cnt} for (a, b), cnt in sorted(best.items())]


def build_nodes(
    selected: list[str],
    usage: dict[str, int],
    rows: list[tuple[str, str, int]],
    display_names: dict[str, str] | None = None,
) -> tuple[list[dict], dict[str, str]]:
    names = display_names or {}
    type_by_id = {c: t for c, t, _ in rows}
    nodes = []
    id_map: dict[str, str] = {}
    for idx, full in enumerate(selected, start=1):
        sid = f"n{idx}"
        id_map[full] = sid
        nodes.append(
            {
                "id": sid,
                "fullId": full,
                "name": names.get(full, full),
                "type": type_by_id.get(full, "other"),
                "usage": usage.get(full, 1),
            }
        )
    return nodes, id_map


def count_types(selected: list[str], rows: list[tuple[str, str, int]]) -> dict[str, int]:
    tmap = {c: t for c, t, _ in rows}
    out = {"dimension": 0, "metric": 0, "calculatedMetric": 0, "segment": 0}
    for c in selected:
        typ = tmap.get(c)
        if typ in out:
            out[typ] += 1
    return out


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    print(
        "component_network_lib is a library module.\n"
        f"From the skill root ({root}), run:\n"
        "  python scripts/build_network_to_outputs.py\n"
        "  python scripts/build_network_to_outputs.py --max-nodes 30 --input outputs/mcp_run_bundle.json\n",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()

"""
Helpers for mapping CJA component ids to human-facing titles.

MCP describe* responses use a top-level ``name`` for dimensions and metrics.
Calculated metrics and segments also expose ``name``; segments may include
``dataName`` when requested via expansions — callers can prefer ``name`` first.

This module does **not** call MCP; agents or offline tooling build a
``dict[full_component_id, title]`` and save it under ``outputs/`` (gitignored)
or embed ``displayNames`` on a run bundle.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def dimension_id_for_describe(full_id: str) -> str:
    if full_id.startswith("variables/"):
        return full_id[len("variables/") :]
    return full_id


def metric_id_for_describe(full_id: str) -> str:
    if full_id.startswith("metrics/"):
        return full_id[len("metrics/") :]
    return full_id


def title_from_describe_payload(payload: Any, *, fallback_id: str) -> str:
    """Pick a display string from a describe* JSON object (dict or error wrapper)."""
    if not isinstance(payload, dict):
        return fallback_id
    if "error" in payload or "message" in payload and "name" not in payload:
        return fallback_id
    name = payload.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return fallback_id


def parse_display_names_json(raw: dict[str, Any]) -> dict[str, str]:
    """
    Accept either a flat map of id -> title, or ``{"displayNames": {...}}``.
    Non-string values are skipped.
    """
    if "displayNames" in raw and isinstance(raw["displayNames"], dict):
        src = raw["displayNames"]
    else:
        src = raw
    out: dict[str, str] = {}
    for k, v in src.items():
        if isinstance(k, str) and isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out


def overlay_from_bundle(raw: dict[str, Any]) -> dict[str, str]:
    """Only the optional ``displayNames`` object on a run bundle (not other bundle keys)."""
    dn = raw.get("displayNames")
    if not isinstance(dn, dict):
        return {}
    return {str(k): str(v) for k, v in dn.items() if isinstance(v, str) and v.strip()}


def load_display_names_file(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return parse_display_names_json(data)


def merge_display_names(*maps: dict[str, str]) -> dict[str, str]:
    """Later maps override earlier keys."""
    out: dict[str, str] = {}
    for m in maps:
        out.update(m)
    return out

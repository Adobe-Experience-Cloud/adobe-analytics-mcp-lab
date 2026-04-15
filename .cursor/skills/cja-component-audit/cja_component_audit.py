#!/usr/bin/env python3
"""
CJA Component Audit Script v1.0
=================================

Analyzes CJA component inventory data collected by the cja-component-audit skill.
Performs multi-type usage classification, duplicate/near-duplicate detection for segments
and calculated metrics, cross-type dependency mapping, ownership analysis, and health scoring.
Generates both JSON results and comprehensive reports (markdown or HTML).

This script is called by the cja-component-audit skill after data collection phases.

Usage:
    python3 cja_component_audit.py <inventory_dir> <data_view_name> <data_view_id> \
        [output_dir] [--format=markdown|html] [--keep-audits=N]

Arguments:
    inventory_dir    - Directory containing inventory JSON files collected by SKILL.md workflow
                       Expected files: segments_inventory.json, calcmetrics_inventory.json,
                       usage_segment.json, usage_calculatedMetric.json
                       Optional: dimensions_inventory.json, metrics_inventory.json
    data_view_name   - Name of the data view being audited
    data_view_id     - ID of the data view being audited
    output_dir       - (Optional) Directory for output files (default: inventory_dir)
    --format=FORMAT  - (Optional) Output format: 'markdown' or 'html' (default: html)
    --keep-audits=N  - (Optional) Keep N recent audits, delete older ones (default: 5, 0=keep all)

Output Files:
    - component_audit_results_YYYY-MM-DD_HH-MM.json: Raw audit data
    - COMPONENT_AUDIT_REPORT_YYYY-MM-DD_HH-MM.md or .html: Comprehensive report

Expected inventory JSON structures:
  segments_inventory.json: array of segment objects from findSegments with expansions
  calcmetrics_inventory.json: array of calc metric objects from findCalculatedMetrics
  usage_segment.json: listComponentUsage results for segments
  usage_calculatedMetric.json: listComponentUsage results for calculated metrics

Version: 1.0.0
Last Updated: March 13, 2026
"""

import json
import sys
import os
import re
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Date parsing helpers
# ---------------------------------------------------------------------------

def parse_iso(dt_str: str | None):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


NOW = datetime.now(timezone.utc)
THRESHOLD_90 = NOW - timedelta(days=90)
THRESHOLD_365 = NOW - timedelta(days=365)


# ---------------------------------------------------------------------------
# Usage classification
# ---------------------------------------------------------------------------

def classify_usage(component: dict, usage_ids: set, component_type: str) -> str:
    """Classify component into Active / Stale / Unused."""
    comp_id = component.get("id", "")

    # Check usage summary counts
    usage_summary = component.get("usageSummary", {})
    usage_count = (
        usage_summary.get("usedInProjects", 0)
        + usage_summary.get("usedInSegments", 0)
        + usage_summary.get("usedInCalculatedMetrics", 0)
        + usage_summary.get("usedInAlerting", 0)
        + usage_summary.get("usedInScheduledProjects", 0)
    )

    # Recent access
    recent_access = parse_iso(component.get("recentRecordedAccess"))

    if comp_id in usage_ids or (recent_access and recent_access > THRESHOLD_90) or usage_count > 0:
        return "Active"
    elif recent_access and recent_access > THRESHOLD_365:
        return "Stale"
    else:
        return "Unused"


# ---------------------------------------------------------------------------
# Duplicate detection (name-based — simple tier for multi-type audit)
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation and extra whitespace for name comparison."""
    return re.sub(r"[\W_]+", " ", name.lower()).strip()


def find_name_duplicates(components: list[dict]) -> list[dict]:
    """Find components with near-identical names after normalization."""
    by_norm = defaultdict(list)
    for c in components:
        norm = normalize_name(c.get("name", ""))
        by_norm[norm].append(c)

    groups = []
    for norm, group in by_norm.items():
        if len(group) > 1:
            groups.append({
                "normalizedName": norm,
                "components": [{"id": c.get("id"), "name": c.get("name"), "owner": c.get("ownerFullName")} for c in group],
                "count": len(group),
            })
    return groups


# ---------------------------------------------------------------------------
# Calculated metric definition comparison (structural)
# ---------------------------------------------------------------------------

def extract_calcmetric_signature(definition: dict | None) -> str | None:
    """Extract a structural signature from a calculated metric definition."""
    if not definition:
        return None
    # Serialize key structural elements: formula type, referenced components
    formula = definition.get("formula", {})
    if not formula:
        return None
    return json.dumps(formula, sort_keys=True)


def find_calcmetric_duplicates(calc_metrics: list[dict]) -> list[dict]:
    """Find calculated metrics with identical formula structures."""
    by_sig = defaultdict(list)
    for cm in calc_metrics:
        definition = cm.get("definition")
        sig = extract_calcmetric_signature(definition)
        if sig:
            by_sig[sig].append(cm)

    groups = []
    for sig, group in by_sig.items():
        if len(group) > 1:
            groups.append({
                "type": "exact_formula_duplicate",
                "components": [{"id": c.get("id"), "name": c.get("name"), "owner": c.get("ownerFullName")} for c in group],
                "count": len(group),
            })
    return groups


# ---------------------------------------------------------------------------
# Ownership analysis
# ---------------------------------------------------------------------------

def analyze_ownership(all_components: list[dict]) -> dict:
    """Aggregate ownership stats across all component types."""
    owner_counts = defaultdict(int)
    owner_unused = defaultdict(int)
    no_owner = []

    for c in all_components:
        owner = c.get("ownerFullName") or "Unknown"
        status = c.get("_usage_status", "Unknown")
        if owner == "Unknown":
            no_owner.append({"id": c.get("id"), "name": c.get("name"), "type": c.get("_component_type")})
        owner_counts[owner] += 1
        if status == "Unused":
            owner_unused[owner] += 1

    top_owners = sorted(owner_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    most_unused_owners = sorted(owner_unused.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "totalOwners": len(owner_counts),
        "noOwnerCount": len(no_owner),
        "topOwners": [{"owner": k, "count": v, "unusedCount": owner_unused.get(k, 0)} for k, v in top_owners],
        "mostUnusedOwners": [{"owner": k, "unusedCount": v} for k, v in most_unused_owners],
    }


# ---------------------------------------------------------------------------
# Health scoring
# ---------------------------------------------------------------------------

def compute_health_score(total: int, active: int, duplicate_count: int, unused_pct: float) -> int:
    """Compute a 0-100 health score for a component type."""
    if total == 0:
        return 100
    active_ratio = active / total
    score = active_ratio * 50  # Up to 50 points for active ratio
    score += max(0, 30 - duplicate_count * 3)  # Up to 30 points for low duplicates
    score += max(0, 20 * (1 - unused_pct / 100))  # Up to 20 points for low unused
    return min(100, max(0, round(score)))


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def generate_recommendations(type_stats: dict, name_dup_groups: list, calc_dup_groups: list) -> list[dict]:
    recs = []

    for ctype, stats in type_stats.items():
        unused = stats.get("unused", [])
        unused_nodeps = [c for c in unused if (
            c.get("usageSummary", {}).get("usedInProjects", 0) == 0 and
            c.get("usageSummary", {}).get("usedInSegments", 0) == 0 and
            c.get("usageSummary", {}).get("usedInCalculatedMetrics", 0) == 0
        )]
        if unused_nodeps:
            recs.append({
                "action": "Delete",
                "icon": "🗑️",
                "componentType": ctype,
                "impact": "High",
                "effort": "Quick",
                "count": len(unused_nodeps),
                "description": (
                    f"{len(unused_nodeps)} unused {ctype}(s) with zero dependencies. "
                    f"Safe to delete — no projects or other components reference them."
                ),
                "components": [{"id": c.get("id"), "name": c.get("name"), "owner": c.get("ownerFullName")} for c in unused_nodeps[:10]],
            })

        stale = stats.get("stale", [])
        if stale:
            recs.append({
                "action": "Archive Review",
                "icon": "📦",
                "componentType": ctype,
                "impact": "Medium",
                "effort": "Moderate",
                "count": len(stale),
                "description": (
                    f"{len(stale)} stale {ctype}(s) (last accessed 90–365 days ago). "
                    f"Review with owners to confirm whether still needed."
                ),
                "components": [{"id": c.get("id"), "name": c.get("name"), "owner": c.get("ownerFullName")} for c in stale[:10]],
            })

    # Calculated metric duplicate formulas
    if calc_dup_groups:
        total_dup = sum(g.get("count", 0) for g in calc_dup_groups)
        recs.append({
            "action": "Merge",
            "icon": "🔗",
            "componentType": "calculatedMetric",
            "impact": "High",
            "effort": "Moderate",
            "count": len(calc_dup_groups),
            "description": (
                f"{len(calc_dup_groups)} duplicate formula group(s) found across calculated metrics "
                f"({total_dup} metrics total). Merge each group — keep the most-used, best-named one."
            ),
            "components": [item for g in calc_dup_groups[:5] for item in g.get("components", [])[:2]],
        })

    # Name-based duplicates (all types)
    if name_dup_groups:
        recs.append({
            "action": "Rename",
            "icon": "✏️",
            "componentType": "all",
            "impact": "Medium",
            "effort": "Quick",
            "count": len(name_dup_groups),
            "description": (
                f"{len(name_dup_groups)} near-identical name group(s) found across component types. "
                f"Review to confirm whether these are true duplicates or related variants."
            ),
            "components": [item for g in name_dup_groups[:5] for item in g.get("components", [])[:2]],
        })

    # Untagged components
    for ctype, stats in type_stats.items():
        all_comps = stats.get("all", [])
        untagged = [c for c in all_comps if not c.get("tags")]
        if len(untagged) > len(all_comps) * 0.5 and len(untagged) > 10:
            recs.append({
                "action": "Tag",
                "icon": "🏷️",
                "componentType": ctype,
                "impact": "Low",
                "effort": "Moderate",
                "count": len(untagged),
                "description": (
                    f"{len(untagged)} {ctype}(s) have no tags ({len(untagged)/len(all_comps)*100:.0f}% untagged). "
                    f"Adding tags improves discoverability and governance."
                ),
                "components": [],
            })

    # Sort by impact priority: High > Medium > Low, then effort: Quick > Moderate
    impact_order = {"High": 0, "Medium": 1, "Low": 2}
    effort_order = {"Quick": 0, "Moderate": 1}
    recs.sort(key=lambda r: (impact_order.get(r["impact"], 9), effort_order.get(r["effort"], 9)))
    return recs


# ---------------------------------------------------------------------------
# Main audit pipeline
# ---------------------------------------------------------------------------

def run_audit(inventory_dir: Path, data_view_name: str, data_view_id: str) -> dict:
    """Load inventory files and run the full multi-type audit."""

    def load_json(filename: str, required: bool = False) -> list:
        path = inventory_dir / filename
        if not path.exists():
            if required:
                print(f"  ⚠️  Required file not found: {filename}")
            return []
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("content", data.get("items", []))

    print("📂 Loading inventory files...")
    segments = load_json("segments_inventory.json", required=True)
    calc_metrics = load_json("calcmetrics_inventory.json", required=True)
    dimensions = load_json("dimensions_inventory.json")
    metrics = load_json("metrics_inventory.json")

    usage_seg = load_json("usage_segment.json")
    usage_cm = load_json("usage_calculatedMetric.json")
    usage_dim = load_json("usage_dimension.json")
    usage_met = load_json("usage_metric.json")

    usage_seg_ids = {u.get("componentId") for u in usage_seg if u.get("componentId")}
    usage_cm_ids = {u.get("componentId") for u in usage_cm if u.get("componentId")}
    usage_dim_ids = {u.get("componentId") for u in usage_dim if u.get("componentId")}
    usage_met_ids = {u.get("componentId") for u in usage_met if u.get("componentId")}

    print(f"  Segments:          {len(segments)}")
    print(f"  Calculated Metrics: {len(calc_metrics)}")
    print(f"  Dimensions:        {len(dimensions)}")
    print(f"  Metrics:           {len(metrics)}")

    # Classify each component type
    type_stats = {}
    all_components_flat = []

    for ctype, components, usage_ids in [
        ("segment", segments, usage_seg_ids),
        ("calculatedMetric", calc_metrics, usage_cm_ids),
        ("dimension", dimensions, usage_dim_ids),
        ("metric", metrics, usage_met_ids),
    ]:
        if not components:
            continue
        active, stale, unused = [], [], []
        for c in components:
            status = classify_usage(c, usage_ids, ctype)
            c["_usage_status"] = status
            c["_component_type"] = ctype
            if status == "Active":
                active.append(c)
            elif status == "Stale":
                stale.append(c)
            else:
                unused.append(c)
            all_components_flat.append(c)

        total = len(components)
        health = compute_health_score(
            total, len(active),
            0,  # duplicate count computed separately
            len(unused) / total * 100 if total > 0 else 0,
        )

        type_stats[ctype] = {
            "all": components,
            "active": active,
            "stale": stale,
            "unused": unused,
            "total": total,
            "activeCount": len(active),
            "staleCount": len(stale),
            "unusedCount": len(unused),
            "healthScore": health,
        }
        print(f"  {ctype}: {len(active)} Active, {len(stale)} Stale, {len(unused)} Unused")

    print("\n🔍 Running duplicate detection...")

    # Segment name duplicates
    seg_name_dups = find_name_duplicates(segments)
    cm_name_dups = find_name_duplicates(calc_metrics)
    all_name_dups = find_name_duplicates(all_components_flat)

    # Calculated metric formula duplicates
    calc_formula_dups = find_calcmetric_duplicates(calc_metrics)

    print(f"  Segment name duplicates:    {len(seg_name_dups)} groups")
    print(f"  CalcMetric formula dups:    {len(calc_formula_dups)} groups")
    print(f"  All-type name dups:         {len(all_name_dups)} groups")

    print("\n👥 Analyzing ownership...")
    ownership = analyze_ownership(all_components_flat)

    print("\n💡 Generating recommendations...")
    recommendations = generate_recommendations(type_stats, all_name_dups, calc_formula_dups)

    # Overall health score (weighted average)
    scores = []
    weights = {"segment": 2, "calculatedMetric": 2, "dimension": 1, "metric": 1}
    for ctype, stats in type_stats.items():
        w = weights.get(ctype, 1)
        scores.extend([stats["healthScore"]] * w)
    overall_health = round(sum(scores) / len(scores)) if scores else 100

    # Summary
    total_all = sum(s["total"] for s in type_stats.values())
    total_active = sum(s["activeCount"] for s in type_stats.values())
    total_stale = sum(s["staleCount"] for s in type_stats.values())
    total_unused = sum(s["unusedCount"] for s in type_stats.values())

    summary = {
        "totalComponents": total_all,
        "activeCount": total_active,
        "staleCount": total_stale,
        "unusedCount": total_unused,
        "duplicateGroups": len(calc_formula_dups) + len(all_name_dups),
        "overallHealthScore": overall_health,
        "perTypeHealthScores": {ctype: stats["healthScore"] for ctype, stats in type_stats.items()},
        "recommendationsCount": len(recommendations),
    }

    # Build serializable type stats (strip full component lists to reduce JSON size)
    serializable_type_stats = {}
    for ctype, stats in type_stats.items():
        serializable_type_stats[ctype] = {
            "total": stats["total"],
            "activeCount": stats["activeCount"],
            "staleCount": stats["staleCount"],
            "unusedCount": stats["unusedCount"],
            "healthScore": stats["healthScore"],
            "topActive": [
                {"id": c.get("id"), "name": c.get("name"), "owner": c.get("ownerFullName")}
                for c in stats["active"][:10]
            ],
            "unusedList": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "owner": c.get("ownerFullName"),
                    "modified": c.get("modified"),
                    "recentAccess": c.get("recentRecordedAccess"),
                    "usageSummary": c.get("usageSummary", {}),
                    "tags": c.get("tags", []),
                }
                for c in stats["unused"]
            ],
            "staleList": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "owner": c.get("ownerFullName"),
                    "recentAccess": c.get("recentRecordedAccess"),
                }
                for c in stats["stale"]
            ],
        }

    return {
        "audit_metadata": {
            "data_view_name": data_view_name,
            "data_view_id": data_view_id,
            "generated_at": NOW.isoformat(),
        },
        "summary": summary,
        "type_stats": serializable_type_stats,
        "duplicates": {
            "calcMetricFormula": calc_formula_dups,
            "nameSimilarity": all_name_dups[:50],  # cap for JSON size
        },
        "ownership": ownership,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def generate_markdown(audit: dict, data_view_name: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = audit.get("audit_metadata", {})
    summary = audit.get("summary", {})
    type_stats = audit.get("type_stats", {})
    duplicates = audit.get("duplicates", {})
    ownership = audit.get("ownership", {})
    recommendations = audit.get("recommendations", [])

    health_emoji = "🟢" if summary.get("overallHealthScore", 0) >= 75 else ("🟡" if summary.get("overallHealthScore", 0) >= 50 else "🔴")

    lines = [
        "# CJA Component Audit Report",
        f"**Data View**: {data_view_name}",
        f"**Generated**: {now}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Components | {summary.get('totalComponents', 0):,} |",
        f"| Active | {summary.get('activeCount', 0):,} |",
        f"| Stale | {summary.get('staleCount', 0):,} |",
        f"| Unused | {summary.get('unusedCount', 0):,} |",
        f"| Duplicate Groups | {summary.get('duplicateGroups', 0)} |",
        f"| Overall Health Score | {health_emoji} {summary.get('overallHealthScore', 0)}/100 |",
        "",
        "### Health Scores by Type",
        "",
    ]

    for ctype, health in summary.get("perTypeHealthScores", {}).items():
        emoji = "🟢" if health >= 75 else ("🟡" if health >= 50 else "🔴")
        lines.append(f"- **{ctype}**: {emoji} {health}/100")
    lines.append("")

    # Per-type breakdown
    for ctype, stats in type_stats.items():
        lines += [
            f"---",
            "",
            f"## {ctype.title()} Breakdown",
            "",
            f"| Bucket | Count | % |",
            f"|--------|-------|---|",
            f"| Active | {stats.get('activeCount',0)} | {stats.get('activeCount',0)/max(stats.get('total',1),1)*100:.0f}% |",
            f"| Stale | {stats.get('staleCount',0)} | {stats.get('staleCount',0)/max(stats.get('total',1),1)*100:.0f}% |",
            f"| Unused | {stats.get('unusedCount',0)} | {stats.get('unusedCount',0)/max(stats.get('total',1),1)*100:.0f}% |",
            f"| **Total** | **{stats.get('total',0)}** | 100% |",
            "",
        ]

        unused_list = stats.get("unusedList", [])
        if unused_list:
            lines += [
                f"### Unused {ctype.title()}s ({len(unused_list)})",
                "",
                "| Name | Owner | Last Access | Usage Refs |",
                "|------|-------|-------------|------------|",
            ]
            for c in unused_list[:20]:
                usage = c.get("usageSummary", {})
                refs = (usage.get("usedInProjects", 0) + usage.get("usedInSegments", 0) +
                        usage.get("usedInCalculatedMetrics", 0))
                last_access = c.get("recentAccess", "Never")
                if last_access and last_access != "Never":
                    last_access = last_access[:10]
                lines.append(
                    f"| {c.get('name','N/A')} | {c.get('owner','Unknown')} | {last_access} | {refs} |"
                )
            if len(unused_list) > 20:
                lines.append(f"| *... and {len(unused_list)-20} more* | | | |")
            lines.append("")

    # Duplicates
    calc_dups = duplicates.get("calcMetricFormula", [])
    name_dups = duplicates.get("nameSimilarity", [])

    if calc_dups:
        lines += [
            "---", "",
            "## Calculated Metric Duplicate Formulas",
            "",
            f"Found {len(calc_dups)} group(s) of calculated metrics with identical formula structures.",
            "",
        ]
        for g in calc_dups[:10]:
            lines.append(f"**Group**: {', '.join(c.get('name','N/A') for c in g.get('components',[]))}")
            lines.append(f"  - Owners: {', '.join(set(c.get('owner','Unknown') for c in g.get('components',[])))}")
            lines.append("")

    if name_dups:
        lines += [
            "---", "",
            "## Near-Identical Names",
            "",
            f"Found {len(name_dups)} group(s) of components with near-identical names.",
            "",
        ]
        for g in name_dups[:10]:
            comps = g.get("components", [])
            lines.append(f"**\"{g.get('normalizedName','')}\"**: {', '.join(c.get('name','N/A') for c in comps)}")
        lines.append("")

    # Ownership
    top_owners = ownership.get("topOwners", [])
    if top_owners:
        lines += [
            "---", "",
            "## Ownership Distribution",
            "",
            "| Owner | Total Components | Unused |",
            "|-------|-----------------|--------|",
        ]
        for o in top_owners[:10]:
            lines.append(f"| {o.get('owner','Unknown')} | {o.get('count',0)} | {o.get('unusedCount',0)} |")
        lines.append("")

    # Recommendations
    if recommendations:
        lines += [
            "---", "",
            "## Recommendations",
            "",
            f"*(sorted by impact and effort)*",
            "",
        ]
        for r in recommendations:
            lines += [
                f"### {r['icon']} {r['action']}: {r.get('componentType','').title()} ({r.get('count',0)} components)",
                f"**Impact**: {r.get('impact','N/A')} | **Effort**: {r.get('effort','N/A')}",
                "",
                r.get("description", ""),
                "",
            ]

    lines += [
        "---", "",
        "## Next Steps",
        "",
        "1. Review **Delete** candidates with their owners before removing",
        "2. Run `cja-segment-audit` for deep segment duplicate analysis with 4-tier logical canonicalization",
        "3. Use `cja-component-find-replace` to swap out deprecated components before retirement",
        "4. Schedule follow-up audit in 90 days to measure progress",
        "",
        "---",
        "",
        "*Generated by cja-component-audit skill*",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------------

def generate_html(audit: dict, data_view_name: str, data_view_id: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    summary = audit.get("summary", {})
    type_stats = audit.get("type_stats", {})
    duplicates = audit.get("duplicates", {})
    ownership = audit.get("ownership", {})
    recommendations = audit.get("recommendations", [])

    health_score = summary.get("overallHealthScore", 0)
    health_color = "#22c55e" if health_score >= 75 else ("#eab308" if health_score >= 50 else "#ef4444")

    # Per-type breakdown charts data
    type_names = list(type_stats.keys())
    active_counts = [type_stats[t].get("activeCount", 0) for t in type_names]
    stale_counts = [type_stats[t].get("staleCount", 0) for t in type_names]
    unused_counts = [type_stats[t].get("unusedCount", 0) for t in type_names]

    type_labels_json = json.dumps(type_names)
    active_json = json.dumps(active_counts)
    stale_json = json.dumps(stale_counts)
    unused_json = json.dumps(unused_counts)

    # Type breakdown sections
    type_sections = ""
    for ctype, stats in type_stats.items():
        unused_list = stats.get("unusedList", [])
        stale_list = stats.get("staleList", [])

        unused_rows = "".join(
            f"<tr><td>{c.get('name','N/A')}</td><td>{c.get('owner','Unknown')}</td>"
            f"<td>{(c.get('recentAccess','Never') or 'Never')[:10]}</td></tr>"
            for c in unused_list[:15]
        )

        health = stats.get("healthScore", 0)
        health_c = "#22c55e" if health >= 75 else ("#eab308" if health >= 50 else "#ef4444")

        type_sections += f"""
        <section class="type-section" id="type-{ctype}">
          <h2>{ctype.title()} <span class="health-badge" style="background:{health_c}">{health}/100</span></h2>
          <div class="cards-row">
            <div class="card">
              <div class="card-label">Total</div>
              <div class="card-value">{stats.get('total',0)}</div>
            </div>
            <div class="card">
              <div class="card-label">Active</div>
              <div class="card-value" style="color:#22c55e">{stats.get('activeCount',0)}</div>
            </div>
            <div class="card">
              <div class="card-label">Stale</div>
              <div class="card-value" style="color:#eab308">{stats.get('staleCount',0)}</div>
            </div>
            <div class="card">
              <div class="card-label">Unused</div>
              <div class="card-value" style="color:#ef4444">{stats.get('unusedCount',0)}</div>
            </div>
          </div>
          {f'''<details class="detail-block"><summary>Unused {ctype.title()}s ({len(unused_list)})</summary>
          <table class="data-table">
            <tr><th>Name</th><th>Owner</th><th>Last Access</th></tr>
            {unused_rows}
            {'<tr><td colspan="3"><em>... and ' + str(len(unused_list)-15) + ' more</em></td></tr>' if len(unused_list) > 15 else ''}
          </table></details>''' if unused_list else ''}
        </section>"""

    # Recommendations
    rec_html = ""
    for r in recommendations:
        impact_color = {"High": "#ef4444", "Medium": "#eab308", "Low": "#22c55e"}.get(r.get("impact",""), "#6b7280")
        rec_html += f"""
        <div class="rec-card">
          <div class="rec-header">
            <span class="rec-icon">{r.get('icon','')}</span>
            <strong>{r.get('action','')} — {r.get('componentType','').title()}</strong>
            <span class="impact-badge" style="background:{impact_color}">{r.get('impact','')} impact</span>
            <span class="effort-badge">{r.get('effort','')} effort</span>
          </div>
          <p>{r.get('description','')}</p>
          <div class="rec-count">{r.get('count',0)} component(s)</div>
        </div>"""

    # Top owners table
    top_owners_rows = "".join(
        f"<tr><td>{o.get('owner','Unknown')}</td><td>{o.get('count',0)}</td>"
        f"<td style='color:#ef4444'>{o.get('unusedCount',0)}</td></tr>"
        for o in ownership.get("topOwners", [])[:10]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CJA Component Audit — {data_view_name}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --accent: #4361ee;
      --accent-light: rgba(67,97,238,0.08);
      --bg: #f8f9fa; --card-bg: #ffffff; --border: #e9ecef;
      --text: #1a1a2e; --text-muted: #6c757d;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: var(--bg); color: var(--text); line-height: 1.6; }}
    header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      color: white; padding: 2rem;
    }}
    header h1 {{ font-size: 1.8rem; font-weight: 700; }}
    header p {{ opacity: 0.9; font-size: 0.9rem; margin-top: 0.25rem; }}
    .layout {{ display: flex; min-height: calc(100vh - 120px); }}
    nav {{
      width: 220px; min-width: 220px; background: var(--card-bg);
      border-right: 1px solid var(--border); padding: 1rem;
      position: sticky; top: 0; height: 100vh; overflow-y: auto;
    }}
    nav h3 {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted);
              margin-bottom: 0.5rem; letter-spacing: 0.05em; }}
    nav ul {{ list-style: none; }}
    nav .nav-link {{ display: block; padding: 0.35rem 0.5rem; color: var(--text);
                    text-decoration: none; font-size: 0.85rem; border-radius: 4px; }}
    nav .nav-link:hover {{ background: var(--accent-light); color: var(--accent); }}
    main {{ flex: 1; padding: 2rem; max-width: 1000px; }}
    section {{ margin-bottom: 2.5rem; }}
    h2 {{ font-size: 1.3rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
    .health-badge {{
      font-size: 0.75rem; color: white; padding: 0.2rem 0.6rem;
      border-radius: 999px; font-weight: 600;
    }}
    .summary-cards {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 1rem; margin-bottom: 2rem;
    }}
    .cards-row {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 0.75rem; margin: 1rem 0;
    }}
    .card {{
      background: var(--card-bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 1rem; text-align: center;
    }}
    .card-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;
                   letter-spacing: 0.05em; margin-bottom: 0.25rem; }}
    .card-value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
    .type-section {{
      background: var(--card-bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;
    }}
    .detail-block {{ border: 1px solid var(--border); border-radius: 6px; margin-top: 0.75rem; }}
    .detail-block summary {{
      padding: 0.75rem 1rem; cursor: pointer; font-weight: 600;
      font-size: 0.9rem; background: var(--bg); border-radius: 6px;
    }}
    .detail-block[open] summary {{ border-bottom: 1px solid var(--border); border-radius: 6px 6px 0 0; }}
    .detail-block > *:not(summary) {{ padding: 1rem; }}
    .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    .data-table th {{ background: var(--bg); padding: 0.5rem; text-align: left;
                      border-bottom: 2px solid var(--border); font-weight: 600; }}
    .data-table td {{ padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--border); }}
    .data-table tr:hover td {{ background: var(--accent-light); }}
    .rec-card {{
      background: var(--card-bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;
    }}
    .rec-header {{
      display: flex; align-items: center; gap: 0.5rem;
      margin-bottom: 0.5rem; flex-wrap: wrap;
    }}
    .rec-icon {{ font-size: 1.2rem; }}
    .impact-badge, .effort-badge {{
      font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 999px;
      color: white; font-weight: 600;
    }}
    .effort-badge {{ background: var(--accent); }}
    .rec-count {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }}
    footer {{ text-align: center; padding: 1.5rem; color: var(--text-muted); font-size: 0.8rem;
              border-top: 1px solid var(--border); margin-top: 2rem; }}
    html {{ scroll-behavior: smooth; }}
  </style>
</head>
<body>
  <header>
    <h1>🏥 CJA Component Audit</h1>
    <p>Data View: {data_view_name} &nbsp;|&nbsp; Generated: {now}</p>
  </header>
  <div class="layout">
    <nav>
      <h3>Sections</h3>
      <ul>
        <li><a href="#summary" class="nav-link">Summary</a></li>
        {''.join(f'<li><a href="#type-{t}" class="nav-link">{t.title()}</a></li>' for t in type_stats)}
        <li><a href="#duplicates" class="nav-link">Duplicates</a></li>
        <li><a href="#ownership" class="nav-link">Ownership</a></li>
        <li><a href="#recommendations" class="nav-link">Recommendations</a></li>
      </ul>
    </nav>
  <main>
    <section id="summary">
      <h2>Executive Summary</h2>
      <div class="summary-cards">
        <div class="card">
          <div class="card-label">Health Score</div>
          <div class="card-value" style="color:{health_color}">{health_score}/100</div>
        </div>
        <div class="card">
          <div class="card-label">Total Components</div>
          <div class="card-value">{summary.get('totalComponents',0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Active</div>
          <div class="card-value" style="color:#22c55e">{summary.get('activeCount',0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Stale</div>
          <div class="card-value" style="color:#eab308">{summary.get('staleCount',0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Unused</div>
          <div class="card-value" style="color:#ef4444">{summary.get('unusedCount',0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Recommendations</div>
          <div class="card-value" style="color:var(--accent)">{summary.get('recommendationsCount',0)}</div>
        </div>
      </div>
      <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:1rem;max-width:700px">
        <h3 style="font-size:0.9rem;margin-bottom:0.75rem">Component Breakdown by Type</h3>
        <canvas id="chart-breakdown" height="250"></canvas>
      </div>
      <script>
        new Chart(document.getElementById('chart-breakdown'), {{
          type: 'bar',
          data: {{
            labels: {type_labels_json},
            datasets: [
              {{ label: 'Active', data: {active_json}, backgroundColor: '#22c55e' }},
              {{ label: 'Stale', data: {stale_json}, backgroundColor: '#eab308' }},
              {{ label: 'Unused', data: {unused_json}, backgroundColor: '#ef4444' }},
            ]
          }},
          options: {{
            responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }},
            scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, beginAtZero: true }} }}
          }}
        }});
      </script>
    </section>

    {type_sections}

    <section id="duplicates">
      <h2>Duplicates & Near-Duplicates</h2>
      {'<p style="color:var(--text-muted)">No duplicates detected.</p>' if not duplicates.get('calcMetricFormula') and not duplicates.get('nameSimilarity') else ''}
      {('<details class="detail-block" open><summary>Calculated Metric Formula Duplicates (' + str(len(duplicates.get("calcMetricFormula",[]))) + ' groups)</summary><div>' +
        "".join(
          f'<p><strong>Group:</strong> {", ".join(c.get("name","N/A") for c in g.get("components",[]))}</p>'
          for g in duplicates.get("calcMetricFormula",[])[:10]
        ) + '</div></details>') if duplicates.get('calcMetricFormula') else ''}
      {('<details class="detail-block"><summary>Near-Identical Names (' + str(len(duplicates.get("nameSimilarity",[]))) + ' groups)</summary><div>' +
        "".join(
          f'<p><strong>"{g.get("normalizedName","")}":</strong> {", ".join(c.get("name","N/A") for c in g.get("components",[]))}</p>'
          for g in duplicates.get("nameSimilarity",[])[:20]
        ) + '</div></details>') if duplicates.get('nameSimilarity') else ''}
    </section>

    <section id="ownership">
      <h2>Ownership Distribution</h2>
      <table class="data-table" style="max-width:600px">
        <tr><th>Owner</th><th>Total</th><th>Unused</th></tr>
        {top_owners_rows}
      </table>
    </section>

    <section id="recommendations">
      <h2>Recommendations</h2>
      {rec_html if rec_html else '<p style="color:var(--text-muted)">No recommendations — components look healthy!</p>'}
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:1rem;margin-top:1.5rem">
        <h3 style="font-size:0.9rem;margin-bottom:0.5rem">Next Steps</h3>
        <ol style="margin-left:1.5rem;font-size:0.9rem">
          <li>Review <strong>Delete</strong> candidates with component owners before removing</li>
          <li>Run <code>cja-segment-audit</code> for deep segment duplicate analysis</li>
          <li>Use <code>cja-component-find-replace</code> to migrate from deprecated components</li>
          <li>Schedule follow-up audit in 90 days to measure progress</li>
        </ol>
      </div>
    </section>
  </main>
  </div>
  <footer>Generated by cja-component-audit skill &nbsp;|&nbsp; CJA MCP Lab</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# File management helpers
# ---------------------------------------------------------------------------

def cleanup_old_files(output_dir: Path, prefix: str, keep: int):
    if keep == 0:
        return
    files = sorted(output_dir.glob(f"{prefix}*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
            print(f"  🗑️  Removed old file: {old.name}")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    inventory_dir = Path(sys.argv[1])
    data_view_name = sys.argv[2]
    data_view_id = sys.argv[3]

    output_dir = inventory_dir
    fmt = "html"
    keep_audits = 5

    for arg in sys.argv[4:]:
        if arg.startswith("--format="):
            fmt = arg.split("=", 1)[1].lower()
        elif arg.startswith("--keep-audits="):
            keep_audits = int(arg.split("=", 1)[1])
        elif not arg.startswith("--"):
            output_dir = Path(arg)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🏥 CJA Component Audit")
    print(f"   Data View: {data_view_name}")
    print(f"   Inventory: {inventory_dir}")
    print(f"   Output:    {output_dir} ({fmt})")
    print()

    audit = run_audit(inventory_dir, data_view_name, data_view_id)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")

    json_path = output_dir / f"component_audit_results_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(audit, f, indent=2, default=str)
    print(f"\n✅ Audit JSON saved: {json_path} ({json_path.stat().st_size:,} bytes)")

    print(f"📝 Generating {fmt.upper()} report...")
    if fmt == "markdown":
        report_content = generate_markdown(audit, data_view_name)
        ext = "md"
    else:
        report_content = generate_html(audit, data_view_name, data_view_id)
        ext = "html"

    report_path = output_dir / f"COMPONENT_AUDIT_REPORT_{ts}.{ext}"
    with open(report_path, "w") as f:
        f.write(report_content)
    print(f"✅ Report saved: {report_path} ({report_path.stat().st_size:,} bytes)")

    if keep_audits > 0:
        print(f"\n🧹 Cleaning up old audit files (keeping {keep_audits} most recent)...")
        cleanup_old_files(output_dir, "component_audit_results_", keep_audits)
        cleanup_old_files(output_dir, "COMPONENT_AUDIT_REPORT_", keep_audits)

    summary = audit.get("summary", {})
    print(f"\n{'='*50}")
    print(f"🏥 Audit complete — {data_view_name}")
    print(f"   Total components:    {summary.get('totalComponents',0)}")
    print(f"   Active:              {summary.get('activeCount',0)}")
    print(f"   Stale:               {summary.get('staleCount',0)}")
    print(f"   Unused:              {summary.get('unusedCount',0)}")
    print(f"   Duplicate groups:    {summary.get('duplicateGroups',0)}")
    print(f"   Overall health:      {summary.get('overallHealthScore',0)}/100")
    print(f"   Recommendations:     {summary.get('recommendationsCount',0)}")
    print(f"{'='*50}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

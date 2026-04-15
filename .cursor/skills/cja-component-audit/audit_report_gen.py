#!/usr/bin/env python3
"""
CJA Component Audit — HTML report generator (standalone).
Reads JSON output from cja_component_audit.py and regenerates an interactive HTML dashboard.

Use this when you want to regenerate an HTML report from an existing audit JSON file
without re-running the full audit pipeline.

Usage:
    python3 audit_report_gen.py <audit_results_json> [output_dir]

Arguments:
    audit_results_json  - Path to JSON file from cja_component_audit.py
    output_dir          - (Optional) Output directory (default: same as input file)

Output:
    COMPONENT_AUDIT_REPORT_YYYY-MM-DD_HH-MM.html

Example:
    python3 audit_report_gen.py ./output/component_audit_results_2026-03-13_10-00.json ./output
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from cja_component_audit import generate_html


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    json_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else json_path.parent

    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Loading audit results from {json_path}...")
    with open(json_path) as f:
        audit = json.load(f)

    meta = audit.get("audit_metadata", {})
    data_view_name = meta.get("data_view_name", "Unknown Data View")
    data_view_id = meta.get("data_view_id", "")

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    report_path = output_dir / f"COMPONENT_AUDIT_REPORT_{ts}.html"

    print(f"📝 Generating HTML report...")
    html = generate_html(audit, data_view_name, data_view_id)

    with open(report_path, "w") as f:
        f.write(html)

    print(f"✅ Report saved: {report_path} ({report_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

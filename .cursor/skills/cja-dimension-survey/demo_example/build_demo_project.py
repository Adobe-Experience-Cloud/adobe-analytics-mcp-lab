"""
Regenerate Workspace **projectBody** JSON for the L611 N=M=10 demo survey config.

Writes **UTF-8**:

- ``outputs/projectBody.json`` (pretty) and ``outputs/projectBody.min.json`` (one line)
- ``outputs/upsert_project_args.json`` / ``upsert_project_args.min.json`` — the exact
  **``expansions`` + ``projectBody``** object shape for the **Cursor CJA MCP**
  ``upsertProject`` tool (stdlib ``json`` only; no network, no auth env vars).

The ``outputs/`` folder is gitignored — use it for MCP captures and iteration notes.

Run from the skill root (``cja-dimension-survey``)::

    python demo_example/build_demo_project.py

Or from this folder::

    python build_demo_project.py

See ``README.txt`` and ``../SKILL.md``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Same expansions string the CJA MCP ``upsertProject`` tool expects (see tool schema).
_UPSERT_EXPANSIONS = "dataId,dataName,definition"

ROOT = Path(__file__).resolve().parent.parent
DEMO = Path(__file__).resolve().parent
CONFIG = DEMO / "l611_n10_m10_survey_config.json"
BUILDER = ROOT / "scripts" / "build_dimension_survey_project.py"
OUTPUTS = DEMO / "outputs"


def main() -> None:
    if not CONFIG.is_file():
        raise SystemExit(f"Missing config: {CONFIG}")
    if not BUILDER.is_file():
        raise SystemExit(f"Missing builder: {BUILDER}")
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    base = [
        sys.executable,
        str(BUILDER),
        "--config",
        str(CONFIG),
    ]
    subprocess.run(
        base + ["--out", str(OUTPUTS / "projectBody.json")],
        check=True,
        cwd=str(ROOT),
    )
    subprocess.run(
        base + ["--minify", "--out", str(OUTPUTS / "projectBody.min.json")],
        check=True,
        cwd=str(ROOT),
    )
    print(f"Wrote {OUTPUTS / 'projectBody.json'}")
    print(f"Wrote {OUTPUTS / 'projectBody.min.json'}")

    body = json.loads((OUTPUTS / "projectBody.min.json").read_text(encoding="utf-8"))
    envelope = {"expansions": _UPSERT_EXPANSIONS, "projectBody": body}
    (OUTPUTS / "upsert_project_args.json").write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUTS / "upsert_project_args.min.json").write_text(
        json.dumps(envelope, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUTS / 'upsert_project_args.json'}")
    print(f"Wrote {OUTPUTS / 'upsert_project_args.min.json'}")
    print(
        "Next: in Cursor, call CJA MCP upsertProject using expansions + projectBody "
        "from these files (e.g. ask the agent to upsert after reviewing outputs/)."
    )


if __name__ == "__main__":
    main()

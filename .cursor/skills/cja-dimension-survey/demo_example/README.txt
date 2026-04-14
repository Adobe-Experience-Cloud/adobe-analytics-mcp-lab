L611 demo example — N=M=10 dimension survey (live org)
======================================================

This folder is a working lab bundle for the L611 MCP & Data Mirror data view
(dv_69b9b1ab3d60bb87c5701251): survey config, build helper, and ephemeral MCP
outputs while you iterate upsertProject until the Workspace project is correct.

This is not a portable template — dataViewId and component ids are org-specific.

Replication (fresh Cursor + this repo — no extra installs beyond Python)
---------------------------------------------------------------------------
  • Cursor with the **CJA MCP server** connected the normal way (see repo README).
  • **Python 3** on PATH — used only for stdlib JSON and the skill’s ``.py`` scripts
    (same as ``scripts/build_dimension_survey_project.py``). No pip packages.
  • **No** Adobe gateway curl scripts, **no** bearer-token env vars, **no** OS-specific
    shell redirects for JSON (always write UTF-8 via these scripts or your editor).
  • **upsertProject** runs **only** through Cursor’s MCP tools (or the CJA UI if you
    paste a definition there yourself). The build step only writes files under
    ``outputs/`` for review and for the agent to read when calling MCP.

Contents
--------
  l611_n10_m10_survey_config.json   Survey seed (top-10 slice, 3x3 grid + summary).
                                     Edit as you tighten qualification or copy forward.
  build_demo_project.py             Writes projectBody JSON + upsert_project_args(.min).json
  helpers/README.txt                Suggested files to drop under outputs/ during iteration
  outputs/                          Gitignored — MCP captures, last upsert envelope, notes

Build (from skill root, cja-dimension-survey)
---------------------------------------------
  python demo_example/build_demo_project.py

Or from this folder:
  python build_demo_project.py

Workflow: follow ../SKILL.md to identify components and lists → update
l611_n10_m10_survey_config.json and/or save MCP JSON under outputs/ → rebuild →
upsertProject → repeat until the CJA project matches intent.

For the full skill workflow, see ../SKILL.md. For the same “demo_example” pattern
in another skill (static fake preview), see ../../cja-component-visualizer/demo_example/README.txt

L611 demo example — N=M=10 dimension survey (live org)
======================================================

This folder is a working lab bundle for the L611 MCP & Data Mirror data view
(dv_69b9b1ab3d60bb87c5701251): survey config, build helper, and ephemeral MCP
outputs while you iterate upsertProject until the Workspace project is correct.

This is not a portable template — dataViewId and component ids are org-specific.

Contents
--------
  l611_n10_m10_survey_config.json   Survey seed (top-10 slice, 3x3 grid + summary).
                                     Edit as you tighten qualification or copy forward.
  build_demo_project.py             Writes outputs/projectBody.json and projectBody.min.json
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

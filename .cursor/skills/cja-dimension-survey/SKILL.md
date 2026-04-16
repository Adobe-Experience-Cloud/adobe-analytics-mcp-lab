---
name: cja-dimension-survey
description: >
  Build strict CJA Workspace dimension survey projects that classify dimensions by usable values and place qualifying dimensions into 3x3 freeform-table panels. Use when asked for a dimension survey, data coverage survey, or similar 'component' survey. Keep this skill separate from the general project builder. Ask for a data view unless one is already established, and use metrics/occurrences for dimension classification and grid tables.
---

# CJA Dimension Survey

Build a Workspace project that surveys dimensions only.

## Do this first
- Ask for a data view unless the conversation already established one.
- Ask for a dimension count when it is not provided.
- Pull usage lists for `dimension` only.

## Use this hardcoded id
- Use `metrics/occurrences` for every dimension classification pass and every 3x3 grid column tree.
- Do not resolve it through MCP discovery.

## Apply these filters
- Skip date-range and time-part dimensions.
- Skip dimensions that error during classification.
- Treat `No value` and similar sentinels as unusable.

## Build the survey in this order
1. Classify each candidate dimension with `runReport` on rows and `metrics/occurrences` on columns.
2. Sort each result group by component id.
3. Build the project body with `scripts/build_dimension_survey_project.py` and `scripts/subPanel_snippet_trimmed.json`.
4. Use `describeDimension` only for titles, never for ordering.

## Output rules
- Build from scratch according to this skill and `scripts/subPanel_snippet_trimmed.json`.
- Do not look for similar projects, template projects, or nearby examples in CJA before building.
- Do not inspect `describeProject` output or copy fragments from saved projects for this workflow.
- Include only the elements of `subPanels` that are listed in `scripts/subPanel_snippet_trimmed.json`, even if another guide or saved project shows more fields.
- Do not invent alternate layouts, helper widgets, or replacement subpanel structures.
- Put only dimensions with two or more usable values on the 3x3 grid.
- Put no-data dimensions and single-value dimensions in one additional summary panel as text.
- Keep `TextReportlet.textContent` and grid `subPanels[].description` as stringified Quill Delta.
- Prefer the smallest valid project body. Do not add metric panels, component catalogs, or extra summary widgets.

## References
- See `references/spec.md` for the exact ordering, Quill, layout, and summary-panel contracts.
- See `scripts/example_survey_config.json` for the config shape used by the builder.
- See `scripts/build_dimension_survey_project.py` for the project-body generator.

## Large `upsertProject` payloads (core)

Dimension-survey project bodies are often tens of thousands of characters. Agents frequently fail when they try to pass the entire `upsertProject` arguments object inline in a single primary-thread MCP call (truncation, escaping, or tool-parameter limits).

**Do this instead:**

1. **Write the payload to disk** in the workspace (for example `tmp/` or `outputs/`): either the full `{"projectBody": {...}}` object or, when updating an existing project, `{"projectId": "<id>", "projectBody": {"definition": ...}}` if metadata and `dataId` are already correct (slightly smaller envelope).
2. **Validate** with `json.loads` (or `python -c "json.load(open(...))"`) so the file is known-good before any MCP call.
3. **Call `upsertProject` without pasting the blob into chat:** have a **subagent** (for example `Task` with `generalPurpose`) read that UTF-8 file, parse JSON, and invoke `upsertProject` with the resulting dict—one focused job, file as source of truth.
4. **Confirm** with `describeProject` (`expansions=definition`) if the UI or response does not make success obvious.

Do not depend on embedding the full minified JSON in the parent agent’s single `call_mcp_tool` message when the file is large.

## Guardrails
- Do not use metrics, calculated metrics, or segments in candidate lists or summary output.
- Do not silently choose a data view.
- Do not auto-run this skill unless the user explicitly asks for a dimension survey, coverage check, or similar bulk analysis.
- Do not invoke `cja-project-builder` for this workflow unless the user explicitly asks for it.
- Do not search for similar projects or treat existing Workspace projects as reference material for this skill.
- Do not deviate from the proposed structure in `scripts/subPanel_snippet_trimmed.json` unless the user explicitly changes the spec.
- Build the project body locally with the script, minify it, and send that exact body to `upsertProject` using **Large `upsertProject` payloads** above (file on disk, validate, subagent MCP call—not a pasted megablob in the primary thread).

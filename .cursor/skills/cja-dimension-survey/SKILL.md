---
name: cja-dimension-survey
description: >
  Build CJA Workspace dimension survey projects from usage-ranked dimensions and standard metrics. Use when asked to identify which dimensions or metrics have data, classify top N dimensions by Events, qualify top M standard metrics under All Data, or assemble the final Workspace project body for a dimension survey. Ask for a data view unless one is already established; use metrics/occurrences for dimension classification and All_Visits for metric qualification.
---

# CJA Dimension Survey

Build a Workspace project that surveys usage-ranked dimensions and standard metrics.

## Do this first
- Ask for a data view unless the conversation already established one.
- Ask for counts when neither N nor M is provided.
- If the user gives only one number, use it for both N and M.
- Pull usage lists for `dimension` and `metric` only.

## Use these hardcoded ids
- `metrics/occurrences` for every dimension classification pass and every 3×3 grid column tree.
- `All_Visits` for metric qualification and the final non-zero metrics table.
- Do not resolve either id through MCP discovery.

## Apply these filters
- Skip date-range and time-part dimensions.
- Skip dimensions that error during classification.
- Use standard metrics only.
- Skip metrics that error or cannot be reported in the chosen data view.
- Treat `No value` and similar sentinels as unusable.

## Build the survey in this order
1. Classify each candidate dimension with `runReport` on rows and `metrics/occurrences` on columns.
2. Qualify each candidate metric with `runReport` using `All_Visits` on rows and the metric set on columns.
3. Sort each result group by component id.
4. Build the project body with `scripts/build_dimension_survey_project.py` and `scripts/subPanel_snippet_trimmed.json`.
5. Use `describeDimension` and `describeMetric` only for titles, never for ordering.

## Output rules
- Include only the elements of `subPanels` that are listed in `scripts/subPanel_snippet_trimmed.json`, even if the guide says more are required.
- Put only dimensions with two or more usable values on the 3×3 grid.
- Put no-data dimensions and single-value dimensions in the final summary panel.
- Put zero metrics in the final summary text block.
- Put non-zero metrics in the final summary table, sorted by metric id.
- Keep `TextReportlet.textContent` and grid `subPanels[].description` as stringified Quill Delta.

## References
- See `references/spec.md` for the exact ordering, Quill, layout, and summary-panel contracts.
- See `scripts/example_survey_config.json` for the config shape used by the builder.
- See `scripts/build_dimension_survey_project.py` for the project-body generator.

## Guardrails
- Do not use calculated metrics or segments in usage-ranked candidate lists.
- Do not silently choose a data view.
- Do not auto-run this skill unless the user explicitly asks for a dimension survey, coverage check, or similar bulk analysis.
- Always call `upsertProject` even with a large definition up to 100k.

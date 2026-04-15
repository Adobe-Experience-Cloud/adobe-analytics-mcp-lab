# cja-dimension-survey spec

## Core ids
- Dimension classification: `metrics/occurrences`
- Metric qualification and final table: `All_Visits`

## Sorting
Sort every published list by the full component id string, not by display name.
- Dimensions with no usable data: sort by dimension id.
- Dimensions with one usable value: sort by dimension id.
- Dimensions with two or more usable values: sort by dimension id.
- Zero metrics: sort by metric id.
- Non-zero metrics: sort by metric id.

## Data view and counts
- Ask for the data view unless it is already established in the conversation.
- Ask for counts when both N and M are missing.
- If only one number is given, use it for both N and M.

## Dimension classification
For each candidate dimension:
- Run `runReport` with the dimension on rows.
- Use `metrics/occurrences` only on columns.
- Use a high enough row cap to reveal usable labels.
- Count only usable row values.
- Treat `No value` and similar sentinels as unusable.

Classify each dimension as:
- no data: zero usable values
- single value: exactly one usable value
- grid candidate: two or more usable values

## Metric qualification
For each candidate metric:
- Run `runReport` with `All_Visits` on rows.
- Put the metric set on columns.
- Split requests only when payload limits require it.
- Split results into zero and non-zero metric groups.

## Layout
### 3x3 grid panels
- Place only grid-candidate dimensions on the grid.
- Use the trimmed cell template from `scripts/subPanel_snippet_trimmed2.json`.
- Keep the structure of each cell fixed; only substitute ids, titles, description Quill, and geometry values.
- Fill slots in row-major order.
- Use 325px row height.

### Dimension subpanel description Quill
Build the description from the dimension id:
1. Remove a leading `variables/` prefix.
2. If the string starts with a 24-character alphanumeric token immediately before the first `.`, replace that token with `...` plus the token's last 4 characters.
3. Split on the final `.`.
4. Emit a Quill Delta with `Y` as the first line, italic `Z` on the second line, and a trailing newline.
5. Store the Delta as JSON text with `JSON.stringify` semantics.

### Final summary panel
Include four subpanels:
1. no-data dimensions text
2. single-value dimensions text
3. zero metrics text
4. non-zero metrics freeform table

## Titles
- Use friendly names only for panel and subpanel titles.
- Never use friendly names for ordering.
- For grid panels, title the panel from the first and last dimension in that panel's id-sorted chunk.

## Builder inputs
Use these files:
- `scripts/build_dimension_survey_project.py`
- `scripts/subPanel_snippet_trimmed2.json`
- `scripts/example_survey_config.json`

Do not query CJA for a template project. Clone the snippet directly.

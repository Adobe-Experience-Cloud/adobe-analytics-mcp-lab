# cja-dimension-survey spec

## Core id
- Dimension classification and every grid table column: `metrics/occurrences`

## Sorting
Sort every published list by the full component id string, not by display name.
- Dimensions with no usable data: sort by dimension id.
- Dimensions with one usable value: sort by dimension id.
- Dimensions with two or more usable values: sort by dimension id.

## Data view and counts
- Ask for the data view unless it is already established in the conversation.
- Ask for the dimension count when it is missing.

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

## Layout
### 3x3 grid panels
- Place only grid-candidate dimensions on the grid.
- Use the trimmed cell template from `scripts/subPanel_snippet_trimmed.json`.
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
Include one text reportlet that contains two sections:
1. no-data dimensions text
2. single-value dimensions text

## Titles
- Use friendly names only for panel and subpanel titles.
- Never use friendly names for ordering.
- For grid panels, title the panel from the first and last dimension in that panel's id-sorted chunk.

## Builder inputs
Use these files:
- `scripts/build_dimension_survey_project.py`
- `scripts/subPanel_snippet_trimmed.json`
- `scripts/example_survey_config.json`

Clone the snippet directly.
Do not query CJA for a template project.
Do not look for similar projects, inspect saved projects, or copy fragments from existing Workspace definitions.
This skill always builds from scratch according to the spec in this folder.

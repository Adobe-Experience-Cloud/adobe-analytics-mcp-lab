---
name: cja-survey-test
description: >
  Build a CJA Workspace project that shows qualifying dimensions with data coverage in a 3x3 grid of freeform tables. Use when asked to create the older survey-style project that finds dimensions with enough non-null values, lays them out in grid panels, and upserts the full project directly from a single focused workflow.
---

# CJA Survey Test

Use this skill when the goal is the legacy "survey test" flow: identify dimensions with enough real values, arrange them in 3x3 grid panels, and create the Workspace project directly.

## Ask first

- Ask how many qualifying dimensions to include. Default to `20`.
- Ask for the minimum number of non-`No value` elements required to include a dimension. Default to `2`.

## Data view selection

- Use `findDataViews` and paginate until all pages are retrieved.
- If a data view named `Omni-Channel - Multi-Industry` exists, suggest it as the default.
- Show the full list and wait for the user's selection before proceeding.

## Qualify dimensions

- Use `findDimensions` for the chosen data view.
- Order candidate dimensions by path or id before filtering.
- Skip standard date and time dimensions such as ids beginning with `daterange` or `timepart`.
- For each remaining dimension, use `searchDimensionItems` with the selected `dataViewId`, the last 30 full days, `limit: 10`, and `page: 0`.
- Count only returned items whose value is not `No value`.
- Keep the dimension when the count is at least the requested threshold.
- Continue until you have the requested number of qualifying dimensions.

## Build the project

- Create a new Workspace project named `Dimension Data Coverage Analysis`.
- Use a description in the form `Grid layout showing [N] dimensions with >=[threshold] non-null items (Events, Last 30 Full Days)`.
- Use a relative last-30-full-days date range.
- Build one panel per group of 9 dimensions in a 3x3 grid.
- Title each panel `<First Dimension Name> - <Last Dimension Name>`.
- Collapse every panel except the first.
- Preserve the exact qualifying-dimension order. Do not regroup by theme.

## Grid subpanels

- Each table subpanel must include an explicit `position` object for grid placement.
- Set `subPanel.reportlet.name` to the dimension display name.
- Set `subPanel.description` to a stringified Quill Delta built from the shortened dimension id:
  1. Remove `variables/`.
  2. If the remaining string starts with a 24-character alphanumeric token before the first `.`, replace that token with `...` plus its last 4 characters.
  3. Split on the final `.`.
  4. Put the prefix on the first line and the suffix in italic on the second line.
- Use this grid:
  - row 1: `(0,0)`, `(33.33,0)`, `(66.66,0)`
  - row 2: `(0,1)`, `(33.33,1)`, `(66.66,1)`
  - row 3: `(0,2)`, `(33.33,2)`, `(66.66,2)`
- Use `width: 33.33`, `fixedHeight: 325`, and `autoHeight: 325` for each subpanel.

## Freeform table settings

- Use `metrics/occurrences` as the metric.
- Show 5 rows with descending metric sort.
- Put the dimension display name in `subPanel.reportlet.name`, not `subPanel.name`.

## Execution

- Build the entire project definition in one focused pass.
- Use `upsertProject` with the complete project definition.
- Return the resulting Workspace link when the create succeeds.

## Legacy bias

- Prefer the direct old-style workflow over broader reusable abstractions when they conflict.
- Do not stop to redesign the project shape unless the user explicitly asks for a different layout.

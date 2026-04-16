---
name: cja-segment-builder
description: natural-language cja segment builder for general and sequential segments. use when the user wants to create, refine, compare, validate, or test a cja segment from plain language; when they need duplicate checking against existing segments; when dimension values must be resolved before string equality; or when the request includes ordered logic such as then, after, within, before, exclude, or nested sequences.
---

# CJA Segment Builder

## Overview

Translate a plain-language segment request into a validated CJA segment definition, check for similar segments first, and only create the segment after explicit approval.

## Workflow

1. **Identify the data view.** If the user has not provided one, ask for it or resolve it with `findDataViews`, then set the working context with `setDefaultSessionDataViewId` when needed.
2. **Determine the segment shape.**
   - **General logic**: simple AND/OR, existence, thresholds, and visitor/visit/hit scope.
   - **Sequential logic**: ordered checkpoints such as THEN, AFTER/WITHIN, ONLY BEFORE, ONLY AFTER, or exclusions.
3. **Check for overlap before building.**
   - Use `findSegments` to spot likely duplicates by name and concept.
   - Use `listSimilarTo` when the user already has a segment ID, or when you need CJA’s similarity ranking.
   - Use `listComponentUsage` or `listFrequentlyUsedWith` only when it helps explain likely reuse or common pairings.
4. **Resolve the exact components.**
   - Use `findDimensions`, `findMetrics`, `describeDimension`, and `describeMetric` to confirm IDs and metadata.
   - For string equality, verify real item values with `searchDimensionItems` before writing the definition.
   - Use `streq-in` with a `list` for string equality. Do not use `equals` or `streq` alone for string matching.
5. **Use the right definition guide.**
   - Call `describeCja` with `SEGMENT_DEFINITION_GUIDE` before building or editing the segment body.
   - For ordered logic, consult `references/sequential-segment-knowledge.md` and keep checkpoints on separate hits/events.
6. **Present a concise proposal for approval.** Include the proposed name, scope, plain-language logic, referenced dimensions/metrics, any similar segments found, and any uncertain values that need confirmation.
7. **Wait for explicit approval.** Do not call `upsertSegment` until the user confirms the planned definition.
8. **Build and test.** After approval, call `upsertSegment` with the validated `definition`, `dataId`, `name`, `description`, and `compatibility`. Then optionally run `runReport` to confirm the segment behaves as expected.

## Guardrails

- Never invent dimension names, item values, or metric IDs.
- Never create a segment without explicit approval.
- Never assume a value like "Mobile" or "Paid Search" is correct until `searchDimensionItems` confirms it.
- Use `searchDimensionItems` whenever a rule depends on an exact string value in the data view.
- Keep sequential checkpoints ordered and separated according to the segment definition guide.
- If the request is ambiguous about scope, time window, or exclusions, ask only the minimum question needed to unblock the build.

## Tool map

| Tool | Use |
|---|---|
| `findDataViews`, `setDefaultSessionDataViewId` | Select the working data view |
| `findSegments`, `describeSegment`, `listSimilarTo` | Avoid duplicates and compare existing segments |
| `findDimensions`, `findMetrics`, `describeDimension`, `describeMetric` | Resolve and verify components |
| `searchDimensionItems` | Confirm exact string values before building filters |
| `describeCja` | Load the segment definition guide and sequential guide |
| `upsertSegment` | Create or update the segment after approval |
| `runReport` | Validate the segment with a quick report |

## Output expectations

When responding to the user, keep the flow tight:
- summarize the intended segment in plain language,
- show the key components and any near matches,
- call out unresolved ambiguities,
- wait for confirmation,
- then create the segment and report the result.

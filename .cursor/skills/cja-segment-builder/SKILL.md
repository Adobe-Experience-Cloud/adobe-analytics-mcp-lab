---
name: cja-segment-builder
description: natural-language cja segment builder for simple and sequential segments. use when the user wants to create, update, compare, validate, or test a cja segment from plain language; when they need duplicate checking against existing segments; when dimension values must be resolved before string equality; or when the request includes ordered logic or modifiers such as then, after, within, before, exclude, does not exist, does not match, nested sequences, logic groups, or scoped person/visit/hit rules.
---

# CJA Segment Builder

## Overview

Translate a plain-language segment request into a validated CJA segment definition, check for similar segments first, and upsert the segment once the logic is clear. Prefer direct creation for simple, unambiguous new segments. For simple updates to existing segments, apply the minimum change and upsert directly. If the request is very unclear, ask the minimum clarifying question needed before building, but still provide the most likely plain-language interpretation and ASCII visual if one is identifiable.

## Core reasoning model

Treat sequential logic as ordered checkpoints over a person, visit, or hit scope. A valid sequence only needs to match once anywhere within the container. Always reason in this order:

1. Identify the container level.
2. Identify the ordered checkpoints.
3. Identify any modifiers that change distance, negation, scope, or boundaries.
4. Verify exact values before building equality predicates.
5. Decide whether a single valid path is enough or whether a constraint must exclude alternatives.

## Segment grammar to keep in mind

Use `references/segment-grammar.md` for the compact UI-to-JSON mapping. Keep the skill focused on interpretation rather than repeating the full source docs.
- `sequence-and` / `sequence-or` are UI logic groups.
- `sequence-prefix` / `sequence-suffix` are boundary-slice forms of sequence logic.
- `time-restriction`, `container-restriction`, and `dimension-restriction` are sequence-stream modifiers, not standalone filters.
- `exclude-next-checkpoint` changes the meaning of the next checkpoint relative to the prior one.

## Workflow

1. **Identify the data view.** If the user has not provided one, ask for it or resolve it with `findDataViews`, then set the working context with `setDefaultSessionDataViewId` when needed.
2. **Determine the segment shape.**
   - **Simple logic**: one or a few AND/OR rules, existence, thresholds, and visitor/visit/hit scope.
   - **Sequential logic**: ordered checkpoints such as THEN, AFTER/WITHIN, ONLY BEFORE, ONLY AFTER, exclusions, and nested checkpoints.
   - **Modifier-heavy logic**: predicates like does not exist, does not match, between, greater/less than, distinct count, allocation model, and time/dimension restrictions.
3. **Check for overlap before building.**
   - Use `findSegments` to spot likely duplicates by name and concept.
   - Use `listSimilarTo` when the user already has a segment ID, or when you need CJA’s similarity ranking.
   - Use `listComponentUsage` or `listFrequentlyUsedWith` only when it helps explain likely reuse or common pairings.
4. **Resolve the exact components.**
   - Use `findDimensions`, `findMetrics`, `describeDimension`, and `describeMetric` to confirm IDs and metadata.
   - For string equality, verify real item values with `searchDimensionItems` before writing the definition.
   - Use exact-value predicates that match the current guide and UI behavior.
5. **Use the right definition guide.**
   - Call `describeCja` with `SEGMENT_DEFINITION_GUIDE` before building or editing the segment body.
   - For ordered or scoped logic, consult `references/sequential-reasoning-framework.md` and `references/segment-grammar.md`. Keep checkpoints on separate hits/events when the logic requires it. For start/stop cases, apply the start/stop checklist before choosing first vs every occurrence or whether overlaps are allowed.
   - For UI-shaped examples, consult `references/segment-ui-samples.md`.
6. **Decide whether to pause.**
   - For a simple, unambiguous request to create a new segment, build and upsert it directly.
   - For a requested update to an existing segment, apply the minimum change and upsert directly.
   - Pause only when the request is ambiguous, multiple segment interpretations are plausible, an exact value is unresolved, or sequential logic needs interpretation.
7. **Build and test.** Call `upsertSegment` with the validated `definition`, `dataId`, `name`, `description`, and `compatibility`. Then validate with a CJA project or report when possible, using a known positive example and a known negative example.

## Validation standard

When validating logic, work inside-out and choose the validation components automatically from the segment logic. Start with the innermost condition or smallest qualifying scope, then move outward one layer at a time.

Use at least:

- one known positive example that should match,
- one known negative example that should not match,
- one report that makes the sequence or modifier visible,
- a comparison against a control segment or baseline when that helps interpretation.

For each step, show a terse proof table with the qualifying component, the expected in-population, and the expected out-population. When the segment logic can prove a qualifying person or non-qualifying person directly, include at least one person-level example as part of the validation proof.

For sequential segments, explicitly verify that the matching path is true at least once and that the ordered checkpoints occur in the right scope.

## Guardrails

- Never invent dimension names, item values, or metric IDs.
- Never assume a value like "Mobile" or "Paid Search" is correct until `searchDimensionItems` confirms it.
- Use `searchDimensionItems` whenever a rule depends on an exact string value in the data view.
- Keep sequential checkpoints ordered and separated according to the segment definition guide.
- If the request is very unclear or ambiguous about scope, time window, exclusions, or whether an existing segment should be updated, ask only the minimum question needed to unblock the build.
- For simple new segment requests, prefer direct upsert over clarification.
- When validation is available, create or update a CJA project with reports that demonstrate the logic in context.
- Use helper segments prefixed with `[validation]` when you need mini-segments to prove a condition or boundary.

## Modifier patterns to preserve

- **exists / does not exist**: map to existence predicates on the correct container level.
- **string equality**: preserve exact value matches after verifying the literal item value(s).
- **not-matches / pattern rules**: preserve the provided glob or regex-style pattern exactly.
- **dimension restriction**: use ordered count restrictions such as `after`, `before`, or `within` when the UI expresses distance from a prior checkpoint.
- **time restriction**: preserve the requested time unit and window, such as `within 1 hour`.
- **allocation model**: keep allocation-model variants when the UI shows instance or deduped-instance behavior.
- **sequence separators**: retain `exclude-next-checkpoint`, `sequence-prefix`, or `sequence-suffix` when the logic depends on order boundaries.

## Tool map

| Tool | Use |
|---|---|
| `findDataViews`, `setDefaultSessionDataViewId` | Select the working data view |
| `findSegments`, `describeSegment`, `listSimilarTo` | Avoid duplicates and compare existing segments |
| `findDimensions`, `findMetrics`, `describeDimension`, `describeMetric` | Resolve and verify components |
| `searchDimensionItems` | Confirm exact string values before building filters |
| `describeCja` | Load the segment definition guide and sequential guide |
| `upsertSegment` | Create or update the segment |
| `runReport` | Validate the segment with a quick report |

## Output expectations

When responding to the user, always use this order and these headings:

1. **Info**
   - Name: use the friendly display name only.
   - Data view: use the friendly data view name only.
   - Link: provide the component URL.

2. **Definition**
   - Plain-language: explain the segment in one short, user-friendly sentence, and keep the segment description aligned with that same wording.
   - Visual: render the definition as an ASCII, UI-like segment sketch using clear symbols where they help readability, such as `=`, `!=`, `<`, `<=`, `>=`, `>`, and `contains`.

3. **Validation**
   - Choose validation components automatically from the segment logic.
   - Validate from the inside out, starting with the innermost condition or smallest qualifying scope and expanding outward.
   - List the validation points as terse proof statements, not prose.
   - Show the proof in a table with columns that make the in/out reasoning obvious.
   - Include a person-level example whenever a real person can prove at least one qualifying or non-qualifying case.
   - When validation is available, create or update a CJA project with reports that demonstrate the logic in context and include the project link.

4. **Notes**
   - Call out similar or duplicate segments.
   - Add suggestions, concerns, or clarifying questions only if needed.
   - Always include: "do you want me to create a project with the validation structures for you?"
   - If the request was refused because a duplicate existed, offer to create a new segment if the user confirms that intent.
   - Put any other notes last.

Keep the ASCII rendering readable and close to the segment builder UI. Prefer human-friendly wording over raw operator names in visible output. When the request is clear, create a fresh segment, note any duplicate or near-duplicate, and still return the new segment details in the required order.

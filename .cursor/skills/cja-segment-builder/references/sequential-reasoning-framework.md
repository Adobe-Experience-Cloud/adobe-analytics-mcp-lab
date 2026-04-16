# Sequential Reasoning Framework

Use this reference when a segment depends on event order, proximity, exclusions, or before/after logic.

## Mental model

- Sequential logic is evaluated on ordered event data grouped by a person, visit, or hit scope.
- A sequence is satisfied when at least one valid path matches inside the container.
- Do not assume every occurrence must match; look for one valid ordered chain and then confirm that the result still respects the requested scope.

## Think in this order

1. **Scope**: person, visit/session, or hit/event.
2. **Checkpoints**: what has to happen first, second, third, and so on.
3. **Distance**: whether a checkpoint must happen within a time or event window.
4. **Exclusion**: whether something must not happen between checkpoints.
5. **Boundary slicing**: whether the logic should return only the portion before or after the sequence.

## Common patterns

- **THEN**: ordered checkpoints.
- **AFTER / WITHIN**: distance constraints between checkpoints.
- **EXCLUDE**: a checkpoint must not occur at that position.
- **ONLY BEFORE / ONLY AFTER**: slice the container around the matched sequence.
- **Nested groups**: use when the business question needs sub-sequences or alternatives.

## Start / stop checklist

Use this checklist for questions that ask where a sequence begins, ends, or repeats:

1. Identify the point of interest.
2. Decide whether to analyze the first occurrence or every occurrence.
3. Decide whether overlapping matches are allowed.
4. Decide whether the returned slice includes the anchor event or only the events before/after it.
5. Add the smallest validation case that proves the boundary behavior.

## Validation habits

- Build one positive example that should match.
- Build one negative example that should not match.
- Confirm the report or project shows the sequence in the right order.
- Check the segment at the correct scope before adjusting any modifiers.

## Practical reminder

For questions like "what happened after X" or "what happened within Y of X", translate the request into an ordered chain first, then add modifiers. Do not treat it like a simple attribute filter.


## Event-level wrapping

- Sequential checkpoints are implicitly event-level by default.
- Wrapping another container inside an event-level checkpoint is usually harmless unless the scope itself is meant to change.
- Use the wrapper that matches the question; do not add container layers just to mirror the UI.

## Persistence and attribution reminders

- When a segment is compared with tables that use persisted dimensions or attribution-configured metrics, validate the comparison carefully.
- If the question depends on a derived field or a metric choice, treat that as part of the interpretation, not just the segment.


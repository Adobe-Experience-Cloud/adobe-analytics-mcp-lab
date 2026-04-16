# Sequential Segment Knowledge

Use this reference when a segment depends on event order, proximity, exclusions, or "before/after" logic.

## Core ideas

- **THEN** means ordered checkpoints. The sequence can match anywhere in the container as long as the checkpoints occur in order.
- **AFTER / WITHIN** control distance between checkpoints.
- **EXCLUDE** means a checkpoint must not happen in the specified position in the sequence.
- **ONLY BEFORE** returns the portion of data before the sequence.
- **ONLY AFTER** returns the portion of data after the sequence.
- **Nesting** is valid when the business question requires groups or sub-sequences.

## Container levels

- **Hit/Event**: smallest unit; a sequence still requires separate events.
- **Visit/Session**: sequence occurs within a single visit or across visit boundaries where the definition allows it.
- **Visitor/Person**: sequence can span the person’s history.

## Practical patterns

- **A then B**: use `sequence` with checkpoints in order.
- **A then B without C in between**: use `exclude-next-checkpoint` between the checkpoints.
- **A within 2 days of B**: use `time-restriction` with `limit: within`, `count: 2`, `unit: day`.
- **Only before X**: use `sequence-suffix` and the exclusion pattern described in the guide.
- **Only after X**: use `sequence-prefix`.

## Useful reminders

- Sequence checkpoints do not need to be adjacent.
- The same definition can behave differently at hit, visit, and visitor scope.
- Use `describeCja` with `SEGMENT_DEFINITION_GUIDE` for the exact JSON structure before calling `upsertSegment`.
- For the tricky "only before" and "only after" cases, follow the existing CJA guide or the support docs rather than improvising.

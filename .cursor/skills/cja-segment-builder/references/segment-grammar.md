# Segment Grammar Reference

Use this reference for the shared definition model and UI-to-JSON mapping.

## Core structure

- `segment` is the top-level wrapper.
- `container` sets the evaluation scope (`person`, `visit/session`, or `hit/event`).
- A predicate returns a container set.
- Checkpoints do not need to be contiguous; they only need to occur in order when using sequential logic.

## Common function mapping

- UI **Logic Group** → JSON `sequence-and` / `sequence-or`.
- UI **Then** → JSON `sequence` stream order.
- UI **Only After Sequence** → JSON `sequence-suffix`.
- UI **Only Before Sequence** → JSON `sequence-prefix`.
- UI **Exclude** / **Does not happen between** → JSON `exclude-next-checkpoint`.
- UI **Within / After** → JSON `time-restriction`.
- UI **Within / After same visit / page view** → JSON `container-restriction` or `dimension-restriction`.

## Predicate families

- String equality and inequality: `streq`, `not-streq`, `contains`, `not-contains`, `starts-with`, `ends-with`, `matches`, `not-matches`.
- Numeric comparisons: `eq`, `not-eq`, `gt`, `gte`, `lt`, `lte`.
- Existence: `exists`, `not-exists`.
- Grouping: `and`, `or`, `without`, `sequence`, `sequence-and`, `sequence-or`.

## Interpretation reminders

- `sequence-and` means all grouped checkpoints must occur, in any order.
- `sequence-or` means at least one grouped checkpoint must occur.
- `exclude-next-checkpoint` changes the meaning of the next checkpoint relative to the prior one.
- Time and instance restrictions are part of the sequence stream, not standalone filters.

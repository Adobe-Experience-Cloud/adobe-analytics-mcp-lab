# Component Selection and Scope

Use this reference when the question is really about *where* a rule should live and *which level* should be evaluated.

## Choose the right component

- Use **standard tables / breakdowns** for simple one-off analysis.
- Use **saved segments** and **calculated metrics** when the logic is modular and should be reused.
- Use **data view fields** or **derived connection fields** when the logic should behave like a native field and be broadly compatible.
- Prefer the simplest reusable component that can answer the question cleanly.

## Choose the right level

- Start from the question, not from a default level.
- Ask whether the analysis is about a **person**, a **session**, or an **event**.
- Ask whether the user wants **complete data** or only a **subset around a point of interest**.
- If checkpoints live at different levels, make the nesting explicit instead of flattening the logic.

## Event containers and wrappers

- In sequential logic, checkpoint rows/events are implicitly wrapped at the event level.
- Adding an event wrapper around another container is usually harmless and does not change the meaning.
- Changing the wrapper to session or person can materially change the result, because it changes the scope of the returned data.

## Slice vs whole-population behavior

- **Include everyone** means the segment can return the full person/session population when the condition is satisfied anywhere in the scope.
- **Only after sequence** and **only before sequence** return a slice around the matched sequence.
- For backward-looking questions, think in terms of a forward evaluation that later slices the returned data.

## Cross-cutting interpretation

- When a segment seems to disagree with a table, check whether persistence, attribution, or a derived field is changing the visible result outside the segment logic.
- Validate with a small known case whenever a rule mixes scope, persistence, or attribution.

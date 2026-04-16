# Validation Playbook

Use this reference when you need to prove that a segment behaves the way the user expects.

## Minimum validation set

- One known positive case.
- One known negative case.
- One report or freeform table that makes the logic visible.
- One short explanation of what the output proves.

## Recommended project layout

Create a small CJA project with:

1. A freeform table filtered by the new segment.
2. A comparison with a control or baseline population.
3. A visualization that exposes the ordered or time-bound behavior.

## How to explain the result

State:

- what was tested,
- what should have matched,
- what should not have matched,
- what the report actually showed,
- and whether the segment should be adjusted.

## Link handling

When the segment is created or updated, append the segment edit link at the end of the response.

When validation includes a project, append the project link after the segment link.

Use the segment link first, then the validation project or report link(s).

## Additional validation checks

- If the segment uses an `only after` or `only before` slice, verify the boundary event itself and one row just outside the boundary.
- If the segment mixes scope levels, verify each checkpoint at its own level before testing the full sequence.
- If persistence or attribution is part of the comparison, use a control table to show whether the difference comes from the segment or from the component settings.


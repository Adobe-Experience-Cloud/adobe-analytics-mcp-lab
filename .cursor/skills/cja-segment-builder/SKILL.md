# CJA Segment Builder

## Purpose

Translate natural language into a valid CJA segment and create it via
`upsertSegment`.

------------------------------------------------------------------------

## Core Behavior

### 1. Default Action

-   Create a NEW segment from user input.

------------------------------------------------------------------------

### 2. Update Safety (STRICT)

-   NEVER update an existing segment unless the user explicitly says to
    update.

Explicit signals include: - "update"\
- "modify"\
- "edit"\
- naming a specific segment to change

Allowed: - Updating a segment created in the current interaction.

If a similar segment exists: - Ask: "Do you want to update the existing
segment or create a new one?" - Do NOT proceed without confirmation.

------------------------------------------------------------------------

### 2a. Demo / Test Segments (OVERRIDE)

-   If the user uses keywords like:
    -   "demo segment"
    -   "test segment"
    -   "example segment"
-   ALWAYS create (upsert) a NEW segment.
-   NEVER update an existing segment in this case.
-   NEVER reuse, copy, or base the segment on an existing segment.
-   Treat as a completely fresh request with no prior reference.
-   This rule overrides duplicate detection.

------------------------------------------------------------------------

### 3. Description Consistency (MANDATORY)

-   Generate ONE plain-language description.
-   Use it EXACTLY as:
    -   the `description` in `upsertSegment`
    -   the definition shown to the user
-   Do NOT reword or summarize.

------------------------------------------------------------------------

### 4. URL Generation (MANDATORY)

Required URL format:
http://experience.adobe.com/#/platform/analytics/#/components/segments/edit/`<SEGMENT_ID>`{=html}

------------------------------------------------------------------------

### 5. Output Requirements

Return: - Segment name - Segment ID - Plain-language definition (exact
description) - Direct URL

------------------------------------------------------------------------

### 6. Preview Metrics (MANDATORY)

events: `<segment_value>`{=html} of `<total_value>`{=html} total\
sessions: `<segment_value>`{=html} of `<total_value>`{=html}\
people: `<segment_value>`{=html} of `<total_value>`{=html}

------------------------------------------------------------------------

## 7. Temporal Segment Frameworks (MANDATORY USE)

### A. Period AFTER a point of interest

-   sequence-prefix (ONLY AFTER)
-   Anchor FIRST → Event exists
-   Time restriction (after N units)
-   Cutoff → exclude-next-checkpoint + guard

Guard MUST use: - Event exists: metrics/occurrences

Pattern: Event → Time → Cutoff

#### JSON Skeleton

``` json
{
  "container": {
    "func": "container",
    "context": "hits",
    "pred": {
      "func": "sequence-prefix",
      "context": "visitors",
      "stream": [
        {
          "context": "hits",
          "func": "container",
          "pred": {
            "func": "event-exists",
            "evt": {
              "func": "event",
              "name": "<event_metric>"
            }
          }
        },
        {
          "func": "time-restriction",
          "count": <N>,
          "limit": "after",
          "unit": "<unit>",
          "container": "hits"
        },
        {
          "func": "exclude-next-checkpoint"
        },
        {
          "context": "hits",
          "func": "container",
          "pred": {
            "func": "event-exists",
            "evt": {
              "func": "event",
              "name": "metrics/occurrences"
            }
          }
        }
      ]
    }
  },
  "func": "segment",
  "version": [1,0,0]
}
```

------------------------------------------------------------------------

### B. Period BEFORE a point of interest

-   Standard sequence (ordered)
-   Cutoff FIRST
-   Time restriction (before N units)
-   Anchor LAST

Guard MUST use: - Event exists: metrics/occurrences

Pattern: Cutoff → Time → Event

#### JSON Skeleton

``` json
{
  "container": {
    "func": "container",
    "context": "hits",
    "pred": {
      "func": "sequence",
      "context": "visitors",
      "stream": [
        {
          "func": "exclude-next-checkpoint"
        },
        {
          "context": "hits",
          "func": "container",
          "pred": {
            "func": "event-exists",
            "evt": {
              "func": "event",
              "name": "metrics/occurrences"
            }
          }
        },
        {
          "func": "time-restriction",
          "count": <N>,
          "limit": "before",
          "unit": "<unit>",
          "container": "hits"
        },
        {
          "context": "hits",
          "func": "container",
          "pred": {
            "func": "event-exists",
            "evt": {
              "func": "event",
              "name": "<event_metric>"
            }
          }
        }
      ]
    }
  },
  "func": "segment",
  "version": [1,0,0]
}
```

------------------------------------------------------------------------

## 8. Validation

-   Validate dimension values
-   Ensure correct sequencing and time logic

------------------------------------------------------------------------

## Summary

-   Default = create
-   Demo/test = always new
-   Use strict temporal templates

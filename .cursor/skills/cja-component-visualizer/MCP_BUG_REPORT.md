# MCP tool notes (`listFrequentlyUsedWith`)

**Date:** February 4, 2026 (updated April 14, 2026)  
**Project:** Component network visualization (lab)

## Issue — `listFrequentlyUsedWith`

For **metric** and **dimension** components, MCP often returns **404** or **empty** results when `componentId` uses a **normal slash** (for example `metrics/occurrences`). That behavior is inconsistent with the same logical id expressed using a **literal** `%252F` in place of each `/`.

### MCP example (problematic shape)

```
user-CJA-listFrequentlyUsedWith
  componentId: metrics/lab.demo.orders
  componentType: metric
  dataViewId: dv_lab00000000000000000000001

Result: 404 or []
```

## Workaround (documented skill path)

Pass **`componentId` as a single string** where each `/` is replaced by the six characters **`%252F`** (for example `metrics%252Foccurrences`, `variables%252Fdaterangeday`). Canonical ids with a plain `/` still tend to **404** on MCP; a single **`%2F`** only (without the extra `25`) is typically rejected as **invalid parameters**.

## Encoding matrix (live MCP probe)

**Context:** `user-CJA-listFrequentlyUsedWith`, data view **Omni-Channel - Multi-Industry (HOL)** `dv_681b875cd7b56a2b266fb9ba` (2026-04-14).

### Metric seed (`componentType: metric`)

| `componentId` value | Outcome (summary) |
|---------------------|-------------------|
| `metrics/occurrences` | **404** — requested resource was not found |
| `occurrences` (prefix stripped) | `[]` |
| `metrics%2Foccurrences` (single-encoded slash) | **Invalid request** — check parameters |
| `metrics%252Foccurrences` (literal `%252F` for slash) | **Non-empty** co-usage list |
| `metrics%25252Foccurrences` (triple `%25252F`) | `[]` |
| `metrics\occurrences` (backslash) | **Unexpected error** (tool execution failed) |
| `metrics\/occurrences` (backslash + slash) | **Unexpected error** |
| `metrics／occurrences` (U+FF0F fullwidth slash) | `[]` |
| `metrics.occurrences` (dot) | `[]` |
| `metrics` followed by ASCII vertical bar then `occurrences` | **Unexpected error** |
| `metrics%252Foccurrences%252Fvalue` (extra segment, wrong id) | `[]` |

### Dimension seed (`componentType: dimension`)

| `componentId` value | Outcome (summary) |
|---------------------|-------------------|
| `variables/daterangeday` | **404** |
| `daterangeday` (prefix stripped) | `[]` |
| `variables%2Fdaterangeday` | **Invalid request** |
| `variables%252Fdaterangeday` | **Non-empty** co-usage list |

## `listSimilarTo` — out of scope for this skill

This skill builds networks from **usage** (`listComponentUsage`) and **co-usage** (`listFrequentlyUsedWith` with the `%252F` workaround). It does **not** use **`listSimilarTo`**: in lab probes that tool returned **`[]`** for every encoding variant tried (including literal `%252F`), including segment seeds where slashes are not involved—so **similarity-based edges are omitted** from the documented workflow.

If you **must** obtain “similar to” data despite MCP behavior, you could explore **Adobe’s Component Analysis HTTP API** on your own; **this skill does not document** endpoints, headers, tokens, or any step-by-step for that path.

## Hypothesis (for MCP maintainers)

The gateway may not be applying the same path-segment encoding for slashy ids as a correctly built client string, or may be double-applying encoding when the caller already passes `%252F`. **`listSimilarTo`** may additionally mishandle responses or target URLs even when the 404 is avoided.

## Recommendation

MCP server maintainers should inspect **`listFrequentlyUsedWith`** (URL encoding for `/` in metric and dimension ids) and **`listSimilarTo`** (empty results despite varied `componentId` shapes).

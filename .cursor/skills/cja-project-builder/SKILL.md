# CJA Project Builder (v96)

Build and modify CJA projects using **known-good patterns**, not a schema.

## Core Rules
- Never invent fields.
- Only use structures seen in:
  - starter_project_v96.json
  - MCP responses (describeProject, component APIs)
- Prefer copying minimal valid fragments.

## Validation Approach
Instead of schema validation:
- Match existing payload shapes
- Reuse exact key structures
- Keep nesting identical to examples

## Versioning
- Always use: `definition.version = "v96"`

## Workflow
1. Discover components via MCP
2. Copy minimal valid fragments
3. Assemble project
4. Patch safely (no structural invention)

## Guardrails
- If unsure: omit, don’t guess
- Smaller valid payload > large incorrect one

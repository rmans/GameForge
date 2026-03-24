---
name: scaffold-implement-plan
description: "Plan implementation for one task. Reads action.json with task info and context docs. Produces a 5-10 line implementation outline. Writes result.json."
argument-hint: (called by /scaffold-implement dispatcher — not user-invocable)
allowed-tools: Read, Write, Grep, Glob
---

# Plan Implementation

This skill is called by the `/scaffold-implement` dispatcher. It reads the task and relevant context, then produces a concise implementation plan.

## Input

Read `.reviews/implement/action.json`:

```json
{
  "action": "plan",
  "task_id": "TASK-004",
  "task_file": "tasks/TASK-004-place-building-impl_draft.md",
  "task_info": {
    "task_type": "behavior",
    "implements": "SPEC-001",
    "content": "... task content ..."
  },
  "context_docs": ["design/architecture.md", "specs/SPEC-001-...", "design/systems/SYS-005-...", ...],
  "steps": [{"number": 1, "text": "Create BuildingPlacementSystem C++ class", "details": []}]
}
```

## Process

1. **Read each context doc** listed in `context_docs`. Only the ones that exist.
2. **Understand the task** — what it implements, what system it belongs to, what spec it fulfills.
3. **Produce a 5-10 line plan** covering:
   - Files to create/modify
   - Key patterns to follow (from engine docs)
   - Signals to register or connect
   - Data tables to update
   - Test layers to cover
   - Anything the task steps don't mention but context implies

## Output

Write `.reviews/implement/result.json`:

```json
{
  "plan": "1. Create src/systems/building_placement_system.h/.cpp\n2. Register in SimulationOrchestrator tick order (after GridSystem)\n3. Wire construction_started signal in game_manager.gd\n4. Add balance CSV entries for placement validation\n5. Regression tests: Layer 1 (placement API), Layer 2 (invalid tiles), Layer 5 (ResourceSystem integration)\n6. Follow singleton node pattern from scene-architecture"
}
```

## Principles

- **Short and actionable.** 5-10 lines. Not a design doc — a checklist.
- **Reference specific patterns.** "Follow singleton node pattern" not "set up the node."
- **Flag what the task steps miss.** If context shows the task needs signal wiring but Steps doesn't mention it, add it to the plan.

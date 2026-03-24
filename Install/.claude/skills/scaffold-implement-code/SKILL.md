---
name: scaffold-implement-code
description: "Write code for one implementation step. Reads action.json with the step, file manifest, and plan. Writes code, reports files created/modified. Writes result.json."
argument-hint: (called by /scaffold-implement dispatcher — not user-invocable)
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Implement One Step

This skill is called by the `/scaffold-implement` dispatcher. It writes code for one task step at a time.

## Input

Read `.reviews/implement/action.json`:

```json
{
  "action": "code",
  "task_id": "TASK-004",
  "step": {"number": 1, "text": "Create BuildingPlacementSystem C++ class", "details": ["Include GDCLASS macro", "Register properties"]},
  "step_number": 1,
  "total_steps": 6,
  "file_manifest": ["src/systems/health_system.h"],
  "context_docs": ["design/architecture.md", ...],
  "plan": "1. Create src/systems/building_placement_system.h/.cpp\n..."
}
```

## Process

1. **Read the step** — understand what this one step requires.
2. **Check the file manifest** — what files already exist from previous steps.
3. **Read relevant context docs** if the step touches signals, architecture, or engine patterns.
4. **Write the code.** Follow the plan. Follow engine conventions.
5. **Track every file** created or modified.

## Output

Write `.reviews/implement/result.json`:

```json
{
  "files_created": ["src/systems/building_placement_system.h", "src/systems/building_placement_system.cpp"],
  "files_modified": [],
  "summary": "Created BuildingPlacementSystem with GDCLASS macro, registered properties, added to SConstruct."
}
```

## Principles

- **One step at a time.** Don't look ahead. Just implement this step.
- **Track files precisely.** Every file created or modified must be in the result.
- **Follow the plan.** If the plan says "follow singleton node pattern," follow it.
- **Follow engine docs.** If the engine doc says "use GDCLASS macro," use it.
- **Don't skip test code.** If this step involves test files, include them.

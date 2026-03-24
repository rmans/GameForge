---
name: scaffold-review-scope-check
description: "Evaluate scope guard tests on a proposed change during document review. Reads action.json for the change and tests. Writes result.json with pass/fail. Shared by /scaffold-iterate and /scaffold-fix."
argument-hint: (called by review dispatchers — not user-invocable)
allowed-tools: Read, Write
---

# Scope Check

This skill is called by the `/scaffold-iterate` dispatcher before an accepted change is finalized. It evaluates whether the proposed change stays within the correct document layer.

## Input

Read `.reviews/iterate/action.json`:

```json
{
  "action": "scope_check",
  "session_id": "...",
  "layer": "systems",
  "change_description": "Rewrite ### Purpose to include specific owned state names.",
  "fix_description": "Rewrite ### Purpose to: 'Owns construction lifecycle...'",
  "section": "### Purpose",
  "scope_guard": {
    "upward": "design doc — game-level design decisions",
    "downward": "architecture, interfaces, engine docs — implementation details",
    "tests": [
      {
        "name": "upward_leakage",
        "question": "Does this change introduce or modify game-level design decisions that belong in the design doc?",
        "guidance": "System designs implement the design doc's vision; they don't redefine the game."
      },
      {
        "name": "downward_leakage",
        "question": "Does this change introduce architectural, interface, or implementation detail?",
        "guidance": "System designs describe behavior, not structure. No signals, methods, node names."
      },
      {
        "name": "architecture_survival",
        "question": "If the architecture changed tomorrow, would this change still be valid?",
        "guidance": "If no, it's encoding an architecture assumption, not behavior."
      }
    ]
  }
}
```

## Process

For each test in `scope_guard.tests`:

1. Read the question.
2. Read the guidance.
3. Evaluate the proposed change (`change_description` + `fix_description`) against the question.
4. Decide: **pass** or **fail**.
5. If fail, explain why — reference the guidance.

## Output

Write `.reviews/iterate/result.json`:

```json
{
  "overall": "pass|fail",
  "tests": [
    {
      "name": "upward_leakage",
      "result": "pass",
      "reasoning": "The change names owned state, which is system-level — not game-level design."
    },
    {
      "name": "downward_leakage",
      "result": "pass",
      "reasoning": "The change describes state in behavioral terms, not implementation."
    },
    {
      "name": "architecture_survival",
      "result": "pass",
      "reasoning": "Naming owned state doesn't depend on architecture choices."
    }
  ]
}
```

`overall` is `"fail"` if ANY test fails. The dispatcher will convert the accepted issue to a rejection.

## Principles

- **Be strict on layer boundaries.** The scope guard exists to prevent documents from creeping into adjacent layers.
- **Be practical on edge cases.** A system doc that says "colonists become unhappy when hungry" is behavioral. A system doc that says "NeedsSystem decrements mood_value" is implementation. The line is clear in most cases.
- **When in doubt, pass.** A marginal scope concern is less harmful than rejecting a valid improvement. Flag the concern in reasoning so the report can surface patterns.

## What NOT to Do

- **Don't adjudicate the issue itself.** That was already done. You're only checking scope.
- **Don't edit files.**
- **Don't read the target document.** The change description is sufficient.

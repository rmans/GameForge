---
name: scaffold-seed-verify
description: "Verify coverage after seeding. Reads action.json with all created docs and upstream requirements. Checks every requirement is covered, every dependency is satisfied. Reports gaps. Writes result.json."
argument-hint: (called by /scaffold-seed dispatcher — not user-invocable)
allowed-tools: Read, Write, Grep, Glob
---

# Verify Seed Coverage

This skill is called by the `/scaffold-seed` dispatcher after all candidates have been created. It checks that nothing was missed.

## Input

Read `.reviews/seed/action.json`:

```json
{
  "action": "verify",
  "layer": "tasks",
  "requirements": [
    {"source_file": "specs/SPEC-042-...", "source_type": "spec", "content_summary": "..."},
    {"source_file": "specs/SPEC-043-...", "source_type": "spec", "content_summary": "..."}
  ],
  "created_docs": [
    {"file": "tasks/TASK-001-...", "candidate": {"proposed_id": "...", "source": "SPEC-042 AC-1..."}},
    {"file": "tasks/TASK-002-...", "candidate": {"proposed_id": "...", "source": "SPEC-042 AC-3..."}}
  ],
  "inventory": {...},
  "coverage_rules": [
    "Every spec AC maps to at least one task step",
    "Every task has a verification mapping to its spec",
    "No task assumes infrastructure that no other task creates"
  ]
}
```

## Process

1. **Read each coverage rule.**

2. **For each rule, check compliance:**
   - "Every spec AC maps to at least one task step" → Read each spec's ACs from `requirements`, check each AC appears in at least one created task's `source` or `content_outline`
   - "Every task has a verification mapping" → Check each created doc references back to its spec
   - "No task assumes infrastructure that no other task creates" → Check each created doc's `needs` against what other docs create + the inventory

3. **Report gaps** — specific, actionable:
   - "SPEC-043 AC-4 (handle invalid placement) has no implementing task"
   - "TASK-003 assumes gdextension is configured but no task creates this setup"
   - "No task covers SPEC-042's failure path (AC-7)"

4. **Report unverifiable assumptions** — carried forward from the propose phase.

## Output

Write `.reviews/seed/result.json`:

```json
{
  "coverage": "partial",
  "gaps": [
    {
      "type": "missing_task",
      "description": "SPEC-043 AC-4 (handle invalid placement) has no implementing task",
      "source": "specs/SPEC-043-...",
      "severity": "HIGH"
    },
    {
      "type": "unmet_dependency",
      "description": "TASK-003 needs signal_registry entry for 'construction_started' but no task creates it",
      "source": "tasks/TASK-003-...",
      "severity": "MEDIUM"
    }
  ],
  "assumptions_remaining": [
    {"assumption": "Signal registry has construction_started", "status": "unverified"}
  ],
  "stats": {
    "requirements_checked": 5,
    "fully_covered": 4,
    "partially_covered": 1,
    "uncovered": 0
  }
}
```

If `gaps` is empty → `"coverage": "complete"`. seed.py proceeds to report.
If `gaps` is non-empty → `"coverage": "partial"`. seed.py enters fill_gaps phase, sending each gap back to `/scaffold-seed-propose` for additional candidates.

## Principles

- **Be specific about gaps.** "Missing coverage" is useless. "SPEC-043 AC-4 has no task" is actionable.
- **Check dependencies, not just content.** A task that exists but can't run because its dependency isn't met is a gap.
- **Don't fabricate coverage.** If you're not sure whether a task covers an AC, call it a gap. Better to over-report than miss something.
- **Assumptions are gaps until verified.** An assumption that "the signal exists" is a gap if no doc creates that signal.

## What NOT to Do

- **Don't create files or propose candidates.** You're verifying, not generating.
- **Don't read files beyond what's in action.json.** The summaries are your context.
- **Don't skip rules.** Check every coverage rule even if results look good.

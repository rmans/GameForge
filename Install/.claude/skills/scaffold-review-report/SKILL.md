---
name: scaffold-review-report
description: "Write the review log and report summary after document review completes. Reads action.json for session data. Writes review log to decisions/review/. Writes result.json. Shared by /scaffold-iterate and /scaffold-fix."
argument-hint: (called by review dispatchers — not user-invocable)
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Write Review Report

This skill is called by the `/scaffold-iterate` dispatcher when the review is complete. It synthesizes across all passes and adjudications to produce the final review log and summary.

## Input

Read `.reviews/iterate/action.json`:

```json
{
  "action": "report",
  "session_id": "...",
  "layer": "systems",
  "target": "design/systems/SYS-005-construction.md",
  "target_name": "SYS-005 — Construction",
  "iterations_completed": 2,
  "max_iterations": 10,
  "changes_applied": 5,
  "adjudications": [
    {
      "pass": "l3",
      "section": "### Purpose",
      "issue": { "severity": "HIGH", "description": "..." },
      "outcome": "accept",
      "reasoning": "..."
    }
  ],
  "escalations": [
    {
      "section": "### Owned State",
      "issue": { "description": "..." },
      "question": "...",
      "options": ["a) ...", "b) ...", "c) ..."]
    }
  ],
  "resolved_root_causes": ["...", "..."],
  "final_questions": [
    { "name": "Biggest Ownership Problem", "prompt": "The boundary most likely to cause confusion..." },
    { "name": "Primary Rework Risk", "prompt": "What part is most likely to need rework..." }
  ],
  "identity_check": {
    "questions": ["If this system stopped running, what state would freeze?", "..."]
  },
  "rating": {
    "scale": 5,
    "descriptions": { "1": "fundamentally broken...", "5": "strong design..." }
  },
  "log_name": "ITERATE-systems-SYS-005-2026-03-22.md",
  "log_path": "scaffold/decisions/review/ITERATE-systems-SYS-005-2026-03-22.md"
}
```

## Process

### 1. Answer Final Questions

For each entry in `final_questions`, synthesize across all adjudications to write a concrete answer. Don't be generic — reference specific issues, sections, and decisions from the review.

### 2. Answer Identity Check (if present)

For each question in `identity_check.questions`, answer based on what you learned during the review. These cut through polished wording — be honest.

### 3. Assign Rating

Using the `rating.descriptions` scale, assign a rating justified by the highest-severity accepted issues. A 4 or 5 requires no major unresolved problems. A 1 or 2 requires major issues.

### 4. Build Per-Pass Summary

Tally by pass level:

| Pass | Issues | Accepted | Rejected | Escalated |
|------|--------|----------|----------|-----------|
| L3 (subsections) | N | N | N | N |
| L2 (sections) | N | N | N | N |
| L1 (document) | N | N | N | N |

### 5. Write Review Log

Write the review log to `log_path` using this structure:

```markdown
# Review Log: [log_name]

> **Layer:** [layer]
> **Target:** [target_name]
> **Date:** YYYY-MM-DD
> **Iterations:** N
> **Changes Applied:** N
> **Rating:** N/5

## Final Questions

### [Question Name]
[Answer]

### Identity Check
[Answers to identity check questions]

## Per-Pass Summary

| Pass | Issues | Accepted | Rejected | Escalated |
|------|--------|----------|----------|-----------|
| ... |

## Adjudication Log

| # | Pass | Section | Severity | Issue | Outcome | Reasoning |
|---|------|---------|----------|-------|---------|-----------|
| ... |

## Escalations

[List of unresolved escalations with questions and options]

## Resolved Root Causes

[List of locked root causes]
```

### 6. Update Review Index

Add a row to `scaffold/decisions/review/_index.md`.

## Output

Write `.reviews/iterate/result.json`:

```json
{
  "log_written": "scaffold/decisions/review/ITERATE-systems-SYS-005-2026-03-22.md",
  "index_updated": true,
  "rating": 4,
  "rating_reason": "Clear ownership, good behavioral coverage, minor gaps in failure states.",
  "report_summary": "## System Review Complete: SYS-005 — Construction\n\n### Biggest Ownership Problem\n..."
}
```

The `report_summary` field is what the dispatcher displays to the user.

## Principles

- **Be specific, not generic.** "Ownership is mostly clear" is useless. "The boundary between ConstructionSystem's build_progress and ResourceSystem's reserved_materials is the most likely conflict point" is useful.
- **Reference actual issues.** The answers should trace back to specific adjudications.
- **Be honest about the rating.** Don't inflate because most issues were minor. Don't deflate because one issue was scary. Weight by what was actually resolved vs what remains.

## What NOT to Do

- **Don't re-adjudicate issues.** The decisions are made. Report them.
- **Don't edit the target document.** That was `/scaffold-review-apply`'s job.
- **Don't run additional review passes.** The review is over.

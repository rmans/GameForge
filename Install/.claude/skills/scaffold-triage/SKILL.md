---
name: scaffold-triage
description: "Resolve human-required issues from fix/iterate review passes. Presents issues as decision checklists (split, merge, reassign, defer). Replaces scaffold-triage-specs and scaffold-triage-tasks."
argument-hint: "<layer> <SLICE-###>"
allowed-tools: Read, Write, Edit, Grep, Glob
user-invocable: true
---

# Triage — Decision Resolution

Resolve human-required issues from review passes: **$ARGUMENTS**

Collects unresolved issues from fix and iterate review logs for a slice. Presents each as a decision with concrete options. Records decisions in a triage log.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<layer>` | Yes | — | What to triage: `specs`, `tasks` |
| `<SLICE-###>` | Yes | — | Which slice's issues to resolve |

## Process

1. Read review logs for the slice's specs or tasks
2. Collect unresolved issues (escalated, ambiguous, coverage gaps)
3. Present each as a numbered decision with options (a/b/c)
4. Record decisions in `decisions/triage-log/TRIAGE-[layer]-SLICE-###.md`
5. Apply decisions (splits, merges, reassignments) via `/scaffold-review-apply`
6. Report what was decided and what changed

## Usage

```
/scaffold-triage specs SLICE-001    ← resolve spec-level issues
/scaffold-triage tasks SLICE-001    ← resolve task-level issues
```

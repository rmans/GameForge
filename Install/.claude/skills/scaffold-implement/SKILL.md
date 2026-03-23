---
name: scaffold-implement
description: "Implement tasks end-to-end. Orchestrated by implement.py — smart context loading, step-by-step code generation, file manifest tracking, retry loops with limits. Replaces scaffold-implement-task."
argument-hint: "<TASK-###> [--max-retries N] [--cri N]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
user-invocable: true
---

# Implement Task — Dispatcher

Implement a task end-to-end: **$ARGUMENTS**

This skill is a **thin dispatcher** backed by `implement.py`. Claude only does one thing at a time — plan one task, write one step, review one file. Python tracks the file manifest, manages retry loops, and sequences the phases.

| Sub-skill | What it does |
|-----------|-------------|
| `/scaffold-implement-plan` | Read context, produce implementation outline |
| `/scaffold-implement-code` | Write code for one task step |
| `/scaffold-add-regression-tests` | Add test coverage (existing skill) |
| `/scaffold-build-and-test` | Build and run tests (existing skill) |
| `/scaffold-code-review` | Adversarial code review (existing skill) |
| `/scaffold-sync-reference-docs` | Sync scaffold docs with code changes (existing skill) |
| `/scaffold-complete` | Mark task Complete (existing skill) |

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<TASK-###>` | Yes | — | Task to implement (e.g., `TASK-004`) |
| `--max-retries` | No | 3 | Maximum build retry attempts before reporting stuck |
| `--cri` | No | 10 | Code review iterations (stops early if no changes) |

## How It Works

```
implement.py orchestrator
│
├── Phase 1: Plan
│   ├── Smart context loading (only reads what this task needs)
│   └── /scaffold-implement-plan → 5-10 line outline
│
├── Phase 2: Code (one step at a time)
│   ├── For each task step:
│   │   └── /scaffold-implement-code → writes code, reports files
│   └── File manifest accumulates automatically
│
├── Phase 3: Test
│   └── /scaffold-add-regression-tests → adds test coverage
│
├── Phase 4: Build
│   ├── /scaffold-build-and-test
│   ├── If FAIL → retry (up to --max-retries)
│   └── If stuck → report, stop
│
├── Phase 5: Review
│   ├── /scaffold-code-review for each changed file
│   └── If review changed files → Phase 6 (rebuild)
│
├── Phase 6: Rebuild (conditional)
│   ├── /scaffold-build-and-test with updated manifest
│   └── Same retry logic as Phase 4
│
├── Phase 7: Sync
│   └── /scaffold-sync-reference-docs → update scaffold docs
│
└── Phase 8: Complete
    └── /scaffold-complete → mark task Complete, report
```

## Execution

### Step 1 — Preflight

```bash
python scaffold/tools/implement.py preflight --task TASK-004
```

Checks: task exists, status is Draft/Approved, dependencies are Complete.

### Step 2 — Dispatch Loop

```bash
python scaffold/tools/implement.py next-action --task TASK-004 [--max-retries 3] [--cri 10]
```

Then loop:

```
loop:
  read action.json
  switch action.type:

    "plan":
      call /scaffold-implement-plan
      python implement.py resolve --session <id>

    "code":
      call /scaffold-implement-code
      python implement.py resolve --session <id>
      # repeats for each task step

    "test":
      call /scaffold-add-regression-tests
      python implement.py resolve --session <id>

    "build":
      call /scaffold-build-and-test
      python implement.py resolve --session <id>
      # if fail → retry or stuck

    "review":
      run iterate.py --reviewer code --layer code --target <file>
      # uses same iterate pattern as doc review, but with code-review.py as LLM backend
      # routes through /scaffold-review-adjudicate for each issue
      python implement.py resolve --session <id>

    "sync":
      call /scaffold-sync-reference-docs
      python implement.py resolve --session <id>

    "complete":
      call /scaffold-complete
      python implement.py resolve --session <id>

    "stuck":
      report error to user, break

    "done":
      break
```

### Step 3 — Summary

Display: files created/modified, tests added, build status, review stats, completion status.

## What implement.py Manages

- **File manifest** — accumulates files across all phases (code, test, review). Never lost.
- **Smart context** — reads task type, only loads relevant docs (no loading signals for a UI task)
- **Step sequencing** — one task step per code action. Claude only thinks about one step.
- **Retry limits** — build fails 3 times → reports stuck, doesn't loop forever
- **Review file tracking** — if code review modifies files, manifest updates and rebuild triggers

## Rules

- **One step at a time.** Claude writes code for one numbered step per exchange.
- **File manifest is authoritative.** Every file created or modified goes in the manifest.
- **Retry has limits.** 3 build failures → stuck report. No infinite loops.
- **Code review changes trigger rebuild.** If review modifies code, build runs again.
- **Dependencies must be Complete.** implement.py checks before starting.

---
name: scaffold-implement
description: "Implement tasks end-to-end. Orchestrated by implement.py — smart context loading, step-by-step code generation, file manifest tracking, build/test/complete handled in Python. Replaces scaffold-implement-task."
argument-hint: "<TASK-###> [--max-retries N] [--cri N]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
user-invocable: true
---

# Implement Task — Dispatcher

Implement a task end-to-end: **$ARGUMENTS**

This skill is a **thin dispatcher** backed by `implement.py`. Claude only does one thing at a time — plan one task, write one step, fix one build error. Python tracks the file manifest, runs builds, handles completion.

| Sub-skill / Tool | What it does |
|------------------|-------------|
| `/scaffold-implement-plan` | Read context, produce implementation outline |
| `/scaffold-implement-code` | Write code for one task step (including tests) |
| `utils.py build-test` | Build and run tests (Python — no skill needed) |
| `iterate.py --reviewer code` | Code review via external LLM (same pattern as doc review) |
| `utils.py sync-refs` | Sync scaffold docs with code changes (Python) |
| `utils.py complete` | Mark task Complete with upstream ripple (Python) |

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
│   └── /scaffold-implement-plan → 5-10 line outline
│
├── Phase 2: Code (one step at a time)
│   └── /scaffold-implement-code → writes code, reports files
│
├── Phase 3: Test
│   └── implement.py test phase → adds test coverage
│
├── Phase 4: Build (Python — runs directly, no skill)
│   ├── utils.py build-test → scons, lint, tests
│   ├── If FAIL → build_failed action → Claude fixes → retry
│   └── If stuck (3 attempts) → report, stop
│
├── Phase 5: Review
│   └── iterate.py --reviewer code → adversarial code review
│
├── Phase 6: Rebuild (conditional, Python)
│   └── utils.py build-test → if review changed code
│
├── Phase 7: Sync
│   └── utils.py sync-refs → update scaffold docs
│
└── Phase 8: Complete (Python — runs directly, no skill)
    └── utils.py complete → status update, rename, index
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
      # build runs automatically in Python after this

    "review":
      iterate.py --reviewer code handles the review loop
      python implement.py resolve --session <id>
      # rebuild runs automatically in Python if files changed

    "sync":
      call /scaffold-sync-reference-docs
      python implement.py resolve --session <id>
      # complete runs automatically in Python after this

    "build_failed":
      Claude reads the error, fixes the code
      python implement.py resolve --session <id>
      # build retries automatically

    "stuck":
      report error to user, break

    "done":
      display results, break
```

### Step 3 — Summary

Display: files created/modified, tests added, build status, review stats, completion status.

## What implement.py Manages

- **File manifest** — accumulates files across all phases. Never lost.
- **Smart context** — reads task type, only loads relevant docs.
- **Step sequencing** — one task step per code action.
- **Build/test** — runs directly via utils.py. No skill overhead.
- **Retry limits** — 3 build failures → stuck report.
- **Completion** — runs directly via utils.py. Status update, rename, index.

## What the Dispatcher Handles

Only actions that need Claude's judgment come to the dispatcher:
- **plan** — Claude reads context and plans
- **code** — Claude writes code for one step
- **test** — Claude adds regression tests
- **review** — Claude adjudicates code review issues
- **sync** — Claude updates scaffold docs
- **build_failed** — Claude reads error and fixes code

Mechanical operations (build, complete, reorder) run in Python.

## Rules

- **One step at a time.** Claude writes code for one numbered step per exchange.
- **File manifest is authoritative.** Every file created or modified goes in the manifest.
- **Retry has limits.** 3 build failures → stuck report.
- **Build and complete are Python.** No skill overhead for mechanical operations.
- **Dependencies must be Complete.** implement.py checks before starting.

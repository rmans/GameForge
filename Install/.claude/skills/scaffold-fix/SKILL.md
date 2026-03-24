---
name: scaffold-fix
description: "Mechanical document cleanup dispatcher. Routes between local-review.py (Python orchestrator) and shared review sub-skills. Runs pattern-based checks in Python, routes judgment calls to Claude. Handles all document layers."
argument-hint: "<layer> [target] [--sections \"Identity,Player Experience\"] [--iterations N]"
allowed-tools: Read, Write, Grep, Glob, Bash
user-invocable: true
---

# Mechanical Document Fix — Dispatcher

Run mechanical cleanup on scaffold documents: **$ARGUMENTS**

This skill is a **thin dispatcher**, identical in pattern to `/scaffold-iterate`. It routes between `local-review.py` (Python orchestrator) and shared review sub-skills.

The difference from iterate: fix runs **internal checklists** (regex, pattern matching) instead of calling an external LLM reviewer. Mechanical checks (missing sections, glossary violations, stale markers) are auto-fixed in Python. Judgment checks (is this section too vague?) route to Claude via the same `/scaffold-review-adjudicate` sub-skill.

| Sub-skill | What it does |
|-----------|-------------|
| `/scaffold-review-adjudicate` | Judge one finding — accept fix, reject, or escalate |
| `/scaffold-review-apply` | Edit target files based on accepted changes |
| `/scaffold-review-report` | Write the fix log and summary |

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<layer>` | Yes | — | Layer to fix: `design`, `systems`, `spec`, `task`, `slice`, `phase`, `roadmap`, `references`, `style`, `input`, `engine`, `cross-cutting` |
| `[target]` | Depends | — | Target document or range. Required for layers with ranges (e.g., `SYS-001`, `SYS-001-SYS-043`). Optional for fixed-target layers. |
| `--sections` | No | all | Comma-separated `##` section names to check |
| `--iterations` | No | from config | Maximum fix-review passes |

## How It Works

```
local-review.py runs mechanical checks (Python)
  ├── Auto-fixable issues → apply directly (no adjudication)
  ├── Judgment issues → route to /scaffold-review-adjudicate
  └── Signals → collected and reported (never fixed)

After fixes applied → re-run checks → converge or iterate
```

## Execution

### Step 1 — Parse Arguments and Resolve Target

Same as `/scaffold-iterate` — read `target_pattern` from the YAML config, glob to resolve files, build work list.

### Step 2 — Preflight

```bash
python scaffold/tools/local-review.py preflight --layer <layer> --target <relative-path>
```

### Step 3 — Dispatch Loop

**Start the session:**
```bash
python scaffold/tools/local-review.py next-action --layer <layer> --target <relative-path> [--iterations N]
```

local-review.py runs all mechanical checks, builds a queue (auto-apply → judgment checks → judgment-apply → convergence → report), and writes the first `action.json`.

Then loop:

```
loop:
  read action.json
  switch action.type:

    "apply":
      call /scaffold-review-apply
      python local-review.py resolve --session <id>

    "adjudicate":
      call /scaffold-review-adjudicate
      python local-review.py resolve --session <id>

    "report":
      call /scaffold-review-report
      python local-review.py resolve --session <id>

    "done":
      break

    "blocked":
      report message to user, break
```

### Step 4 — Summary

Display the fix report.

## What local-review.py Manages

- **Mechanical checks** — regex, pattern matching, template comparison, glossary compliance, registration sync
- **Auto-fix application** — queues auto-fixable issues for `/scaffold-review-apply`
- **Judgment routing** — routes structural quality and clarity checks to `/scaffold-review-adjudicate`
- **Signal detection** — governance, ownership, cross-system, layer boundary signals
- **Convergence** — after fixes, re-runs checks. Stops when clean, stable, human-only, or limit reached
- **Cross-system pass** — for range reviews, runs cross-system signals after all individual docs fixed

## Check Categories

Each layer's YAML config defines three categories of checks:

### Mechanical Checks (Python)
Pattern-matchable, auto-fixable or user-flagged:
- Missing sections (template diff)
- Stale markers (SEEDED, TODO)
- Glossary NOT-column violations
- Registration gaps (index sync)
- Implementation language (code constructs in design docs)
- Table structure (missing columns)
- Filename/status sync

### Judgment Checks (Claude)
Require reading comprehension — routed to `/scaffold-review-adjudicate`:
- Section clarity (is Purpose concise enough?)
- Structural quality (are Player Actions numbered steps, not prose?)
- Specificity (are Edge Cases specific enough?)

### Signals (Detected, Reported)
Detected and collected for the iterate pass — never fixed:
- Governance (invariant, boundary, control model conflicts)
- Ownership (single-writer violations, authority mismatches)
- Cross-system (dependency asymmetry, orphan systems)
- Layer boundary (implementation/presentation detail in wrong layer)

## File Locations

| File | Lifetime | Purpose |
|------|----------|---------|
| `.reviews/fix/session-<id>.json` | Full fix session | Durable session state |
| `.reviews/fix/action.json` | One exchange | local-review.py → sub-skill instruction |
| `.reviews/fix/result.json` | One exchange | Sub-skill → local-review.py response |
| `scaffold/decisions/review/FIX-*` | Permanent | Fix log output |

## Range Reviews

For ranges (e.g., `SYS-001-SYS-043`):
1. Glob matching files, sort by ID.
2. For each document, run the full fix cycle.
3. After all documents, run cross-system signals pass.
4. Print combined summary.

## Rules

- **This skill never reads documents or makes judgments.** Sub-skills do that.
- **This skill never edits files.** `/scaffold-review-apply` does that.
- **Auto-fixes are safe mechanical operations.** They don't change meaning.
- **Judgment fixes require Claude's evaluation.** They go through adjudication.
- **Signals are never fixed.** They feed into `/scaffold-iterate`.
- **Only edit files in the editable_files list** from the layer config.
- **If local-review.py errors**, report and stop.

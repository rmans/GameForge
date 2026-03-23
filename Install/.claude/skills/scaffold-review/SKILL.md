---
name: scaffold-review
description: "Full document review — runs /scaffold-fix (mechanical cleanup) then /scaffold-iterate (adversarial review) automatically. Same sub-skills, chained."
argument-hint: "<layer> [target] [--focus \"concern\"] [--sections \"Identity,Player Experience\"] [--iterations N] [--max-exchanges N] [--fast]"
allowed-tools: Read, Write, Grep, Glob, Bash
user-invocable: true
---

# Full Document Review — Dispatcher

Run a complete review of scaffold documents: **$ARGUMENTS**

This skill chains `/scaffold-fix` (mechanical cleanup) then `/scaffold-iterate` (adversarial review) automatically. Same dispatcher pattern, same shared sub-skills. The document gets mechanically cleaned first, then the cleaned version goes to an external LLM for deep review.

```
/scaffold-review systems SYS-005

Phase 1: Fix (local-review.py)
  → mechanical checks → auto-apply → judgment checks → converge → fix report

Phase 2: Iterate (iterate.py → adversarial-review.py)
  → L3 subsections → apply → L2 sections → apply → L1 document → apply → converge → iterate report

Combined report
```

You can still run them independently:
- `/scaffold-fix systems SYS-005` — just mechanical cleanup
- `/scaffold-iterate systems SYS-005` — just adversarial review
- `/scaffold-review systems SYS-005` — both, chained

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<layer>` | Yes | — | Layer to review — any layer supported by both fix and iterate |
| `[target]` | Depends | — | Target document or range |
| `--focus` | No | — | Narrow the adversarial review (iterate phase) to a specific concern |
| `--sections` | No | all | Scope both fix and iterate to specific `##` section groups |
| `--iterations` | No | from config | Maximum iterations per phase |
| `--max-exchanges` | No | from config | Maximum exchanges per review call (iterate phase) |
| `--fast` | No | false | Batch L3 subsection reviews in iterate phase |

## Execution

### Step 1 — Parse Arguments and Resolve Target

Same as `/scaffold-fix` and `/scaffold-iterate`.

### Step 2 — Preflight

```bash
python scaffold/tools/review.py preflight --layer <layer> --target <relative-path>
```

Runs preflight for both fix and iterate. Both must pass.

### Step 3 — Dispatch Loop

**Start the session:**
```bash
python scaffold/tools/review.py next-action --layer <layer> --target <relative-path> [args]
```

review.py starts the fix phase by delegating to local-review.py. The dispatcher loop is identical:

```
loop:
  read action.json
  switch action.type:

    "apply":
      call /scaffold-review-apply
      python review.py resolve --session <id>

    "adjudicate":
      call /scaffold-review-adjudicate
      python review.py resolve --session <id>

    "scope_check":
      call /scaffold-review-scope-check
      python review.py resolve --session <id>

    "report":
      call /scaffold-review-report
      python review.py resolve --session <id>

    "phase_complete":
      log "Fix complete. Starting adversarial review..."
      python review.py resolve --session <id>
      # review.py transitions to iterate phase, writes next action

    "done":
      break

    "blocked":
      report message to user, break
```

The dispatcher doesn't know which phase is active — it just routes actions to sub-skills. review.py handles the phase transition internally.

### Step 4 — Summary

Display the combined report (fix summary + iterate summary).

## Phase Transition

When fix completes, review.py writes `{action: "phase_complete"}`. The dispatcher logs the transition message and calls `resolve`, which triggers review.py to start the iterate phase. The next `action.json` will be from iterate.py (the first L3 subsection adjudication).

The transition is seamless — the dispatcher loop never breaks. It just keeps routing actions.

## Rules

- **This skill never reads documents or makes judgments.** Sub-skills do that.
- **This skill never edits files.** `/scaffold-review-apply` does that.
- **Fix runs first, iterate runs second.** Always.
- **Both phases use the same sub-skills** — adjudicate, apply, scope-check, report.
- **If fix finds the doc is already clean**, iterate starts immediately.
- **If review.py errors**, report and stop.

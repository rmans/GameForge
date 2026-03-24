---
name: scaffold-review
description: "Full document review pipeline — runs /scaffold-fix (mechanical cleanup) then /scaffold-iterate (adversarial review) then /scaffold-validate (structural gate) automatically. Three phases, chained."
argument-hint: "<layer> [target] [--focus \"concern\"] [--sections \"Identity,Player Experience\"] [--iterations N] [--max-exchanges N] [--fast]"
allowed-tools: Read, Write, Grep, Glob, Bash
user-invocable: true
---

# Full Document Review — Dispatcher

Run a complete review of scaffold documents: **$ARGUMENTS**

This skill chains three phases automatically: `/scaffold-fix` (mechanical cleanup) → `/scaffold-iterate` (adversarial review) → `/scaffold-validate` (structural gate). Same dispatcher pattern, same shared sub-skills. The document gets mechanically cleaned, then reviewed by an external LLM, then validated as structurally sound.

```
/scaffold-review systems SYS-005

Phase 1: Fix (local-review.py)
  → mechanical checks → auto-apply → judgment checks → converge → fix report

Phase 2: Iterate (iterate.py → adversarial-review.py)
  → L3 subsections → apply → L2 sections → apply → L1 document → apply → converge → iterate report

Phase 3: Validate (validate.py)
  → structural checks → pass/fail/warn → validation verdict

Combined report with verdict
```

You can still run them independently:
- `/scaffold-fix systems SYS-005` — just mechanical cleanup
- `/scaffold-iterate systems SYS-005` — just adversarial review
- `/scaffold-validate --scope systems` — just structural validation
- `/scaffold-review systems SYS-005` — all three, chained

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

review.py starts the fix phase by delegating to local-review.py. The dispatcher loop is identical. Loop **continuously without pausing for user input** — the entire loop runs in one turn.

**File locations:** action.json and result.json are always at `scaffold/.reviews/review/` (NOT `.reviews/fix/` or `.reviews/iterate/` — review.py copies actions from sub-orchestrators to its own directory). Every action.json includes `review_session_id` — **always use that ID** when calling `review.py resolve`.

```
loop:
  read scaffold/.reviews/review/action.json
  switch action.type:

    "apply":
      call /scaffold-review-apply               ← follow the sub-skill instructions inline
      python review.py resolve --session <review_session_id>

    "adjudicate":
      call /scaffold-review-adjudicate          ← follow the sub-skill instructions inline
      python review.py resolve --session <review_session_id>

    "scope_check":
      call /scaffold-review-scope-check         ← follow the sub-skill instructions inline
      python review.py resolve --session <review_session_id>

    "self_review":
      Review the section yourself using action.section_content and action.questions.
      Apply the layer's action.rules. Use action.context_summary for reference.
      Write result.json: {"_self_review": true, "issues": [...]}
      Each issue: {"severity": "HIGH|MEDIUM|LOW", "section": "...", "description": "...", "suggestion": "..."}
      Be adversarial — find real problems, don't rubber-stamp.
      If no issues found, write: {"_self_review": true, "issues": []}
      python review.py resolve --session <review_session_id>

    "report":
      call /scaffold-review-report              ← follow the sub-skill instructions inline
      python review.py resolve --session <review_session_id>

    "no_issues":
      log action.message
      python review.py resolve --session <review_session_id>

    "phase_complete":
      log action.message
      python review.py next-action --layer <layer> --target <target> [args]

    "done":
      break

    "blocked":
      report message to user, break
```

**IMPORTANT:** Do NOT pause or wait for user input between loop iterations. Each sub-skill call means "follow that skill's instructions inline" — read action.json, do the work, write result.json, then immediately call resolve and continue the loop. The only time to stop is on "done" or "blocked".

The dispatcher doesn't know which phase is active — it just routes actions to sub-skills. review.py handles the phase transition internally.

### Step 4 — Summary

Display the combined report (fix summary + iterate summary + validation verdict).

## Phase Transitions

Two transitions happen during a full review:

**Fix → Iterate:** When fix completes, review.py writes `{action: "phase_complete", message: "Fix complete. Starting adversarial review..."}`. The dispatcher logs the message and calls `review.py next-action`. review.py sees `phase == "iterate"`, starts iterate.py.

**Iterate → Validate:** When iterate completes, review.py writes `{action: "phase_complete", message: "Adversarial review complete. Running validation gate..."}`. The dispatcher calls `review.py next-action`. review.py sees `phase == "validate"`, runs validate.py synchronously (one call, no sub-skill routing), and writes the final `done` action with the validation verdict.

Validate is the simplest phase — it runs all checks in one call and reports pass/fail/warn. No iteration, no adjudication, no file edits.

The final `done` action includes all three reports + the verdict:
```json
{
  "action": "done",
  "fix_report": "...",
  "iterate_report": "...",
  "validate_report": {"verdict": "PASS", "results": [...]},
  "verdict": "PASS",
  "blocking": false
}
```

## Rules

- **This skill never reads documents or makes judgments.** Sub-skills do that.
- **This skill never edits files.** `/scaffold-review-apply` does that.
- **Fix runs first, iterate second, validate third.** Always in this order.
- **Fix and iterate use the same sub-skills** — adjudicate, apply, scope-check, report.
- **Validate is read-only** — no sub-skills needed, runs in one call.
- **If fix finds the doc is already clean**, iterate starts immediately.
- **If validate returns FAIL**, the done action includes `blocking: true`. The dispatcher should warn the user.
- **If review.py errors**, report and stop.

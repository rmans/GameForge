---
name: scaffold-iterate
description: "Adversarial document review dispatcher. Routes between iterate.py (Python orchestrator) and sub-skills (adjudicate, apply, scope-check, report). Handles all scaffold document types — 18 layers covering every ranked doc, decision doc, glossary, and doc-authority."
argument-hint: "<layer> [target] [--focus \"concern\"] [--sections \"Identity,Player Experience\"] [--iterations N] [--max-exchanges N] [--signals \"...\"] [--fast]"
allowed-tools: Read, Write, Grep, Glob, Bash
user-invocable: true
---

# Adversarial Document Review — Dispatcher

Run an adversarial review of scaffold documents: **$ARGUMENTS**

This skill is a **thin dispatcher**. It does not read documents, make judgments, or edit files. It routes between `iterate.py` (Python orchestrator) and focused sub-skills:

| Sub-skill | What it does |
|-----------|-------------|
| `/scaffold-review-adjudicate` | Judge one issue — accept, reject, escalate, or pushback |
| `/scaffold-review-scope-check` | Evaluate scope guard tests on a proposed change |
| `/scaffold-review-apply` | Edit target files based on accepted issues |
| `/scaffold-review-report` | Write the review log and fill in final questions/rating |

Communication between iterate.py and sub-skills uses two temp files:
- **`action.json`** — iterate.py writes the next instruction (what to do + all context needed)
- **`result.json`** — sub-skill writes its output (decision, edits made, report content)

The dispatcher reads one, calls the appropriate sub-skill, reads the other, passes it back. That's it.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<layer>` | Yes | — | Layer to review: `design`, `systems`, `spec`, `task`, `slice`, `phase`, `roadmap`, `references`, `style`, `input`, `engine`, `adr`, `ki`, `dd`, `playtest-feedback`, `playtest-session`, `glossary`, `doc-authority` |
| `[target]` | Depends | — | Target document or range. Required for layers with ranges (e.g., `SYS-001`, `SPEC-001-SPEC-020`). Optional for fixed-target layers (e.g., `design` always reviews `design-doc.md`). |
| `--focus` | No | — | Narrow review to a specific concern within each pass |
| `--sections` | No | all | Comma-separated `##` section names to review (e.g., `"Identity,Player Experience"`). Scopes L3 and L2 passes to matching sections. L1 still runs in full. |
| `--iterations` | No | from config | Maximum outer loop iterations |
| `--max-exchanges` | No | from config | Maximum back-and-forth exchanges per review call |
| `--signals` | No | — | Design signals from the corresponding fix skill |
| `--fast` | No | false | Batch L3 subsection reviews by parent section instead of one-at-a-time. Fewer API calls, less granular. |

## Three-Pass Review Model

The review uses L3 (subsections) → L2 (sections) → L1 (document). Each pass builds on the previous — fix the bricks before judging the wall. Changes are applied after each pass level so later passes see improvements.

```
Default:    20 L3 calls → apply → 6 L2 calls → apply → 1 L1 call → apply (systems example)
--fast:      6 L3 calls → apply → 6 L2 calls → apply → 1 L1 call → apply
```

## Execution

### Step 1 — Parse Arguments and Resolve Target

Parse `$ARGUMENTS` to extract layer, target, and options.

To resolve a target like `SYS-005` to a file path, read the YAML config's `target_pattern` (e.g., `design/systems/SYS-*.md` for systems) and glob for the matching file. For range targets (e.g., `SYS-001-SYS-043`), glob all matches in the range and build a work list sorted by ID. For fixed-target layers (e.g., `design` → `target: design/design-doc.md`), the target is predetermined — no glob needed.

### Step 2 — Preflight

```bash
python scaffold/tools/iterate.py preflight --layer <layer> --target <relative-path>
```

Check the JSON output:
- `"status": "ready"` → proceed. Note any `skip_sections`.
- `"status": "blocked"` → report the message to the user and stop.

### Step 3 — Dispatch Loop

For each document in the work list, start the session then run the dispatch loop.

**Start the session** (once per document):
```bash
python scaffold/tools/iterate.py next-action \
    --layer <layer> --target <relative-path> \
    [--focus "..."] [--sections "..."] [--iterations N] [--max-exchanges N] [--fast]
```

This creates the session, calls the reviewer for the first section, and writes `action.json` with the first instruction. Then loop:

```
loop:
  read action.json
  switch action.type:

    "adjudicate":
      call /scaffold-review-adjudicate         ← reads action.json, writes result.json
      python iterate.py resolve --session <id>  ← reads result.json, writes next action.json
      # accept → scope_check action next
      # reject/escalate → next issue or next section
      # pushback → sends counter to reviewer, new adjudicate action

    "scope_check":
      call /scaffold-review-scope-check        ← reads action.json, writes result.json
      python iterate.py resolve --session <id>
      # pass → confirms accept, next issue or next section
      # fail → converts to reject, next issue or next section

    "apply":
      call /scaffold-review-apply              ← reads action.json, edits files, writes result.json
      python iterate.py resolve --session <id>
      # advances to next pass level; if changes + under limit → inserts verification pass

    "report":
      call /scaffold-review-report             ← reads action.json, writes review log + result.json
      python iterate.py resolve --session <id>  ← writes "done" action

    "no_issues":
      log action.message                            ← e.g., "No issues found in ### Purpose"
      python iterate.py resolve --session <id>      ← no result.json needed, advances to next section

    "done":
      break

    "blocked":
      report message to user, break
```

The dispatcher never reads `result.json` — it just calls the sub-skill (which writes `result.json`) then calls `resolve` (which reads it internally). Three lines per action type: call skill, call resolve, loop.

Escalated issues are collected during adjudication and presented in the final report — not surfaced mid-review.

### Step 4 — Summary

After the loop ends with `"done"`, display the report summary that `/scaffold-review-report` generated.

## What iterate.py Manages

The Python orchestrator owns all the logic the old 11 skills used to carry in their heads:

- **Pass sequencing** — L3 → apply → L2 → apply → L1 → apply
- **Section iteration** — walks through each ### and ## in YAML config order
- **Review calls** — calls adversarial-review.py, gets reviewer feedback
- **Review lock** — tracks resolved root causes, filters duplicates
- **Scope check routing** — after an accept, writes a scope_check action before confirming
- **Convergence** — after all passes + applies, checks if changes were made; if yes, rebuilds the queue for a verification pass; if no new issues on verification, stops
- **Session state** — persists everything in session JSON
- **Context files** — resolves and passes context to each review call
- **Verification pass** — after changes are applied, re-queues the affected pass levels. Only a pass with ZERO new issues counts as clean. iterate.py will not write `"done"` until a clean verification pass completes or the iteration limit is reached

## What Sub-Skills Handle

Each sub-skill reads `action.json`, does its focused job, writes `result.json`.

### /scaffold-review-adjudicate
- Reads the issue, the relevant section content, layer rules, and context
- Decides: accept, reject, escalate, or pushback (with counter-argument)
- If accept: includes a description of the proposed fix
- If pushback: includes the counter-argument text to send back to the reviewer

### /scaffold-review-scope-check
- Reads the proposed change and scope guard tests from the action
- Evaluates each test (upward leakage, downward leakage, survival test)
- Returns pass/fail per test with reasoning

### /scaffold-review-apply
- Reads the list of accepted issues with their fix descriptions
- Reads the target file
- Interprets each suggestion and makes the actual edits
- Returns what was changed (files, sections, line counts)

### /scaffold-review-report
- Reads the full session data (all adjudications, per-section summaries)
- Synthesizes across all passes to answer final questions
- Assigns the rating with justification
- Writes the review log to `scaffold/decisions/review/`
- Updates `scaffold/decisions/review/_index.md`

## File Locations

| File | Lifetime | Purpose |
|------|----------|---------|
| `.reviews/iterate/session-<id>.json` | Full review | Durable session state |
| `.reviews/iterate/action.json` | One exchange | iterate.py → sub-skill instruction |
| `.reviews/iterate/result.json` | One exchange | Sub-skill → iterate.py response |
| `scaffold/decisions/review/ITERATE-*` | Permanent | Review log output |

## Multi-Doc Layers

For style, input, references, engine:

```
For each doc in the layer:
  iterate.py runs L3 + L2 per-doc (with per-doc tailored questions)
  apply after each pass level

After all docs:
  iterate.py runs L1 cross-doc integration pass
  apply
```

The dispatcher doesn't need to know this — iterate.py handles it internally. The dispatcher just keeps reading `action.json` and routing.

## Range Reviews

For ranges (e.g., `SYS-001-SYS-043`):

1. Glob matching files, sort by ID.
2. Log the work list.
3. For each document, run the full dispatch loop (Steps 2-4).
4. After all documents, print combined summary.

## Rules

- **This skill never reads documents or makes judgments.** That's what sub-skills are for.
- **This skill never edits files.** That's what `/scaffold-review-apply` is for.
- **Clean up temp files** (action.json, result.json) after each exchange.
- **Sleep between API calls** as configured per layer.
- **If iterate.py errors**, report the error and stop — don't retry.
- **If a sub-skill errors**, report and let iterate.py decide next action.

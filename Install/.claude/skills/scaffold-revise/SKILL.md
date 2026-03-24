---
name: scaffold-revise
description: "Detect drift and revise scaffold docs from implementation feedback. Reads ADRs, KIs, triage logs, code review, playtest patterns. Classifies signals, auto-applies safe changes, escalates dangerous changes, dispatches restabilization. Replaces all 10 layer-specific revise skills."
argument-hint: "<layer> [--source PHASE-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
user-invocable: true
---

# Revise — Dispatcher

Detect drift and revise scaffold documents: **$ARGUMENTS**

This skill is a **thin dispatcher** backed by `revise.py`. It reads implementation feedback one signal at a time, classifies each as safe (auto-update) or dangerous (escalate), applies safe changes, presents escalations, then dispatches a restabilization loop (`/scaffold-review`).

| Sub-skill | What it does |
|-----------|-------------|
| `/scaffold-review-adjudicate` | Classify one signal: auto-update, escalate, or skip |
| `/scaffold-review-apply` | Apply safe auto-updates |
| `/scaffold-review-report` | Write revision summary |

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<layer>` | Yes | — | Layer to revise: `design`, `systems`, `references`, `engine`, `style`, `input`, `foundation`, `roadmap`, `phases`, `slices` |
| `--source` | No | auto-detect | What triggered the revision: `PHASE-###` (phase completed), `SLICE-###` (slice completed), `foundation-recheck` |
| `--signals` | No | — | Comma-separated signal filter (e.g., `ADR-007,KI:ownership`) |

## How It Works

```
revise.py orchestrator
│
├── Phase 1: Gather Feedback (Python)
│   ├── Scan ADRs, KIs, triage logs, code review, playtest patterns
│   ├── Filter by --source and --signals if provided
│   └── Build signal list
│
├── Phase 2: Classify (one signal at a time)
│   ├── For each signal:
│   │   └── /scaffold-review-adjudicate → auto-update | escalate | skip
│   └── Accumulate safe updates and escalations
│
├── Phase 3: Apply Safe Updates
│   └── /scaffold-review-apply → edit docs with auto-updates
│
├── Phase 4: Escalate (if any)
│   └── Present escalations to user with options
│
├── Phase 5: Restabilize
│   └── Dispatch /scaffold-review <layer> to fix + iterate + validate
│
└── Phase 6: Report
    └── /scaffold-review-report → revision summary
```

## Execution

### Step 1 — Preflight

```bash
python scaffold/tools/revise.py preflight --layer <layer>
```

### Step 2 — Dispatch Loop

```bash
python scaffold/tools/revise.py next-action --layer <layer> [--source PHASE-001] [--signals ADR-007]
```

Then loop:

```
loop:
  read action.json
  switch action.type:

    "impact_preview":
      present impact summary to user:
        "N signals found. M docs reference these signals:"
        list each signal ID → affected doc paths
      user acknowledges (or filters signals to skip)
      python revise.py resolve --session <id>

    "classify":
      call /scaffold-review-adjudicate
      python revise.py resolve --session <id>

    "apply":
      call /scaffold-review-apply
      python revise.py resolve --session <id>

    "escalate":
      present to user, collect decisions
      python revise.py resolve --session <id>

    "restabilize":
      action.reviews contains per-file targets with changed sections:
        [{ target: "SYS-003", sections: "Owned State,Dependencies" }, ...]
      for each entry in action.reviews:
        /scaffold-review <layer> <target> --sections "<sections>"
      python revise.py resolve --session <id>

    "report":
      call /scaffold-review-report
      python revise.py resolve --session <id>

    "done":
      break
```

## Classification

Each feedback signal gets one classification:

| Classification | Action | Example |
|---------------|--------|---------|
| `auto_update` | Apply immediately | Stale reference, renamed ADR, dependency entry |
| `escalate` | Human decision needed | Ownership shift, governance change, scope widening |
| `skip` | No action needed | Already addressed, not relevant to this layer |

Design-led drift (backed by ADR/user decision) → doc should catch up.
Implementation-led drift (unapproved divergence) → escalate, don't auto-update.

## Rules

- **One signal at a time.** Claude classifies one feedback item per exchange.
- **Design-led vs implementation-led.** Auto-update only for design-led changes.
- **Escalations present options.** Never auto-apply dangerous changes.
- **Restabilize after changes.** `/scaffold-review` runs to fix + iterate + validate.
- **This skill never reads docs or makes judgments.** Sub-skills do that.

---
name: scaffold-seed
description: "Dependency-aware document generation. Reads upstream docs + project state, proposes candidates one at a time, discovers dependencies, verifies coverage, creates files in order. Replaces all seed skill."
argument-hint: "<layer> [--target scope]"
allowed-tools: Read, Write, Grep, Glob, Bash
user-invocable: true
---

# Dependency-Aware Seed — Dispatcher

Generate scaffold documents from upstream context: **$ARGUMENTS**

This skill replaces all 9 `bulk-seed-*` skills with a single dispatcher that generates documents **one upstream requirement at a time**, discovers dependencies as it goes, verifies coverage after creation, and fills gaps.

The key difference from the old seed skill: Claude only thinks about one thing at a time. seed.py holds the full inventory (what exists, what's been created, the dependency graph) in session state — Python doesn't forget.

| Sub-skill | What it does |
|-----------|-------------|
| `/scaffold-seed-propose` | Propose candidates from one upstream requirement + project state |
| `/scaffold-seed-verify` | Check coverage after all candidates are created |
| `/scaffold-review-adjudicate` | User confirmation of candidate list |
| `/scaffold-review-apply` | Create files from templates |
| `/scaffold-review-report` | Summary of what was created |

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<layer>` | Yes | — | What to seed: `design`, `systems`, `references`, `engine`, `style`, `input`, `phases`, `slices`, `specs`, `tasks` |
| `--target` | No | — | Scope within layer (e.g., `SLICE-001` to seed specs for one slice) |
| `--auto-fill` | No | false | Fill coverage gaps automatically without asking. Default: present gaps for user decision (fill/defer/dismiss). |

## How It Works

```
seed.py orchestrator
│
├── Phase 1: Context Gathering (Python)
│   ├── Read upstream docs (design doc, systems, specs, engine...)
│   ├── Read project state (file system, engine config, existing docs)
│   ├── Detect testing tools (test frameworks, lint tools, CI setup)
│   ├── Build "what exists" inventory
│   └── Present inventory for user confirmation/correction
│
├── Phase 2: Candidate Proposal (one at a time)
│   ├── For each upstream requirement:
│   │   ├── /scaffold-seed-propose → proposes candidates + dependencies
│   │   ├── If dependency missing → propose prerequisite candidate
│   │   └── seed.py tracks all candidates + dependency graph
│   └── Topological sort → creation order
│
├── Phase 3: User Confirmation
│   ├── Present full candidate list with dependency graph
│   ├── Flag unverifiable assumptions
│   └── /scaffold-review-adjudicate → user confirms/adjusts/removes
│
├── Phase 4: Creation (dependency order)
│   ├── For each confirmed candidate:
│   │   ├── /scaffold-review-apply → create file from template + context
│   │   └── Update inventory with new file
│   └── Register in indexes
│
├── Phase 5: Coverage Verification
│   ├── /scaffold-seed-verify → check every requirement is covered
│   ├── Gaps found → loop back to Phase 2 for gap-filling proposals
│   └── No gaps → proceed to report
│
└── Phase 6: Report
    └── /scaffold-review-report → what was created, dependencies, assumptions
```

## Execution

### Step 1 — Preflight

```bash
python scaffold/tools/seed.py preflight --layer <layer>
```

### Step 2 — Dispatch Loop

**Start:**
```bash
python scaffold/tools/seed.py next-action --layer <layer> [--target scope]
```

seed.py builds the inventory, extracts upstream requirements, writes the first `propose` action. Then loop:

```
loop:
  read action.json
  switch action.type:

    "confirm_inventory":
      present detected project state (test frameworks, lint tools, CI, directories)
      user confirms, corrects, or adds missing tools
      python seed.py resolve --session <id>

    "review_existing":
      present what already exists for this layer
      user: confirm (seed only gaps), reseed (regenerate specific docs), or skip
      python seed.py resolve --session <id>
      # only gaps and reseeded docs go through the proposal phase

    "propose":
      call /scaffold-seed-propose
      python seed.py resolve --session <id>

    "confirm":
      call /scaffold-review-adjudicate      ← user confirms candidate list
      python seed.py resolve --session <id>

    "create":
      call /scaffold-review-apply           ← create file from template
      python seed.py resolve --session <id>

    "verify":
      call /scaffold-seed-verify
      python seed.py resolve --session <id>
      # gaps found → review_gaps (or fill_gaps if --auto-fill)
      # no gaps → report

    "review_gaps":
      call /scaffold-review-adjudicate      ← user decides: fill / defer / dismiss each gap
      python seed.py resolve --session <id>
      # fill gaps → propose → confirm → create → re-verify
      # all deferred/dismissed → report

    "report":
      call /scaffold-review-report
      python seed.py resolve --session <id>

    "done":
      break

    "blocked":
      report message to user, break
```

### Step 3 — Summary

Display what was created, the dependency graph, and any remaining assumptions.

## What seed.py Manages

- **Inventory** — what exists in the project (files, engine config, scaffold docs)
- **Upstream requirements** — extracted from source docs, processed one at a time
- **Candidate list** — accumulated across all propose calls, deduplicated
- **Dependency graph** — built as candidates are proposed, topologically sorted
- **Coverage tracking** — which requirements are covered, which have gaps
- **Assumption tracking** — what couldn't be verified from the inventory

## What Sub-Skills Handle

### /scaffold-seed-propose
- Receives ONE upstream requirement + full inventory + existing candidates
- Proposes candidate docs with dependency analysis
- Creates prerequisite candidates for missing dependencies
- Flags unverifiable assumptions

### /scaffold-seed-verify
- Receives ALL created docs + upstream requirements
- Checks coverage rules (every AC has a task, every mechanic has a system, etc.)
- Reports specific gaps with severity

### /scaffold-review-adjudicate (reused)
- User confirms the full candidate list
- Can remove, adjust, or add candidates

### /scaffold-review-apply (reused)
- Creates files from templates
- Fills content from upstream context
- Registers in indexes

### /scaffold-review-report (reused)
- Summary of what was created
- Dependency graph visualization
- Remaining assumptions

## Layers

| Layer | Upstream Sources | Creates |
|-------|-----------------|---------|
| `design` | project file system + user interview | design-doc.md (with Technical Stack from auto-detection) |
| `systems` | design-doc.md | SYS-### system designs |
| `references` | system designs | architecture, authority, interfaces, state-transitions, entity-components, resource-definitions, signal-registry, balance-params, enums |
| `engine` | architecture, system designs | 15 engine convention docs |
| `style` | design-doc, system designs | style-guide, color-system, ui-kit, interaction-model, feedback-system, audio-direction |
| `input` | design-doc, interaction-model | action-map, input-philosophy, bindings-kbm, bindings-gamepad, ui-navigation |
| `phases` | roadmap, design-doc | PHASE-### phase scope gates |
| `slices` | phase, system designs, interfaces | SLICE-### vertical slices |
| `specs` | slices, system designs, state-transitions | SPEC-### behavior specs |
| `tasks` | specs, engine docs, architecture | TASK-### implementation tasks |

### Design Layer (special)

`/scaffold-seed design` is different from other layers — it has no upstream docs to read (it IS the upstream). Instead:

1. **Scans the project** — engine, languages, test frameworks, build system, CI, dependencies
2. **Presents findings** — "I see Godot 4, GDScript, GUT, no C++. Correct?"
3. **Interviews the user** — one section group at a time (Identity, Shape, Control, etc.)
4. **Writes the design doc** — with Technical Stack pre-filled from the scan
5. **Verifies** — all sections filled, governance populated, scope honest
6. **Reviews** — fix + iterate + validate

This replaces `/scaffold-init-design`. The Technical Stack section becomes the authoritative source for what tools the project uses — all downstream seeds read it instead of guessing.

## Rules

- **This skill never reads documents or makes judgments.** Sub-skills do that.
- **This skill never creates files.** `/scaffold-review-apply` does that.
- **One requirement at a time.** Claude only sees one spec/system/phase per propose call.
- **Create prerequisites, don't work around them.** Missing dependency → create a task for it.
- **Verify after creation.** Coverage check catches what was missed.
- **Flag assumptions explicitly.** Unverifiable claims go in the report, not hidden in content.

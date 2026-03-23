# Scaffold

This is the document pipeline for your game. Every design decision, style rule, system behavior, interface contract, and implementation constraint lives here as a versioned markdown file with a clear authority rank.

## How to Use This

**If you're starting fresh**, follow [WORKFLOW.md](WORKFLOW.md) — it's a step-by-step recipe from design doc to code, with a skill command for each step.

**If you're mid-project**, use [_index.md](_index.md) to find the document you need. Every directory has its own `_index.md` — drill down, read only what you need, never load entire directories.

**If two documents conflict**, the higher-ranked document wins. See [doc-authority.md](doc-authority.md) for the full precedence chain.

## Key Files

| File | What It Does |
|------|-------------|
| [_index.md](_index.md) | Master entry point — directory map, ID system, retrieval protocol |
| [doc-authority.md](doc-authority.md) | Precedence rules — which document wins when they conflict |
| [WORKFLOW.md](WORKFLOW.md) | Step-by-step recipe — from design through implementation |
| [SKILLS.md](SKILLS.md) | Man-page reference — all skills with arguments, descriptions, and examples |

## The Pipeline

```
OUTER LOOP (architecture stability — runs between phases)
│
├─ Pre-Gate Context (Steps 1–6, once)
│   Design → Systems → References → Engine → Visual/UX → Inputs
│   (surface architectural pressure points)
│
├─ Foundation Architecture (Step 7)
│   Revise (no-op initial / dispatch on recheck) → fix (cross-doc integration) → validate (gate)
│
├─ INNER LOOP (planning + implementation — runs per slice)
│   │
│   ├─ Roadmap (two loops):
│   │   Loop 1: create → fix → iterate → validate (initial)
│   │   Loop 2: revise → fix → iterate → validate (after each phase)
│   │   - 20-section living document with capability ladder, phase boundaries, system coverage
│   │   - 13 deterministic validation checks, 5-topic adversarial review
│   │
│   ├─ Phases (two loops):
│   │   Loop 1: seed → fix → iterate → validate → approve (first phase)
│   │   Loop 2: revise (from feedback) → fix → iterate → validate → approve (next)
│   │   - Only one active (Approved) phase at a time
│   │   - Approval is a lifecycle gate (9 preconditions including escalation check and slice readiness)
│   │   - Approved phases stay Approved during implementation (scope refinement, not regression)
│   │
│   ├─ Per approved phase — Slices (two loops):
│   │   Loop 1: seed → fix → iterate → validate → approve (first slice)
│   │   Loop 2: revise (from feedback) → fix → iterate → validate → approve (next)
│   │   - Slices declare dependencies (Depends on: SLICE-###)
│   │   - Only one active (Approved) slice per phase at a time
│   │   - Lifecycle-aware seeding (fresh vs in-progress vs active phase)
│   │   - Approval is a lifecycle gate (8 preconditions, not a soft checklist)
│   │
│   ├─ Per approved slice:
│   │   Specs: seed → fix → iterate → triage → (repeat) → validate → approve
│   │       ↓
│   │   Tasks: seed → fix → iterate → triage → (repeat) → validate → reorder → approve
│   │       ↓
│   │   Implementation: code → tests → build → code review → docs → complete
│   │
│   └─ Feedback: ADRs, known issues, triage logs
│
├─ Feedback Absorption
│   Roadmap loop (revise→fix→iterate→validate) → phase loop (revise→fix→iterate→validate→approve)
│
└─ Foundation Recheck → resolve drift → next phase
```

The **Foundation Architecture** step (Step 7) follows a streamlined pipeline: revise → fix → validate. On initial pass, revise is a readiness check (no-op). On recheck after each phase completes, revise reads implementation feedback and dispatches revision loops to affected Step 1–6 docs (including `revise-design` if design drift is detected, which triggers the full Step 1 stabilization loop), then fix runs cross-doc integration and validate gates. It prevents the most expensive class of rewrite — discovering that identity, storage, save/load, or spatial assumptions were wrong after systems depend on them. Each foundation area must be Locked, Partial (bounded gap tracked in known-issues), or explicitly Deferred.

The top rows define the game. The bottom rows build it. Three feedback mechanisms close the loop:
- **ADRs** — when implementation reality conflicts with the plan, decisions feed back into upcoming phases, specs, and tasks.
- **Known Issues** — problems discovered during any stage that aren't yet decisions. Tracked centrally, read by all planning skills.
- **Triage Decision Logs** — persistent records of planning decisions and upstream changes. Read during phase transitions and by downstream approval/reorder skills.

## Design Philosophy

**Design for the final product, implement incrementally.** Specs describe final product behavior. Slices only control *when* that behavior is implemented, not *how* it is designed. Never introduce temporary designs that will require rework — prefer correct ownership, correct system boundaries, and correct contracts even if a slice only builds a subset.

## Stabilization Loops

**Design** (Step 1) follows a two-loop pattern — initial creation and post-implementation revision:

```
Loop 1 (initial):     init-design → fix-design → iterate-design → validate --scope design
Loop 2 (after each):  revise-design → fix-design → iterate-design → validate --scope design
```

The design doc is a singleton living document — the highest authority for player-facing intent and non-breakable design rules. Loop 2 is triggered from the outer loop (Step 14) when `revise-foundation --mode recheck` detects Step 1 drift, or manually after a phase/slice completes. `revise-design` classifies drift as design-led (intentional, ADR-backed) vs implementation-led (unapproved divergence) and auto-updates only safe mechanical changes — governance impacts are always escalated.

**Systems** (Step 2) follow the same two-loop pattern:

```
Loop 1 (initial):     bulk-seed-systems → fix-systems → iterate-systems → validate --scope systems
Loop 2 (after each):  revise-systems → fix-systems → iterate-systems → validate --scope systems
```

System designs define per-system ownership, behavior, and interaction boundaries. `revise-systems` reads ADRs, known issues, spec/task friction, and code review findings. It classifies drift as design-led vs implementation-led, auto-updates safe changes (dependencies, edge cases), and escalates ownership shifts and authority violations.

**References + Architecture** (Step 3) follow the same two-loop pattern across all 9 docs:

```
Loop 1 (initial):     bulk-seed-references → fix-references → iterate-references → validate --scope refs
Loop 2 (after each):  revise-references → fix-references → iterate-references → validate --scope refs
```

The reference layer (architecture, authority, interfaces, state-transitions, entity-components, resource-definitions, signal-registry, balance-params, enums-and-statuses) defines cross-system contracts and data shapes. `revise-references` reads ADRs, system doc changes, spec/task friction, and code review findings. It respects canonical direction (authority→entity-components, interfaces→signal-registry, state-transitions→enums), auto-updates safe changes (missing registrations, column updates, stale references), and escalates authority changes, architecture changes, contract changes, and state machine changes.

**Roadmap** follows the same two-loop pattern as phases:

```
Loop 1 (initial):     new-roadmap → fix-roadmap → iterate-roadmap → validate --scope roadmap
Loop 2 (after each):  revise-roadmap → fix-roadmap → iterate-roadmap → validate --scope roadmap
```

The roadmap is a singleton living document — no bulk-seed or approve gate. Validate and iterate serve as the quality gate before phase seeding. After each phase completes, the full revision loop (revise → fix → iterate → validate) ensures the roadmap stays structurally sound as it evolves. `revise-roadmap` handles the macro view, `revise-phases` handles the micro view. The roadmap uses Draft/Approved/Complete status vocabulary (no "Active" or "Planned") — `Current Phase` points to the Approved phase.

**Slices** use two loops — one for initial setup, one after each implementation cycle:

```
Loop 1 (fresh phase):  Seed → Fix → Iterate → Validate → Approve (first slice only)
Loop 2 (after each):   Revise → Fix → Iterate → Validate → Approve (next slice only)
```

Only one slice is Approved (active) per phase at a time, and only one phase is Approved (active) at a time. Later slices and phases stay Draft because implementation feedback may change them. Slices declare explicit dependencies (`Depends on: SLICE-###`) — all dependencies must be Complete before a slice can be approved. Seeding is lifecycle-aware at both layers: fresh roadmaps/phases get full seeding, existing ones get additive-only proposals.

**Phases** follow the same two-loop pattern:

```
Loop 1 (fresh roadmap): Seed → Fix → Iterate → Validate → Approve (first phase only)
Loop 2 (after each):    Revise → Fix → Iterate → Validate → Approve (next phase only)
```

Approved phases stay Approved during implementation. Scope refinement happens directly — no status regression. Only scope invalidation (contradicting completed slices) requires an ADR.

**Specs and tasks** go through the same stabilization pattern before implementation:

All four fix skills (`fix-phase`, `fix-slice`, `fix-spec`, `fix-task`) auto-fix mechanical issues and surface strategic issues for human decision. All four planning layers follow the same pipeline pattern: seed → fix → iterate → validate → approve.

```
Seed → Fix (mechanical auto-fix) → Review (read-only audit) → Iterate (adversarial review) → Triage (human decisions)
                                                                          ↓
                              ← Repeat until stable ←←←←←←←←←←←←←←←←←←←←
                                                                          ↓
                                                          Validate → Approve
```

**Stability conditions** (all four must be met):
1. No unresolved human-required issues remain
2. No new specs/tasks were created in the last triage pass
3. No merges or splits remain pending
4. Two consecutive iterate passes produce no new meaningful issues

Deferred issues with recorded decisions do not block stabilization.

## Document Authority (highest wins)

| Rank | Document | What It Controls |
|------|----------|-----------------|
| 1 | `design/design-doc.md` | Core vision, non-negotiables |
| 2 | `design/style-guide.md`, `color-system.md`, `ui-kit.md`, `glossary.md`, `interaction-model.md`, `audio-direction.md` | Visual identity, terminology, interaction model, audio direction |
| 3 | `inputs/*` | Player actions and bindings |
| 4 | `design/architecture.md`, `design/interfaces.md`, `design/authority.md` | Engineering conventions, contracts, data ownership |
| 5 | `design/systems/SYS-###`, `design/state-transitions.md` | Per-system behavior, state machines |
| 6 | `reference/*` | Signals, entities, resources, balance, enums/statuses |
| 7 | `phases/P#-###` | Scope and milestones |
| 8 | `specs/SPEC-###` | Atomic testable behaviors |
| 9 | `engine/*` | Engine constraints |
| 10 | `tasks/TASK-###` | Implementation steps |
| 11 | `theory/*` | Advisory only — never authoritative |

## Directory Overview

| Directory | Layer | Rank | What Goes Here |
|-----------|-------|------|---------------|
| `design/` | Canon | 1–5 | Vision, style, colors, UI, glossary, architecture, systems, interfaces, authority, state machines |
| `inputs/` | Canon | 3 | Action map, keyboard/mouse bindings, gamepad bindings, navigation, input philosophy |
| `reference/` | Reference | 6 | Signal registry, entity components, resource definitions, balance params |
| `decisions/` | History | — | ADRs, known issues, design debt, playtest feedback, triage decision logs |
| `phases/` | Scope | 7 | Roadmap, phase scope gates |
| `slices/` | Integration | — | Vertical slice contracts within phases |
| `specs/` | Behavior | 8 | Atomic behavior specs tied to slices |
| `tasks/` | Execution | 9 | Implementation tasks tied to specs |
| `engine/` | Implementation | 10 | Engine-specific constraints: coding, UI, input, scene, performance, simulation runtime, save/load, AI/task execution, data pipeline, localization, post-processing, implementation patterns |
| `theory/` | Advisory | 11 | Game design principles, UX heuristics, architecture patterns — no authority |
| `decisions/review/` | Tooling | — | Adversarial review logs from `/scaffold-iterate`, `/scaffold-iterate roadmap` (ITERATE-roadmap-*), `/scaffold-iterate phase` (ITERATE-phase-*), `/scaffold-iterate slice` (ITERATE-slice-*), `/scaffold-iterate spec`, `/scaffold-iterate task` |
| `art/` | Content | — | Generated art assets from art skills |
| `audio/` | Content | — | Generated audio assets from audio skills |
| `templates/` | Meta | — | Templates for all document types and engine docs |
| `tools/` | Tooling | — | Scripts and utilities (validate-refs.py, adversarial-review.py, code-review.py) |

## Decision Layer

The `decisions/` directory contains eight subdirectories for tracking planning knowledge:

| Directory | ID Format | Purpose | Lifecycle |
|-----------|-----------|---------|-----------|
| `architecture-decision-record/` | ADR-### | Committed design decisions | Proposed → Accepted → (Deprecated/Superseded) |
| `known-issues/` | KI-### | TBDs, gaps, conflicts, ambiguities | Open → Resolved |
| `design-debt/` | DD-### | Intentional compromises with payoff plans | Active → Paid Off |
| `playtest-feedback/` | PF-### | Playtester observations and patterns | Open → Resolved |
| `cross-cutting-finding/` | XC-### | Cross-document integrity issues | Open → Resolved |
| `code-review/` | (per review) | Adversarial code review logs | Written by code-review |
| `revision-log/` | REVISION-* | Drift detection and update records | Written by revise-* |
| `triage-log/` | TRIAGE-* | Spec/task triage decision records | Written by triage, read by approve/reorder |
| `review/` | ITERATE/FIX/REVIEW-* | Adversarial document review logs | Written by iterate-* |

**Flow:** Problem discovered → `known-issues/` → if resolved → ADR → propagated to planning docs.

## Validation

`/scaffold-validate` checks structural integrity across all scaffold documents:

| Scope | What It Checks |
|-------|---------------|
| `--scope refs` | Python script (system IDs, authority, signals, interfaces, states, glossary, bidirectional) + expanded checks (doc existence, section structure, column completeness, value validity, cross-doc consistency, duplicates, production chains) |
| `--scope design` | Design doc exists, section structure (10 core-required FAIL, rest WARN), weighted health, governance format (invariants, anchors, pressure tests, gravity, boundaries), system index sync, glossary compliance, ADR consistency, provisional markers, review freshness (13 checks) |
| `--scope systems` | System index, design-doc sync (file-canonical), status sync, section structure (9 core-required FAIL), core-section defaults, weighted health (50%/70%), owned state format, glossary compliance, dependency symmetry, owned state overlap (exact names only), dependency cycles (upstream graph), orphan detection, dependency table format, template drift, seeded markers, review freshness (16 checks). Supports `--range SYS-###-SYS-###`. |
| `--scope foundation` | Foundation docs exist, area coverage, area status, authority consistency, interface completeness, signal consistency, entity consistency, iterate freshness (8 checks) |
| `--scope roadmap` | Roadmap exists, structure (13 sections), vision sync, design pillars, ship definition, capability ladder sync, phase sync, order integrity, phase boundaries, system coverage, ADR currency, completed phases, current phase (13 checks) |
| `--scope phases` | Phase index, roadmap sync, order integrity, status sync, structure, entry chain, single-active-phase, system resolution, slice resolution, review freshness (10 checks) |
| `--scope slices` | Slice index, phase resolution, status sync, interface resolution, dependency resolution, dependency order, single-active-slice, review freshness |
| `--scope specs` | Spec index, spec-slice membership, system resolution, spec status sync, spec triage targets |
| `--scope tasks` | Task index, slice-task membership, status-filename sync, slice-table status, order integrity, task triage targets, reference file resolution |
| `--scope all` | Everything above |

Severity: PASS / FAIL / WARN / SKIP (maturity-aware — checks activate when their preconditions are met).

## Rules

1. **Authority is law.** Higher-ranked documents always win. Code never "works around" higher-level intent. To change a higher document, file an ADR.
2. **Layers don't mix.** Design docs describe *what*. Engine docs describe *how*. Theory docs advise. A single document never crosses layers.
3. **IDs are permanent.** Once assigned, an ID (`SYS-001`, `SPEC-003`, `TASK-012`) never changes, even if the document is renamed or moved.
4. **Single writer per variable.** Every piece of game data has exactly one owning system defined in `design/authority.md`. No system writes to another system's data without an ADR.
5. **ADRs are the feedback mechanism.** When implementation conflicts with design, file an ADR. ADRs feed back into the roadmap, re-scope phases, and update specs. Never silently deviate.
6. **Known issues are the problem registry.** When a problem is discovered but not yet resolved, file it in `decisions/known-issues/`. All planning skills read it. Resolution happens through ADRs.
7. **Triage decisions are classified.** Local decisions apply immediately. Architecture-impacting decisions get upstream actions or ADR stubs — the architecture layer must absorb them before the graph is fully stable. If a pending upstream action changes ownership, authority, cross-system contracts, state-machine meaning, persistence expectations, or other behavior-defining architecture, the spec/task graph is not stable until that action is resolved or explicitly deferred by the user.
8. **Theory informs, never dictates.** Documents in `theory/` provide advisory context. Skills read them when creating and reviewing documents, but they carry no authority.

## Creating Documents

Use the skill commands — they pre-fill from higher-authority documents and register in the correct `_index.md` automatically.

To create manually:

1. Pick the template from [templates/](templates/_index.md).
2. Assign the next sequential ID for that type.
3. Create the file in the correct directory (not in `templates/`).
4. Register it in the directory's `_index.md`.

## Retrieval Protocol

Never load entire directories. Follow this protocol:

1. Start at [_index.md](_index.md) to find the correct directory.
2. Open the directory's `_index.md` to find the specific document.
3. Read only the document(s) you need.
4. If two documents conflict, the higher-authority document wins.

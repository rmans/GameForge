---
name: scaffold-new-roadmap
description: Create the project roadmap by defining phases from start to ship. Proposes a phase skeleton from design context, maps systems to phases, validates ordering and coverage, then writes the roadmap. Use after design docs, systems, and reference docs are complete.
allowed-tools: Read, Edit, Write, Grep, Glob
---

# New Roadmap

Create the project roadmap at `scaffold/phases/roadmap.md`.

Instead of purely conversational phase-by-phase questioning, this skill proposes a phase skeleton from design context, lets the user refine it, then writes the roadmap with structural validation.

## Step 1 — Read Context

1. **Read `scaffold/phases/roadmap.md`** to check its current state. If already populated (not template defaults), stop: "Roadmap already exists. Use `/scaffold-fix-roadmap` to clean up or `/scaffold-revise-roadmap` after phase completion."
2. **Read `scaffold/design/design-doc.md`** — especially Core Fantasy, Design Pillars, Scope Reality Check, Core Loop, Secondary Loops, Content Structure, and Target Platforms.
3. **Read `scaffold/design/systems/_index.md`** and skim system files for maturity.
4. **Read `scaffold/design/architecture.md`** for foundation decisions.
5. **Read `scaffold/decisions/known-issues.md`**, **`scaffold/decisions/design-debt.md`**, and **`scaffold/decisions/playtest-feedback.md`** for open issues and patterns.
6. **If the design doc is empty or systems aren't designed**, stop: "Design doc and systems must be complete before roadmap planning. Run `/scaffold-new-design` and `/scaffold-bulk-seed-systems` first."

### Systems readiness signal

Check system maturity before planning:
- Count systems with substantive design content vs empty stubs.
- If >30% of systems are stubs, warn: "N systems in the index lack design content. Roadmap phases may be unstable until they are defined. Consider running `/scaffold-new-system` on stubs first."

## Step 2 — Extract Design Pillars and Ship Definition

### Design Pillars

Extract 3–5 design pillars from the design doc that every phase must preserve. These act as phase sanity checks.

### Ship Definition

Define what "done" looks like — the minimum viable product. Extract from the design doc's Scope Reality Check. This anchors the roadmap's endpoint.

## Step 3 — Propose Phase Skeleton

Based on the design context, propose an initial phase structure. Show the whole roadmap shape at once — don't fragment thinking into isolated phases.

**Phase count guardrail:** Most projects should have 3–7 phases. If the design context suggests more than 7, recommend merging. Fewer than 3 is probably too coarse.

Typical capability progression (suggest but adapt to the project):

| Phase | Capability Pattern | Example |
|-------|--------------------|---------|
| Foundation | Core loop proof — the smallest playable thing | "Player can establish and sustain a basic colony" |
| Systems | Primary systems create dynamic behavior | "Colonists react to environmental threats" |
| Content | Strategic depth emerges from system interaction | "Multiple colony strategies are viable" |
| Polish | Experience is readable, responsive, accessible | "Player can play comfortably at target quality" |
| Ship | Release-ready experience | "Full product delivered" |

Present the skeleton:

```
## Proposed Phase Skeleton

P1-001 [Name] — [Capability unlocked]
P2-001 [Name] — [Capability unlocked]
P3-001 [Name] — [Capability unlocked]
...

Does this structure match your vision, or should we adjust?
```

**Assign phase IDs immediately** — `P1-001`, `P2-001`, etc. Don't use temporary names that cause renaming chaos later.

Wait for user confirmation or adjustment before proceeding.

## Step 4 — Map Systems to Phases

For each system in the systems index, propose which phase introduces it. Present as a table:

```
## System Coverage Map

| System | Proposed Phase | Notes |
|--------|---------------|-------|
| SYS-001 — [Name] | P1-001 | Core loop dependency |
| SYS-002 — [Name] | P2-001 | Requires P1 foundation |
| SYS-003 — [Name] | — | Deferred (out of scope) |
```

**Every gameplay-facing or player-visible system must appear in at least one phase or be explicitly deferred.** Internal support systems (utility helpers, animation blending, accessibility layers) may emerge within slices later and don't need roadmap-level phase assignment. Flag uncovered gameplay systems.

Surface known issues and design debt that affect phase placement:
- "KI-### affects [system] — consider placing it in [phase] or earlier."
- "DD-### suggests [system] needs attention — scope into [phase]."

## Step 5 — Define Phase Details

For each confirmed phase, capture:

| Field | Question |
|-------|----------|
| Goal | "What does this phase prove?" (outcome-oriented, not task-oriented) |
| Capability Unlocked | "What new capability exists after this phase that did not exist before?" |
| Key Systems | (derived from Step 4 mapping) |
| Demo Scenario | "Walk through a 3–5 step narrative of what happens in a demo at the end of this phase." (Not just a deliverable name — a concrete scenario like: "Start colony → storm approaches → colonists seek shelter → exposed colonists take damage → colony survives.") |
| Success Metrics | 1–2 measurable signals that the phase succeeded. (e.g., "Colony sustains for 10 minutes", "Colonists reach shelter in >80% of storms.") These give the phase an objective finish line beyond subjective "feels done." |
| Risk Focus | "What uncertainty does this phase resolve?" |
| Deferred to later | "What problems are you intentionally NOT solving yet in this phase?" |
| Good enough definition | "What criteria let you move on from this phase without endless polishing?" |

**Phase boundary definition:** Each phase must define what it intentionally defers and what "good enough" looks like. Without explicit boundaries, phases expand until they become impossible milestones. The boundary prevents scope creep during slice generation and implementation.

**Behavior-not-systems test:** Phase goals must describe observable behavior, not internal systems. Apply the actor test: can the goal be phrased as "[Actor] can now [do something new]"? "Implement the event system" → reject (no actor, no observable behavior). "Colonists react to storms and seek shelter" → accept. Never name a phase after a system — systems belong inside phases, not as phases. If a goal isn't sliceable (can't generate vertical slices from it), ask the user to reframe.

**Sliceability count check:** Each phase should be able to generate 3–6 vertical slices. If fewer than 3, the phase may be too narrow (merge with adjacent). If you can easily list more than 6, the phase may be too broad (split). This is a planning heuristic, not a hard rule — but it catches both over-scoped and under-scoped phases early.

## Step 6 — Ordering Sanity Check

Before writing, validate:

1. **Dependency logic** — does each phase's goal depend only on capabilities delivered by earlier phases? Flag phases that assume work not yet done.
2. **Risk distribution** — are high-risk systems (architecturally novel, cross-cutting, untested) addressed early? A roadmap that defers all risky work to later phases is fragile.
3. **Foundation first** — is the first phase the smallest playable proof of the core loop?
4. **Capability progression** — does each phase build meaningfully on the previous one? Could you demo after every phase?

Report any issues and propose fixes.

## Step 7 — Roadmap Risk Analysis

Before finalizing, detect planning risks:

| Signal | What it means |
|--------|---------------|
| Phase without a demo deliverable | Phase may not be a real milestone |
| System appearing in >2 unrelated phases | Scope is scattered |
| Phase without a new capability | Phase may be infrastructure, not a milestone |
| Phase with >5 systems | Likely over-scoped |
| All risky systems in late phases | Fragile plan — discovery happens too late |

Surface any detected risks to the user.

## Step 8 — Write the Roadmap

Write `scaffold/phases/roadmap.md` with these sections:

1. **Header** (Authority, Layer, Conforms to, Status: Draft)
2. **Purpose**
3. **Vision Checkpoint** — Core Fantasy from design doc
4. **Design Pillars** — 3–5 principles every phase must preserve
5. **Ship Definition** — what "done" looks like
6. **Capability Ladder** — one-line capability per phase showing the progression
7. **Phase Overview** — table with Phase ID, Goal, Capability Unlocked, Status (all `Draft`), Key Deliverable
8. **Phase Boundaries** — for each phase: what it proves, what it intentionally defers, and what "good enough" looks like. This prevents phases from expanding into impossible milestones during slice generation and implementation.
9. **System Coverage Map** — which phase introduces each system
10. **Phase Ordering Rationale** — why phases are in this order
10. **Current Phase** — set to P#-001 with link (once phase file exists)
11. **Known Planning Risks** — risks detected in Step 7
12. **ADR Feedback Log** — empty (populated after phase completion)
13. **Known Issues Impact** — KIs that affect phase planning
14. **Design Debt Impact** — DD items that affect phase planning
15. **Completed Phases** — empty (populated after phase completion)
16. **Upcoming Phases** — brief descriptions of each phase beyond the first
17. **Revision History** — initial entry with today's date
18. **Phase Transition Protocol** — standard protocol for phase completion
19. **Rules** — living document, upcoming phases are tentative, ADR feedback, vision is constant

**Status model:** All phases start as `Draft` in the Phase Overview — not "Active" or "Planned". The phase lifecycle (Draft → Approved → Complete) begins when `/scaffold-approve-phases` runs.

## Step 9 — Report

```
## Roadmap Created

| Metric | Value |
|--------|-------|
| Phases defined | N |
| Systems covered | N / M (N deferred) |
| Planning risks detected | N |
| Systems readiness | N% designed |

### Capability Ladder
| Phase | Capability Unlocked |
|-------|--------------------|
| P1-001 | [capability] |
| P2-001 | [capability] |
| ... | ... |

### Next Steps
- Run `/scaffold-fix-roadmap` to clean up any mechanical issues
- Run `/scaffold-iterate roadmap` for adversarial review
- Run `/scaffold-validate --scope roadmap` to check structural integrity
- Run `/scaffold-bulk-seed-phases` to create phase scope gate documents
```

## Rules

- **Propose first, then refine.** Show the whole skeleton before drilling into details. Users plan better when they see the full shape.
- **Use the user's voice.** Capture intent faithfully — don't rewrite into generic project-management language.
- **If the user says "skip" or "later"**, leave a TODO marker and move on.
- **Phases must be outcome-oriented** ("prove the core loop works") not task-oriented ("implement 5 systems"). Reject task-oriented goals and ask the user to reframe.
- **Every system must be covered or explicitly deferred.** Uncovered systems cause downstream slice planning failures.
- **Phase IDs are assigned immediately.** Don't use temporary names.
- **All phases start as Draft.** The Approved/Complete lifecycle is managed by approve-phases and complete.
- **Known issues, design debt, and playtest feedback actively influence phase placement** — surface them during planning, don't just read them passively.
- **The roadmap is a living document** that updates after every phase completion via `/scaffold-revise-roadmap`.
- **Created documents start with Status: Draft.**

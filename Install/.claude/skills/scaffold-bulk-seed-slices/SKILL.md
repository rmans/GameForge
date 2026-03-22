---
name: scaffold-bulk-seed-slices
description: Read phases, systems, and interfaces to bulk-create vertical slice stubs with goals and integration points. Phase goals drive slice selection. Lifecycle-aware — behaves differently for fresh vs in-progress phases. Use after phases are defined.
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Seed Slices from Phases

Read all phases, system designs, and interface contracts to bulk-create vertical slice stubs. Phase goals are the primary driver — system designs and interfaces flesh out integration points, but only for what the phase needs to prove.

## Prerequisites

1. **Read `scaffold/design/design-doc.md`** — Core vision and game loops. Slices must trace back to phase goals that trace back to the design doc's vision.
2. **Read `scaffold/doc-authority.md`** — Document authority ranking and influence map. Use to resolve conflicts and understand how slices are influenced by upstream documents.
3. **Read `scaffold/phases/_index.md`** to get the list of registered phases.
4. **Read every phase file** in `scaffold/phases/` (Glob `scaffold/phases/P*-*.md`).
5. **Read the roadmap** at `scaffold/phases/roadmap.md` to understand phase ordering and priorities.
6. **Read the systems index** at `scaffold/design/systems/_index.md`.
7. **Read relevant system designs** from `scaffold/design/systems/`.
8. **Read the interfaces doc** at `scaffold/design/interfaces.md`.
9. **Read the authority doc** at `scaffold/design/authority.md` for data ownership boundaries.
10. **Read the slice template** at `scaffold/templates/slice-template.md`.
11. **Read the slices index** at `scaffold/slices/_index.md` to find the next available ID and check existing slices.
12. **Read all ADRs** — Glob `scaffold/decisions/ADR-*.md` — ADRs may have changed phase scope.
13. **Read known issues** at `scaffold/decisions/known-issues.md` — known issues may affect which slices are needed or what they must prove.
14. **If fewer than 1 phase is defined**, stop and tell the user to create phases first.

## Step 0 — Assess Phase Maturity

Before generating candidates, classify each phase by what already exists:

| Phase State | Existing Slices | Behavior |
|-------------|----------------|----------|
| **Fresh** | No slices exist for this phase | Full seeding pass — generate complete candidate set |
| **In-progress** | Has Draft slices only | Additive pass — propose new candidates around existing Drafts, flag overlaps |
| **Active** | Has at least one Approved slice | Additive-only — propose new candidates that fit around the established order. Warn that new slices will be inserted, not appended. |
| **Partially complete** | Has Complete slices | Additive-only — only propose candidates for uncovered phase proof items. Completed slices are fixed points in the order. |

**If a phase has Approved or Complete slices, do not reseed it as a fresh phase.** Present only additive or revision candidates and warn the user that the established order constrains where new slices can be inserted.

For each existing slice, read its file and classify:
- **Draft (bare)** — no specs or tasks seeded. Can be revised, merged, or replaced by candidates freely.
- **Draft (with artifacts)** — has seeded specs and/or tasks. Soft-fixed: can still be revised, but reshaping it requires downstream spec/task triage. Flag this cost when proposing changes that affect it.
- **Approved** — fixed in the order; candidates must work around it.
- **Complete** — fixed point; candidates must not re-prove what it already proved.

## Phase 1 — Derive Slice Candidates from Phase Goals

For each phase, the **phase goal and scope** are the primary drivers. System designs and interfaces are supporting evidence.

### 1a. Identify what the phase must prove

Read the phase's Goal, In Scope, Exit Criteria, Slice Strategy, Risk Focus, Phase Demo, System Readiness, and Architectural Constraints. Answer:
- What end-to-end experiences must be demonstrable by the end of this phase?
- What cross-system integrations must be proven working?
- What player-visible milestones does the phase deliver?

### 1b. Group into vertical slice candidates

For each end-to-end experience the phase must prove:
1. Identify the **system cluster** — which systems must work together for this experience.
2. Identify the **interface contracts** from `interfaces.md` that this experience exercises.
3. Identify the **authority boundaries** from `authority.md` that this experience crosses.
4. Verify the candidate is truly **vertical** — it must prove behavior across at least two participating systems, or across one primary system plus a player-visible reaction path mediated by another system or interface. If a scope item maps to a single system with no cross-boundary effects, combine it with related items.

**Do not seed slices for phase scope items that are purely internal to one system.** Those become specs within a vertical slice, not slices themselves.

### 1c. Filter weak candidates

Before ordering or presenting, reject candidates that fail quality checks:

| Weakness | Test | Action |
|----------|------|--------|
| **Not vertical** | Candidate touches only 1 system with no cross-boundary effects | Reject — combine with another candidate or drop |
| **Progress theater** | Candidate only validates trivial behavior (e.g., "data structure exists") with no cross-system reaction | Reject — ask: *if this passes, what important thing do we now know?* |
| **Fake vertical** | Candidate claims cross-system proof but nothing actually triggers the reaction chain (e.g., "RoomSystem detects rooms" but no building placement triggers it) | Reject — the slice isn't truly vertical |
| **Duplicate proof** | Candidate proves something an existing Complete or Approved slice already proved at the goal level | Reject — redundant certainty |
| **Unfalsifiable demo** | Candidate's demo could pass even if the real integration is broken (expected results too vague) | Revise demo before presenting, or reject if unrevivable |
| **Hidden prerequisite** | Candidate demo or goal assumes infrastructure, rules, or prior proofs not established by earlier slices, declared dependencies, or current phase scope | Reject — or force dependency declaration before presenting |

Present rejected candidates in a separate section so the user can override if they disagree.

### 1d. Define implementation order and dependencies

Slices within a phase usually follow a natural implementation order — unless a different order yields a stronger proof:
1. **Foundation slices first** — prove core data structures and system wiring work.
2. **Integration slices next** — prove systems communicate correctly.
3. **Feature slices after** — prove player-visible behavior works end-to-end.
4. **Polish slices last** — prove UI, feedback, and edge cases work.

This is a heuristic, not a required progression. Sometimes the strongest first slice is a small player-visible feature that also proves integration.

**Use temporary candidate labels (Candidate A, B, C...) during ordering.** Dependencies between candidates reference these labels, not SLICE-### IDs. IDs are assigned only after confirmation.

For each candidate, determine its dependency — which earlier candidates must be Complete before it can be approved:
- If a candidate builds on infrastructure or behaviors proven by an earlier candidate, declare the dependency using the temporary label.
- The first candidate in implementation order has dependency "—".
- A candidate may depend on zero, one, or multiple earlier candidates.
- If the phase has existing slices, candidates may depend on existing SLICE-### IDs (for Complete/Approved slices) or temporary labels (for other new candidates).

Present the suggested order and dependency graph to the user. Only the first slice will be approved initially — later slices stay Draft and may be revised after implementation feedback.

### 1e. Check ADR and known-issue impacts

For each slice candidate:
- Check whether any accepted ADRs affect the systems or interfaces this slice covers.
- Check whether any open known issues constrain or complicate the slice's proof goal.
- If ADRs or known issues affect a slice, annotate the candidate with the reference and impact.

### 1f. Check against existing slices

Before presenting candidates, compare against existing slices in `scaffold/slices/`:

**Overlap severity depends on downstream artifacts:**

| Existing Slice State | Overlap Risk | Presentation |
|---------------------|-------------|--------------|
| Draft, no specs | Low — merge/keep/skip decision | Standard overlap options |
| Draft, has seeded specs | Medium — merge requires spec reassignment | Warn: "Overlaps existing slice with seeded specs. Merging requires spec triage." |
| Approved, has approved specs | High — merge requires spec and possibly task rework | Escalate: "Overlaps existing slice with approved specs. Merging is expensive — recommend keep-separate or skip." |
| Complete | Redundant — candidate re-proves completed work | Default to skip unless the user has a specific reason |

Do not silently create near-duplicates.

**No SLICE-### IDs are consumed until the user confirms the full candidate set.** Overlap decisions, merges, ordering, and dependencies are all resolved on temporary labels first.

### 1g. Draft each candidate

For each candidate that passed filtering (1c):
- **Goal** — one sentence describing the end-to-end experience from the player's perspective.
- **Systems Covered** — which systems participate.
- **Depends on** — temporary labels for new candidates, or SLICE-### IDs for existing slices.
- **Integration Points** — which interfaces from `interfaces.md` are exercised, which authority boundaries are crossed.
- **Suggested Specs** — what behaviors need to work (these become spec candidates in Step 19).
- **Done Criteria** — testable conditions that prove the slice works.
- **Proof Value** — what uncertainty this slice reduces. Examples: proves risky integration, proves manual player loop, proves authority crossing, proves persistence safety, proves infrastructure dependency.
- **Demo Script Skeleton** — the player-visible walkthrough that proves the goal is met.

## Phase 2 — Present for Confirmation

Present all candidate slices to the user, organized by phase:

```
### Phase: P#-### — [Name] (State: Fresh / In-progress / Active / Partially complete)

**Phase goal:** [what this phase delivers]
**Existing slices:** [list with status, or "None"]
**Suggested implementation order:** [first → last, using temporary labels for new candidates]

Candidate A: [name]
- Goal: [one sentence]
- Proof value: [what uncertainty this reduces — e.g., proves risky integration, proves manual player loop]
- Depends on: [Candidate labels or existing SLICE-### IDs, or "—"]
- Systems: SYS-###, SYS-###
- Interfaces exercised: [list from interfaces.md]
- Authority crossings: [list from authority.md]
- ADR impacts: [if any]
- Known issue impacts: [if any]
- Existing slice overlap: [if any — with severity-rated merge/keep/skip options]

Candidate B: [name]
...

#### Rejected Candidates (user may override)
| Candidate | Reason | Override? |
|-----------|--------|-----------|
| [name] | Progress theater — validates trivial behavior | User decides |
| [name] | Duplicate proof — SLICE-### already proves this | User decides |

If a rejected candidate is overridden by the user, present it with a warning banner in the confirmed set and require explicit confirmation before file creation. Overridden candidates do not silently re-enter the candidate set.

#### Coverage Assessment
✓ Phase proof items covered: [list — what certainty each candidate buys]
✓ Uncertainty reduced: [list — map each candidate's Proof Value to the phase risk it retires]
⚠ Phase proof items NOT covered: [list — these need slices or explicit deferral]
⚠ Duplicate proof items: [list — multiple candidates proving the same thing]
⚠ Risky proof items: [list — depend on assumptions not locked by architecture or earlier slices]
⚠ Systems in scope but not exercised by any slice: [list]
⚠ Interfaces not tested by any slice: [list]
```

Present decisions using the Human Decision Presentation pattern (see WORKFLOW.md). Each overlap, rejected candidate override, and ordering decision gets numbered options (a/b/c). Wait for the user's decisions on each issue before proceeding. **All decisions — including ordering, dependencies, and overlap resolutions — must be finalized before any SLICE-### IDs are assigned.**

### Cross-Phase Restraint

When seeding multiple phases in one run:
- **Current phase** (marked as current in `scaffold/phases/roadmap.md`) and **next phase** (immediately following in roadmap order) — generate concrete candidates with full detail.
- **Later phases** (2+ phases out from current in roadmap order) — generate coarser candidates unless the phase doc is already very mature (has detailed scope, exit criteria, and system references). Flag these as "provisional — will be revised when this phase is closer."

This prevents brittle future slices that revise heavily when the project catches up to them.

## Phase 3 — Create Slice Files

**Only after the user confirms the final candidate set, order, overlap decisions, and dependencies for each phase.**

For each confirmed candidate:

1. **Assign the next sequential SLICE-### ID** from `scaffold/slices/_index.md`.
2. **Convert temporary dependency labels** to the newly assigned SLICE-### IDs. Dependencies on existing slices keep their original IDs.
3. **Create** `scaffold/slices/SLICE-###-<name>_draft.md` using the slice template. Write substantive content for ALL sections — remove template HTML comments and replace with authored prose. No section should be left at template defaults.

   | Section | What to write | Minimum content |
   |---------|--------------|-----------------|
   | **Goal** | One sentence describing the end-to-end experience this slice delivers, from confirmed description | Complete sentence, player-perspective |
   | **Proof Value** | What uncertainty this slice reduces — why it matters for the phase | 1-2 sentences with concrete examples (e.g., "proves BuildingSystem → RoomSystem integration") |
   | **Assumptions** | What must already exist — infrastructure, systems, behaviors this slice depends on | At least 2 bullet points |
   | **Starting Conditions** | What must be true before the demo begins — makes demos reproducible | At least 2 conditions describing the pre-demo state |
   | **Specs Included** | Table of specs this slice covers — populate with suggested spec names | At least 1 row; specs not yet created may use descriptive names marked "TBD — create with `/scaffold-new-spec`" |
   | **Tasks** | Leave empty — tasks are seeded by `/scaffold-bulk-seed-tasks` after specs are defined | Empty table structure only |
   | **Integration Points** | How systems connect in this slice — reference interfaces.md | At least 1 integration point describing which systems cross and what data flows |
   | **Done Criteria** | What must be true for this slice to be complete — testable conditions | At least 2 verifiable criteria |
   | **Failure Modes This Slice Should Catch** | What breakage should be visible if this slice fails | At least 2 failure modes — a strong slice is defined by the bugs it would expose |
   | **Visible Proof** | What the tester should visibly see if the slice works — not logs or internal inspection | At least 2 observable outcomes |
   | **Demo Script** | Step-by-step walkthrough demonstrating the slice works end-to-end | At least 3 numbered steps with specific player actions and expected results |

   - Set `> **Depends on:**` from the confirmed dependency graph (SLICE-### IDs or "—").
4. **Register** the slice in `scaffold/slices/_index.md` with the phase reference, inserted at the correct position in the implementation order (not just appended). Existing Approved and Complete slices keep their relative order — newly created Draft slices are inserted around those fixed points according to the confirmed candidate order.

## Phase 4 — Report

Summarize what was seeded:
- Slices created: X total, across Y phases
- Per phase: how many slices, implementation order, which scope items they cover
- Specs suggested: X behavior specs to create next
- First slice to implement: SLICE-### (the one to approve first)

Flag any remaining gaps:
- Phase scope items not covered by any slice
- Systems in scope but not exercised by any slice
- Interfaces not tested by any slice
- ADRs or known issues that affect slice scope

Remind the user of next steps. Only the first slice goes through the full pipeline initially:
- Run `/scaffold-review-slice SLICE-###` on the first slice
- Run `/scaffold-iterate slice SLICE-###` for adversarial review
- Run `/scaffold-validate --scope slices` to check structural integrity
- Run `/scaffold-approve-slices SLICE-###` to approve the first slice for spec seeding
- Then run `/scaffold-bulk-seed-specs` for the approved slice's specs
- Later slices will be revised and approved one at a time after each implementation cycle

## Rules

- **Seeded files must contain substantive content, not template placeholders.** Every section that the skill populates (Goal, Systems Covered, Integration Points, Done Criteria, Proof Value, Demo Script Skeleton) must have real authored prose derived from phase goals and system designs. Do not leave pre-filled sections as TODO, HTML comment prompts, or single generic sentences. Remove template HTML comments from sections that receive authored content. A slice file where Goal is "TBD" or Done Criteria is the template's HTML comment has failed the seed.
- **Phase goals drive slice selection.** Derive candidates from what the phase must prove end-to-end, not from exhaustive system enumeration.
- **Never write without confirmation.** Present all proposed slices before creating files. All ordering, dependency, and overlap decisions must be finalized first.
- **No IDs until confirmation.** Use temporary candidate labels (A, B, C) during the confirmation phase. Assign permanent SLICE-### IDs only after the user confirms the final candidate set, order, and dependencies.
- **Slices must be vertical.** Every slice must prove behavior across at least two participating systems, or across one primary system plus a player-visible reaction path mediated by another system or interface.
- **Reject weak candidates before presentation.** Filter out progress theater, fake-vertical, duplicate-proof, and unfalsifiable candidates. Present rejections separately so the user can override.
- **Only the first slice gets approved initially.** Later slices stay Draft — they may be revised after implementation feedback.
- **Lifecycle-aware seeding.** If a phase already has Approved or Complete slices, do not reseed as a fresh phase. Present only additive candidates and respect the established order.
- **Overlap severity scales with downstream artifacts.** A candidate overlapping a Draft slice with no specs is a simple merge decision. A candidate overlapping an Approved slice with specs is an expensive planning decision. Surface the cost.
- **Design for the final product.** Slice boundaries should reflect the final architecture, not temporary scaffolding. Correct ownership and correct system boundaries matter even in early slices.
- **Preserve existing slices.** If slices already exist, add to them — don't overwrite or duplicate. Complete slices are fixed points.
- **Cross-phase restraint.** Early phases get concrete candidates. Later phases get coarser candidates unless the phase doc is already mature.
- **IDs are sequential and permanent** — never skip or reuse.
- **Integration points must reference real interfaces** from interfaces.md. Don't invent interfaces that don't exist.
- **Flag conflicts, don't resolve them.** If phase scope items can't be cleanly divided into slices, present the conflict to the user.
- **ADR and known-issue impacts must be noted.** Annotate affected candidates.
- **Created documents start with Status: Draft.**

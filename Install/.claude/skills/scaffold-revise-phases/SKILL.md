---
name: scaffold-revise-phases
description: Update remaining Draft phases based on implementation feedback from a completed phase. Reads ADRs, known issues, playtest patterns, triage logs, and foundation recheck results. Writes a persistent revision log. Also refines the active Approved phase's scope from feedback.
argument-hint: P#-### (the just-completed phase)
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Revise Phases

Update remaining phases based on what was learned from implementing: **$ARGUMENTS**

This skill is the feedback loop between phase completion and the next phase's planning. After a phase is Complete, ADRs, known issues, playtest patterns, triage decisions, and foundation recheck results may change what remaining phases need to deliver.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `P#-###` | Yes | — | The phase that was just completed. Feedback from its implementation drives the revision. |

## Preconditions

1. **Source phase exists** — glob `scaffold/phases/P#-###-*.md`. If not found, stop.
2. **Source phase is Complete** — verify `> **Status:**` is `Complete`. If not Complete, stop.
3. **Check for remaining phases** — if no Draft or Approved phases remain, switch to **report-only mode**: gather feedback and surface roadmap-level insights, but skip scope edits. The feedback loop is mandatory even at end-of-project.

## Step 1 — Gather Implementation Feedback

### 1a. ADRs filed during the phase

Glob `scaffold/decisions/ADR-*.md`. Filter to ADRs that:
- Reference systems delivered by the completed phase, or systems depended on by remaining phases
- Were created or accepted after the source phase was approved
- Appear in triage logs for slices in the completed phase

### 1b. Known issues discovered

Read `scaffold/decisions/known-issues.md`. Check for entries added or updated during the completed phase's implementation.

### 1c. Playtest feedback patterns

Read `scaffold/decisions/playtest-feedback.md`. Check for Pattern or ACT NOW entries that reference systems in scope for remaining phases.

### 1d. Triage decision logs

Glob `scaffold/decisions/triage-logs/TRIAGE-*SLICE-*.md` for slices in the completed phase. Check for upstream actions that affect other phases' scope.

### 1e. Foundation recheck results

Check whether `/scaffold-review-foundation --mode recheck` was run after phase completion. If a recheck log exists, read it for foundation drift that affects remaining phases.

### 1f. Prototype findings (advisory)


### 1g. Slice and spec review logs

Glob `scaffold/decisions/review/ITERATE-slice-SLICE-*.md` and `scaffold/decisions/review/REVIEW-slice-SLICE-*.md` for slices in the completed phase. Check for recurring issues, rejected scope, or integration pain that signals planning misalignment for remaining phases.

### 1h. Implementation friction signals

Check for signs of planning misalignment during the completed phase:
- Repeated slice splits (a slice was split after initial seeding)
- Heavy task reorder (reorder-tasks made large changes)

If detected, flag as implementation friction in the revision log. This doesn't block changes but surfaces design pressure that remaining phases should account for.

## Step 2 — Identify Affected Phases

**The next Approved phase** (if one exists) is the primary revision target. Scope refinement happens directly — the phase stays Approved.

**Remaining Draft phases** are secondary targets. Scope changes are applied normally.

**Later phases not yet in the roadmap** — record as roadmap notes only. Do not invent new phases. Do not detail phases not yet represented in the roadmap. Only describe the pressure or likely future need.

## Step 3 — Analyze and Classify Impact

For each affected phase, classify proposed changes:

### Direct-apply: Safe scope refinement
- **Narrowing scope** — defer items to a later phase based on what was learned
- **Sharpening exit criteria** — make them more precise based on implementation reality (must preserve or strengthen milestone meaning — never weaken rigor)
- **Adding ADR/KI references** — annotate scope with new constraints
- **Updating deliverables** — adjust based on what infrastructure now exists
- Applied immediately to both Approved and Draft phases. No user pause needed.
- A safe refinement may clarify, constrain, or sharpen, but must not weaken the approved phase's capability or reduce the rigor of its exit criteria.

### Confirmation-required: Scope widening
- **Adding systems or features** — implementation revealed gaps the phase must fill
- **Adding exit criteria** — new conditions must be met before the phase can complete
- Present with clear justification. Require user confirmation for Approved phases. Apply directly to Draft phases.

### Confirmation-required: Milestone weakening (Approved phase only)
- **Reducing exit criteria rigor** — e.g., "storm damage visible in colony sim" → "storm damage visible in debug overlay"
- **Narrowing deliverables so the approved capability is no longer truly delivered**
- **Moving core work out of the phase after approval**
- Milestone weakening occurs when the approved phase's promised capability becomes incomplete, indirect, or observable only through debugging or developer tools rather than normal gameplay. These look like refinements but actually weaken what approval meant. Require user confirmation, or an ADR if the change materially redefines the milestone.

### ADR-required: Scope invalidation
- **Removing something a Complete slice already delivered** — contradicts existing work
- **Changing entry criteria of the active phase** — would invalidate the phase's own approval
- These require an ADR, not a scope edit

### Draft phase changes
- All of the above classifications apply, but without Approved-phase guards
- Same classification logic as revise-slices: local vs architecture-impacting vs later-phase

## Step 4 — Present Proposed Changes

```
## Phase Revision: Post P#-### — [Name]

**Completed phase:** P#-### — [Name] (Status: Complete)
**Feedback sources:** N ADRs, N known issues, N playtest patterns, N triage actions

### Most Dangerous Planning Change
[The revision most likely to cause downstream disruption if mishandled.]

### Active Phase: P#-### — [Name] (Approved)

#### Safe Refinements
| # | Section | Current | Proposed | Reason |
|---|---------|---------|----------|--------|
| 1 | Exit Criteria | [current] | [proposed] | ADR-### constraint |

#### Scope Widening (requires confirmation)
| # | Section | Current | Proposed | Reason |
|---|---------|---------|----------|--------|
| 2 | In Scope | [current] | [proposed] | Implementation revealed gap |

### Draft Phase: P#-### — [Name]

#### Changes
| # | Section | Current | Proposed | Reason |
|---|---------|---------|----------|--------|
| 3 | In Scope | [current] | [proposed] | KI-### defers work |

### Roadmap Notes
[Impacts on phases not yet defined, or "None."]
```

**If only direct-apply changes exist** (safe refinements to Approved/Draft phases, all Draft-phase changes): apply immediately, write the revision log, and report. No user pause needed. **Volume guardrail:** if more than 5 direct-apply changes affect a single phase, surface a summary and require user acknowledgement before applying — silent large-scale rewrites are dangerous even when individually safe.

**If confirmation-required or ADR-required changes exist**: present those using the Human Decision Presentation pattern (see WORKFLOW.md). Each proposed change gets numbered options — typically (a) apply as proposed, (b) modify, (c) reject. Scope widening and milestone weakening for Approved phases get additional classification (local vs architecture-impacting). Wait for the user's decisions on confirmation-class items only, then proceed. Direct-apply items are applied regardless.

## Step 5 — Apply Confirmed Changes

**For Approved phases:**
- Apply safe refinements directly.
- Apply confirmed scope widening.
- Never apply scope invalidation — those require ADRs.
- The phase stays Approved. No status regression.

**For Draft phases:**
- Apply all confirmed changes normally.

**Editable sections (Approved phase):**
- In Scope, Out of Scope, Deliverables, Exit Criteria, Dependencies, Notes
- Never change: Goal (unless user explicitly requests), Entry Criteria, Phase ID, Status

**Editable sections (Draft phase):**
- All sections except Phase ID

## Step 6 — Write Revision Log

Write to `scaffold/decisions/revision-logs/REVISION-post-P#-###.md`. If the file already exists, append a new dated section.

```markdown
# Revision Log: Post-P#-### — [Name]

> **Date:** YYYY-MM-DD
> **Completed phase:** P#-### — [Name]
> **Feedback sources:** N ADRs, N known issues, N playtest patterns, N triage actions

## Most Dangerous Planning Change
[Risk-ranked.]

## Revisions Applied

| # | Phase | Section | Classification | Change | Reason |
|---|-------|---------|---------------|--------|--------|
| 1 | P#-### | Exit Criteria | Safe refinement | Added constraint | ADR-### |

## Proposed Changes Rejected

| # | Phase | Section | Proposed Change | Reason Rejected |
|---|-------|---------|----------------|----------------|
| 2 | P#-### | In Scope | Add save/load | User: belongs in next phase |

## Roadmap Notes
[Impacts on future phases, or "None."]
```

## Step 7 — Report

```
## Revision [Complete / Conditional / Report-Only]: Post-P#-### Implementation

| Metric | Value |
|--------|-------|
| Feedback sources read | N ADRs, N KIs, N playtest, N triage |
| Phases checked | N |
| Phases revised | N |
| Phases unchanged | N |
| Proposals rejected | N |
| Scope widening (Approved) | N |
| Milestone weakening (Approved) | N |
| Implementation friction signals | N |

### Most Dangerous Planning Change
[Repeated from revision log.]

### Next Phase Risk Level
**LOW / MEDIUM / HIGH** — [Based on: milestone weakening proposals, large refinement volume, ADR-required changes, implementation friction signals. LOW = routine refinements only. MEDIUM = scope widening or friction detected. HIGH = milestone weakening or ADR-required changes.]

### Recommended Next Phase
**P#-### — [Name]** is the next phase in roadmap order.

### Next Steps
- Run `/scaffold-fix-phase P#-###` on the next phase
- Run `/scaffold-iterate phase P#-###` for adversarial review
- Run `/scaffold-validate --scope phases` to check structural integrity
- Run `/scaffold-approve-phases P#-###` to approve the next phase for slice seeding
```

## Rules

- **Source phase must be Complete.** Do not revise based on incomplete implementation.
- **Approved phases stay Approved.** Scope refinement happens directly — no status regression. The phase was approved for good reason; revisions refine, not restart.
- **Four-tier classification: direct-apply, confirmation-required (widening), confirmation-required (weakening), ADR-required (invalidation).** Direct-apply changes proceed without user pause. Only confirmation and ADR items stop for decisions.
- **Safe refinements must preserve or strengthen milestone meaning.** Clarifying, constraining, or sharpening is safe. Reducing exit rigor, narrowing deliverables, or moving core work out is milestone weakening — not safe refinement.
- **Never change an Approved phase's Goal without explicit user request.** The goal is what the phase was approved to deliver.
- **Never remove something a Complete slice delivered.** That contradicts existing implementation — file via `/scaffold-file-decision --type adr` instead.
- **Explicit edit boundaries.** This skill may edit: Approved phase editable sections, Draft phase all sections. This skill must never edit: completed phases, roadmap ordering, phase IDs, slice/spec/task docs, architecture docs, or ADRs themselves.
- **Write a persistent revision log every run.** Even no-op runs log that no revisions were needed.
- **Revisions must be grounded in feedback.** Revised scope should preserve alignment with higher-authority documents and the intended final architecture, without introducing speculative scope not supported by implementation feedback.
- **Feedback must trigger a real planning change to warrant revision.** A feedback item only triggers revision if it changes at least one of: remaining phase scope, exit criteria, system dependencies, or phase ordering assumptions. Filter out ADRs/KIs that are historically interesting but don't change what remaining phases need to deliver.
- **Flag post-completion edits on the source phase.** If the completed phase file was modified after it became Complete, note this in the revision log as a risk signal — the feedback base may be unstable.
- **Feedback loop is mandatory.** Even if no phases remain, the feedback analysis runs.

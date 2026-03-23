---
name: scaffold-revise-roadmap
description: Update the roadmap after a phase completes. Moves the phase to Completed Phases with delivery notes, updates Current Phase, absorbs ADR feedback, and surfaces roadmap-level changes for decision.
argument-hint: PHASE-### (the just-completed phase)
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Revise Roadmap

Update the roadmap after completing a phase: **$ARGUMENTS**

This skill formalizes the Phase Transition Protocol. After a phase is Complete, the roadmap itself needs updating — the completed phase moves to the Completed Phases section, ADR feedback is logged, the Current Phase advances, and any roadmap-level insights from implementation are captured.

This is distinct from `/scaffold-revise-phases` which updates remaining phase *files*. This skill updates the *roadmap document itself*.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PHASE-###` | Yes | — | The phase that was just completed. |

## Preconditions

1. **Source phase exists** — glob `scaffold/phases/PHASE-###-*.md`. If not found, stop.
2. **Source phase is Complete** — verify `> **Status:**` is `Complete`. If not Complete, stop.
3. **Roadmap exists** — verify `scaffold/phases/roadmap.md` exists and is not at template defaults.
4. **Required sections exist** — verify the roadmap contains: Completed Phases, ADR Feedback Log, Phase Overview, Current Phase, Revision History. If any are missing, stop and instruct to run `/scaffold-fix roadmap` first. Writing into missing sections corrupts the document.

## Step 1 — Gather Completion Context

### 1a. Phase delivery summary

Read the completed phase file. Extract:
- Goal and Capability Unlocked
- Exit Criteria (all should be satisfied)
- Deliverables produced
- Systems implemented

### 1b. ADRs filed during the phase

Glob `scaffold/decisions/ADR-*.md`. Filter to ADRs that were created or accepted during the phase's implementation window AND reference systems implemented or modified during the completed phase. Prefer ADRs about completed-phase systems; if an ADR was written during the phase but only affects future phases, include it but mark impact as "future-phase" in the log entry. These must be logged in the roadmap's ADR Feedback Log.

### 1c. Known issues discovered

Read `scaffold/decisions/known-issues.md`. Check for entries added during this phase that affect the roadmap (not just remaining phases).

### 1d. Playtest feedback patterns

Read `scaffold/decisions/playtest-feedback.md`. Check for Pattern or ACT NOW entries that emerged during this phase.

### 1e. Revision log from revise-phases

If a revision log exists at `scaffold/decisions/revision-logs/REVISION-post-PHASE-###.md`, incorporate its roadmap notes. If not, continue — this skill does not require revise-phases to have run first.

### 1f. Implementation friction signals

Check for signs the phase was harder than expected:
- Was the phase revised during implementation? (Check revision log existence)
- Were slices split? (Check for slice revision logs, slices added after initial seeding, or slices marked "split" in revision notes — don't rely on comparing initial vs final counts unless the initial count is recorded.)
- Were ADRs filed that changed scope mid-phase?

**Friction rubric:**
- **LOW** = no revision log, no slice splits, 0–1 ADRs affecting scope
- **MEDIUM** = one of: revision log exists, slice splits occurred, or 2 scope-affecting ADRs
- **HIGH** = multiple slice splits, revision activity, AND 2+ scope-affecting ADRs

## Step 2 — Update Roadmap Sections

### 2a. Move to Completed Phases

**Dedupe check:** If PHASE-### already has a Completed Phases entry, update/append notes rather than duplicate.

Add (or update) an entry in the Completed Phases section:

```markdown
### PHASE-### — [Name]
- **Completed:** YYYY-MM-DD
- **Delivered:** [Capability Unlocked text]
- **Key deliverables:** [list from phase file]
- **ADRs filed:** [count and IDs]
- **Delivery notes:** [derived from: completed phase summary, ADRs filed, friction signals, revision log notes if available]
- **Implementation friction:** [LOW/MEDIUM/HIGH per rubric]
```

### 2b. Update ADR Feedback Log

**Dedupe check:** If an ADR ID already exists in the log, skip it — don't add duplicate entries.

For each new ADR filed during this phase, add an entry:

```markdown
| ADR-### | PHASE-### | [Brief description] | [Impact on remaining phases] |
```

### 2c. Update Phase Overview

- Sync the completed phase's roadmap status to `Complete` (mirroring the phase file).
- For the next phase in roadmap order: mirror its actual phase file status (`Draft` or `Approved`). Do not set any phase to a status its file doesn't reflect.

### 2d. Update Current Phase

- Find the earliest Approved-not-Complete phase by checking actual phase file statuses (not roadmap assumptions). If one exists, Current Phase points to it.
- If no Approved phase exists, Current Phase becomes: "No active phase — next phase pending approval. Run `/scaffold-approve-phases`."
- Never point Current Phase to a Draft phase as if it were active. Never embed a phase ID in the pending message unless verified against actual file status.

### 2e. Update Upcoming Phases (if needed)

If implementation feedback suggests roadmap-level changes beyond individual phase scope:
- New phases needed (flag as roadmap note — do not create)
- Phases that may no longer be needed (flag for user decision)
- Ordering changes suggested by implementation reality (flag for user decision)

### 2f. Add Revision History Entry

Append to the Revision History section:

```markdown
| YYYY-MM-DD | PHASE-### completed; roadmap advanced to PHASE-### [status]; N ADRs logged; friction: [level] |
```

## Step 3 — Classify Roadmap Changes

### Direct-apply (no pause needed)
- Moving phase to Completed Phases (with dedupe)
- ADR Feedback Log entries (with dedupe)
- Phase Overview status sync (mirroring phase files)
- Current Phase pointer update
- Revision History entry
- Delivery notes derived from completion context

### Confirmation-required
- Updating Upcoming Phases descriptions based on feedback
- Changing phase ordering suggestions
- Flagging phases as potentially unnecessary
- Adding roadmap notes about new phase needs

### Not permitted (this skill)
- Creating new phases (use `/scaffold-new-phase`)
- Deleting phases from the roadmap
- Changing phase IDs
- Editing phase files (use `/scaffold-revise-phases`)

## Step 4 — Apply Changes

**Direct-apply changes** proceed immediately.

**Confirmation-required changes** are presented using the Human Decision Presentation pattern (see WORKFLOW.md) with numbered options (a/b/c). Wait for user decisions.

## Step 5 — Report

```
## Roadmap Revised: Post-PHASE-### — [Name]

### Phase Completion Summary
- **Capability delivered:** [Capability Unlocked text]
- **ADRs filed:** N
- **Implementation friction:** LOW / MEDIUM / HIGH
- **Slices completed:** N

### Roadmap Updates Applied
| # | Section | Change |
|---|---------|--------|
| 1 | Completed Phases | Added PHASE-### entry with delivery notes |
| 2 | ADR Feedback Log | Added N ADR entries |
| 3 | Phase Overview | PHASE-### → Complete |
| 4 | Current Phase | [PHASE-### (Approved) / No active phase — pending approval] |
| 5 | Revision History | Added transition entry |

### Roadmap-Level Observations
[Structured as: signals (friction, ADR patterns), risks emerging, confirmation-required changes. "None" if the roadmap structure holds.]

### Roadmap Confidence
**Stable / Decreased / Improved** — [Based on: friction level, ADR count, number of roadmap-level observations, whether downstream revisions found major changes.]

### Next Steps
- Run `/scaffold-revise-phases PHASE-###` to update remaining phase files from feedback
- Run `/scaffold-fix phase PHASE-###` on the next phase
- Run `/scaffold-iterate phase PHASE-###` for adversarial review
- Run `/scaffold-approve-phases PHASE-###` to approve the next phase
```

## Rules

- **Only edit the roadmap file.** Never edit phase files, indexes, design docs, or ADRs.
- **Phase file status is canonical.** The roadmap mirrors phase file statuses (Draft/Approved/Complete), not the other way around. Never set a roadmap status that differs from the phase file.
- **No "Active" status.** The roadmap uses Draft/Approved/Complete to match the phase lifecycle. Current Phase points to the Approved phase; there is no separate "Active" status.
- **Delivery notes are honest and multi-sourced.** Derive from: completed phase summary, ADRs filed, friction signals, revision log notes. Don't sanitize friction — record what actually happened.
- **Dedupe before writing.** Check Completed Phases and ADR Feedback Log for existing entries before adding. Update/append, never duplicate.
- **Do not invent new phases.** Flag the need, but creation happens through `/scaffold-new-phase`.
- **Do not delete phases.** Flag the concern, but removal is a user decision.
- **ADR feedback logging is mandatory.** Every ADR from the completed phase must appear in the log.
- **Recommended order: revise-roadmap before revise-phases.** The roadmap update captures the macro view; phase revision handles micro adjustments. But this skill is resilient to running in either order — it incorporates revision logs if they exist, and proceeds without them if they don't.
- **Always add a Revision History entry.** Every run produces a dated record of what changed.
- **Confidence heuristic.** Improved: LOW friction, ≤1 ADR, no roadmap-level observations. Stable: MEDIUM friction, ≤2 ADRs, minor observations. Decreased: HIGH friction, ≥3 ADRs, or major observations/structural changes.

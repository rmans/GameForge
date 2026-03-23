---
name: scaffold-revise-slices
description: Update remaining Draft slices in the same phase based on implementation feedback from a completed slice. Reads ADRs, known issues, and triage logs. Writes a persistent revision log.
argument-hint: SLICE-### (the just-completed slice)
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Revise Slices

Update remaining Draft slices based on what was learned from implementing: **$ARGUMENTS**

This skill is the feedback loop between implementation and planning. After a slice is implemented and marked Complete, the ADRs, known issues, triage decisionsfrom that work may change what remaining slices need to prove. This skill reads all feedback, proposes changes to remaining Draft slices in the same phase, and applies confirmed changes.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLICE-###` | Yes | — | The slice that was just completed. Feedback from its implementation drives the revision. |

## Preconditions

Before revising, verify:

1. **Source slice exists** — glob `scaffold/slices/SLICE-###-*.md`. If not found, report and stop.
2. **Source slice is Complete** — read the file and verify `> **Status:**` is `Complete`. If the slice is still mid-implementation (Draft or Approved), stop — revising based on incomplete work produces unreliable changes.
3. **Phase can be resolved** — extract the Phase reference and verify the phase file exists.
4. **Check for remaining Draft slices** — if no same-phase Draft slices remain, switch to **report-only mode**: still gather feedback, analyze later-phase impacts, surface missing coverage candidates, create upstream actions, and write the revision log — but skip Steps 3-5 (no slice edits). The feedback loop is mandatory even when there are no slices left to revise.

## Step 1 — Gather Implementation Feedback

Read all feedback produced during the completed slice's implementation:

### 1a. ADRs filed during implementation

Glob `scaffold/decisions/ADR-*.md`. Filter to ADRs that are relevant to this revision — specifically ADRs that:
- Reference systems used by the completed slice (by SYS-### ID)
- Were created or accepted after the source slice was approved (by date)
- Appear in the triage log for the completed slice

Do not analyze the entire ADR history — only recent, relevant decisions. This prevents noisy revision proposals from old, unrelated ADRs.

### 1b. Known issues discovered

Read `scaffold/decisions/known-issues.md`. Check for entries that reference systems used by the completed slice, or that were added/updated after the baseline date. Determine the baseline using this priority: (1) the source slice's header completion date if present, (2) the most recent `REVISION-post-SLICE-*.md` date for this phase, (3) file modified timestamp as a last-resort fallback.

### 1c. Triage decision logs

Read `scaffold/decisions/triage-logs/TRIAGE-SLICE-###.md` and `TRIAGE-SPECS-SLICE-###.md` if they exist. Check for upstream actions that affect other slices' systems or specs.

### 1d. Prototype findings


### 1e. Completed slice outcomes

Read the completed slice file. Check:
- Were all Done Criteria met? If not, what was deferred?
- Did the Demo Script reveal unexpected behavior?
- Were specs or tasks added/removed during implementation?
- Did system boundaries change from what was planned?

## Step 2 — Identify Affected Slices

**Same-phase Draft slices** are the primary revision candidates. Read each Draft slice in the same phase.

**Later-phase slices** are checked for likely impacts only — flag them as roadmap notes but do not propose detailed changes unless the user explicitly requests cross-phase revision. Detailed revision of distant future slices creates planning churn.

## Step 3 — Analyze and Classify Impact

For each same-phase Draft slice, check whether implementation feedback affects it. For each proposed change, classify it:

### Local revision (apply directly)
Changes that update slice content without altering architecture intent:
- Sharpening goal text for clarity
- Adding or removing integration proof points based on what was learned
- Updating suggested specs to match implementation reality
- Adding risk/blocker notes from known issues
- Updating done criteria based on discovered constraints

### Architecture-impacting revision (escalate)
Changes that alter architecture-level intent — apply only safe local wording, then create an upstream action or ADR stub:
- Changing which systems a slice covers (ownership change)
- Changing authority boundaries the slice crosses
- Changing interface contracts the slice exercises
- Changing state-machine meaning for systems in the slice
- Altering persistence assumptions
- Changing what a slice fundamentally proves in a way that alters phase intent

### Later-phase impact (flag only)
Impacts on slices outside the current phase:
- Flag as a roadmap note in the revision log
- Do not propose detailed changes unless explicitly requested
- Recommend checking during the next phase transition (Step 23)

### Missing coverage (surface for user)
Revision may reveal that remaining slices are insufficient:
- A behavior discovered during implementation has no slice to prove it
- An integration path was established that no remaining slice exercises
- A new system boundary was created that needs a vertical proof

Flag as a **new slice candidate** for the user to decide — do not create the slice here.

## Step 4 — Present Proposed Changes

For each affected slice, present proposed changes with classification:

```
## Slice Revision: Phase PHASE-### — [Name]

**Completed slice:** SLICE-### — [Name] (Status: Complete)
**Feedback sources:** N ADRs, N known issues, N triage actions

### Most Dangerous Planning Change
[The single revision most likely to cause problems if not handled correctly. If none, write "No critical planning changes."]

### Affected Slice: SLICE-### — [Name] (Draft)

#### Local Revisions
| # | Section | Current | Proposed | Reason |
|---|---------|---------|----------|--------|
| 1 | Suggested Specs | [current] | [proposed] | KI-### adds constraint |
| 2 | Done Criteria | [current] | [proposed] | Learned during implementation |

#### Architecture-Impacting Revisions
| # | Section | Current | Proposed | Reason | Upstream Action |
|---|---------|---------|----------|--------|----------------|
| 3 | Systems Covered | SYS-005, SYS-008 | SYS-005, SYS-008, SYS-012 | ADR-### added RoomSystem dependency | Update architecture.md |

#### No Changes Needed
[Sections checked and still valid.]

### Later-Phase Impacts
[Flag likely impacts on slices in future phases. No detailed proposals.]

### Missing Coverage
[New slice candidates or uncovered integration paths. For user decision.]

### Order Recommendation
[If feedback reveals new dependencies, recommend reordering. Do not apply — ordering is managed through slice approval.]
```

Present proposals using the Human Decision Presentation pattern (see WORKFLOW.md). Each proposed change gets numbered options — typically (a) apply as proposed, (b) modify, (c) reject. Architecture-impacting revisions additionally get classified before application. Wait for the user's decisions on each issue before proceeding.

**For each change, state which option is best for the final shipped game.** Design for the final product — never propose temporary scope that would require redesigning later.

## Step 5 — Apply Confirmed Changes

For each confirmed change:

**Editable sections** (only these may be modified in Draft slices):
- Goal
- Proof Value
- Assumptions
- Starting Conditions
- Depends on (update dependency declarations if implementation revealed new prerequisites or removed assumed ones)
- Systems Covered
- Integration Points
- Suggested Specs
- Done Criteria
- Failure Modes This Slice Should Catch
- Visible Proof
- Demo Script
- Risks / Blockers / Notes

**Never edit:**
- Slice ID
- Phase reference
- Status (stays Draft)
- Completed slice files
- Specs, tasks, system designs, or architecture docs

For architecture-impacting revisions: apply only the safe local wording change to the slice, then create an upstream action or ADR stub. The architecture layer must absorb the change before the slice is considered fully revised.

## Step 5b — Reconcile Index Order with Dependencies

After all slice edits are applied, check whether `scaffold/slices/_index.md` order is still a valid topological sort of the dependency graph. This step prevents the scenario where a slice split or new dependency creates an impossible implementation sequence (e.g., SLICE-004 depends on SLICE-010, but SLICE-010 appears after SLICE-004 in the index).

1. **Read `scaffold/slices/_index.md`** and extract the current implementation order for same-phase slices.
2. **Build the dependency graph** from all same-phase slices' `> **Depends on:**` fields.
3. **Check topological validity** — for every slice, all its declared dependencies must appear earlier in the index order.
4. **If the order is invalid:**
   - Compute a valid topological sort that minimizes movement from the current order (prefer moving the fewest slices).
   - Present the proposed reorder to the user:
     ```
     ### Index Order Reconciliation

     The current index order is invalid after revision changes.

     **Problem:** SLICE-004 depends on SLICE-010, but SLICE-010 is at position 10 (after SLICE-004 at position 4).

     **Proposed order:**
     | Position | Slice | Depends on | Change |
     |----------|-------|------------|--------|
     | 1 | SLICE-001 | — | unchanged |
     | 2 | SLICE-003 | SLICE-001 | unchanged |
     | 3 | SLICE-010 | SLICE-003 | ← moved from position 10 |
     | 4 | SLICE-004 | SLICE-003, SLICE-010 | unchanged |
     | ... | ... | ... | ... |
     ```
   - On user confirmation, reorder the rows in `scaffold/slices/_index.md`.
5. **If the order is already valid**, skip with a note: "Index order is consistent with dependency graph."

**This step is mandatory whenever Step 5 modified any `Depends on` fields or when Missing Coverage candidates were confirmed as new slices.** Skip if no dependency-affecting changes were made.

## Step 6 — Write Revision Log

**Before writing the log**, check if `scaffold/decisions/revision-logs/REVISION-post-SLICE-###.md` already exists. If it does, ask the user whether this is: (a) a re-run after further feedback, (b) a correction of a previous revision, or (c) an accidental duplicate. If re-run or correction, append a new dated section rather than overwriting. If no response is provided (e.g., automated execution), append by default — never overwrite existing revision logs automatically.

Write to `scaffold/decisions/revision-logs/REVISION-post-SLICE-###.md`. If the directory does not exist, create it.

```markdown
# Revision Log: Post-SLICE-### — [Name]

> **Date:** YYYY-MM-DD
> **Completed slice:** SLICE-### — [Name]
> **Feedback sources:** N ADRs, N known issues, N triage actions

## Most Dangerous Planning Change
[Select the revision most likely to cause downstream architectural inconsistency or slice mis-sequencing if ignored. Always rank risk — do not write "None" unless zero revisions were proposed. If no revisions exist, state "No revisions proposed."]

## Revisions Applied

| # | Slice | Section | Classification | Change | Reason |
|---|-------|---------|---------------|--------|--------|
| 1 | SLICE-### | Suggested Specs | Local | Added edge case spec | KI-### |
| 2 | SLICE-### | Systems Covered | Architecture | Added SYS-012 | ADR-### |

## Proposed Changes Rejected

| # | Slice | Section | Proposed Change | Reason Rejected |
|---|-------|---------|----------------|----------------|
| 3 | SLICE-### | Goal | Expand to include AI behavior | User: AI belongs in a separate slice |

If no proposals were rejected, write: "None — all proposals accepted."

## Upstream Actions Created

| # | Target Document | Action | Reason | Status |
|---|----------------|--------|--------|--------|
| 1 | architecture.md | Update system dependency graph | ADR-### added RoomSystem | Pending |

## Later-Phase Impacts Flagged
[List impacts on future phases, or "None."]

## Missing Coverage / New Slice Candidates
[List, or "None."]

## Index Order Reconciliation
[Was the index reordered? If yes, list the moves. If the order was already valid, write "Index order consistent — no reorder needed." If no dependency-affecting changes were made, write "No dependency changes — skipped."]

## Order Recommendations
[Additional ordering suggestions beyond what was applied in reconciliation, or "No further reordering needed."]
```

## Step 7 — Report

```
## Revision [Complete / Conditional / Report-Only]: Post-SLICE-### Implementation

**Complete** — all revisions applied, no pending architecture actions.
**Conditional** — revisions applied but architecture-impacting upstream actions are still pending. Resolve before approving the next slice.
**Report-Only** — no same-phase Draft slices remain. Feedback analyzed, later-phase impacts and missing coverage surfaced.

| Metric | Value |
|--------|-------|
| Feedback sources read | N ADRs, N KIs, N triage actions |
| Same-phase Draft slices checked | N |
| Slices revised | N |
| Slices unchanged | N |
| Proposals rejected | N |
| Architecture-impacting revisions | N |
| Upstream actions created (pending) | N |
| Later-phase impacts flagged | N |
| Missing coverage candidates | N |
| Index reordered | Yes (N slices moved) / No / Skipped |

### Most Dangerous Planning Change
[Repeated from revision log.]

### Recommended Next Slice
**SLICE-### — [Name]** is recommended next in the implementation order. This recommendation assumes pending upstream actions do not require reordering. If no same-phase Draft slices remain, write "Phase complete — proceed to Phase Transition Protocol (Step 23)."

### Next Steps

**If Complete:**
- Run `/scaffold-review-slice SLICE-###` on the next slice
- Run `/scaffold-iterate` on the next slice for adversarial review
- Run `/scaffold-validate --scope slices` to check structural integrity
- Run `/scaffold-approve-slices SLICE-###` to approve the next slice for spec seeding

**If Conditional:**
- Resolve pending upstream actions via direct file editing or file ADRs
- Then follow the Complete steps above

**If Report-Only:**
- Proceed to Phase Transition Protocol (Step 23)
- Review later-phase impacts and missing coverage candidates during phase transition
```

## Rules

- **Source slice must be Complete.** Do not revise based on incomplete implementation. If the source slice is still Draft or Approved, stop.
- **Never decide for the user, but always recommend.** Present proposed changes and state which option produces the strongest design for the final shipped game.
- **Only edit Draft slice files in the same phase.** Never edit completed slices, later-phase slices (unless explicitly requested), specs, tasks, system designs, or architecture docs.
- **Classify every revision.** Local revisions apply directly. Architecture-impacting revisions get upstream actions. Later-phase impacts are flagged only. Missing coverage is surfaced for user decision.
- **Do not change slice ordering directly.** This skill may recommend reordering, but does not itself change the implementation sequence. Ordering changes are applied through `/scaffold-approve-slices` and user decisions.
- **Write a persistent revision log.** Every revision run produces `REVISION-post-SLICE-###.md` so the reasoning is traceable.
- **Implementation feedback is the primary input.** ADRs, known issues, and triage logs drive revision — not speculation about what might change.
- **Design for the final product.** Revised scope should reflect the final architecture. Never propose temporary scope that would require redesigning later.
- **New issues go to known-issues.md.** If revision reveals problems that don't fit any slice, recommend adding them to `known-issues.md`.
- **Missing coverage becomes a candidate, not a slice.** If remaining slices are insufficient, flag it — don't create new slices here. The user decides whether to add slices via `/scaffold-new-slice`.
- **No-op runs still log.** A revision run that produces no changes is still successful and must write a revision log stating that no revisions were required. The feedback loop is mandatory every cycle.

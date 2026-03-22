---
name: scaffold-triage-specs
description: Collect unresolved human-required issues from spec reviews and walk through them as decisions. Splits, merges, reassigns, or defers specs. Writes a persistent decision log.
argument-hint: SLICE-###
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Triage Specs

Collect and resolve human-required planning issues for specs in: **$ARGUMENTS**

This skill is the human decision gate in the spec planning loop. It gathers unresolved issues from `/scaffold-fix-spec` and `/scaffold-iterate` runs, presents them as a decision checklist, and applies the user's decisions.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLICE-###` | Yes | — | The slice whose specs are being triaged. Scopes issue collection to this slice's specs. |

## Step 1 — Collect Issues

Gather all human-required issues from the most recent review and fix passes.

### 1a. Scan Review Logs

Grep `scaffold/decisions/review/REVIEW-*` for review logs that reference specs in this slice. Extract issues marked as **human-required**, **unresolved**, or **escalated**.

### 1b. Scan Fix-Spec Output

Read spec files for notes about human-required issues that fix-spec couldn't resolve (e.g., `<!-- TODO -->` markers, scope mismatch notes).

### 1c. Scan Spec Files for Annotations

Grep `scaffold/specs/SPEC-*.md` for specs in this slice. Look for:
- Notes mentioning unresolved issues, open questions, or "human decision needed"
- `TODO` or `FIXME` markers
- References to KI-### blockers or unresolved DD-### entries

### 1d. Check Slice Coverage

Read the slice's goals and system coverage. For each goal, check whether at least one spec covers the behavior. If a slice goal has no implementing spec, classify the gap:
- **Missing behavior spec** — the behavior is well-understood and just needs a spec written. Record as **New Spec**.
- **Missing contract/architecture decision** — the behavior requires a cross-system contract or ownership decision that doesn't exist yet. Record as **Authority** or **File ADR** — don't patch architecture holes by creating specs.
- **Missing ownership decision** — it's unclear which system should own this behavior. Record as **Reassignment** for the user to decide.

Coverage gaps are the most dangerous issue type — they mean behavior will be missing from the slice.

### 1e. Detect Spec Overlap

Look for specs that define the same behavior or have overlapping acceptance criteria. This typically happens after multiple seed/review cycles. Record as **Merge** issues.

### 1f. Detect Orphan Specs

Check each spec's slice membership. Flag specs where:
- The spec is not listed in any slice's Specs table.
- The spec's behavior no longer maps to its parent system's scope (system was revised but spec wasn't updated).

### 1g. Check System Alignment

For each spec, verify its behavior stays within its parent system's defined scope per `scaffold/design/systems/SYS-###-*.md`. If a spec describes behavior that belongs to a different system, record as **Reassignment** or **Scope** issue.

### 1h. Check Authority Compliance

Cross-reference specs with `scaffold/design/authority.md`. If a spec implies cross-system data writes not defined in the authority table, record as **Authority** issue.

### 1i. Check Known Issues

Read `scaffold/decisions/known-issues.md`. If any open known issue affects a system or behavior covered by specs in this slice, check whether the specs account for it (as an edge case, constraint, or AC). If not, record as a **Scope** issue — the spec may need to address the known constraint.

If triage discovers a new issue that doesn't fit any existing category (e.g., an architectural smell, performance concern, or system coupling problem), recommend filing via `/scaffold-file-decision --type ki` rather than trying to resolve it as a spec change.

### 1j. Check ADR Compliance

Read all accepted ADRs (`scaffold/decisions/ADR-*.md` with status `Accepted`). For each ADR that affects systems covered by this slice's specs, check whether the relevant specs reflect the ADR's decisions. If a spec ignores or contradicts an accepted ADR, record as a **Scope** issue (spec needs updating) or **State conflict** (if the ADR changed state transitions the spec references).

### 1k. Check State Transition Alignment

Read `scaffold/design/state-transitions.md`. For each spec that references or implies state transitions, verify:
- The transitions exist in the state machine.
- The spec's trigger conditions match the state machine's entry conditions.
- No transitions are omitted that the spec's behavior would require.

Record mismatches as **State conflict** issues.

### 1l. Check Registration Synchronization

Detect registration drift that could corrupt downstream processing:
- Spec file exists but not registered in `scaffold/specs/_index.md`.
- Spec file exists but not listed in any slice's Specs table.
- Slice table references a SPEC-### whose file no longer exists.
- Index row points to a filename that doesn't exist.

Record as **Registration** issues. These must be fixed before stability can be claimed.

### 1m. Deduplicate Issues

Merge identical issues from multiple sources. Two issues are considered identical if they reference: (a) the same spec(s), (b) the same section (Trigger, Behavior, Observable Outcome, Failure Outcome, Secondary Effects, Acceptance Criteria, etc.), and (c) the same underlying problem, even if phrased differently across sources. Keep the most detailed description.

## Step 2 — Categorize Issues

Group collected issues by decision type:

| Category | What the User Decides | Actions Available |
|----------|----------------------|-------------------|
| **Split** | A spec covers too much behavior — where to split? | Create new spec stubs, narrow original |
| **Merge** | Two specs overlap — combine? | Merge ACs/behavior into one spec, remove the other |
| **Scope** | Spec behavior too broad or too narrow | Narrow or expand behavior, update ACs |
| **New spec** | Missing coverage — new spec needed | Create new spec stub |
| **Reassignment** | Spec belongs to a different system | Move to correct system, update slice |
| **Authority** | Spec implies unauthorized cross-system writes | Redesign behavior, file ADR, or update authority.md |
| **State conflict** | Spec and state-transitions.md disagree | Decide which is right, update accordingly |
| **Blocker** | KI or prerequisite blocks the spec — spec cannot proceed to task seeding | Defer spec, resolve blocker first, or accept risk |
| **Defer** | Issue is real but not worth fixing now — spec may proceed with documented design debt | Record as design debt |
| **Registration** | Index/slice/file synchronization is broken | Fix registration, rerun validate |

## Step 3 — Present Decision Checklist

Present all issues to the user, grouped by category:

```
## Spec Triage: SLICE-### — [Name]

### Issues Found: N total

#### Coverage Gaps (N issues)
1. **Gap**: Slice goal "[goal]" has no implementing spec
   - Options: (a) Create new spec (b) Expand existing SPEC-### (c) Defer to later slice

#### Overlaps (N issues)
2. **SPEC-### — [Name]** + **SPEC-### — [Name]**: [description of overlap]
   - Options: (a) Merge into SPEC-### (b) Merge into SPEC-### (c) Keep both, narrow each

#### Scope Changes (N issues)
3. **SPEC-### — [Name]** (System: SYS-### — [Name]): [description of scope issue]
   - Options: (a) Narrow scope (b) Expand scope (c) Keep as-is

#### Reassignments (N issues)
4. **SPEC-### — [Name]**: behavior belongs to SYS-### not SYS-###
   - Options: (a) Reassign to SYS-### (b) Split behavior across systems (c) Keep as-is

#### Oversized Specs (N issues)
5. **SPEC-### — [Name]**: covers multiple behaviors (placement + validation + resource deduction + room trigger)
   - Options: (a) Split into SPEC-### and SPEC-### (b) Narrow scope to one behavior (c) Keep as-is

#### Authority Issues (N issues)
6. **SPEC-### — [Name]**: implies [SystemA] writes [SystemB] data
   - Options: (a) Redesign within single system (b) File ADR to update authority (c) Accept and document

#### Duplicate Slice Intent (N issues)
7. **SPEC-### — [Name]** + **SPEC-### — [Name]**: both attempt to prove the same slice goal "[goal]"
   - Options: (a) Merge (b) Narrow each to distinct proof aspects (c) Remove one

...
```

Wait for the user's decisions on each issue before proceeding.

## Step 4 — Classify and Apply Decisions

Before applying each decision, classify it:

**Local decision** — changes only spec documents, indexes, and slice tables. Examples: narrowing scope, tightening ACs, fixing terminology, splitting an oversized spec into two specs within the same system. Apply immediately.

**Architecture-impacting decision** — changes architecture-level intent. Apply only the safe local portions, then create an upstream action or ADR stub for the architecture change. Mark stability as incomplete until the upstream action is resolved.

A decision is architecture-impacting if it does any of the following:
- Changes which system owns a behavior
- Allows a cross-system write that did not previously exist
- Defines a new cross-system contract not in `interfaces.md`
- Changes persistence expectations (what gets saved/loaded)
- Changes state-machine meaning (new states, removed transitions)
- Changes orchestration/tick-order assumptions
- Merges or splits specs in a way that changes system boundaries

These are not bad decisions — they are just too important to live only in spec docs. The architecture layer must absorb them before the graph is fully stable.

For each decision the user makes:

### Split
1. Read the original spec.
2. Create new spec stub(s) using the spec template. Assign next sequential SPEC-### ID(s).
3. Narrow the original spec's behavior and ACs.
4. Register new spec(s) in `scaffold/specs/_index.md`.
5. Add new spec(s) to the slice's Specs table.

### Merge
1. Read both spec files.
2. **Check atomicity before merging.** Only merge if the resulting spec still defines one primary behavior testable as a single unit. If merge would create a multi-behavior spec, reject merge and recommend narrowing/splitting instead.
3. Combine behavior, ACs, and edge cases into the surviving spec.
4. Remove the absorbed spec file.
5. Update `scaffold/specs/_index.md` — remove the absorbed spec's row.
6. Update the slice's Specs table — remove the absorbed spec's row.

### Scope Change
1. Read the spec file.
2. Apply the scope change — add/remove behavior steps, update ACs, update Observable Outcome and Failure Outcome to reflect the new scope.
3. Update edge cases, Secondary Effects, and Out of Scope to match the new scope.

### New Spec
1. Create spec stub using the spec template. Assign next sequential SPEC-### ID.
2. Fill in summary and initial behavior from the identified gap.
3. Register in `scaffold/specs/_index.md`.
4. Add to the slice's Specs table.

### Reassignment
1. Update the spec's system reference.
2. Move behavior language to match the new system's scope.
3. Update the slice's Specs table if the spec moves to a different slice.
4. **Check for ripple effects:**
   - If reassignment changes the slice's proof story (e.g., the slice no longer covers the system the spec moved away from), record an upstream action against the slice.
   - If the destination system already has specs covering similar behavior, surface a follow-up **Merge** or **Scope** issue immediately — reassignment can silently create duplicates.
   - If existing tasks reference this spec, note that task `Implements:` references may need updating after task seeding.

### Authority — Redesign
1. Update the spec to keep behavior within a single system's authority.

### Authority — File ADR
1. Create an ADR stub in `scaffold/decisions/` proposing the authority change.
2. Set status to `Proposed`.

### Blocker / Defer
1. Add appropriate note to the spec (`> **Blocked by:**` or design debt reference).

## Step 5 — Write Decision Log

Write a persistent decision log to `scaffold/decisions/triage-logs/TRIAGE-SPECS-SLICE-###.md`. If the directory does not exist, create it.

```markdown
# Spec Triage Log: SLICE-### — [Name]

> **Date:** YYYY-MM-DD
> **Issues found:** N
> **Decisions applied:** N

## Decisions

| # | Category | Spec(s) | Decision | Result |
|---|----------|---------|----------|--------|
| 1 | Merge | SPEC-###, SPEC-### | Merge into SPEC-### | SPEC-### removed |
| 2 | New spec | — | Coverage gap for slice goal | Created SPEC-### |
| ... | ... | ... | ... | ... |

## Upstream Actions Required

| # | Source Decision | Target Document | Action | Reason | Status |
|---|----------------|----------------|--------|--------|--------|
| 1 | #4 | authority.md | Add cross-system write rule | Spec requires NeedSystem → HealthSystem write | Pending |

**Status values:** Pending, Filed, Deferred, Resolved

If no upstream actions are needed, write: "None — all decisions were spec-scoped."
```

If a previous triage log exists for this slice's specs, append a new dated section.

## Step 6 — Stability Check

```
## Spec Triage Summary: SLICE-### — [Name]

### Most Dangerous Unresolved Issue
[The single biggest remaining risk — the issue most likely to cause downstream problems if not resolved before task seeding. If no critical risks remain, write "No critical risks identified."]

### Spec Graph Stability
- Active specs: N (ready for task generation)
- Specs created: N new
- Specs removed: N merged/removed
- Specs modified: N scope changes
- Specs deferred: N blocked
- Registration issues: N (must be zero for stability)
- Unresolved issues: N remaining (deferred with recorded decisions do NOT count)
- Upstream actions pending: N

### Stability Assessment: [Stable / Needs another pass]

**Stable** means:
- No unresolved human-required issues remain
- No new specs need to be created
- No pending merges or splits
- No registration synchronization issues
- Two consecutive iterate passes produced no new meaningful issues

**Needs another pass** means:
- New specs were created that haven't been reviewed yet
- Splits produced specs that may have their own issues
- Registration drift detected

### Next Steps
- If **Stable**: Run `/scaffold-validate` then `/scaffold-approve-specs SLICE-###` then proceed to task seeding
- If **Needs another pass**: Run `/scaffold-fix-spec` on new/modified specs, then `/scaffold-iterate spec`, then `/scaffold-triage-specs` again
```

## Rules

- **Never decide for the user, but always recommend.** Present options and wait for decisions — but for each issue, state which option produces the strongest design for the final shipped game. Specs should describe final product behavior; slices only control when that behavior is implemented, not how it is designed. Never recommend solutions that would require redesigning the system later. Avoid temporary simplified designs that will be ripped out — prefer correct ownership, correct system boundaries, and correct authority even if the slice only implements a subset. The user makes the final call, but they should never have to guess which option you think is strongest.
- **Only edit spec files and indexes.** Never edit system designs, authority, or interfaces. If those need changing, record as upstream actions.
- **New specs follow all conventions.** Sequential IDs, spec template, registered in index, added to slice table.
- **Merged specs are fully removed.** Delete the file, remove from index, remove from slice table. IDs are never reused.
- **ADR stubs are Proposed, not Accepted.** The user must review and accept ADRs separately.
- **Deferred is not unresolved.** An issue with a recorded decision counts as resolved for stability purposes.
- **Architecture gaps escalate.** If a gap exists because a cross-system contract is undefined, classify as Authority or File ADR — not automatically as New Spec.
- **Merges must preserve atomicity.** Only merge two specs if the result still defines one primary behavior testable as a single unit. If merge would create a multi-behavior spec, reject and recommend narrowing/splitting instead.
- **Reassignment checks for ripple.** When a spec moves systems, check whether the slice proof story changes, whether the destination system has overlapping specs, and whether existing tasks need updating.
- **Registration issues block stability.** If spec files, index, and slice tables are out of sync, the spec set is not stable regardless of content quality.
- **Stability assessment is honest.** If new specs were created, they need review. Don't claim stability when the set has changed.

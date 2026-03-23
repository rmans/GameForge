---
name: scaffold-revise-systems
description: Detect system design drift from implementation feedback and apply safe updates or escalate for decisions. Reads ADRs, known issues, spec/task friction, and code review findings to identify when system docs no longer match what was actually built. Use after a phase or slice completes, or when revise-foundation detects Step 2 drift.
argument-hint: [--source PHASE-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword,TRIAGE:action]
allowed-tools: Read, Edit, Grep, Glob
---

# Revise Systems

Detect system design drift and update system docs from implementation feedback: **$ARGUMENTS**

System designs are the simulation layer's source of truth — they define what each system owns, how it behaves, and how it interacts with others. But implementation reveals realities that design couldn't anticipate: ownership boundaries shift, behaviors need new failure paths, dependencies change, and new cross-system interactions emerge. This skill reads implementation feedback, classifies what changed, applies safe evidence-backed updates directly, and escalates design-level changes for human decision.

This is distinct from:
- **`fix-systems`** — repairs mechanical structure (this skill identifies *design-level* drift, not formatting)
- **`iterate-systems`** — adversarial design review (this skill processes *implementation signals*, not reviewer critique)
- **`seed systems`** — creates system docs from scratch (this skill updates existing docs from feedback)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source` | No | auto-detect | What triggered the revision: `PHASE-###` (phase completed), `SLICE-###` (slice completed), `foundation-recheck` (dispatched from revise-foundation). If omitted, scans all recent feedback. |
| `--signals` | No | — | Comma-separated list of specific drift signals to process. When provided, skip the broad feedback scan and process only these items. Accepted formats: `ADR-###`, `KI:keyword`, `TRIAGE:action-keyword`, `SPEC:friction-keyword`, `CODE-REVIEW:finding-keyword`. This is the primary dispatch mechanism — `revise-foundation` identifies which signals affect system docs and passes them here. |

## Preconditions

1. **System docs exist** — verify at least one `design/systems/SYS-###-*.md` exists and is not at template defaults. If none exist, stop: "No system docs to revise. Run `/scaffold-seed systems` first."
2. **System docs have been through Step 2 pipeline** — verify at least one fix or iterate log exists in `scaffold/decisions/review/`. If no logs exist, stop: "System docs haven't been stabilized yet. Run the Step 2 pipeline (seed → fix → iterate → validate) first."
3. **Implementation feedback exists** — if `--signals` is provided, at least one signal must resolve to a real source document (see signal resolution rules). If `--signals` is not provided, at least one of: accepted ADRs, known issues entries, triage logs, code review findings, or spec/task friction signals must exist. If none exist, report: "No implementation feedback found. Nothing to revise."

## Step 1 — Gather Implementation Feedback

**If `--signals` is provided:** Skip the broad scan. Read only the specific documents referenced by the signal list:
- `ADR-###` → read `scaffold/decisions/ADR-###-*.md`
- `KI:keyword` → search `scaffold/decisions/known-issues.md` for the matching entry
- `TRIAGE:keyword` → search triage logs for the matching upstream action
- `SPEC:keyword` → search spec files for friction notes matching the keyword
- `CODE-REVIEW:keyword` → search code review logs for findings matching the keyword

**Signal resolution rules:**
- **Single match** → proceed normally.
- **No match** → WARN: "Signal [X] could not be resolved. Skipping." Continue with remaining signals.
- **Multiple matches** → use most recent by date. If ambiguous, present matches to user.

**If `--signals` is not provided:** Run the broad scan below.

### 1a. ADRs

Glob `scaffold/decisions/ADR-*.md`. Filter to accepted ADRs. For each, check:
- Does it reference a specific system (SYS-### ID)?
- Does it change system ownership, behavior, dependencies, or interfaces?
- Does it affect the single-writer rule for any system's owned state?

### 1b. Known issues

Read `scaffold/decisions/known-issues.md`. Check for entries that:
- Identify system behavior that proved wrong during implementation
- Flag ownership boundaries that broke during spec/task work
- Note cross-system interactions that weren't anticipated

### 1c. Spec/task friction

Search completed specs and tasks for explicit drift evidence. Only treat a spec/task artifact as a drift signal if it contains one of:
- Explicit friction note or unresolved question tied to a system
- Explicit upstream action from triage that moved behavior between systems
- Explicit completion note stating the system doc was inaccurate
- Explicit ownership or dependency correction applied during implementation

Normal implementation detail is not friction. The signal must be explicit, not inferred from code patterns.

### 1d. Code review findings

Search code review logs for:
- Architecture findings that suggest system boundaries are wrong
- Cross-system mutation detected that violates the single-writer rule
- Missing system interactions discovered during implementation

**Evidence threshold:** Code review findings alone indicate divergence but are not sufficient authority for design-led updates unless backed by an accepted ADR, resolved triage decision, completed spec, or explicit user decision. Treat code review findings as WARN-level signals that corroborate other evidence, not standalone authority.

### 1e. Triage and revision logs

Glob triage logs and revision logs. Check for:
- Upstream actions that escalated system-level questions
- Spec/task changes that imply the system doc is outdated
- Recurring friction traceable to a specific system's design

Only check docs that exist — skip missing sources silently.

### 1f. Architectural drift detection (broad scan only)

When running a broad scan (no `--signals`), perform these additional checks that detect systemic drift even when no explicit signal was filed:

**System identity drift** — for each system, compare Purpose and Simulation Responsibility against the behavior described in Player Actions, System Resolution, and State Lifecycle. If the behavior sections now describe a substantially different system than what Purpose claims, flag as identity drift. This is the most dangerous form of silent erosion — a system that quietly became something else while its identity statement stayed the same.

**Cross-system responsibility overlap** — compare Player Actions and Simulation Responsibility across all systems. If two systems describe performing the same simulation decision or controlling the same gameplay outcome (even with different wording), flag as responsibility collision. This differs from owned-state overlap (which validate catches mechanically) — responsibility overlap is behavioral, not structural.

**Spec/system mismatch** — for completed specs, check whether the spec's behavior actor matches the system doc's Simulation Responsibility. If a spec assigns behavior to a system that the system doc says another system owns, flag as boundary erosion.

**Repeated drift pattern** — if a system has received drift signals from 3+ sources (ADRs, triage, specs, code review) within the current phase, flag as system instability. Suggest running `iterate-systems` on that system rather than patching further.

**Emergent subsystem detection** — if a system has accumulated significant new edge cases, new dependencies, and behavior descriptions not present in the latest stabilized version prior to the current implementation feedback window, it may be outgrowing its original scope. These thresholds are heuristics suggesting scope pressure, not proof that a new system is required. Flag for review: does this system need to split, or does it need a scope refresh?

**Interface contract drift** — if a dependency was added or removed in a system doc, and the interacting systems have contracts in `interfaces.md`, verify the interface still matches. Flag stale or missing interface contracts.

**Invariant violation drift** — when implementation feedback implies behavior that contradicts a system's Design Constraints or a referenced Design Invariant, flag as a design-constraint-change signal. This always escalates and may require `revise-design` if the violated constraint originates from a global Design Invariant.

**Dependency direction drift** — when specs, triage decisions, or implementation notes imply that a system previously treated as upstream is now acting downstream (or vice versa), flag as boundary erosion rather than a simple dependency update. A reversed dependency often means the ownership boundary has changed, not just the table entry.

**State lifecycle drift** — if implementation changes when state is created, persisted, cleared, or handed off between systems, flag it. State that now survives longer or shorter than the system doc describes, or state whose lifecycle stage moved between systems, may affect State Lifecycle, Failure / Friction States, and ownership interpretation even when Owned State names do not change.

These detections produce drift signals that flow into Step 2 classification like any other signal. They are classified and escalated normally — not auto-fixed.

## Step 2 — Classify Drift Signals

### 2a. Map signals to systems

For each drift signal, identify which system(s) it affects and what section(s) need attention:

| Signal type | Likely affected sections |
|-------------|------------------------|
| Ownership changed by ADR | Simulation Responsibility, Owned State, Non-Responsibilities |
| New behavior discovered | Player Actions, System Resolution, State Lifecycle, Failure / Friction States |
| Dependency changed | Upstream Dependencies, Downstream Consequences |
| Cross-system contract changed | Upstream Dependencies, Downstream Consequences, Non-Responsibilities |
| Invariant impact | Design Constraints |
| Visibility to player changed | Visibility to Player |
| New edge cases discovered | Edge Cases & Ambiguity Killers |

### 2b. Severity classification

| Severity | Meaning | Action |
|----------|---------|--------|
| **Cosmetic** | Wording clarification that preserves the same meaning already supported elsewhere in the same system doc or by explicit feedback. No new behavioral implication, no narrowing/broadening of scope, no resolution of ambiguity where multiple interpretations exist. | Auto-update: tighten wording |
| **Stale reference** | System doc references renamed/restructured ADR, spec, or system | Auto-update: update reference |
| **Dependency update** | Implementation revealed a new dependency or removed an old one, backed by explicit evidence (ADR, completed spec, triage decision) | Auto-update: add/remove table entry |
| **New edge case** | Implementation discovered an edge case not in the system doc | Auto-update: add to Edge Cases section |
| **Behavior gap (design-led)** | Implementation intentionally added behavior (ADR-backed) not in system doc | Escalate: update system doc to match, with user confirmation |
| **Behavior gap (implementation-led)** | Implementation diverged from system doc without explicit approval | Escalate: system doc should not move to match unapproved divergence |
| **Ownership shift** | State ownership moved between systems (ADR-backed or triage-decided) | Escalate: update Owned State and Non-Responsibilities in both affected systems |
| **Authority violation** | Implementation broke the single-writer rule for owned state | Escalate: reconcile authority |
| **Design constraint change** | Implementation revealed an invariant or boundary no longer applies to this system | Escalate: may require design doc update via revise-design |

### 2b-ii. Design-led vs implementation-led

Before acting on any drift signal, determine its origin:
- **Design-led change** — backed by an accepted ADR, triage decision, or user approval. System doc should catch up.
- **Implementation-led divergence** — the build wandered from the system doc without approval. System doc should *not* automatically update. Escalate.

## Step 3 — Apply Safe Updates

For each **Cosmetic**, **Stale reference**, **Dependency update**, and **New edge case** item:

1. Read the affected system file.
2. Apply the update using the Edit tool.
3. Record what was changed, why, and what feedback triggered it.

**Safety rules:**
- Only edit system files. Never edit design doc, authority.md, interfaces.md, specs, tasks, or other upstream/downstream documents.
- Never change Purpose or Simulation Responsibility — those define the system's identity.
- Never add new Owned State entries. If implementation suggests new state ownership, escalate.
- Never remove Owned State entries. If state was moved to another system, escalate.
- Dependency updates (adding/removing table entries) are safe only when backed by explicit evidence (ADR, completed spec, triage decision). Never update dependencies based on inference alone.
- Edge case additions must describe observed behavior, not invented scenarios.
- Mark auto-updated content with `<!-- REVISED: [date] — [trigger] -->` so fix/iterate passes know what was changed from feedback vs original authoring.

## Step 4 — Escalate Design-Level Changes

For each drift signal classified as non-auto-fixable — including **Behavior gap** (design-led or implementation-led), **Ownership shift**, **Authority violation**, **Design constraint change**, **Identity drift**, **Responsibility collision**, **Dependency direction drift**, **State lifecycle drift**, **Spec/system mismatch**, **Repeated drift pattern**, **Emergent subsystem detection**, and **Invariant violation drift**:

Present using the Human Decision Presentation pattern (see WORKFLOW.md):

```
### System Escalation #N

**Signal:** [source — ADR-###, spec friction, triage action, code review finding]
**Affected system(s):** SYS-### [Name]
**Section(s):** [Owned State, Player Actions, etc.]
**Current system doc says:** [what the system doc states]
**Implementation reality:** [what was actually built or observed]
**Design-led or implementation-led:** [backed by ADR/triage, or unapproved divergence]

**Options:**
a) Update system doc to match implementation — [implication]
b) file via `/scaffold-file-decision --type adr` to correct the implementation — [implication]
c) Defer — file via `/scaffold-file-decision --type ki` for future resolution

**Likely follow-up:** [iterate-systems Topics N,N / revise-design / revise-foundation / none]
```

**For emergent subsystem detection, ownership shift, or identity drift:** include option (d):

```
d) Create a new system to absorb the drifted responsibility — `/scaffold-new-system [name] --split-from SYS-### --trigger [signal]`
```

This routes to the single-system creation skill with full split context. The new system goes through its own overlap/authority audit and interactive definition, then the parent system's Non-Responsibilities and dependency tables are updated automatically.

**For ownership shifts:** present both affected systems side by side so the user can see the full ownership transfer. Likely follow-up: iterate-systems Topics 1,4 on both systems, or option (d) if the shift implies a new system.

**For design constraint changes:** note that this may cascade to `revise-design` if the constraint originates from a Design Invariant. Likely follow-up: revise-design.

**For identity drift:** likely follow-up: iterate-systems Topic 1 (ownership) + Topic 5 (fitness) to evaluate whether the system needs a purpose rewrite or a split via option (d).

## Step 5 — Cross-System Consistency Check

After applying updates and resolving escalations, verify:

- **Dependency symmetry** — if a dependency was added to System A, does System B now need a reciprocal Downstream Consequences entry?
- **Non-Responsibilities alignment** — if an ownership shift moved state from System A to System B, does System A's Non-Responsibilities now list that concern with "(owned by SYS-### [B])"?
- **Authority.md consistency** — if ownership changed and authority.md exists, flag that it may need updating (don't auto-edit it).

Apply safe symmetry updates within system files only when the underlying dependency change is already accepted and unambiguous. If the dependency itself is under escalation or still ambiguous, do not propagate symmetry. Flag authority.md and interfaces.md updates for human action.

## Step 6 — Update Revision History

After all actions (auto-updates, escalation resolutions), append a revision entry to a persistent log:

**Log location:** `scaffold/decisions/revision-logs/REVISION-systems-YYYY-MM-DD.md`

```markdown
# System Revision: YYYY-MM-DD

**Source:** [PHASE-### completed / SLICE-### completed / foundation-recheck / broad scan]
**Feedback items processed:** N
**Auto-updated:** N
**Escalated:** N issues
**Deferred:** N issues
**Systems affected:** [SYS-### list]
**Section groups changed:** [Owned State, Dependencies, Edge Cases, etc.]

## Updates Applied
| # | System | Section | Change | Trigger | Signal Type | Classification |
|---|--------|---------|--------|---------|------------|----------------|
| 1 | SYS-### | Upstream Dependencies | Added SYS-### dependency | ADR-### | ADR | Design-led |
| 2 | SYS-### | Edge Cases | Added "interrupted mid-construction" case | SPEC-### friction | Spec friction | Observed |

## Escalations
| # | Type | System(s) | Resolution |
|---|------|-----------|------------|
| 1 | Ownership shift | SYS-###, SYS-### | User chose option (a) — updated both |
| 2 | Authority violation | SYS-### | User chose option (c) — deferred to KI |

## Deferred Issues
| # | System | Issue | Reason |
|---|--------|-------|--------|
| 1 | SYS-### | New failure path discovered | Needs more implementation data |
```

## Step 7 — Report

```
## Systems Revised

### Summary
| Field | Value |
|-------|-------|
| Source | [PHASE-### / SLICE-### / foundation-recheck / broad scan] |
| Feedback items | N processed |
| Auto-updated | N |
| Escalated | N issues (N resolved, N deferred) |
| Systems affected | N |
| Section groups changed | [list] |

### Systems Confidence
**Stable / Decreased / Improved** — [Based on: number and severity of drift signals, whether ownership boundaries held, whether cross-system consistency is intact.]

### Next Steps
- Run `/scaffold-fix systems SYS-###-SYS-###` to clean up mechanical issues from updates
- Run `/scaffold-iterate systems --topics "[affected topics]" SYS-###-SYS-###` to review changed areas
- Run `/scaffold-validate --scope systems` to confirm structural readiness
```

If no drift detected:
```
## Systems Revised

**Status: No drift detected** — system docs are consistent with implementation feedback. No changes made.
```

## Rules

- **Only edit system files.** Never edit design doc, authority.md, interfaces.md, specs, tasks, engine docs, or other documents.
- **System identity is sacred until the user changes it.** Never auto-update Purpose, Simulation Responsibility, or Design Constraints. Those define what the system is.
- **Ownership changes are always escalated.** Never auto-add or auto-remove Owned State entries. Moving state between systems is a design decision.
- **Only accepted or observed signals count as drift.** Do not revise system docs based on speculative proposals, unaccepted ADRs, or triage options that were discussed but not chosen. Proposed ≠ accepted. Explored ≠ decided.
- **Design-led changes catch up. Implementation-led divergence escalates.** If the team intentionally changed direction (ADR-backed), the system doc should update. If the build wandered without approval, escalate — don't silently accept.
- **Dependency updates require explicit evidence.** Only add/remove dependency table entries when backed by an ADR, completed spec, or triage decision. Never update dependencies based on inference from code alone.
- **Edge case additions describe observed behavior.** Only add edge cases that were actually encountered during implementation or testing. Don't invent hypothetical scenarios.
- **Cross-system updates are bounded.** Apply symmetry fixes (reciprocal dependency entries) within system files. Flag authority.md and interfaces.md updates for human action.
- **Deferred issues are routed by type.** Active risks or mismatches go to `scaffold/decisions/known-issues.md`. Purely strategic deferred decisions may remain in the revision log only.
- **No inferred behavior catch-up.** Missing behavior discovered during implementation is not auto-added to the system doc unless explicitly approved through ADR, triage, or user decision. The skill may record the gap or escalate it, but must not convert emergent implementation behavior into design canon by implication.
- **Revision suppression when identity is unstable.** If identity drift, repeated drift pattern, or emergent subsystem detection is present for a system, prefer escalation over continued local catch-up. Auto-updates may still apply for unrelated stale references, but behavior-adjacent updates should be suppressed until the system boundary is reviewed.
- **Repeated drift pattern suppresses further patching.** When a system is flagged as unstable (3+ drift sources), do not continue non-essential auto-updates. Escalate as a meta-signal and suggest `iterate-systems` instead.
- **Interface contract drift is always escalation, never auto-update.** Even if the interface mismatch seems obvious, this skill cannot edit `interfaces.md`. Flag it for human action.
- **Global invariants outrank system-level constraints.** When checking invariant violation drift, Design Invariants in `design/design-doc.md` take precedence over a system's local Design Constraints section if they conflict.
- **Foundation-recheck boundary.** When triggered by `--source foundation-recheck`, only process signals that change system ownership assumptions, documented interfaces, or cross-system dependencies. Pure engine/internal architecture changes from the foundation layer do not directly revise system docs.
- **Classify before acting.** Every feedback item must be classified before any edits occur.
- **Always write a revision log.** Every run produces a dated record in `scaffold/decisions/revision-logs/`.
- **Confidence heuristic.** Improved: mostly auto-updates, ownership boundaries held, no escalations. Stable: mix of auto-updates and escalations, ownership intact. Decreased: ownership shifts, authority violations, or multiple systems affected by the same drift signal.

---
name: scaffold-approve-phases
description: Lifecycle gate that approves a single Draft phase for slice seeding. Enforces ordering, freshness, entry criteria satisfaction, and content readiness. Renames file, updates index and roadmap.
argument-hint: PHASE-###
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# Approve Phase

Approve a single phase for slice seeding: **$ARGUMENTS**

This skill is a **lifecycle gate**, not a planning-analysis skill. It relies on earlier skills (`fix-phase`, `iterate-phase`, `validate`) for deep review, then runs a hard, narrow readiness check and transitions the file.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PHASE-###` | Yes | — | The specific phase to approve. Must be the next Draft phase in roadmap order. |

## Edge Cases

- **Phase file missing** → stop: "PHASE-### is registered but no file exists."
- **Phase is already Approved** → stop: "PHASE-### is already Approved. No action needed."
- **Phase is Complete** → stop: "PHASE-### is already Complete."
- **Status-filename mismatch** → run `/scaffold-validate --scope phases` and stop.

## Preconditions

Run in order. If any hard stop fails, report and stop.

### 1. Phase validation passes

Run `/scaffold-validate --scope phases` as part of approval. Do not rely on prior results — always run fresh. Approval cannot proceed if validation fails.

This is a **hard stop**.

### 2. No other phase is Approved but not Complete

If another phase is already Approved and not Complete (active), **stop**: "Another phase is already active: PHASE-### — [Name] (Status: Approved). Complete it before approving another."

This is a **hard stop** — only one active phase at a time, matching the single-active-slice discipline at the slice level.

### 3. Phase is next in roadmap order

The target must be the next Draft phase in `scaffold/phases/roadmap.md` ordering.

If not, **stop**: "PHASE-### is not the next Draft phase in roadmap order. PHASE-### is earlier and still Draft."

**Override path:** User may explicitly confirm out-of-order approval.

This is a **hard stop with explicit override**.

### 4. Entry criteria are satisfied

Read the phase's Entry Criteria. For each criterion:
- If it references a phase ID (e.g., "P1-001 Complete"), verify that phase's status is Complete.
- If it references a system ID (e.g., "SYS-003 designed"), verify the system file exists and contains more than placeholder content (not an empty stub or TODO-only document).
- If it references a foundation decision, verify architecture.md addresses it.

If any entry criterion is unmet, **stop** and report which criteria are unsatisfied.

This is a **hard stop** — no override. A phase with unmet entry criteria cannot start.

### 5. Review and iterate freshness

Verify an iterate log exists:
- Glob `scaffold/decisions/review/ITERATE-phase-PHASE-###-*.md` for the iterate log.

If no iterate log exists, **stop**: "PHASE-### was never iterated. Run `/scaffold-iterate phase` before approving."

If the phase file was modified after the most recent iterate log, **stop**: "PHASE-### was modified after its last review (log: YYYY-MM-DD, file modified: YYYY-MM-DD). Rerun `/scaffold-fix phase` and `/scaffold-iterate phase`."

This is a **hard stop**.

### 6. No unresolved escalated issues from iterate

Read the latest iterate log (`scaffold/decisions/review/ITERATE-phase-PHASE-###-*.md`). If it contains escalated issues presented to the user (Human Decision Presentation pattern), verify they have been resolved. Unresolved escalations mean the reviewer and Claude could not agree — approval without human resolution is unsafe.

If unresolved escalations exist, **stop**: "Iterate log contains N unresolved escalated issues. Resolve them before approving."

This is a **hard stop**.

### 7. No pending ADRs or KIs that affect scope

Check for accepted ADRs created after the timestamp of the most recent iterate log that affect systems in this phase's scope. An ADR/KI "affects scope" if it: changes an in-scope system's authority, changes phase ordering prerequisites, adds/removes an explicit dependency, or invalidates a capability, deliverable, or exit criterion. Check known issues that constrain this phase.

If pending items materially affect the phase's scope, **stop** and require resolution or explicit override.

This is a **hard stop with explicit override**.

### 8. Content readiness

| Section | Readiness Criteria |
|---------|-------------------|
| Goal | Outcome-oriented, not task-oriented. Not template text. |
| Capability Unlocked | States what the team can now do that they couldn't before. Concrete enough that QA could test it without reading code. |
| Entry Criteria | References specific IDs (phase, system, or foundation). Prefers phase IDs for sequencing. |
| In Scope | At least 1 specific, sliceable scope item. No vague categories (e.g., "StormSystem" alone is not sliceable — "storm events damage exposed structures" is). |
| Out of Scope | Present and draws at least one meaningful boundary. May be minimal if scope is already singular and unambiguous. |
| Non-Goals | At least 1 thing intentionally not solved. |
| Deliverables | At least 1 demonstrable output. |
| Exit Criteria | Falsifiable conditions demonstrable in a playtest or dev demo. |
| Slice Strategy | Describes expected slice characteristics — guides downstream slice seeding. |
| Risk Focus | At least 1 major risk or unknown this phase reduces. |
| Phase Demo | Step-by-step walkthrough with concrete actions and expected results. |
| System Readiness | Expected maturity for each in-scope system (table). |
| Dependencies | Specific references or explicitly "none". |
| General | No TODOs, template text, or placeholders. |

### 9. Slice seeding readiness

Verify that In Scope items are specific enough to generate slice candidates without introducing new systems or inventing undefined behaviors. This is the final gate before slice generation — approval unlocks `/scaffold-seed slices`.

If In Scope items are too abstract (system names instead of behaviors), **stop**: "In Scope items are not sliceable. Run `/scaffold-fix phase` or `/scaffold-iterate phase` to tighten scope."

This is a **hard stop**.

If any content readiness or slice readiness check fails, **stop** and suggest running `/scaffold-fix phase`.

## Step 1 — Approve the Phase

1. Update `> **Status:**` from `Draft` to `Approved`.
2. Rename: `PHASE-###-name_draft.md` → `PHASE-###-name_approved.md` using `git mv`.
3. Update `scaffold/phases/_index.md` with the new filename.
4. Update `scaffold/phases/roadmap.md` Phase Overview status.

## Step 2 — Report

```
## Phase Approved: PHASE-### — [Name]

### Gate Summary
| Check | Result |
|-------|--------|
| Validation | PASS |
| Single active phase | PASS |
| Roadmap order | PASS |
| Entry criteria satisfied | PASS |
| Review freshness | PASS (iterated YYYY-MM-DD) |
| Unresolved escalations | PASS |
| ADR/KI currency | PASS |
| Content readiness | PASS |
| Slice seeding readiness | PASS |

### Approved Phase Summary
- **Goal:** [what this phase delivers]
- **In Scope:** [systems and features]
- **Exit Criteria:** [verifiable conditions]

### Remaining Draft Phases
| Order | Phase | Status |
|-------|-------|--------|
| N+1 | PHASE-### — [Name] | Draft |
| ... | ... | ... |

### Next Steps
- Run `/scaffold-seed slices` to generate vertical slices for this phase
- Or run `/scaffold-new-slice [slice-name]` to create slices one at a time
- After implementing this phase, run `/scaffold-revise-phases PHASE-###` to update remaining phases
```

## Rules

- **This is a lifecycle gate, not a review skill.** It checks whether the phase has passed through the pipeline and is ready to transition.
- **This skill never rewrites phase content to make it approvable.** If any check fails, stop and direct the user to `/scaffold-fix phase` or `/scaffold-iterate phase`. The gate is pure — it only reads and judges.
- **One phase at a time.** Only one Approved-not-Complete phase may exist.
- **Roadmap order is enforced.** Out-of-order approval requires explicit override.
- **Entry criteria are a hard stop.** No override — prerequisites must be met.
- **Review freshness is enforced.** Modified-after-review blocks approval.
- **Content must be operationally ready.** Every section must pass concrete readiness criteria.
- **File renames use git mv.**
- **Index and roadmap updates are mandatory.**
- **The report is an audit trail.** The gate summary makes approval decisions traceable.

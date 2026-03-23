---
name: scaffold-approve-slices
description: Lifecycle gate that approves a single Draft slice for spec seeding. Enforces order, freshness, single-active-slice discipline, dependency resolution, and content readiness. Renames file, updates index.
argument-hint: SLICE-###
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# Approve Slice

Approve a single slice for spec seeding: **$ARGUMENTS**

This skill is a **lifecycle gate**, not a planning-analysis skill. It relies on earlier skills (`review-slice`, `iterate-slice`, `validate`) for deep review, then runs a hard, narrow readiness check and transitions the file. If this gate passes, the slice is safe to enter spec seeding.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLICE-###` | Yes | — | The specific slice to approve. Must be the next Draft slice in implementation order. |

## Edge Cases

Before running preconditions, handle these deterministically:

- **Slice file missing** (index row exists but file doesn't) → stop with error: "SLICE-### is registered in _index.md but no file exists. Fix the index or recreate the file."
- **Slice is already Approved** → stop: "SLICE-### is already Approved. No action needed."
- **Slice is Complete** → stop: "SLICE-### is already Complete. Approval is a pre-implementation gate."
- **Index row exists but filename/status mismatch** → run `/scaffold-validate --scope slices` and stop. Let validation own this responsibility.

## Preconditions

Before approving, verify **all** conditions. If any hard stop fails, report and stop. Run preconditions in order — later checks may depend on earlier ones.

### 1. Slice validation passes

Run `/scaffold-validate --scope slices` or verify its results are current. Approval cannot proceed if validation fails. Validate covers structural integrity (slice index sync, slice-phase membership, status-filename sync, dependency resolution, dependency order, interface resolution).

This is a **hard stop**.

### 2. Single active slice discipline

Read all slices in the same phase. If another slice is already **Approved but not yet Complete**, **stop**. Only one slice may be active (Approved and in-progress) at a time per phase.

Report: "Another slice in this phase is already active: SLICE-### — [Name] (Status: Approved). Complete that slice before approving another."

This is a **hard stop** — it prevents multi-slice activation, which defeats the one-at-a-time feedback loop.

### 3. Slice is next in implementation order

Determine canonical order from `scaffold/slices/_index.md`. The target must be the **earliest slice in that order with status Draft**.

If not, **stop**: "SLICE-### is not the next Draft slice in implementation order. SLICE-### (position N) is earlier and still Draft. Approve that one first, or explicitly override."

**Override path:** The user may explicitly confirm with something like "Approve SLICE-### out of order despite earlier Draft slice SLICE-###." Do not infer override intent — the user must state it.

This is a **hard stop with explicit override**.

### 4. All declared dependencies are Complete

Read the slice's `> **Depends on:**` field. If it lists SLICE-### IDs:
- For each dependency, verify the referenced slice file exists and has `> **Status:** Complete`.
- If any dependency is not Complete, **stop**. Report which dependencies are unmet and their current status.

If the field is "—" or absent, skip this check.

This is a **hard stop** — no override. Approving a slice with unmet dependencies defeats the purpose of the dependency declaration.

### 5. Review and iterate freshness

The pipeline before approval is: `review-slice` → `iterate-slice` → `approve-slices`. Both stages must have run.

Verify that **both** review and iterate logs exist for this slice:
- Glob `scaffold/decisions/review/REVIEW-slice-SLICE-###-*.md` for the review log (from `/scaffold-review-slice`).
- Glob `scaffold/decisions/review/ITERATE-slice-SLICE-###-*.md` for the iterate log (from `/scaffold-iterate slice`).

Checks:
- If no review log exists, **stop**: "No review log found for SLICE-###. Run `/scaffold-review-slice` and `/scaffold-iterate slice` before approving."
- If a review log exists but no iterate log exists, **stop**: "SLICE-### was reviewed but never iterated. Run `/scaffold-iterate slice` before approving."
- If both exist, determine the **latest** timestamp across the newest REVIEW log and the newest ITERATE log. Compare the slice file's last-modified date against that latest timestamp. If the slice file was modified after it, **stop**: "SLICE-### was modified after its last review/iterate (latest log: YYYY-MM-DD, file modified: YYYY-MM-DD). Rerun `/scaffold-review-slice` and `/scaffold-iterate slice`."

This is a **hard stop** — approving content that skipped adversarial review bypasses the review gate.

### 6. No pending upstream actions that affect slice scope

Read all upstream action sources for this phase:
- Accepted ADRs (`scaffold/decisions/ADR-*_accepted.md`) filed after this slice was last reviewed
- Open known issues (`scaffold/decisions/known-issues.md`)
- Revision logs (`scaffold/decisions/revision-logs/REVISION-post-SLICE-*.md`) for completed slices in this phase
- Review/iterate logs that logged out-of-slice action items (`scaffold/decisions/review/REVIEW-*SLICE-*.md`)

If any upstream action with status **Pending** materially affects this slice's:
- Systems covered
- Interfaces exercised
- Authority assumptions
- Phase proof intent

Then **stop**. Report the affected areas and require the user to resolve the upstream action or explicitly confirm approval against current architecture.

The user must explicitly state approval — do not infer override intent.

This is a **hard stop with explicit override**.

### 7. Phase-scope alignment

Read the parent phase file. Verify the slice's goal still matches the phase's current in-scope proof.

If the phase was re-scoped (check revision logs, ADRs filed after slice creation, or phase file modification date vs slice review date) and the slice wasn't updated to match, **stop**: "Phase PHASE-### may have been re-scoped since this slice was last updated. Verify the slice still matches phase scope, or rerun `/scaffold-review-slice`."

This is a **hard stop with explicit override**.

### 8. No spec pipeline drift

Check whether any **later** slice in the phase (by index order) already has seeded or Approved specs.

- If a later slice has Approved specs, **stop**: "SLICE-### (later in order) already has Approved specs. The pipeline has drifted out of order. Resolve before approving this slice."
- If a later slice has Draft specs, **warn**: "SLICE-### (later in order) already has seeded specs. This is unusual — verify the pipeline order is intentional."

## Step 1 — Verify Content Readiness

Read the slice file. Verify all required sections pass these operational checks:

| Section | Readiness Criteria |
|---------|-------------------|
| Goal | Describes a player-visible proof across 2+ systems. Not a template default, TODO, or internal technical milestone. |
| Proof Value | States what uncertainty this slice reduces. Specific enough to evaluate whether the slice is worth implementing. |
| Assumptions | Lists what must already be true. Consistent with Depends on and earlier completed slices. |
| Starting Conditions | Explicit pre-demo state. Reproducible. |
| Systems Covered | Non-empty. Every listed system is referenced in the goal or demo. |
| Integration Points | References real interfaces from `interfaces.md`, or explicitly justifies direct dependencies. |
| Done Criteria | Every criterion is falsifiable — a test can definitively pass or fail it. |
| Failure Modes | At least 1 failure this slice would expose. Defines the slice by bugs it catches. |
| Visible Proof | Player-visible results — not logs or internal inspection. |
| Demo Script | Proves each Done Criterion. Uses Starting Conditions. Executable steps with concrete expected results. |
| General | No unresolved placeholders, TODOs, or template text anywhere in the file. |
| Hidden prerequisites | No behavior assumed by the goal/demo that earlier completed slices have not established and that is not declared in Assumptions, Systems Covered, or Depends on. |

If any check fails, **stop** and suggest running `/scaffold-review-slice` first.

## Step 2 — Approve the Slice

1. Update the slice file's `> **Status:**` line from `Draft` to `Approved`.
2. Rename the file: `SLICE-###-name_draft.md` → `SLICE-###-name_approved.md` using `git mv`.
3. Update `scaffold/slices/_index.md` — change the filename reference to the new name.

## Step 3 — Report

```
## Slice Approved: SLICE-### — [Name]

**Phase:** PHASE-### — [Name]
**Implementation order position:** N of M slices in phase

### Gate Summary
| Check | Result |
|-------|--------|
| Validation | PASS |
| Single active slice | PASS |
| Implementation order | PASS |
| Dependencies Complete | PASS / N/A (no dependencies) |
| Review freshness | PASS (reviewed YYYY-MM-DD) |
| Upstream actions | PASS / PASS (overridden — [reason]) |
| Phase-scope alignment | PASS |
| Spec pipeline order | PASS |
| Content readiness | PASS |

### Approved Slice Summary
- **Goal:** [the end-to-end experience]
- **Depends on:** [SLICE-### IDs or "—"]
- **Systems:** [list]
- **Integration Points:** [list]
- **Done Criteria:** [list]

### Remaining Draft Slices in Phase
| Order | Slice | Status | Notes |
|-------|-------|--------|-------|
| N+1 | SLICE-### — [Name] | Draft | Next after this one |
| N+2 | SLICE-### — [Name] | Draft | |
| ... | ... | ... | ... |

### Next Steps
- Run `/scaffold-seed specs` for SLICE-### to generate behavior specs
- Or run `/scaffold-new-spec` to create specs one at a time
- After implementing this slice, run `/scaffold-revise-slices SLICE-###` to update remaining slices
```

## Rules

- **This is a lifecycle gate, not a review skill.** It does not analyze slice quality — that's `review-slice` and `iterate-slice`. It checks whether the slice has passed through the review pipeline and is structurally ready to transition.
- **One slice at a time.** Exactly one slice per invocation. Batch approval defeats the purpose — later slices may change based on implementation feedback.
- **One active slice per phase.** If another slice is Approved but not Complete, this gate blocks. Complete the active slice first.
- **Implementation order is enforced.** Out-of-order approval requires explicit user override with stated reason.
- **Validation is a prerequisite.** `/scaffold-validate --scope slices` must pass.
- **Review freshness is enforced.** If the slice changed after its last review, re-review before approving.
- **Dependencies are a hard stop.** No override — all declared dependencies must be Complete.
- **Upstream actions require resolution or explicit override.** Pending actions that affect this slice's scope block approval.
- **Phase-scope drift blocks approval.** If the phase was re-scoped and the slice wasn't updated, stop.
- **Content must be operationally ready.** Every section must pass concrete readiness criteria, not just "looks filled in."
- **File renames use git mv.** Always use `git mv` so git tracks the rename.
- **Index updates are mandatory.** `scaffold/slices/_index.md` stores filename references.
- **The report is an audit trail.** The gate summary makes approval decisions traceable.

**Why one slice at a time:** Slices are living planning documents. Each implementation cycle produces ADRs, known issues, and triage decisions that may change remaining slices. Approving all slices upfront locks in assumptions that haven't been validated. Approving one at a time ensures each slice reflects current reality.

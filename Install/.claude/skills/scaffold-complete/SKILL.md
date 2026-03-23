---
name: scaffold-complete
description: Mark a planning-layer document (task, spec, slice, or phase) as Complete. Automatically ripples upward through the planning hierarchy when all children are done.
argument-hint: [document-path or ID]
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# Mark Document Complete

Mark a planning-layer document as `Complete` and ripple the status upward through the hierarchy: **$ARGUMENTS**

## Scope

This skill applies only to **planning-layer documents** — tasks, specs, slices, and phases. Design docs, style docs, reference docs, engine docs, and theory docs use `Approved` as their terminal status and are not eligible for `Complete`.

**Phase policy:** Phases can be targeted directly (manual completion), but are **never auto-rippled** from slice completion. Phase scope may exceed the slices that currently exist as files — future slices may not yet be defined. Completing a phase is always a deliberate user decision.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `document-path` | Yes | File path or document ID (e.g., `TASK-001`, `SPEC-003`, `SLICE-002`, `P1-001`) |

## Steps

### 1. Resolve Target

Resolve the document path:
- If a path is given, verify the file exists.
- If a document ID is given, find the matching file:
  - `TASK-###` → `scaffold/tasks/TASK-###-*.md`
  - `SPEC-###` → `scaffold/specs/SPEC-###-*.md`
  - `SLICE-###` → `scaffold/slices/SLICE-###-*.md`
  - `PHASE-###` → `scaffold/phases/PHASE-###-*.md`

If the document is not a planning-layer type (task, spec, slice, or phase), report the error and stop. Only planning-layer docs can be marked Complete.

### 2. Read the Document

Read the target document. Extract:
- Its current `> **Status:**` value.
- Its type (task, spec, slice, or phase) from the path or ID prefix.
- Its parent linkage fields (see Linkage Fields below).

### 2b. Early Exit if Already Complete

If the document's status is already `Complete`, report that and stop. Skip all remaining steps — no eligibility checks, no ripple, no file operations.

### 3. Check Eligibility

**For tasks:** Tasks can be marked Complete from any status (Draft, Review, or Approved). No child check needed — tasks are leaf nodes.

**For specs, slices, and phases:** Before marking Complete, verify that **all children** are already Complete:
- **Spec:** Find all existing tasks that implement it (grep `scaffold/tasks/TASK-*.md` for `Implements: SPEC-###`). All must have `Status: Complete`. This means "all defined implementing tasks are done" — if future tasks haven't been created yet, that's the user's responsibility to ensure before targeting the spec.
- **Slice:** Read the slice's "Specs Included" table. Every listed spec must have `Status: Complete`.
- **Phase:** Find all slices in this phase (grep `scaffold/slices/SLICE-*.md` for `Phase: PHASE-###`). All must have `Status: Complete`.

If any children are not Complete, report what's still pending and stop. Do not mark the document Complete.

### 3b. ADR Absorption Check (slices only)

When the target is a **slice** (or when ripple reaches a slice in step 5), verify that all ADRs filed during the slice's implementation have been absorbed into affected planning documents before marking it Complete.

1. Read the slice to identify its covered systems (from "Systems Covered" table) and specs (from "Specs" table).
2. Find all ADRs with status `Accepted` (grep `scaffold/decisions/ADR-*.md` for `Status:` line, filter to Accepted only).
3. From those accepted ADRs, grep for references to any of this slice's system IDs (e.g., `SYS-011`) or spec IDs (e.g., `SPEC-016`). Draft or Proposed ADRs do not block completion.
4. For each matching accepted ADR:
   - Identify which system designs (`scaffold/design/systems/SYS-###-*.md`) and specs (`scaffold/specs/SPEC-###-*.md`) the ADR affects.
   - Check if those documents have a `Changelog` entry mentioning the ADR (e.g., "per ADR-008").
5. If any accepted ADR has **not** been absorbed into all affected system designs and specs, report the gap:
   - List the ADR, the affected documents, and what's missing.
   - **Stop.** Do not mark the slice Complete until ADR changes are reflected in all affected planning docs.
6. If all ADRs are absorbed (or no ADRs reference this slice's systems/specs), proceed to step 4.

**Assumption:** This check relies on ADRs referencing affected systems and specs by their canonical IDs (`SYS-###`, `SPEC-###`). ADRs that use only prose references without IDs will not be discovered. Accepted ADRs **must** include explicit `SYS-###` and/or `SPEC-###` references to affected documents for this check to work.

**Rationale:** ADRs represent design changes discovered during implementation. If the code changed but the specs and system designs weren't updated to match, the planning docs are inaccurate. This check ensures the scaffold stays self-consistent — implementation feeds back into design before a slice closes.

### 4. Set Status to Complete

Update the document's `> **Status:**` line to `Complete` using the Edit tool.

### 4b. Rename File to Match Status

Rename the file to replace its current status suffix (`_draft`, `_review`, or `_approved`) with `_complete` using `git mv`. For example: `TASK-001-name_approved.md` → `TASK-001-name_complete.md`. Then update the type-specific `_index.md` link to point to the new filename:

- Task → `scaffold/tasks/_index.md`
- Spec → `scaffold/specs/_index.md`
- Slice → `scaffold/slices/_index.md`
- Phase → `scaffold/phases/_index.md`

### 5. Ripple Upward

After marking the target Complete, check whether the target's parent can now also be marked Complete. Follow the ripple chain:

**Task → Spec:**
1. Read the task's `Implements: SPEC-###` field to find the parent spec.
2. Find the parent spec file (`scaffold/specs/SPEC-###-*.md`).
3. Find all existing tasks that implement this spec (grep `scaffold/tasks/TASK-*.md` for `Implements: SPEC-###`). Only tasks that currently exist as files are considered — undefined future tasks do not block ripple.
4. If ALL existing tasks for this spec are now Complete, set the spec's status to Complete and rename the file to replace its current status suffix with `_complete` using `git mv`. Update `scaffold/specs/_index.md`.
5. If the spec was marked Complete, continue rippling to its slice.

**Spec → Slice:**
1. Find which slice includes this spec. Grep `scaffold/slices/SLICE-*.md` for the spec ID (e.g., `SPEC-###`). If multiple slices reference the spec, report the ambiguity and stop — a spec must belong to exactly one slice.
2. Read the slice's "Specs Included" table to get all its specs.
3. If ALL specs in the slice are now Complete, run the **ADR Absorption Check (step 3b)** before proceeding. If the check fails, stop rippling and report the unabsorbed ADRs.
4. If the ADR check passes, set the slice's status to Complete and rename the file to replace its current status suffix with `_complete` using `git mv`. Update `scaffold/slices/_index.md`.
5. If the slice was marked Complete, continue rippling to its phase.

**Slice → Phase: No automatic ripple.** Phases have exit criteria and scope that extend beyond the slices that currently exist as files — future slices may not yet be defined. Completing a phase is a manual decision. When a slice completes, report which phase it belongs to but do **not** check or update the phase's status.

At each ripple level, if not all children are Complete, stop rippling. The parent stays at its current status.

### 6. Report

Present a summary to the user:

- **Marked Complete:** List every document whose status was changed to Complete (the target + any parents that rippled).
- **Ripple stopped at:** If ripple stopped before reaching the top, state which parent still has pending children and list them.
- **Already Complete:** If the target was already Complete, report that and skip all steps.

## Linkage Fields

| Doc Type | Parent Link Field | How to Find Children |
|----------|------------------|---------------------|
| Task | `Implements: SPEC-###` | (leaf node — no children) |
| Spec | (found via slice's "Specs Included" table) | Grep `scaffold/tasks/TASK-*.md` for `Implements: SPEC-###` |
| Slice | `Phase: PHASE-###` | Read "Specs Included" table in the slice |
| Phase | (top of hierarchy) | Grep `scaffold/slices/SLICE-*.md` for `Phase: PHASE-###` |

## Rules

- **Planning-layer only.** Never mark design, style, reference, engine, or theory docs as Complete. Report an error if attempted.
- **No strict prerequisite for tasks.** A task can go from Draft, Review, or Approved directly to Complete.
- **Children must be Complete first.** Specs, slices, and phases cannot be marked Complete unless all their children are already Complete.
- **Ripple is automatic up to slice level.** After marking a document Complete, always check parents. Never skip the ripple check. Ripple stops at slices — phases are never auto-completed.
- **Stop rippling on failure.** If a parent has incomplete children, stop. Don't continue checking grandparents.
- **Idempotent.** If the target is already Complete, report it and do nothing.
- **Read before writing.** Always read a document's current status before attempting to change it.

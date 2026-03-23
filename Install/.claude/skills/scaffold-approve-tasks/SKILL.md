---
name: scaffold-approve-tasks
description: Mark all Draft tasks in a slice as Approved after reorder confirms the task graph is clean. Renames files, updates indexes, and syncs the slice table.
argument-hint: SLICE-###
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# Approve Tasks

Approve all implementation-ready tasks in: **$ARGUMENTS**

This skill is the final gate before implementation. It marks Draft tasks as Approved, renames files to match the status convention, and updates all indexes. Run this only after the task stabilization loop produces no new issues, `/scaffold-reorder-tasks` has confirmed the task graph is clean, and `/scaffold-validate --scope tasks` passes.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLICE-###` | Yes | — | The slice whose tasks should be approved. |

## Preconditions

Before approving, verify all three conditions. If any fails, stop and report.

### 1. Task graph validation passes

Run `/scaffold-validate --scope tasks`. Approval cannot proceed if validation fails. Validate covers structural integrity (task index sync, slice-task membership, status-filename sync, slice-table-status sync, order integrity, reference file resolution, triage upstream targets).

Additionally, check content readiness: the slice's Tasks table must have populated Order values and the table structure must match reorder's output format (Order, ID, Name, Spec, Status, Dependencies columns). If the table looks like it hasn't been through reorder, stop and suggest running `/scaffold-reorder-tasks` first.

### 2. No graph integrity issues that block approval

Check for structural problems that make approval unsafe:
- Check for any task whose dependencies reference a task ID not present in the slice table. A dependency on a task outside the slice is valid only if that task's file exists and has status `Approved` or `Complete` — it represents completed upstream work. Otherwise it's a broken edge.
- Walk the dependency annotations in the slice table to check for cycles of any length (A → B → C → A), not just pairwise mutual dependencies.

If broken edges or cycles are found, report them and stop.

Tasks with `> **Blocked by:**` notes do **not** block approval of other tasks. They remain Draft and are skipped in Step 1. Only graph integrity problems stop the whole approval run.

### 3. No pending upstream actions that affect task meaning

Read `scaffold/decisions/triage-logs/TRIAGE-SLICE-###.md` if it exists. If any upstream action with status **Pending** affects behavior-defining architecture that tasks depend on, **stop**. This includes actions that change:
- Acceptance criteria
- System ownership (which system owns a behavior or data)
- Authority rules (cross-system data writes)
- State transitions (state-machine meaning)
- Interfaces/contracts (cross-system behavioral contracts)
- Persistence assumptions (what gets saved/loaded)
- ADR outcomes that alter implementation assumptions

Report the affected tasks and require the user to resolve the upstream action or explicitly confirm approval against current architecture. The user must explicitly state approval — do not infer override intent from vague confirmation. Ask specifically: "Approve these N tasks against current architecture despite pending upstream action #X?"

Upstream actions that don't affect task meaning (e.g., documentation clarifications, glossary additions) do not block approval.

## Step 1 — Identify Tasks to Approve

1. Read the slice's Tasks table.
2. For each task in the table, read the actual task file. If a task file referenced in the table does not exist, report the inconsistency and stop — suggest rerunning `/scaffold-reorder-tasks` to resync.
3. Check the task's `> **Status:**` line and scan its Notes section.
4. Categorize each task:

| Category | Condition | Action |
|----------|-----------|--------|
| **To approve** | Status is `Draft`, no blocker notes | Approve in Step 2 |
| **Risk-accepted** | Status is `Draft`, Notes contain `> **Known risk:**` | Approve in Step 2, but report prominently |
| **Blocked** | Notes contain `> **Blocked by:**` | Skip — stays Draft, report separately |
| **Deferred** | Triage log `TRIAGE-SLICE-###.md` Decisions table has a Defer decision matching this task's ID | Skip — stays Draft, report separately |
| **Already approved** | Status is `Approved` | Skip |
| **Already complete** | Status is `Complete` | Skip — verify slice table also shows Complete |

Tasks with unresolved blockers remain Draft. Other tasks may still be approved — blocked tasks do not prevent approval of the rest of the slice's tasks.

5. If no tasks are eligible for approval, report that and exit without modifying files.

## Step 2 — Approve Each Task

For each task to approve (including risk-accepted tasks):

1. Update the task file's `> **Status:**` line from `Draft` to `Approved`.
2. Rename the file: `TASK-###-name_draft.md` → `TASK-###-name_approved.md` using `git mv`.
3. Update `scaffold/tasks/_index.md` — change the filename reference to the new name.
4. Update the slice's Tasks table — set the Status column to `Approved`.

Note: The slice's Tasks table stores status, not filenames. Filename references live only in `scaffold/tasks/_index.md`.

## Step 3 — Report

```
## Approval Complete: SLICE-### — [Name]

### Most Dangerous Blocking Issue
[If any tasks were blocked, deferred, or have known risks, state the single issue most likely to cause downstream problems. If none, write "No blocking issues."]

| Metric | Value |
|--------|-------|
| Tasks approved | N |
| Risk-accepted | N (approved with known risks) |
| Already approved | N (skipped) |
| Already complete | N (skipped) |
| Blocked/deferred | N (skipped — stays Draft) |
| Total in slice | N |

### Approved Tasks
| ID | Name | Spec | Order | Notes |
|----|------|------|-------|-------|
| TASK-### | [Name] | SPEC-### | 1 | |
| TASK-### | [Name] | SPEC-### | 3 | ⚠ Known risk: KI-### |
| ... | ... | ... | ... | ... |

### Blocked/Deferred Tasks
[List tasks that were skipped with reason. If none, write "None."]

### Next Steps
- Run `/scaffold-implement TASK-###-TASK-###` in the order from `/scaffold-reorder-tasks`
- If blocked tasks need resolving, address their blockers then re-run `/scaffold-approve-tasks`
```

## Rules

- **Only approve Draft tasks.** Never re-approve Approved or Complete tasks.
- **Validation is a prerequisite.** `/scaffold-validate --scope tasks` must pass before approval. Structural integrity is validate's job — approval only adds content-readiness checks on top.
- **Blocked tasks stay Draft but don't block others.** Tasks with `> **Blocked by:**` notes remain Draft. Other eligible tasks in the slice may still be approved.
- **Risk-accepted tasks are approvable.** Tasks with `> **Known risk:**` notes are approved but reported prominently.
- **Complete tasks must be consistent.** If a task has status Complete in the file, verify the slice table also shows Complete. Flag mismatches.
- **Architecture-impacting upstream actions are a hard stop.** If a pending upstream action would change ownership, authority, state transitions, interfaces, persistence, acceptance criteria, or other behavior-defining architecture that tasks depend on, stop and require resolution or explicit override.
- **No-op exits cleanly.** If no tasks are eligible for approval, report that and exit without modifying files.
- **Missing files are an inconsistency.** If the slice table references a task whose file doesn't exist, stop and suggest rerunning `/scaffold-reorder-tasks`.
- **File renames use git mv.** Always use `git mv` so git tracks the rename.
- **Index updates are mandatory.** `scaffold/tasks/_index.md` stores filename references. The slice's Tasks table stores status and order. Both must be updated, but they track different things.

**Why approval is a separate skill:** Reorder is graph logic (dependency analysis, topological sort, table regeneration). Approval is lifecycle management (status changes, file renames, index updates). Keeping them separate means reorder can run multiple times without side effects, and approval is a clear, auditable gate.

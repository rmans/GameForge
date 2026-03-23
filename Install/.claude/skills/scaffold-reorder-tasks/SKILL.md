---
name: scaffold-reorder-tasks
description: Analyze task dependencies within a slice and propose/apply an optimal implementation order. Use after task graph has stabilized.
argument-hint: SLICE-###
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# Reorder Tasks

Analyze dependencies and reorder tasks for: **$ARGUMENTS**

This skill discovers all tasks in a slice, builds a dependency graph, detects issues, and proposes an optimal implementation order. It then regenerates the slice's Tasks table from scratch. Run this after the task graph has stabilized — after fix-task, iterate, and triage have resolved all planning issues.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLICE-###` | Yes | — | The slice whose tasks should be reordered. |

## Step 1 — Discover Slice Tasks

Task files are the source of truth — not the existing slice Tasks table.

1. **Resolve the slice** — Glob `scaffold/slices/SLICE-###-*.md`. If not found, report and stop.
2. **Read the slice** — extract the specs listed in the Specs table.
3. **Find all task files** — Grep `scaffold/tasks/TASK-*.md` for `Implements: SPEC-###` matching any spec in this slice. This discovers the actual task set, including tasks triage created or merged that may not be in the existing table yet.
4. **Cross-check against existing table** — compare discovered tasks to the slice's current Tasks table. Flag:
   - **Stale rows** — tasks listed in the table but whose files no longer exist (merged/removed during triage).
   - **Missing rows** — task files that implement slice specs but aren't in the table (created during triage).
   - **Membership anomalies** — tasks in the existing table that still exist as files but don't map to any current slice spec (e.g., cross-cutting tasks reassigned during triage, or tasks whose `Implements:` was changed). Do not silently drop these — flag them for the user to confirm whether they belong in this slice.
5. **Read every discovered task file.** For each task, extract:
   - Objective
   - `Implements: SPEC-###`
   - Steps (scan for references to other systems, files, signals, APIs)
   - Files Created
   - Files Modified
   - Depends on (explicit TASK-### dependencies in the header)
   - Notes (additional dependency annotations)
   - Status
6. **Read `scaffold/design/architecture.md`** — tick order, dependency graph, component checklists.
7. **Read the specs** for this slice — understand precondition chains and acceptance criteria.

## Step 2 — Build Dependency Graph

For each task, determine what it **produces** and what it **consumes**:

### Productions (what a task creates)
- New files listed in Files Created
- New classes, systems, or data structures mentioned in Steps
- New signals registered
- New APIs exposed
- New scene nodes added
- New CSVs or data files created

### Consumptions (what a task requires to exist)
- Files in its Files Modified list where the needed structure is created by another task in this slice. Modifying a file that already exists in the repo before this slice does NOT create an in-slice dependency unless another slice task specifically creates the structure being consumed.
- APIs it calls from other systems
- Signals it connects to (must be registered first)
- Scene nodes it references (must exist in tree)
- Data files it reads (must be created first)
- Explicit "Depends on: TASK-###" in the task header (hard constraint)
- Explicit "depends on TASK-###" annotations in Notes

### Dependency Rules

Build edges in the dependency graph based on:

1. **File creation before modification.** If TASK-A creates `foo.h` and TASK-B modifies `foo.h`, A → B.
2. **File overlap ordering.** If two tasks modify the same file and one clearly produces structure the other consumes (e.g., TASK-A adds methods, TASK-B wires those methods into a scene), add a dependency edge A → B. If the overlap is ambiguous or the tasks' changes could conflict, flag as an issue in Step 3 instead of inventing an edge.
3. **System before wiring.** If TASK-A creates a system and TASK-B wires its signals in `game_manager.gd`, A → B.
4. **Data structures before logic.** If TASK-A creates data structures and TASK-B implements logic using them, A → B.
5. **Core logic before UI.** If TASK-A implements backend behavior and TASK-B adds UI for it, A → B.
6. **Registration before use.** If TASK-A registers a class in `register_types.cpp` and TASK-B adds it to a scene, A → B.
7. **Explicit annotations.** "Depends on: TASK-###" in the task header or "depends on TASK-###" in Notes creates a direct edge. The header field is the primary source; Notes annotations are supplementary.
8. **Spec preconditions.** Only derive spec-order dependencies from explicit precondition text in spec documents (e.g., "Precondition: SPEC-A behavior is active") or explicit dependency notes. Never assume spec order just because one spec sounds more foundational — that's a heuristic for tie-breaking in Step 4, not a dependency edge.
9. **Architecture tick order.** Systems earlier in the tick order should generally be implemented first (they're dependencies for later systems).

### Independence Detection

Tasks with no dependency edges between them can be implemented in any order. Group these as **parallel candidates** — they could theoretically run simultaneously.

## Step 3 — Detect Issues

### Circular Dependencies
If the graph contains cycles, report them:
```
CIRCULAR DEPENDENCY: TASK-### → TASK-### → TASK-### → TASK-###
```
Circular dependencies must be resolved before ordering. Suggest breaking points.

### Missing Prerequisites
For each consumption, apply a three-way test:
1. **Produced by another task in this slice** — dependency edge exists, no issue.
2. **Already exists in the codebase before this slice** — check whether the file/class/signal/node is already present in the repo. No in-slice dependency needed.
3. **Does not exist anywhere** — flag as missing:
```
MISSING PREREQUISITE: TASK-### requires [thing] — not produced by any slice task and not found in the codebase
```
Only category 3 is a real issue. Do not over-flag items that fall into category 2.

### Ambiguous File Overlaps
If multiple tasks modify the same file and the dependency direction is unclear:
```
AMBIGUOUS OVERLAP: TASK-### and TASK-### both modify [file] — manual ordering needed
```

### Orphan Tasks
Tasks with no incoming or outgoing edges — they don't depend on anything and nothing depends on them. Not necessarily wrong, but worth flagging.

### Overly Long Chains
If the critical path (longest dependency chain) is very long relative to the total task count, flag it — it means most tasks are sequential with little parallelism.

## Step 4 — Propose Order

Produce a topological sort of the dependency graph. When multiple valid orderings exist, prefer:

1. **Foundation first** — data structures, infrastructure, CSVs
2. **Core logic next** — system implementations
3. **Wiring after logic** — signal connections, orchestrator updates, scene tree
4. **UI after backend** — panels, overlays, renderers
5. **Integration tests last** — verification that crosses system boundaries
6. **Within a tier, follow tick order** — systems earlier in architecture.md Section 3 come first

### Order Number Convention

Follow the slice's existing convention:
- Pre-blocker tasks: `0a`, `0b`, `0c`, `0d` (lettered groups)
- Sub-tasks within a group: `0b.01`, `0b.02`, etc.
- Main sequence: `1`, `2`, `3`, etc. (integer order)
- Dependency annotations inline: `— depends on TASK-###`
- Parallelism annotations inline: `— independent, can parallel with N–M`

### Present Proposed Order

```
## Proposed Task Order: SLICE-### — [Name]

### Dependency Graph
[Brief description of the major dependency chains]

### Critical Path
[The longest chain, with task count and estimated implementation depth]

### Parallel Opportunities
[Groups of tasks that could be implemented in any internal order]

### Proposed Order

| Order | ID | Name | Spec | Status | Dependencies | Notes |
|-------|----|------|------|--------|-------------|-------|
| 1 | TASK-### | [Name] | SPEC-### | Draft | none | Foundation — creates base data structures |
| 2 | TASK-### | [Name] | SPEC-### | Draft | TASK-### | Core logic — uses structures from order 1 |
| 3 | TASK-### | [Name] | SPEC-### | Draft | TASK-### | Independent of order 2, can parallel |
| 4 | TASK-### | [Name] | SPEC-### | Draft | TASK-###, TASK-### | Wiring — connects systems from 2 and 3 |
| ... | ... | ... | ... | ... | ... | ... |

### Table Changes
- Stale rows removed: [list tasks that were in the old table but no longer exist]
- New rows added: [list tasks discovered from files that weren't in the old table]
- Order changes: [list tasks whose order changed and why]

### Issues Found
- [Circular dependencies, missing prerequisites, ambiguous overlaps, orphans, long chains]
```

Ask the user to confirm, adjust, or reject the proposed order.

## Step 5 — Regenerate Slice Tasks Table

After the user confirms, regenerate the slice's Tasks table from scratch. This synchronizes the slice-level planning view with the authoritative task file set so downstream skills (`/scaffold-approve-tasks`, `/scaffold-complete`) operate on current structure.

1. **Replace the entire Tasks table** in the slice file with only the confirmed discovered task set in the confirmed order. Use the full column set: Order, ID, Name, Spec, Status, Dependencies. Only tasks with existing files appear. Preserve tasks with status `Complete` in their computed order — completed tasks still matter to ripple logic and history.
2. **Pull Status from each task file** — read the actual `> **Status:**` line, don't trust the old table.
3. **Include dependency and parallelism annotations** in the Notes/Dependencies column.
4. **Update `scaffold/tasks/_index.md`** — the task index is global, not slice-scoped. Apply these rules carefully:
   - Ensure every discovered task in this slice has a correct row pointing to its current filename.
   - Remove rows only if the task file no longer exists anywhere (confirmed deleted/merged). Check with `Glob scaffold/tasks/TASK-###-*.md` before removing.
   - Do NOT remove rows merely because a task is no longer part of this slice — it may have moved to a different slice or spec during triage.
5. **Do NOT renumber task IDs.** Only the Order column and table membership change. Task IDs are permanent.
6. **Do NOT edit task files.** This skill modifies the slice's Tasks table, the tasks index, and the triage log — never task content or status.

## Step 6 — Check Upstream Actions

Read `scaffold/decisions/triage-logs/TRIAGE-SLICE-###.md` if it exists. Check the **Upstream Actions Required** table for entries with status **Pending** or **Filed**.

For each pending upstream action:
1. Check whether the action has already been completed (e.g., the target document was updated in a prior step or conversation).
2. If completed, update the status to **Resolved** in the triage log.
3. If still pending, surface it in the report as a pre-implementation reminder.

Actions with status **Deferred** are intentional — leave them as-is and do not flag them.

If no triage log exists for this slice, skip this step.

## Step 7 — Report

```
## Reorder Complete: SLICE-### — [Name]

| Metric | Value |
|--------|-------|
| Tasks discovered | N (from task files) |
| Stale rows removed | N |
| New rows added | N |
| Tasks reordered | N of M total |
| Dependency edges | N |
| Critical path length | N tasks |
| Parallel groups | N |
| Issues found | N (circular: X, missing prereq: Y, overlap: Z, orphan: W) |
| Upstream actions pending | N |

### Final Order
[Regenerated Tasks table from the slice]

### Pending Upstream Actions
[List any unresolved upstream actions from the triage log that should be addressed before or during implementation. If none, write "None — all upstream actions resolved or deferred."]

### Next Steps
- If issues were found: resolve them before implementation
- If upstream actions are pending: address them via `/scaffold-update-doc` before implementation, unless they don't affect acceptance criteria
- If clean: Run `/scaffold-approve-tasks SLICE-###` to mark tasks Approved, then `/scaffold-implement TASK-###-TASK-###` in the proposed order
```

## Rules

- **Task files are the source of truth.** Discover tasks by scanning task files for `Implements: SPEC-###`, not by reading the existing slice table. The table is an output, not an input.
- **Never change task IDs.** IDs are permanent. Only the Order column in the slice's Tasks table changes.
- **Never edit task files.** This skill modifies the slice's Tasks table, the task index, and the triage log — never task content or status.
- **Confirm before applying.** Present the proposed order and wait for user approval.
- **Circular dependencies are blockers.** Do not propose an order that contains cycles. Report them and stop.
- **Respect explicit annotations.** "Depends on: TASK-###" in the task header and "depends on TASK-###" in task Notes are hard constraints — never reorder against them.
- **Spec ordering requires evidence.** Only create dependency edges from explicit precondition text in specs or dependency notes. Never infer spec order from names or perceived importance.
- **File overlap: edge or issue, never both.** If the dependency direction is clear from the tasks' content, add an edge. If ambiguous, flag as an issue. Don't do both.
- **Parallelism is informational.** Note which tasks can run in parallel, but the Order column is still sequential (for `/scaffold-implement` range execution).
- **Pre-blocker tasks stay first.** Tasks with order `0*` are pre-blockers and should not be reordered into the main sequence. If dependency analysis implies a non-`0*` task must precede a pre-blocker task, flag this as a **pre-blocker ordering conflict** and stop — the pre-blocker designation or the dependency is wrong and needs human resolution.
- **Integration tests stay last.** Integration and verification tasks should remain at the end of the order.
- **Reorder synchronizes planning views.** The slice Tasks table and task index are derived artifacts. Reorder republishes the authoritative task file set into these views so `/scaffold-approve-tasks` and `/scaffold-complete` operate on current structure.
- **Never edit upstream architecture.** Reorder updates the slice table and task index (planning views), but never specs, system designs, or architecture docs.

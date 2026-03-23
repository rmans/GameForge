---
name: scaffold-triage-tasks
description: Collect unresolved human-required issues from task reviews and walk through them as decisions. Creates new tasks, applies scope changes, records deferrals.
argument-hint: SLICE-###
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Triage Tasks

Collect and resolve human-required planning issues for: **$ARGUMENTS**

This skill is the human decision gate in the task planning loop. It gathers unresolved issues from `/scaffold-fix task` and `/scaffold-iterate` runs, presents them as a decision checklist, and applies the user's decisions.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLICE-###` | Yes | — | The slice whose tasks are being triaged. Scopes issue collection to this slice's tasks. |

## Step 1 — Collect Issues

Gather all human-required issues from the most recent review and fix passes.

### 1a. Scan Review Logs

Grep `scaffold/decisions/review/REVIEW-*` for review logs that reference tasks in this slice. For each log:
- Extract issues marked as **human-required**, **unresolved**, or **escalated**.
- Record the issue category, affected task, and the reviewer's description.

### 1b. Scan Fix-Task Output

If `/scaffold-fix task` was run recently, its output contains a Human-Required Issues table. Read the task files themselves for clues — fix-task may have added Notes about human-required issues it couldn't resolve.

### 1c. Scan Task Files for Annotations

Grep `scaffold/tasks/TASK-*.md` for tasks implementing specs in this slice. Look for:
- Notes mentioning unresolved issues, open questions, or "human decision needed"
- `TODO` or `FIXME` markers in task content
- References to KI-### blockers or unresolved DD-### entries

### 1d. Scan Spec Acceptance Criteria

Read the specs implemented by tasks in this slice. For each spec's acceptance criteria, check whether at least one task covers it (via steps, verification, or explicit AC references). If an acceptance criterion has no implementing task, record a **New Task** category issue — this is the most dangerous failure mode, since it means coverage gaps will reach implementation undetected.

### 1e. Detect Duplicate Tasks

Look for tasks that implement the same spec behavior or reference the same acceptance criteria. This typically happens after multiple triage cycles create overlapping tasks through different paths (e.g., TASK-017 "Implement damage signal" and TASK-023 "Add damage event signal"). Record duplicates as **Merge** category issues.

### 1f. Detect Orphan Tasks

Check each task's `Implements: SPEC-###` reference. Flag tasks where:
- The referenced spec no longer exists (deleted or deprecated).
- The task's behavior no longer maps to any acceptance criterion in the referenced spec (spec was revised but the task wasn't updated).

This typically happens after spec changes during review cycles. Record orphans as **Scope** issues (if the task should be narrowed to match the current spec) or **Spec Conflict** issues (if the spec may be wrong).

### 1g. Detect Integration Gaps

Scan tasks for cross-system data flows: signals emitted/consumed, shared data written/read, or API calls between systems. If a producer task and a consumer task both exist but no task explicitly wires them together (signal registration, tick ordering, interface hookup), record a **New Task** category issue for the missing integration task.

Example: TASK-021 emits `DamageSignal` in CombatSystem, TASK-034 handles it in HealthSystem, but no task registers the signal connection or validates the flow end-to-end.

Sources to cross-reference:
- `scaffold/reference/signal-registry.md` — are all referenced signals registered?
- `scaffold/design/interfaces.md` — are cross-system contracts covered by tasks?
- `scaffold/design/authority.md` — does a task exist for each data-ownership boundary crossing?

### 1h. Detect Weak Verification

For each task, check whether its verification steps actually demonstrate the acceptance criteria are satisfied. Flag tasks where:
- Verification is only "compiles successfully" or "no errors" for behavior-defining ACs.
- Verification tests a different behavior than the AC describes.
- Verification has no observable output (no log check, no state assertion, no visual confirmation).

Record as **Scope** issues — the task itself may be fine but needs stronger verification before it's implementation-ready.

### 1i. Detect File Overlap Conflicts

Scan the "Files Created" and "Files Modified" sections across all tasks in the slice. If multiple tasks modify the same file in ways that could conflict (e.g., both add methods to the same class, both modify the same function, or both restructure the same subsystem), or if multiple tasks list the same file under "Files Created", record as:
- **Ordering** issue if the tasks can coexist but must run in a specific sequence.
- **Scope** issue if the tasks' changes to the shared file are incompatible and one task's boundaries need adjusting.

This is distinct from duplicate detection (1e) — overlapping tasks do different things but touch the same code.

### 1j. Validate Execution Paths

For each spec behavior implemented in this slice, reconstruct the complete runtime path:

**Trigger → Producer → Integration → Consumer → Observable Result**

Verify that a task exists for every link in the chain. If any stage is missing, the slice will compile but the behavior will never actually run.

How to check:
1. Read each spec's acceptance criteria to identify the expected behavior.
2. Identify the **trigger** — what causes this behavior to start? (tick, signal, player input, state change)
3. Identify the **producer** — which system/task generates the data or event?
4. Identify the **integration** — what wires producer to consumer? (signal registration, tick ordering, interface call)
5. Identify the **consumer** — which system/task reacts to the data or event?
6. Identify the **observable result** — what proves to the player (or test) that it worked?

If any stage has no implementing task:
- Record as a **New Task** issue if the cross-system contract is already defined (in interfaces.md or signal-registry.md) and just needs an implementing task.
- Record as a **Spec Conflict** or **File ADR** issue if the integration mechanism itself is undefined — that's an architecture gap, not a task gap.

Example:
```
Execution path: Room temperature affects colonist mood
  Trigger: simulation tick                    → TASK-019 ✓
  Producer: TemperatureSystem computes temp   → TASK-020 ✓
  Integration: temp data flows to NeedSystem  → ??? MISSING
  Consumer: NeedSystem adjusts comfort need   → TASK-021 ✓
  Result: UI shows mood change                → TASK-022 ✓

Issue: No task wires TemperatureSystem output to NeedSystem input.
```

Sources to cross-reference:
- `scaffold/design/interfaces.md` — defined cross-system contracts
- `scaffold/reference/signal-registry.md` — signal producer/consumer pairs
- `scaffold/design/state-transitions.md` — state change triggers
- `scaffold/design/authority.md` — data ownership boundaries that require explicit handoff

### 1k. Detect Data Ownership Violations

Cross-reference `scaffold/design/authority.md` with each task's implementation steps. Flag tasks where:
- A task modifies data owned by a different system (e.g., NeedSystem writes to `Colonist.temperature` which is owned by TemperatureSystem).
- Multiple tasks in different systems write to the same component or field without a defined interface contract in `scaffold/design/interfaces.md`.
- A task reads owned data without going through the owning system's public interface.

Data ownership violations in simulation architectures cause save/load inconsistencies, tick-order bugs, and race conditions. Record as **Ownership** issues.

### 1l. Detect Incomplete State Transitions

For systems with defined state machines in `scaffold/design/state-transitions.md`, verify that the slice's tasks cover all transitions for the states they touch. Flag gaps where:
- A state is entered by a task but has no task implementing its exit transitions.
- A transition is defined in the state machine but no task in the slice implements it (e.g., `Starving → Collapse` is defined but only `Hungry → Starving` has a task).
- A task introduces a new state not present in the state machine definition.

Incomplete state coverage creates invisible gameplay dead-ends. Record as **New Task** issues for missing transitions, or **Spec Conflict** if the state machine itself may need updating.

### 1m. Detect Persistence Gaps

If a task introduces new persistent game state (new components, fields, resources, or configuration that must survive save/load), check whether tasks exist to:
- **Serialize** the new state into the save format.
- **Deserialize** it on load.
- **Version** it (handle saves from before this state existed).

Cross-reference the canonical component and resource definition docs (typically `scaffold/reference/entity-components.md` and `scaffold/reference/resource-definitions.md`) for newly introduced data. If these docs don't exist yet, scan task steps for new fields, components, or resources that are clearly persistent.

If no save/load task covers the new state:
- Record as a **New Task** issue if the save/load architecture is already defined and the gap is just a missing task.
- Record as a **Spec Conflict** or **File ADR** issue if the save/load model itself is undefined — that's an architecture gap, not a task gap. Don't try to patch over missing architecture with tasks.

This prevents the classic bug where everything works until the player saves and reloads.

### 1n. Check Known Issues

Read `scaffold/decisions/known-issues.md`. If any open known issue affects systems or behaviors that tasks in this slice implement, check whether the tasks account for it (as a step, verification check, or noted constraint). If not, record as a **Scope** issue.

If triage discovers a new problem that doesn't fit task-level resolution (architectural smell, performance concern, system coupling), recommend filing via `/scaffold-file-decision --type ki` rather than creating a task to fix it.

### 1o. Deduplicate Issues

Merge identical issues that appear across multiple sources (e.g., the same "task too large" issue flagged by both fix-task and iterate). Keep the most detailed description.

## Step 2 — Categorize Issues

Group collected issues by decision type:

| Category | What the User Decides | Actions Available |
|----------|----------------------|-------------------|
| **Split** | A task is too large — where to split? | Create new task stubs, reduce original |
| **Merge** | Two tasks overlap — combine? | Merge steps/files into one task, remove the other |
| **Scope** | Task does too much or too little | Narrow scope, add/remove steps, update objective |
| **Ordering** | Dependency is wrong or missing | Note for `/scaffold-reorder-tasks` |
| **New task** | Missing coverage — a new task is needed | Create new task stub |
| **Spec conflict** | Task and spec disagree | Decide which is right, file ADR if spec needs changing |
| **Blocker** | KI or prerequisite blocks progress | Defer task, resolve blocker first, or accept risk |
| **Defer** | Issue is real but not worth fixing now | Record as accepted design debt |
| **Ownership** | Unclear which system owns the behavior | Assign ownership, update task accordingly |

## Step 3 — Present Decision Checklist

Present all issues to the user, grouped by category:

```
## Task Triage: SLICE-### — [Name]

### Issues Found: N total

#### Splits (N issues)
1. **TASK-### — [Name]** (Implements: SPEC-### — [Spec Name]): [description of why it needs splitting]
   - Suggested split point: [where to divide]
   - Options: (a) Split at suggested point (b) Split differently (c) Keep as-is

#### Merges (N issues)
2. **TASK-### — [Name]** + **TASK-### — [Name]** (Implements: SPEC-### — [Spec Name]): [description of overlap]
   - Options: (a) Merge into TASK-### (b) Merge into TASK-### (c) Keep both

#### Scope Changes (N issues)
3. **TASK-### — [Name]** (Implements: SPEC-### — [Spec Name]): [description of scope issue]
   - Options: (a) Narrow scope [suggested change] (b) Expand scope (c) Keep as-is

#### New Tasks Needed (N issues)
4. **Gap**: SPEC-### — [Spec Name], AC [criteria]: [description of missing coverage]
   - Options: (a) Create new task (b) Expand existing TASK-### (c) Defer to later slice

#### Spec Conflicts (N issues)
5. **TASK-### — [Name]** vs **SPEC-### — [Spec Name]**: [description of disagreement]
   - Options: (a) Task is right — update spec (b) Spec is right — update task (c) File ADR

#### Blockers (N issues)
6. **TASK-### — [Name]** (Implements: SPEC-### — [Spec Name]) blocked by KI-###: [description]
   - Options: (a) Defer task (b) Resolve blocker first (c) Accept risk and proceed

...
```

Wait for the user's decisions on each issue before proceeding.

## Step 4 — Classify and Apply Decisions

Before applying each decision, classify it:

**Local decision** — changes only task documents, indexes, and slice tables. Examples: splitting an oversized task, merging duplicate tasks, narrowing scope, updating verification steps. Apply immediately.

**Architecture-impacting decision** — changes architecture-level intent. Apply only the safe local portions, then create an upstream action or ADR stub for the architecture change. Mark stability as incomplete until the upstream action is resolved.

A decision is architecture-impacting if it does any of the following:
- Changes which system owns a behavior or data
- Introduces a cross-system write not defined in `authority.md`
- Creates a new cross-system contract not in `interfaces.md`
- Changes persistence expectations (new persistent state, save/load model changes)
- Changes state-machine meaning (new states, removed transitions)
- Changes orchestration/tick-order assumptions
- Changes signal contracts not reflected in `signal-registry.md`

These are not bad decisions — they are just too important to live only in task docs. The architecture layer must absorb them before the graph is fully stable.

For each decision the user makes:

### Split
1. Read the original task file.
2. Create new task stub(s) using the task template. Assign next sequential TASK-### ID(s).
3. Reduce the original task's steps and files to its narrowed scope.
4. Update objective and verification for both tasks.
5. Register new task(s) in `scaffold/tasks/_index.md`.
6. Add new task(s) to the slice's Tasks table (order TBD — noted for reorder step).

### Merge
1. Read both task files.
2. Combine steps, files, and verification into the surviving task.
3. Update the surviving task's objective to cover the merged scope.
4. If the tasks implement different specs (e.g., TASK-A implements SPEC-014, TASK-B implements SPEC-019), the surviving task must choose one `Implements:` reference. Update verification to cover only the chosen spec's acceptance criteria. The uncovered spec may need a **New Task** issue — record it if so.
5. Remove the absorbed task file.
6. Update `scaffold/tasks/_index.md` — remove the absorbed task's row.
7. Update the slice's Tasks table — remove the absorbed task's row.

### Scope Change
1. Read the task file.
2. Apply the scope change — add/remove steps, update files created/modified, update objective.
3. Update verification to match the new scope.

### New Task
1. Create task stub using the task template. Assign next sequential TASK-### ID.
2. Fill in objective, steps, files, and verification from the identified gap.
3. Set `Implements: SPEC-###` to the relevant spec.
4. Register in `scaffold/tasks/_index.md`.
5. Add to the slice's Tasks table (order TBD — noted for reorder step).

### Spec Conflict — Task is Right
1. Note the change needed in the spec. **Do not edit the spec directly** — flag it for the user to update via direct file editing.

### Spec Conflict — Spec is Right
1. Update the task to align with the spec.

### Spec Conflict — File ADR
1. Create an ADR stub in `scaffold/decisions/` using the decision template.
2. Note the conflict and options. Set status to `Proposed`.

### Blocker — Defer
1. Add a note to the task: `> **Blocked by:** KI-### — [description]. Deferred until resolved.`
2. Do not remove from the slice — it stays in the task list but is flagged.

### Blocker — Accept Risk
1. Add a note to the task: `> **Known risk:** KI-### — [description]. Proceeding despite blocker.`

### Defer
1. File via `/scaffold-file-decision --type dd` if a design debt entry doesn't already exist.
2. Add a note to the task referencing the DD-### entry.

### Ownership
1. Update the task's steps and notes to clarify which system owns the behavior.
2. If the task needs to move to a different spec, update `Implements:` and re-register.

## Step 5 — Write Decision Log

After applying all task-level decisions, write a persistent decision log to `scaffold/decisions/triage-logs/TRIAGE-SLICE-###.md`. If `scaffold/decisions/triage-logs/` does not exist, create it.

This file records every decision made during triage so the trail is not lost when the conversation ends.

```markdown
# Triage Log: SLICE-### — [Name]

> **Date:** YYYY-MM-DD
> **Issues found:** N
> **Decisions applied:** N

## Decisions

| # | Category | Task(s) | Decision | Result |
|---|----------|---------|----------|--------|
| 1 | Split | TASK-### | Split at step 5 | Created TASK-### |
| 2 | New task | — | Coverage gap for AC-3 | Created TASK-### |
| 3 | Scope | TASK-### | Narrowed to backend only | Updated |
| 4 | Defer | TASK-### | KI-### blocker | Deferred |

## Upstream Actions Required

Decisions that require changes to non-task documents. Triage does NOT apply these — they must be handled explicitly by the user via direct file editing or by filing ADRs.

| # | Source Decision | Target Document | Action | Reason | Status |
|---|----------------|----------------|--------|--------|--------|
| 1 | #5 | SYS-### | Update ownership section | Triage assigned ownership to ZoneSystem | Pending |
| 2 | #3 | SPEC-### | Revise AC-2 wording | Scope narrowed — AC no longer matches task | Pending |
| 3 | #7 | — | Create ADR for [topic] | Architectural gap identified | Filed |

**Status values:**
- **Pending** — action not yet taken
- **Filed** — ADR stub created with `Proposed` status, awaiting review
- **Deferred** — intentionally postponed (record why in Reason)
- **Resolved** — action completed in a later step or conversation

If no upstream actions are needed, write: "None — all decisions were task-scoped."
```

If a previous triage log exists for this slice, append a new dated section rather than overwriting — triage may run multiple times as the task graph stabilizes.

## Step 6 — Stability Check

After applying all decisions, assess whether the task graph is stable:

```
## Triage Summary: SLICE-### — [Name]

### Task Graph Stability
- Active implementable tasks: N (tasks ready for implementation — not deferred or blocked)
- Tasks created: N new
- Tasks removed: N merged/removed
- Tasks modified: N scope changes
- Tasks deferred: N blocked/deferred
- Circular dependencies: N detected
- Unresolved issues: N remaining (deferred issues with recorded decisions do NOT count as unresolved)
- Upstream actions pending: N

### Stability Assessment: [Stable / Needs another pass]

**Stable** means:
- No unresolved human-required planning issues remain
- No new tasks need to be created
- No pending splits or merges
- No circular dependencies between tasks (TASK-A depends on TASK-B depends on TASK-A)
- The task set is ready for `/scaffold-reorder-tasks`

**Needs another pass** means:
- New tasks were created that haven't been reviewed yet
- Splits produced tasks that may have their own issues
- Some decisions depend on other decisions not yet made

### Upstream Actions
- If upstream actions are pending, list them with suggested next steps (e.g., "Run `direct file editing SYS-024` to update ownership")
- Upstream actions do NOT block task implementation unless they change acceptance criteria

### Next Steps
- If **Stable**: Run `/scaffold-reorder-tasks SLICE-###` then `/scaffold-implement`
- If **Needs another pass**: Run `/scaffold-fix task` on new/modified tasks, then `/scaffold-iterate task`, then `/scaffold-triage-tasks` again
```

## Rules

- **Never decide for the user, but always recommend.** Present options and wait for decisions — but for each issue, state which option produces the strongest design for the final shipped game. Tasks should implement toward the final architecture; slices only control when work happens, not how systems are designed. Never recommend implementations that would require rework later. Prefer correct ownership, correct system boundaries, and correct contracts even if the slice only builds a subset. The user makes the final call, but they should never have to guess which option you think is strongest.
- **Only edit task files and indexes.** Never edit specs, system designs, or architecture docs. If a spec needs changing, flag it for the user.
- **New tasks follow all conventions.** Sequential IDs, task template, registered in index, added to slice table.
- **Merged tasks are fully removed.** Delete the file, remove from index, remove from slice table. IDs are never reused.
- **Ordering is deferred.** New or modified tasks get a TBD order — `/scaffold-reorder-tasks` handles final ordering.
- **ADR stubs are Proposed, not Accepted.** The user must review and accept ADRs separately.
- **Design debt entries are descriptive.** Include what was deferred, why, and what the impact is.
- **Stability assessment is honest.** If new tasks were created, they need review. Don't claim stability when the graph has changed.
- **Deferred is not unresolved.** An issue that has been intentionally deferred with a recorded decision (noted in the task, tracked in design-debt or as a blocker) counts as resolved for stability purposes. Only issues without a decision are unresolved.
- **Architecture gaps escalate, not patch.** If a gap exists because a cross-system architectural decision is undefined (e.g., no save/load model, no defined integration mechanism), classify as **Spec Conflict** or **File ADR** — not automatically as **New Task**. Don't try to fix missing architecture by creating tasks.

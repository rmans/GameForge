---
name: scaffold-iterate-task
description: Adversarial per-topic task review using an external LLM. Reviews tasks across 5 topics (spec coverage, architecture, integration, executability, edge cases) with back-and-forth discussion. Use for deep task review beyond what fix-task catches.
argument-hint: [TASK-### or TASK-###-TASK-###] [--focus "concern"] [--iterations N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Task Review

Run an adversarial per-topic review of implementation tasks using an external LLM reviewer: **$ARGUMENTS**

This skill reviews task documents across 5 sequential topics, each with its own back-and-forth conversation. The reviewer focuses deeply on one concern at a time. This is the task-specific equivalent of `/scaffold-iterate` — it uses the same Python infrastructure but with task-optimized topics instead of monolithic review.

## Architecture

```
TOPIC LOOP (5 sequential topics per iteration)
├─ Topic 1: Spec Coverage
│   ├─ Python script sends task + context to reviewer → structured issues JSON
│   ├─ INNER LOOP (exchanges — back-and-forth)
│   │   ├─ Claude evaluates each issue (agree / pushback / partial)
│   │   ├─ If pushback → Python sends Claude's response to reviewer
│   │   ├─ Reviewer counter-responds → Claude re-evaluates
│   │   └─ ... until consensus or max exchanges
│   ├─ Consensus → apply agreed changes
│   └─ Log topic results
├─ Topic 2: Architecture Compliance
│   └─ ... same inner loop
├─ ... Topics 3–5
└─ Sleep 10s between topics to avoid rate limits

OUTER LOOP (iterations — repeat full 5-topic cycle on updated task)
├─ Iteration 1: Topics 1-5 with discussion
├─ Iteration 2: Topics 1-5 on updated task (if --iterations > 1)
└─ ... up to max iterations or until no issues found
```

## Topics

| # | Topic | What It Evaluates |
|---|-------|-------------------|
| 1 | Spec Coverage | Does the task implement all relevant acceptance criteria? Are steps mapped to spec behaviors? Missing coverage? Extra behaviors not in spec? |
| 2 | Architecture Compliance | Tick order placement, authority chain, signal wiring conventions, data flow rules, entity storage patterns, component checklists |
| 3 | Integration Correctness | Signal names and payloads match registry, APIs called correctly, dependencies resolved, cross-system contracts honored |
| 4 | Step Executability | Can a developer follow these steps as written? Concrete enough? Correct file paths? Right engine patterns? Executable order? |
| 5 | Edge Cases, Safety & Lifecycle | Null guards for destroyed entities, handle validation, lifecycle transitions (creation/destruction, signal disconnect, resource cleanup), save/load implications, system startup order, race conditions, cleanup on failure |

**After all topics complete**, the reviewer must answer two final questions:

1. **What is the single most dangerous thing in this task?** — the issue most likely to cause implementation failure or spec non-compliance.

2. **What could go wrong that this task's verification wouldn't catch?** — list the bugs, integration failures, and edge cases that could exist even if all verification steps pass green. If the list is long, the verification is weak. A good task is defined not just by what it builds, but by what its verification would catch.

Both answers go at the top of the report, before topic-level detail.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| task | Yes | — | Single `TASK-###` or range `TASK-###-TASK-###` |
| `--focus` | No | — | Narrow the review within each topic to a specific concern. Example: `--focus "signal wiring"`, `--focus "save/load safety"` |
| `--iterations` | No | 10 | Maximum outer loop iterations (full 5-topic cycles). Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | all | Review only a specific topic (1-5). Skips other topics. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic before forcing consensus. |

## Range Behavior

If the argument contains a hyphen between two TASK-### IDs:
1. Extract start and end numbers. Build ordered list.
2. Execute the full review pipeline for each task sequentially. **Parallelization:** Tasks whose `Depends on` fields are satisfied (all dependencies already processed or have no dependencies) can run in parallel. Tasks with unmet dependencies wait until those dependencies complete. See WORKFLOW.md Range Parallelization for the full pattern.
3. Between each task, output a horizontal rule (`---`) and a header: `## Reviewing: TASK-### — [Name] ([N of M])`
4. Skip missing task files with a note: `**TASK-###: No file found — skipping.**`
5. After all tasks, output a summary table:

```
## Range Review Summary: TASK-### through TASK-###

| Task | Topics | Issues | Accepted | Rejected | Iterations | Status |
|------|--------|--------|----------|----------|------------|--------|
| TASK-### — Name | 5/5 | N | N | N | M | Updated / Unchanged |
| TASK-### — Name | — | — | — | — | — | Skipped (no file) |
| ... | ... | ... | ... | ... | ... | ... |
```

## Step 1 — Resolve Target

Parse the argument:
- If a TASK-### ID is given, Glob `scaffold/tasks/TASK-###-*.md`.
- If a range is given, resolve each task in order (per Range Behavior above).
- If the task file doesn't exist, skip it (range mode) or report and stop (single mode).

Read the task file. Validate it has an `Implements: SPEC-###` reference. If malformed, report and skip/stop.

## Step 2 — Gather Context Files

Read and pass these as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| Parent spec file (follow `Implements: SPEC-###`) | Spec coverage evaluation |
| Parent system design (follow spec's system reference) | Architecture and domain context |
| `scaffold/design/architecture.md` | Tick order, signal wiring, data flow, component checklists |
| `scaffold/reference/signal-registry.md` | Signal names and payloads for integration checks |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| Relevant engine docs from `scaffold/engine/` | Engine pattern compliance |
| ADRs referenced in the task, spec, or architecture | Implementation constraints |

Additionally, if the task involves specific domains:
- Entity work → `scaffold/reference/entity-components.md`
- UI work → `scaffold/engine/ui.md`
- Input work → `scaffold/engine/input.md`

Only include context files that exist — skip missing ones silently.

## Step 3 — Topic Loop

Determine which topics to review:
- If `--topic N` is provided, review only that topic.
- Otherwise, review topics 1 through 5 sequentially.

For each topic:

### 3a. Request Topic Review

Run:
```bash
python scaffold/tools/doc-review.py review <task-path> --iteration N --topic T --context-files <file1> <file2> ... [--focus "<value>"]
```

Parse the JSON output. If `"error"` key exists, report the error and stop.

Output the topic header:
```
## Topic T: [Name]
```

### 3b. Filter Issues

Keep all issues (HIGH, MEDIUM, LOW) — tasks use Full tier.

If no issues remain, skip to the next topic — this topic passed.

### 3c. Inner Loop — Evaluate Issues

For each issue, read the relevant section of the task and any context files. Evaluate:

- **AGREE** — The issue is valid. Note the change to make.
- **PUSHBACK** — The issue is wrong or out of scope. Explain why with reference to project documents. When pushing back, Claude draws on full project knowledge — not just the context files sent to the reviewer. This means Claude may cite ADRs, `authority.md`, slice docs, or other documents the reviewer hasn't seen. This asymmetry is intentional: it's how disputed context enters the conversation on demand, and why Claude is the authority.
- **PARTIAL** — The issue has merit but the suggested fix isn't right. Propose an alternative.

Compose Claude's response covering all issues for this topic, write to a temporary file, then send:

```bash
python scaffold/tools/doc-review.py respond <task-path> --iteration N --topic T --message-file <temp-file>
```

Parse the reviewer's counter-response. Continue exchanges up to `--max-exchanges`.

**Key rule:** Claude is the authority on this codebase. Ties go to Claude.

### 3d. Request Topic Consensus

After exchanges complete:

```bash
python scaffold/tools/doc-review.py consensus <task-path> --iteration N --topic T
```

Parse the consensus JSON.

### 3e. Adjudication

When evaluating reviewer issues, use this table to determine the correct outcome:

| Outcome | When to Apply |
|---------|---------------|
| **Accept** | Issue is valid, fix is correct, improves the task. Apply the change. |
| **Reject** | Issue is wrong, out of scope, or contradicts a higher-authority document. Explain why with document references. |
| **Partial** | Issue has merit but the suggested fix is wrong or overkill. Propose an alternative that addresses the root concern. |
| **Flag ambiguous spec intent** | Parent spec or engine doc permits multiple valid implementation approaches. Not incorrect — genuinely ambiguous upstream. Escalate to user for implementation decision rather than forcing one approach at task level. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- If the reviewer cites a higher-authority document → verify the citation. Accept if accurate, reject if misread.
- If the reviewer and Claude disagree on interpretation → Claude wins (codebase authority).
- If multiple valid implementation approaches exist because the spec or engine doc is ambiguous → flag ambiguous spec intent for user decision. Do not treat ambiguity as a defect or force a single approach at task level.

### 3f. Apply Changes

For each change in `changes_to_apply` from the consensus:
- Read the relevant section of the task document.
- Apply the change using the Edit tool.
- Never apply changes that violate document authority (higher-rank docs win).
- **Only edit the task file.** Never edit specs, slices, indexes, or other documents.

### 3g. Log Topic Results

Record for the review log:
- Topic name and score (if provided)
- Issues raised, their resolutions (accepted/rejected/modified)
- Changes applied
- **Injected failure scenario** for this topic and whether the current task's verification would detect it

### 3h. Transition to Next Topic

Output a summary line:
```
### Topic T: [Name] — Issues: A raised, B accepted, C rejected
```

Add `sleep 10` between topics to avoid rate limits, then proceed to the next topic.

## Step 4 — Iterate

### Single-Task Review

If `--iterations > 1`:

1. After all 5 topics complete, re-read the task file (it may have been modified) and repeat the full topic loop on the updated content.
2. Track reappearing issues. Two issues are considered the **same issue** if they match on all three criteria: (a) same document section (e.g., Step 3, Files Created, Files Modified, Verification), (b) same issue type (e.g., missing coverage, wrong file path, authority violation), and (c) same underlying problem, even if phrased differently by the reviewer across iterations. If the same issue appears in 2+ iterations, escalate to the user.

### Range Review

For a range (e.g., `TASK-001-TASK-050`), **every task in the range must be reviewed**. The range is a work list. Reviewing one task and stopping is a skill failure.

1. **Build work list.** Glob all task files matching the range. Sort by ID. Log: "Reviewing N tasks: TASK-001, TASK-002, ..."
2. **Spawn parallel agents.** One agent per task, all spawned in parallel (use multiple Agent tool calls in a single message). Each agent runs a **complete, self-contained review** of ONE task — all 5 topics, all exchanges, all iterations up to `--iterations` max, all adjudication, all edits. An agent is the same as running `iterate-task TASK-###` on that task alone. Each agent receives the task file, context files (parent spec, slice, system design, engine docs, architecture, authority, interfaces, reference docs, ADRs, known issues), review config, and full topic/adjudication instructions.
3. **Collect results.** As agents complete, log progress: "TASK-### — Rating: X/5, Issues: Y accepted, Z rejected (N of M complete)"
4. **Agent failure handling.** Failed agents retry once after all others complete. If retry fails, report as "review failed" with the error.

**Stop conditions** (any one stops iteration):
- **Clean:** No issues found in a full 5-topic pass.
- **Stable:** No new issues compared to the previous iteration — the same rejected issues keep cycling.
- **Converged:** Changes were applied but no further issues remain after applying them.
- **Limit:** Iteration limit reached.

**Verification pass rule:** A pass that found issues and applied fixes is NOT clean — it is a "fixed" pass. After a fixed pass, you MUST run at least one more full pass on the updated document to verify no new issues were introduced by the fixes and no previously-hidden issues are now exposed. Only a pass that finds ZERO new issues counts as **Clean**. Stopping after fixing issues without a verification pass is a skill failure.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue. Examples:
- "implementation steps too vague" and "developer would need to guess" → same issue if they stem from the same step's lack of specificity.
- "spec misalignment" and "task contradicts acceptance criteria" → same issue if about the same AC.

**Lock enforcement:**
- The reviewer must NOT reintroduce a resolved issue in a different form.
- The reviewer must NOT raise stricter variants of a resolved issue unless: (a) new evidence exists that wasn't available when the issue was resolved, OR (b) the fix itself introduced a new problem.
- If a previously resolved issue reappears: classify it as a **review inconsistency**, not a new issue. Prefer rejecting the reappearance unless the reviewer provides materially different evidence.

**Cross-topic lock:** If Topic 1 resolves an issue, later topics may not re-raise it under a different name. The cross-topic consistency check catches this retroactively, but the lock prevents wasted exchanges proactively.

**Tracking:** Maintain a running resolved-issues list in the review log during execution. Before engaging with any new reviewer claim, check it against the resolved list by root cause. If it matches, reject with "previously resolved — see [iteration N, topic M]."

### Scope Collapse Guard

Before accepting any change to a task, enforce these three tests to prevent task-layer expansion into spec or engine-doc territory:

**1. Upward Leakage Test:**
Does this change introduce behavioral decisions that belong in specs, or architectural/convention decisions that belong in engine docs?
- If YES → reject. Tasks implement a specific spec's behavior using engine conventions; they don't define behavior or set project-wide conventions.
- Tasks may: define implementation steps, file/class names, method signatures, test plans, and engine-specific code patterns.
- Tasks must NOT: redefine what behavior to implement (spec territory), or establish new project-wide coding conventions (engine doc territory).

**2. Behavioral Redefinition Test:**
Does this change alter what the task implements rather than how it implements?
- If the task changes acceptance criteria, edge case handling, or observable behavior → it's spec leakage. Reject or flag for spec revision.
- If the task changes implementation approach, code structure, or engine patterns → correct layer. Accept.

**3. "Would This Apply Beyond This Task?" Test:**
Does this change establish a pattern or convention that would apply to other tasks too?
- If YES → it belongs in an engine doc (coding-best-practices, implementation-patterns), not in a single task. Reject or flag for engine doc update.
- If NO → task-scoped implementation decision. Accept.

These tests apply to both reviewer-proposed changes AND existing task content flagged during review.

## Step 5 — Create Review Log

After all iterations complete, create a review log in `scaffold/decisions/review/`:
- Use the template at `scaffold/templates/review-template.md`.
- Name it: `REVIEW-task-TASK-###-<YYYY-MM-DD>.md`
- Fill in all sections from the iteration data.
- Update `scaffold/decisions/review/_index.md` with a new row.

**This skill does not approve or rename task files.** Approval happens later in the workflow, after human triage resolves strategic issues and `/scaffold-reorder-tasks` finalizes the task graph.

## Step 6 — Report

```
## Task Review Complete: TASK-### — [Name]

### Most Dangerous Thing
[The single issue most likely to cause implementation failure or spec non-compliance. If no critical issues, write "No critical risks identified."]

### Undetected Failure Risk
[What bugs could exist if all verification steps pass? List integration failures, edge cases, and race conditions that could slip through. Short list = strong verification. Long list = weak verification.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Spec Coverage | N | N | N |
| 2. Architecture Compliance | N | N | N |
| 3. Integration Correctness | N | N | N |
| 4. Step Executability | N | N | N |
| 5. Edge Cases, Safety & Lifecycle | N | N | N |

**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/REVIEW-task-TASK-###-YYYY-MM-DD.md
```

## Rules

- **Claude is the authority on this codebase.** Ties go to Claude. The reviewer is an outsider with no project context beyond what's provided.
- **Only edit the task file.** Never edit specs, slices, indexes, engine docs, or other documents during review. If a change requires editing outside the task, log it as an action item.
- **Never apply changes that violate document authority.** If the reviewer suggests something that contradicts a higher-ranked document, reject it and explain why.
- **Never blindly accept.** Every issue gets evaluated against project context and the authority chain.
- **Pushback is expected and healthy.** The value is in the discussion, not automatic acceptance.
- **Reappearing material issues escalate to the user.** If the same significant issue persists across 2+ iterations, Claude and the reviewer cannot agree — the user decides. Present escalated issues using the Human Decision Presentation pattern (see WORKFLOW.md) — numbered, with concrete options (a/b/c). Trivial repeated nitpicks do not warrant escalation.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Upward leakage — does this introduce behavioral decisions (spec territory) or project-wide conventions (engine doc territory)? If yes, reject. (2) Behavioral redefinition — does this change what to implement (wrong) vs how to implement (correct)? (3) "Would this apply beyond this task?" — if the pattern applies project-wide, it belongs in an engine doc, not a single task.
- **Sleep between API calls.** Add `sleep 10` between topic transitions to respect rate limits.
- **Clean up temporary files** (message files used for `--message-file`) after use.
- **If the Python script fails, report the error and stop.** Do not work around script errors.
- **Ambiguous upstream intent is not a task defect.** When a spec or engine doc genuinely permits multiple valid implementation approaches and the task chose a reasonable one, do not treat the task as incorrect. Flag for user decision to lock the interpretation upstream. The reviewer's preferred approach is not automatically correct — implementation ambiguity often means the spec or engine doc needs tightening, not the task.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the task harder to implement or verify? (b) does this improve implementation clarity, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving implementability, optimize for review criteria over practical coding guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing tasks that are hyper-consistent but less actionable or buildable. The goal is tasks a developer can execute, not ones that score perfectly on an internal consistency audit.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "steps too vague" and "developer would guess" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.

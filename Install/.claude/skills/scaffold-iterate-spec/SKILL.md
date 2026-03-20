---
name: scaffold-iterate-spec
description: Adversarial per-topic spec review using an external LLM. Reviews specs across 6 topics (behavioral correctness, system alignment, slice coverage, cross-system contracts, acceptance criteria, edge cases) with back-and-forth discussion. Use for deep spec review beyond what fix-spec catches.
argument-hint: [SPEC-### or SPEC-###-SPEC-###] [--focus "concern"] [--iterations N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Spec Review

Run an adversarial per-topic review of behavior specs using an external LLM reviewer: **$ARGUMENTS**

This skill reviews spec documents across 6 sequential topics, each with its own back-and-forth conversation. The reviewer focuses deeply on one concern at a time. This is the spec-specific equivalent of `/scaffold-iterate-task` — it uses the same Python infrastructure but with spec-optimized topics.

## Architecture

```
TOPIC LOOP (6 sequential topics per iteration)
├─ Topic 1: Behavioral Correctness
│   ├─ Python script sends spec + context to reviewer → structured issues JSON
│   ├─ INNER LOOP (exchanges — back-and-forth)
│   │   ├─ Claude evaluates each issue (agree / pushback / partial)
│   │   ├─ If pushback → Python sends Claude's response to reviewer
│   │   ├─ Reviewer counter-responds → Claude re-evaluates
│   │   └─ ... until consensus or max exchanges
│   ├─ Consensus → apply agreed changes
│   └─ Log topic results
├─ Topic 2: System Behavior Alignment
│   └─ ... same inner loop
├─ ... Topics 3–6
└─ Sleep 10s between topics to avoid rate limits

OUTER LOOP (iterations — repeat full 6-topic cycle on updated spec)
├─ Iteration 1: Topics 1-6 with discussion
├─ Iteration 2: Topics 1-6 on updated spec (if --iterations > 1)
└─ ... up to max iterations or until no issues found
```

## Topics

| # | Topic | What It Evaluates |
|---|-------|-------------------|
| 1 | Behavioral Correctness | Atomicity (one behavior, testable as a unit), determinism (no vague selection), Trigger section clarity (explicit initiating action or event), actor clarity, sequence clarity, Observable Outcome completeness (player-visible success results), Failure Outcome completeness (visible rejection/failure behavior), internal consistency across sections. Core question: *could two engineers implement this the same way?* |
| 2 | System Behavior Alignment | Spec behavior matches parent system design's Player Actions and System Resolution, authority boundaries respected, no cross-system data writes without defined contracts, state transitions match state-transitions.md, referenced system is the correct owner. Core question: *does this spec belong to this system and match what it defines?* |
| 3 | Slice Goal Alignment | Spec's Proof Intent section connects to slice proof goal, behavior is relevant to what the slice demonstrates end-to-end, no spec drift from slice intent, spec isn't too early/late/irrelevant for this slice. Core question: *does this spec help prove what the slice is trying to prove?* |
| 4 | Cross-System Behavior & Contracts | Secondary Systems header field lists all cross-system dependencies, Secondary Effects section describes follow-on effects in other systems, cross-system reactions behaviorally represented (not as implementation detail), interface contracts honored, no hidden coupling or undocumented side effects. Explicitly check for hidden dependencies: economy effects implied but not named, room/pathfinding reactions assumed but not acknowledged, AI/state/persistence consequences missing, cross-system ownership handoffs not declared. Core question: *is this spec hiding system dependencies that will cause integration pain?* |
| 5 | Acceptance Criteria Quality | ACs are testable and concrete, each AC maps to a behavior step, ACs cover both Observable Outcome (success path) and Failure Outcome (rejection/failure path), Out of Scope section prevents AC creep, no redundant ACs, no missing coverage of key behaviors, results are player-visible or test-observable. Core question: *can someone actually verify this spec passes or fails?* |
| 6 | Robustness & Decision Compliance | Edge cases cover real boundary conditions (not filler), known issues from known-issues.md reflected where relevant, accepted ADRs absorbed, no deferred behavior reintroduced, terminology consistency across sections. **Failure path parity** — does this spec describe failure/interruption paths with the same rigor as success paths? In a colony sim, the interruption path is exercised more often than the happy path. A spec that thoroughly describes success but hand-waves failure is designing backwards for this genre. Core question: *is this spec ignoring prior decisions or known constraints?* |

**After all topics complete**, the reviewer must answer two final questions:

1. **What is the single most dangerous thing in this spec?** — the issue most likely to cause implementation divergence, integration pain, or testing failure.

2. **What implementation bugs could exist if all acceptance criteria pass?** — list the behavioral failures, integration breaks, and edge cases that could slip through even if every AC is verified green. If the list is long, the ACs are weak. A good spec is defined not just by what it tests, but by what bugs its tests would catch.

Both answers go at the top of the report, before topic-level detail.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| spec | Yes | — | Single `SPEC-###` or range `SPEC-###-SPEC-###` |
| `--focus` | No | — | Narrow the review within each topic to a specific concern. Example: `--focus "cross-system coupling"`, `--focus "determinism"` |
| `--iterations` | No | 10 | Maximum outer loop iterations (full 6-topic cycles). Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | all | Review only a specific topic (1-6). Skips other topics. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic before forcing consensus. |

## Range Behavior

If the argument contains a hyphen between two SPEC-### IDs:
1. Extract start and end numbers. If start > end, swap them.
2. Build ordered list. Execute the full review pipeline for each spec sequentially. **Parallelization:** Specs within a slice are independent — range processing can run all items in parallel. See WORKFLOW.md Range Parallelization.
3. Between each spec, output a horizontal rule (`---`) and a header: `## Reviewing: SPEC-### — [Name] ([N of M])`
4. Skip missing spec files with a note: `**SPEC-###: No file found — skipping.**`
5. After all specs, output a summary table:

```
## Range Review Summary: SPEC-### through SPEC-###

| Spec | Topics | Issues | Accepted | Rejected | Iterations | Status |
|------|--------|--------|----------|----------|------------|--------|
| SPEC-### — Name | 6/6 | N | N | N | M | Updated / Unchanged |
| SPEC-### — Name | — | — | — | — | — | Skipped (no file) |
| ... | ... | ... | ... | ... | ... | ... |
```

## Step 1 — Resolve Target

Parse the argument:
- If a SPEC-### ID is given, Glob `scaffold/specs/SPEC-###-*.md`.
- If a range is given, resolve each spec in order (per Range Behavior above).
- If the spec file doesn't exist, skip it (range mode) or report and stop (single mode).

Read the spec file. Validate it has a System reference and belongs to a slice. If malformed, report and skip/stop.

## Step 2 — Gather Context Files

Read and pass these as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| Parent system design (follow spec's system reference) | System alignment and authority evaluation |
| Parent slice file (find via spec index or slice tables) | Slice goal alignment |
| `scaffold/design/state-transitions.md` | State machine validation |
| `scaffold/design/interfaces.md` | Cross-system contract verification |
| `scaffold/design/authority.md` | Data ownership boundary checks |
| `scaffold/reference/signal-registry.md` | Signal flow consistency |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| `scaffold/decisions/known-issues.md` | Known constraint awareness |
| ADRs referenced in the spec or parent system | Design decision compliance |

Only include context files that exist — skip missing ones silently.

## Step 3 — Topic Loop

Determine which topics to review:
- If `--topic N` is provided, review only that topic.
- Otherwise, review topics 1 through 6 sequentially.

For each topic:

### 3a. Request Topic Review

Run:
```bash
python scaffold/tools/doc-review.py review <spec-path> --iteration N --topic T --context-files <file1> <file2> ... [--focus "<value>"]
```

Parse the JSON output. If `"error"` key exists, report the error and stop.

Output the topic header:
```
## Topic T: [Name]
```

### 3b. Filter Issues

Keep all issues (HIGH, MEDIUM, LOW) — specs use Full tier.

If no issues remain, skip to the next topic — this topic passed.

### 3c. Inner Loop — Evaluate Issues

For each issue, read the relevant section of the spec and any context files. Evaluate:

- **AGREE** — The issue is valid. Note the change to make.
- **PUSHBACK** — The issue is wrong or out of scope. Explain why with reference to project documents. Claude draws on full project knowledge — not just the context files sent to the reviewer. Claude may cite ADRs, authority.md, slice docs, system designs, or other documents the reviewer hasn't seen. This asymmetry is intentional.
- **PARTIAL** — The issue has merit but the suggested fix isn't right. Propose an alternative.

**Key constraint for specs:** When evaluating changes, ensure they stay at the behavior level. If a reviewer suggests adding implementation details (signal names, method calls, node paths), reject the suggestion and propose a behavioral alternative.

Compose Claude's response covering all issues for this topic, write to a temporary file, then send:

```bash
python scaffold/tools/doc-review.py respond <spec-path> --iteration N --topic T --message-file <temp-file>
```

Parse the reviewer's counter-response. Continue exchanges up to `--max-exchanges`.

**Key rule:** Claude is the authority on this codebase. Ties go to Claude.

### 3d. Request Topic Consensus

After exchanges complete:

```bash
python scaffold/tools/doc-review.py consensus <spec-path> --iteration N --topic T
```

Parse the consensus JSON.

### 3e. Apply Changes

For each change in `changes_to_apply` from the consensus:
- Read the relevant section of the spec document.
- Apply the change using the Edit tool.
- Never apply changes that violate document authority (higher-rank docs win).
- Never introduce implementation details into spec behavior. If an agreed change would leak implementation, rewrite it in behavioral terms before applying.
- **Only edit the spec file.** Never edit slices, system designs, indexes, or other documents during review. If a change requires editing outside the spec, log it as an action item.

### 3f. Log Topic Results

Record for the review log:
- Topic name and score (if provided)
- Issues raised, their resolutions (accepted/rejected/modified)
- Changes applied
- **Injected failure scenario** for this topic and whether the current spec's ACs would detect it

### 3g. Transition to Next Topic

Output a summary line:
```
### Topic T: [Name] — Issues: A raised, B accepted, C rejected
```

Add `sleep 10` between topics to avoid rate limits, then proceed to the next topic.

## Step 4 — Iterate

### Single-Spec Review

If `--iterations > 1`:

1. After all 6 topics complete, re-read the spec file (it may have been modified) and repeat the full topic loop on the updated content.
2. Track reappearing issues. Two issues are considered the **same issue** if they match on all three criteria: (a) same spec section (e.g., Behavior step 3, AC-2), (b) same issue type (e.g., determinism, authority violation, missing failure path), and (c) same underlying problem, even if phrased differently by the reviewer across iterations. If the same issue appears in 2+ iterations, escalate to the user.

### Range Review

For a range (e.g., `SPEC-001-SPEC-030`), **every spec in the range must be reviewed**. The range is a work list. Reviewing one spec and stopping is a skill failure.

1. **Build work list.** Glob all spec files matching the range. Sort by ID. Log: "Reviewing N specs: SPEC-001, SPEC-002, ..."
2. **Spawn parallel agents.** One agent per spec, all spawned in parallel (use multiple Agent tool calls in a single message). Each agent runs a **complete, self-contained review** of ONE spec — all 6 topics, all exchanges, all iterations up to `--iterations` max, all adjudication, all edits. An agent is the same as running `iterate-spec SPEC-###` on that spec alone. Each agent receives the spec file, context files (system design, slice file, design doc, glossary, interfaces, authority, ADRs, known issues), review config, and full topic/adjudication instructions.
3. **Collect results.** As agents complete, log progress: "SPEC-### — Rating: X/5, Issues: Y accepted, Z rejected (N of M complete)"
4. **Agent failure handling.** Failed agents retry once after all others complete. If retry fails, report as "review failed" with the error.

**Stop conditions** (any one stops iteration):
- **Clean:** No issues found in a full 6-topic pass.
- **Stable:** No new issues compared to the previous iteration — the same rejected issues keep cycling.
- **Converged:** Changes were applied but no further issues remain after applying them.
- **Limit:** Iteration limit reached.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue. Examples:
- "acceptance criteria too vague" and "no testable success condition" → same issue if they stem from the same AC.
- "system boundary violation" and "spec writes to wrong system's state" → same issue if about the same ownership conflict.

**Lock enforcement:**
- The reviewer must NOT reintroduce a resolved issue in a different form.
- The reviewer must NOT raise stricter variants of a resolved issue unless: (a) new evidence exists that wasn't available when the issue was resolved, OR (b) the fix itself introduced a new problem.
- If a previously resolved issue reappears: classify it as a **review inconsistency**, not a new issue. Prefer rejecting the reappearance unless the reviewer provides materially different evidence.

**Cross-topic lock:** If Topic 1 resolves an issue, later topics may not re-raise it under a different name. The cross-topic consistency check catches this retroactively, but the lock prevents wasted exchanges proactively.

**Tracking:** Maintain a running resolved-issues list in the review log during execution. Before engaging with any new reviewer claim, check it against the resolved list by root cause. If it matches, reject with "previously resolved — see [iteration N, topic M]."

### Issue Adjudication

Every issue raised by the reviewer must be classified into exactly one outcome:

| Outcome | Action |
|---------|--------|
| **Accept → edit spec** | Apply change immediately. The issue is valid and the fix is within spec scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or the issue is out of scope. |
| **Escalate to user** | Requires behavioral judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag ambiguous behavior intent** | Spec's parent system design or slice permits multiple valid behavioral interpretations. Not incorrect — genuinely ambiguous upstream. Escalate to user for behavior decision rather than forcing one reading at spec level. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- Prefer fixing the spec over escalating — most issues are behavioral clarity or consistency.
- Never "half-accept" — choose exactly one outcome per issue.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of system behavior or slice scope exist and the spec chose a reasonable one → flag ambiguous behavior intent for user decision. Do not treat ambiguity as a defect or force a single reading at spec level.

### Scope Collapse Guard

Before accepting any change to a spec, enforce these three tests to prevent spec-layer expansion into system, slice, or task territory:

**1. Upward Leakage Test:**
Does this change introduce system-level responsibilities, slice-level scope, or design decisions that belong in higher-ranked docs?
- If YES → reject. Specs define one atomic behavior, not system scope or slice boundaries.
- Specs may: define testable behavior, acceptance criteria, edge cases, and cross-system contract usage.
- Specs must NOT: redefine system responsibilities, alter slice scope, or introduce design requirements not in Steps 1-5.

**2. Downward Leakage Test:**
Does this change prescribe specific implementation approaches, engine patterns, or code structure?
- If YES → reject. Specs describe WHAT happens (behavior), not HOW to build it (implementation).
- Specs may: describe observable behavior and acceptance criteria.
- Specs must NOT: specify class names, method signatures, engine APIs, or implementation strategies. Those belong in tasks and engine docs.

**3. "Would This Survive Implementation Change?" Test:**
If the engine or implementation approach changed tomorrow, would this spec still be valid?
- If NO → the spec is encoding an implementation assumption, not a behavioral description. Reject or rewrite as behavior.
- If YES → safe behavioral spec. Accept.

These tests apply to both reviewer-proposed changes AND existing spec content flagged during review.

## Step 5 — Create Review Log

After all iterations complete, create a review log in `scaffold/decisions/review/`:
- Use the template at `scaffold/templates/review-template.md`.
- Name it: `REVIEW-spec-SPEC-###-<YYYY-MM-DD>.md`
- Fill in all sections from the iteration data.
- Update `scaffold/decisions/review/_index.md` with a new row.

**This skill does not approve or rename spec files.** Approval happens later in the workflow, after human triage resolves strategic issues and `/scaffold-approve-specs` finalizes the spec set.

## Step 6 — Report

```
## Spec Review Complete: SPEC-### — [Name]

### Most Dangerous Thing
[The single issue most likely to cause implementation divergence, integration pain, or testing failure. If no critical issues, write "No critical risks identified."]

### Undetected Failure Risk
[What implementation bugs could exist if all acceptance criteria pass? List behavioral failures, integration breaks, and edge cases that could slip through even if every AC is verified green. Short list = strong ACs. Long list = weak ACs.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Behavioral Correctness | N | N | N |
| 2. System Behavior Alignment | N | N | N |
| 3. Slice Goal Alignment | N | N | N |
| 4. Cross-System Behavior & Contracts | N | N | N |
| 5. Acceptance Criteria Quality | N | N | N |
| 6. Robustness & Decision Compliance | N | N | N |

**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/REVIEW-spec-SPEC-###-YYYY-MM-DD.md
```

## Rules

- **Claude is the authority on this codebase.** Ties go to Claude. The reviewer is an outsider with no project context beyond what's provided.
- **Specs describe BEHAVIOR, not IMPLEMENTATION.** If the reviewer suggests implementation-level changes (signal names, class names, engine constructs), reject them and propose behavioral alternatives. This is the most common reviewer error for spec review.
- **Only edit the spec file.** Never edit slices, system designs, indexes, engine docs, or other documents during review. If a change requires editing outside the spec, log it as an action item.
- **Never apply changes that violate document authority.** If the reviewer suggests something that contradicts a higher-ranked document, reject it and explain why.
- **Never blindly accept.** Every issue gets evaluated against project context and the authority chain.
- **Pushback is expected and healthy.** The value is in the discussion, not automatic acceptance.
- **Reappearing material issues escalate to the user.** If the same significant issue persists across 2+ iterations, Claude and the reviewer cannot agree — the user decides. Present escalated issues using the Human Decision Presentation pattern (see WORKFLOW.md) — numbered, with concrete options (a/b/c). Trivial repeated nitpicks do not warrant escalation.
- **Ambiguous upstream behavior is not a spec defect.** When a system design or slice genuinely permits multiple valid behavioral interpretations and the spec chose a reasonable one, do not treat the spec as incorrect. Flag for user decision to lock the interpretation upstream. The reviewer's preferred behavior is not automatically correct — behavioral ambiguity often means the system design needs tightening, not the spec.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the spec harder to implement or test? (b) does this improve behavioral clarity, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving testability, optimize for review criteria over practical implementation guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing specs that are hyper-consistent but less implementable or testable. The goal is specs a developer can build and verify against, not ones that score perfectly on an internal consistency audit.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "AC too vague" and "no testable condition" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Upward leakage — does this introduce system responsibilities, slice scope, or design decisions belonging in higher-ranked docs? If yes, reject. (2) Downward leakage — does this prescribe implementation approaches, engine patterns, or code structure? Specs describe behavior, not implementation. (3) "Would this survive implementation change?" — if the engine changed, would this spec still hold? If no, it's encoding implementation, not behavior.
- **Sleep between API calls.** Add `sleep 10` between topic transitions to respect rate limits.
- **Clean up temporary files** (message files used for `--message-file`) after use.
- **If the Python script fails, report the error and stop.** Do not work around script errors.

---
name: scaffold-iterate-slice
description: Adversarial per-topic slice review using an external LLM. Reviews slices across 5 topics (proof quality, boundary design, integration completeness, demo sufficiency, sequencing & transition) with back-and-forth discussion. Use for deep slice review beyond what review-slice catches.
argument-hint: [SLICE-### or SLICE-###-SLICE-### range] [--focus "concern"] [--iterations N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Slice Review

Run an adversarial per-topic review of vertical slices using an external LLM reviewer: **$ARGUMENTS**

This skill reviews slice documents across 5 sequential topics, each with its own back-and-forth conversation. The reviewer focuses deeply on one concern at a time. This is the slice-specific equivalent of `/scaffold-iterate-spec` — it uses the same Python infrastructure but with slice-optimized topics that probe planning quality rather than behavioral correctness.

## Architecture

```
TOPIC LOOP (5 sequential topics per iteration)
├─ Topic 1: Proof Quality & Risk Reduction
│   ├─ Python script sends slice + context to reviewer → structured issues JSON
│   ├─ INNER LOOP (exchanges — back-and-forth)
│   │   ├─ Claude evaluates each issue (agree / pushback / partial)
│   │   ├─ If pushback → Python sends Claude's response to reviewer
│   │   ├─ Reviewer counter-responds → Claude re-evaluates
│   │   └─ ... until consensus or max exchanges
│   ├─ Consensus → apply agreed changes
│   └─ Log topic results
├─ Topic 2: Slice Boundary Design
│   └─ ... same inner loop
├─ ... Topics 3–5
└─ Sleep 10s between topics to avoid rate limits

OUTER LOOP (iterations — repeat full 5-topic cycle on updated slice)
├─ Iteration 1: Topics 1-5 with discussion
├─ Iteration 2: Topics 1-5 on updated slice (if --iterations > 1)
└─ ... up to max iterations or until no issues found
```

## Topics

| # | Topic | What It Evaluates |
|---|-------|-------------------|
| 1 | Proof Quality & Risk Reduction | Does this slice meaningfully reduce project uncertainty? Does it prove a risky integration, a player loop, or an infrastructure dependency — or just exercise an easy happy path? **Check the Proof Value section** — does it clearly state what uncertainty the slice reduces? If Proof Value is vague or missing, the slice may be progress theater. **Check Assumptions** — are they realistic, or do they hide unproven prerequisites? **Detect progress theater:** if the slice only validates trivial behavior (e.g., "place a wall" with no cross-system reaction), it's not buying certainty. Ask: *if this slice passes, what important thing do we now know that we didn't know before?* Core question: *is this slice buying certainty or producing progress theater?* |
| 2 | Slice Boundary Design | Is the slice boundary optimal? Could it be split into smaller proofs or merged with another slice for a stronger combined proof? Does the scope leak into what later slices should prove? Does it collapse multiple future slices into one over-ambitious proof? **Detect fake verticality:** if the slice claims to prove a cross-system behavior but nothing actually triggers the reaction chain (e.g., "RoomSystem detects rooms" but no building placement exists to trigger it), the slice isn't truly vertical. **Final-product design check** — does this slice implement a correct subset of final behavior, or does it introduce a temporary design that will require rework? A slice that proves "colonist needs with correct ownership and authority boundaries, but only hunger — not fatigue or stress yet" is incremental. A slice that proves "a simplified needs system with different ownership that will be redesigned when we add the real one" is temporary design. The former builds toward the final product; the latter creates rework debt. Slices control *when* behavior is implemented, not *how* it is designed. Core question: *are we proving exactly the right amount — not too much, not too little?* |
| 3 | Integration & Cross-System Completeness | Are all cross-system interactions the goal implies actually covered? Are authority boundaries respected? Are hidden dependencies on other systems made explicit — are there systems the slice depends on but does not declare in Systems Covered? **Detect missing system reactions:** does the slice include the full reaction chain (events, recalculations, state propagation, UI feedback), or only the initiating system? Does the slice acknowledge secondary system reactions or side effects? **Detect fragile state:** does the slice introduce new persistent state that could break on reload or reinitialization? Could the system's behavior change if the game saved and reloaded after this slice? Is the slice only proving the happy path, or does it include at least one meaningful failure/rejection path where relevant? Core question: *will this slice actually prove the systems work together, or just that they exist?* |
| 4 | Demo & Done Criteria Sufficiency | Is the demo script convincing proof, or could it pass even if the integration is broken? **Detect unfalsifiable demos:** can the demo distinguish between correct and broken behavior? If the expected results are vague ("system works"), the demo cannot fail and therefore proves nothing. **Check Visible Proof section** — does it describe what the tester should visibly see? If Visible Proof is empty or relies on logs/internal state, the slice is proving something invisible. **Detect invisible proofs:** does the slice produce player-visible feedback, or does the demo rely on inspecting internal state/logs? If someone watched the demo without developer tools, would they know the slice succeeded? **Check Starting Conditions section** — Starting Conditions is a first-class section separate from Demo Script. Are starting conditions explicit enough to reproduce the demo? Are expected results concrete enough to verify pass/fail? **Check Failure Modes This Slice Should Catch** — does the slice define what breakage should be visible if it fails? A strong slice is defined by the bugs it would expose, not just the happy path. Does the demo exercise every done criterion? Is there a gap between what the demo proves and what the goal claims? Core question: *if someone ran this demo, would they actually know whether the slice works?* |
| 5 | Sequencing, Prerequisites & Transition | Does this slice depend on behavior that should be proven by an earlier slice? Check the `> **Depends on:**` field — are declared dependencies correct, complete, and not missing any implicit prerequisites? Are there undeclared dependencies that should be explicit? **Detect ordering traps:** automation before the manual loop works, detection/classification before the underlying rules are stable, systems tested under trivial conditions instead of realistic ones. Does it assume infrastructure that hasn't been established? **Detect temporary architecture:** does the slice prove behavior using the final architecture defined in `architecture.md`, or does it use temporary plumbing that will be rewritten? Are system boundaries, ownership assignments, and contracts designed for the shipped game even though this slice only implements a subset? A slice that uses correct ownership but only exercises one path is incremental. A slice that uses wrong ownership because "the real system isn't built yet" is temporary design — and violates the design-for-final-product rule. If this slice completes, does it unlock cleaner spec/task generation for the next slice, or does uncertainty remain basically unchanged? Is it a dead-end proof with little downstream leverage? Core question: *does this slice fit correctly in the implementation sequence and leave the project in a better state?* |

**After all topics complete**, the reviewer must answer two final questions:

1. **What is the single most dangerous thing about this slice?** — the issue most likely to cause implementation failure, integration surprise, or planning rework.

2. **What could go wrong that this slice would fail to detect?** — list the architectural failures, integration breaks, and propagation bugs that could exist even if the demo passes. If the list is long, the slice is weak. A good slice is defined not by what it proves works, but by what failures it would catch.

Both answers go at the top of the report, before topic-level detail.

**The most valuable failure to detect:** The slice demo can pass even if the architecture is wrong. That means the slice is validating the wrong thing.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| slice | Yes | — | Single `SLICE-###` or range `SLICE-###-SLICE-###` |
| `--focus` | No | — | Narrow the review within each topic to a specific concern. Example: `--focus "save/load prerequisites"`, `--focus "room system integration"` |
| `--iterations` | No | 10 | Maximum outer loop iterations (full 5-topic cycles). Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | all | Review only a specific topic (1-5). Skips other topics. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic before forcing consensus. |

## Range Behavior

If the argument contains a hyphen between two SLICE-### IDs:
1. Extract start and end numbers. If start > end, swap them.
2. Build ordered list. Execute the full review pipeline for each slice sequentially. **Parallelization:** Slices whose `Depends on` fields are satisfied (all dependencies already processed or have no dependencies) can run in parallel. Slices with unmet dependencies wait until those dependencies complete. See WORKFLOW.md Range Parallelization for the full pattern.
3. Between each slice, output a horizontal rule (`---`) and a header: `## Reviewing: SLICE-### — [Name] ([N of M])`
4. Skip missing slice files with a note: `**SLICE-###: No file found — skipping.**`
5. After all slices, output a summary table:

```
## Range Review Summary: SLICE-### through SLICE-###

| Slice | Topics | Issues | Accepted | Rejected | Iterations | Status |
|-------|--------|--------|----------|----------|------------|--------|
| SLICE-### — Name | 5/5 | N | N | N | M | Updated / Unchanged |
| SLICE-### — Name | — | — | — | — | — | Skipped (no file) |
| ... | ... | ... | ... | ... | ... | ... |
```

## Step 1 — Resolve Target

Parse the argument:
- If a SLICE-### ID is given, Glob `scaffold/slices/SLICE-###-*.md`.
- If a range is given, resolve each slice in order (per Range Behavior above).
- If the slice file doesn't exist, skip it (range mode) or report and stop (single mode).

Read the slice file. Validate it has a Phase reference and Goal section. If malformed, report and skip/stop.

Determine slice status from the `> **Status:**` field in the slice header. If missing, treat the slice as Draft.

## Step 2 — Gather Context Files

Read and pass these as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| Parent phase file (follow Phase reference) | Phase scope and exit criteria |
| System designs for all systems in Systems Covered | Integration and authority context |
| `scaffold/design/interfaces.md` | Cross-system contracts |
| `scaffold/design/authority.md` | Data ownership boundaries |
| `scaffold/design/architecture.md` | Foundation decisions |
| `scaffold/decisions/known-issues.md` | Known constraints |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| Relevant ADRs — filter to ADRs that reference systems in Systems Covered, interfaces in Integration Points, or were created after the slice's approval baseline. Determine the baseline using: (1) slice approval date if explicitly present in header, (2) most recent revision log date for this slice, (3) file timestamp as fallback. | Design decision context |
| Earlier slice files in the same phase with status Complete or Approved, ordered before the target slice in implementation order | Sequencing and prerequisite context |

Only include context files that exist — skip missing ones silently.

## Step 3 — Topic Loop

Determine which topics to review:
- If `--topic N` is provided, review only that topic.
- Otherwise, review topics 1 through 5 sequentially.

**Failure injection:** For each topic, inject at least one plausible important failure scenario and evaluate whether the current goal, integration points, done criteria, and demo would detect it. This is the core adversarial technique — don't just check if the slice looks good, check if it would catch real problems.

For each topic:

### 3a. Request Topic Review

Run:
```bash
python scaffold/tools/doc-review.py review <slice-path> --iteration N --topic T --context-files <file1> <file2> ... [--focus "<value>"]
```

Parse the JSON output. If `"error"` key exists, report the error and stop.

### 3b. Filter Issues

Keep all issues (HIGH, MEDIUM, LOW) — slices use Full tier.

If no issues remain, skip to the next topic — this topic passed.

### 3c. Inner Loop — Evaluate Issues

For each issue, read the relevant section of the slice and any context files. Evaluate:

- **AGREE** — The issue is valid. Note the change to make.
- **PUSHBACK** — The issue is wrong or out of scope. Explain why with reference to project documents. Claude draws on full project knowledge — not just the context files sent to the reviewer. Claude may cite ADRs, phase scope, other slices, architecture docs, or known issues the reviewer hasn't seen. This asymmetry is intentional.
- **PARTIAL** — The issue has merit but the suggested fix isn't right. Propose an alternative.

**Key constraint for slices:** When evaluating changes, ensure they stay at the planning level. If a reviewer suggests adding implementation details (specific code patterns, engine constructs, class names), reject the suggestion and propose a planning-level alternative. Slices describe what to prove, not how to code it.

Compose Claude's response, write to a temporary file, then send:

```bash
python scaffold/tools/doc-review.py respond <slice-path> --iteration N --topic T --message-file <temp-file>
```

Parse the reviewer's counter-response. Continue exchanges up to `--max-exchanges`.

**Key rule:** Claude is the authority on this codebase. Ties go to Claude.

### 3d. Request Topic Consensus

After exchanges complete:

```bash
python scaffold/tools/doc-review.py consensus <slice-path> --iteration N --topic T
```

Parse the consensus JSON.

### 3e. Apply Changes

For each change in `changes_to_apply` from the consensus:
- Read the relevant section of the slice document.
- Apply the change using the Edit tool.
- Never apply changes that violate document authority (higher-rank docs win).
- Never introduce implementation details into slice content.
- **Only edit the slice file.** Never edit phases, specs, tasks, system designs, or other documents during review. If a change requires editing outside the slice, log it as an action item.

### 3f. Log Topic Results

Record for the review log:
- Topic name and score (if provided)
- Issues raised, their resolutions (accepted/rejected/modified)
- Changes applied
- **Injected failure scenario** for this topic and whether the current slice would detect it

### 3g. Transition to Next Topic

Output a summary line:
```
### Topic T: [Name] — Issues: A raised, B accepted, C rejected
```

Add `sleep 10` between topics to avoid rate limits, then proceed to the next topic.

## Step 4 — Iterate

### Single-Slice Review

If `--iterations > 1`:

1. After all 5 topics complete, re-read the slice file (it may have been modified) and repeat the full topic loop on the updated content.
2. Track reappearing issues. Two issues are considered the **same issue** if they match on all three criteria: (a) same slice section (e.g., Goal, Integration Points, Demo Script), (b) same issue type (e.g., hidden prerequisite, scope leak, weak proof), and (c) same underlying problem, even if phrased differently by the reviewer across iterations. If the same issue appears in 2+ iterations, escalate to the user.

### Range Review

For a range (e.g., `SLICE-001-SLICE-010`), **every slice in the range must be reviewed**. The range is a work list. Reviewing one slice and stopping is a skill failure.

1. **Build work list.** Glob all slice files matching the range. Sort by ID. Log: "Reviewing N slices: SLICE-001, SLICE-002, ..."
2. **Spawn parallel agents.** One agent per slice, all spawned in parallel (use multiple Agent tool calls in a single message). Each agent runs a **complete, self-contained review** of ONE slice — all 5 topics, all exchanges, all iterations up to `--iterations` max, all adjudication, all edits. An agent is the same as running `iterate-slice SLICE-###` on that slice alone. Each agent receives the slice file, context files (phase file, specs, system designs, interfaces, design doc, glossary, ADRs, known issues), review config, and full topic/adjudication instructions.
3. **Collect results.** As agents complete, log progress: "SLICE-### — Rating: X/5, Issues: Y accepted, Z rejected (N of M complete)"
4. **Agent failure handling.** Failed agents retry once after all others complete. If retry fails, report as "review failed" with the error.

**Stop conditions** (any one stops iteration):
- **Clean:** No issues found in a full 5-topic pass.
- **Stable:** No new issues compared to the previous iteration — the same rejected issues keep cycling.
- **Converged:** Changes were applied but no further issues remain after applying them.
- **Limit:** Iteration limit reached.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue. Examples:
- "slice scope too broad" and "too many systems in one slice" → same issue if they stem from the same scope concern.
- "done criteria vague" and "no clear completion test" → same issue.

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
| **Accept → edit slice** | Apply change immediately. The issue is valid and the fix is within slice scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or the issue is out of scope. |
| **Escalate to user** | Requires design judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag for phase/architecture revision** | The slice may be correct but a higher-authority document needs updating. Log as action item. |
| **Flag ambiguous slice boundary** | Slice boundary or done criteria permits multiple valid interpretations. Not incorrect — genuinely ambiguous. Escalate to user for scoping decision rather than forcing one reading. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- Prefer fixing the slice over escalating — most issues are slice-level clarity.
- Never "half-accept" — choose exactly one outcome per issue.
- If the issue depends on a phase-level or architecture-level decision → flag for phase/architecture revision, not slice fix.
- If the issue is slice-specific clarity or proof design → accept and fix.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of slice boundary, done criteria, or integration scope exist → flag ambiguous slice boundary for user decision. Do not treat ambiguity as a defect or force a single reading at review level.

### Scope Collapse Guard

Before accepting any change to a slice, enforce these three tests to prevent slice-layer expansion into phase, system, or spec territory:

**1. Upward Leakage Test:**
Does this change introduce phase-level scope decisions, system behavior, or design choices that belong in higher-ranked docs?
- If YES → reject. Slices define what vertical chunk to build and prove, not what the game is or how phases are scoped.
- Slices may: define integration goals, done criteria, system touchpoints, and proof targets.
- Slices must NOT: redefine phase scope, alter system responsibilities, or introduce design requirements not in Steps 1-3.

**2. Downward Leakage Test:**
Does this change prescribe specific spec-level behavior or task-level implementation steps?
- If YES → reject. Slices define boundaries and goals; specs and tasks fill in the behavioral and implementation detail.
- Slices may: describe what capability the slice proves at a high level.
- Slices must NOT: dictate specific acceptance criteria for individual behaviors or prescribe implementation approaches.

**3. "Would This Survive Phase Rescoping?" Test:**
If the phase scope changed tomorrow, would this slice definition still make sense?
- If NO → the slice is encoding a phase assumption, not an independent proof target. Reject or rewrite as a dependency.
- If YES → safe slice definition. Accept.

These tests apply to both reviewer-proposed changes AND existing slice content flagged during review.

## Step 5 — Create Review Log

After all iterations complete, create a review log in `scaffold/decisions/review/`:
- Use the template at `scaffold/templates/review-template.md`.
- Name it: `ITERATE-slice-SLICE-###-<YYYY-MM-DD>.md`
- Fill in all sections from the iteration data.
- **Include an Action Items section** listing any out-of-slice changes logged during review, with target document, reason, and suggested action for each.
- Update `scaffold/decisions/review/_index.md` with a new row.

**This skill does not approve slice files.** Approval happens later in the workflow via `/scaffold-approve-slices`.

## Step 6 — Report

```
## Slice Review Complete: SLICE-### — [Name]

### Most Dangerous Thing
[The single issue most likely to cause implementation failure, integration surprise, or planning rework. If no critical issues, write "No critical risks identified."]

### Undetected Failure Risk
[List architectural failures, integration breaks, and propagation bugs that could exist even if this slice's demo passes. If the list is short, the slice is strong. If the list is long, the slice needs strengthening.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Proof Quality & Risk Reduction | N | N | N |
| 2. Slice Boundary Design | N | N | N |
| 3. Integration & Cross-System Completeness | N | N | N |
| 4. Demo & Done Criteria Sufficiency | N | N | N |
| 5. Sequencing, Prerequisites & Transition | N | N | N |

**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N (edits made to the slice file)
**Action items logged:** N (required changes outside the slice file — phase, architecture, etc.)
**Review log:** scaffold/decisions/review/ITERATE-slice-SLICE-###-YYYY-MM-DD.md
```

## Rules

- **Claude is the authority on this codebase.** Ties go to Claude. The reviewer is an outsider with no project context beyond what's provided.
- **Slices describe WHAT TO PROVE, not HOW TO CODE IT.** If the reviewer suggests implementation-level changes (engine patterns, class structures, code organization), reject them and propose a planning-level alternative.
- **Only edit the slice file.** Never edit phases, specs, tasks, system designs, or other documents during review. If a change requires editing outside the slice, log it as an action item.
- **Never apply changes that violate document authority.** If the reviewer suggests something that contradicts a higher-ranked document, reject it and explain why.
- **Never blindly accept.** Every issue gets evaluated against project context and the authority chain.
- **Pushback is expected and healthy.** The value is in the discussion, not automatic acceptance.
- **Design for the final product.** When evaluating slice boundary or scope changes, prefer the option that builds toward the final shipped architecture. Never accept changes that would introduce temporary designs requiring later rework.
- **Status-aware review posture.** Draft slices: optimize boundary and proof design. Approved slices: be stricter on readiness and sequencing. Complete slices: focus on drift and whether the slice doc still matches reality. Determine status from the `> **Status:**` header field.
- **Stay slice-scoped.** If the reviewer proposes changes that alter the phase structure (adding/removing slices, reordering multiple slices, redefining phase scope), log it as an action item for phase revision rather than modifying the slice. This skill refines individual slice design — it does not redesign the phase plan.
- **Ordering comes from _index.md.** Determine "earlier slices" based on the ordering in `scaffold/slices/_index.md`, not just ID numbering. Index order is canonical.
- **Reappearing material issues escalate to the user.** If the same significant issue persists across 2+ iterations, Claude and the reviewer cannot agree — the user decides. Present escalated issues using the Human Decision Presentation pattern (see WORKFLOW.md) — numbered, with concrete options (a/b/c). Trivial repeated nitpicks do not warrant escalation.
- **Sleep between API calls.** Add `sleep 10` between topic transitions to respect rate limits.
- **Clean up temporary files** (message files used for `--message-file`) after use.
- **If the Python script fails, report the error and stop.** Do not work around script errors.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Upward leakage — does this introduce phase scope, system behavior, or design choices belonging in higher-ranked docs? If yes, reject. (2) Downward leakage — does this prescribe spec-level behavior or task-level implementation? Slices set boundaries, not detail. (3) "Would this survive phase rescoping?" — if the phase changed, would this slice still make sense? If no, it's encoding phase assumptions, not an independent proof target.
- **Ambiguous slice boundaries are not defects.** When a slice genuinely permits multiple valid boundary definitions, done criteria, or integration scope interpretations, do not treat ambiguity as an error. Flag for user decision. The reviewer's preferred boundary is not automatically correct — slice flexibility may reflect intentional scoping decisions.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the slice harder to implement as a vertical proof? (b) does this improve clarity for development, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving implementability, optimize for review criteria over practical development guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing slices that are hyper-consistent but less buildable or flexible. The goal is slices the team can implement end-to-end, not ones that score perfectly on an internal consistency audit.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "slice scope too broad" and "too many systems" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.

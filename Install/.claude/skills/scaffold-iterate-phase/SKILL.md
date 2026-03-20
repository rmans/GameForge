---
name: scaffold-iterate-phase
description: Adversarial per-topic phase review using an external LLM. Reviews phases across 4 topics (scope quality, entry/exit chain, system coverage, risk awareness) with back-and-forth discussion. Use for deep phase review beyond what fix-phase catches.
argument-hint: [P#-### or P#-###-P#-###] [--focus "concern"] [--iterations N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Phase Review

Run an adversarial per-topic review of phase scope gates using an external LLM reviewer: **$ARGUMENTS**

This skill reviews phase documents across 4 sequential topics, each with its own back-and-forth conversation. It uses the same Python infrastructure as iterate-slice/iterate-spec/iterate-task but with phase-optimized topics.

## Topics

| # | Topic | What It Evaluates |
|---|-------|-------------------|
| 1 | Scope Quality & Milestone Clarity | Is the goal outcome-oriented or task-oriented? **Check Capability Unlocked** — is the phase outcome expressed as a new demonstrable capability, not a bundle of tasks? Could QA tell the difference between before-phase and after-phase without reading code? **Phase contract consistency** — do Capability Unlocked, Goal, Deliverables, and Exit Criteria all describe the same outcome? If they diverge (e.g., capability says "storms damage structures" but exit criteria says "storm prototype demo exists"), flag as phase contract inconsistency. Are In Scope items specific enough to generate slices? Are Out of Scope items drawing the right lines? Are deliverables demonstrable? Is the phase achievable in one implementation cycle? If In Scope contains more than 5 systems, flag as likely over-scoped. **Behavior count check** — if Capability Unlocked implies multiple independent gameplay behaviors (e.g., "storms damage structures, storms cause instability, storms disrupt logistics"), flag as likely multiple milestones hidden in one phase. A phase with 1 system but 3 independent behaviors is still over-scoped. Treat behaviors as independent only if they could reasonably be implemented, tested, and deferred separately without breaking the core capability. Linked consequences of a single behavior (e.g., "storms damage structures" and "storms cause fires from surge events") may be one milestone, not two. **Phantom deliverable check** — do the deliverables and exit criteria actually cause the capability to exist in the simulation, or could they be satisfied by a mock, visualization, or diagnostic tool alone? If the capability could pass exit criteria without affecting simulation behavior (e.g., a debug overlay shows storm damage values but structures aren't actually damaged), flag as phantom deliverable. **Slice readiness check** — for each In Scope item, could a vertical slice be generated without introducing new systems or inventing undefined behaviors? If an item is too abstract to generate slices (e.g., "StormSystem" rather than "storm events damage exposed structures"), flag as underspecified for slice generation. **Final-product design check** — does this phase scope *when* to build, or does it silently introduce a temporary design that will require rework? Specs describe final behavior; phases only control when that behavior is implemented. If the phase scope says "simple version now, redesign later," that violates the design-for-final-product rule. Are system boundaries, ownership, and contracts designed for the shipped game even though this phase only implements a subset? Would implementing this phase create technical debt that contradicts the architecture, or does it build correctly toward the full system? Core question: *what can the team do after this phase that it could not do before?* |
| 2 | Entry/Exit Chain & Sequencing | Do entry criteria reference specific IDs? **Compare prior phase exit wording to this phase's entry wording semantically, not just by referenced ID.** "Prototype demo exists" and "system implemented" are not equivalent even if the phase ID matches. Can entry criteria be satisfied by prior phases' actual exit guarantees? Do exit criteria match the goal? Are exit criteria observable without reading code — testable via playtest, dev demo, UI display, or deterministic test scenario? Are there hidden prerequisites not declared in entry criteria or dependencies? Does this phase depend on foundation decisions not yet locked? If entry criteria reference more than 3 prior phases, flag as dependency chain too deep — brittle if any earlier phase slips. **Roadmap ordering check** — if the phase's goal or scope depends on systems that are first introduced in a later roadmap phase, flag as roadmap ordering violation. Check the roadmap to verify all required systems are available by the time this phase starts. Core question: *can this phase start when its predecessors complete, and can the next phase start when this one completes?* |
| 3 | System Coverage & Authority | Does the scope cover the right systems for the goal? Are authority boundaries respected — does this phase claim to deliver behavior that belongs to systems outside its scope? **Does the phase mix systems from different authority layers without naming the integration purpose?** Does the phase imply cross-layer mutation that contradicts the authority model? Are cross-system interactions acknowledged? Does the scope match what the roadmap intended for this phase? If goal or exit criteria imply behavior owned by systems not listed in In Scope, flag as hidden system dependency. **Incremental-not-temporary check** — does this phase implement a correct subset of final behavior, or does it implement a different behavior that will need to be torn out and replaced? A phase that delivers "half the colonist needs loop with correct ownership" is incremental. A phase that delivers "a simplified needs system with wrong ownership that will be redesigned in Phase 3" is temporary design. The former is fine; the latter violates design-for-final-product. Core question: *does this phase own what it claims to deliver?* |
| 4 | Risk Awareness & Decision Currency | Are relevant ADRs reflected in scope? Are known issues that constrain this phase acknowledged? Are playtest patterns addressed? Does the scope account for foundation architecture decisions? **Does this phase still reflect the current roadmap position and intent, or is it carrying stale assumptions from before roadmap/design changes?** Are there risks the phase ignores that could force mid-phase re-scoping? What downstream work does this phase unlock — if unclear, the phase may not be a real milestone? **Downstream boundary check** — if deliverables or exit criteria implement behavior that logically belongs to a later phase's capability, flag as phase boundary leakage. A phase that silently absorbs the next phase's milestone undermines the roadmap. Do not flag enabling prerequisites as leakage — only flag behavior that directly satisfies a later phase's core capability (e.g., "damage thresholds exist" is a prerequisite, "full collapse simulation" is leakage). Core question: *is this phase planning against current reality or stale assumptions?* |

**After all topics complete**, the reviewer must answer three final questions and provide a rating:

1. **What is the single most dangerous thing about this phase?** — the issue most likely to cause re-scoping, slice rework, or blocked implementation.

2. **What could go wrong that this phase's exit criteria wouldn't catch?** — list the failures that could exist even if all exit criteria pass. Short list = strong phase. Long list = weak phase.

3. **Is this phase worth existing as a separate phase?** — should it merge with an adjacent phase, or is it genuinely a distinct milestone? Sometimes the correct answer is that a phase should not exist independently.

4. **Phase Strength Rating (1–5):**
   - 1 = fundamentally broken (capability missing, contract inconsistent, hidden dependencies)
   - 2 = major restructuring needed (scope unclear, chain broken, authority violations)
   - 3 = workable but weak (vague criteria, missing risk awareness, over-scoped)
   - 4 = solid milestone (clear capability, clean chain, minor wording issues)
   - 5 = strong milestone (demonstrable capability, tight criteria, good boundaries)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| phase | Yes | — | Single `P#-###` or range `P#-###-P#-###` |
| `--focus` | No | — | Narrow the review within each topic to a specific concern |
| `--iterations` | No | 10 | Maximum outer loop iterations (full 4-topic cycles). Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | all | Review only a specific topic (1-4) |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic |

## Preflight

Before running external review:

1. **Check status.** If `Status: Complete` → stop ("phase already complete, nothing to review"). If `Status: Approved` → review in read-only mode (report issues but do not modify the phase file — approved phases require an ADR or `/scaffold-revise-phases` to change).
2. **Check structure.** Verify the phase has required structural sections: Goal, Capability Unlocked, Entry Criteria, In Scope, Out of Scope, Deliverables, Exit Criteria, Dependencies. If any are structurally missing (not just empty — absent), stop and instruct the user to run `/scaffold-fix-phase` first. Don't waste adversarial cycles on a malformed doc.

## Context Files

**Read the target phase file first.** Extract referenced systems, ADRs, dependencies, and adjacent phase IDs. Then build the context set from those references — don't dump generic context.

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| `scaffold/phases/roadmap.md` | Roadmap alignment and sequencing |
| `scaffold/design/design-doc.md` | Vision alignment |
| `scaffold/design/architecture.md` | Foundation decision awareness |
| `scaffold/design/authority.md` | Data ownership boundaries |
| `scaffold/design/interfaces.md` | Cross-system contract verification |
| `scaffold/decisions/known-issues.md` | Known constraint awareness |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| ADRs referenced in the phase or affecting its systems | Decision compliance |
| Prior/next phase files (if they exist) | Entry/exit chain validation — **mandatory for Topics 2 and 3** when available. Chain review without neighboring phases is half-blind. |

Only include context files that exist — skip missing ones silently.

## Execution

### Single-Phase Review

For a single phase, follow the standard topic loop, inner loop (exchanges), consensus, and apply-changes pattern. Run all topics sequentially with back-and-forth exchanges up to `--max-exchanges`, then iterate up to `--iterations` max.

### Range Review

For a range (e.g., `P1-001-P1-005`), **every phase in the range must be reviewed**. The range is a work list, not a suggestion. Reviewing one phase and stopping is a skill failure.

1. **Build work list.** Glob all phase files matching the range. Sort by ID. Log: "Reviewing N phases: P1-001, P1-002, ..."
2. **Spawn parallel agents.** One agent per phase, all spawned in parallel (use multiple Agent tool calls in a single message). Each agent runs a **complete, self-contained review** of ONE phase — all topics, all exchanges, all iterations up to `--iterations` max, all adjudication, all edits. An agent is the same as running `iterate-phase P#-###` on that phase alone. Each agent receives the phase file, context files (roadmap, design doc, glossary, systems index, ADRs, known issues), review config, and full topic/adjudication instructions.
3. **Collect results.** As agents complete, log progress: "P#-### — Rating: X/5, Issues: Y accepted, Z rejected (N of M complete)"
4. **Agent failure handling.** Failed agents retry once after all others complete. If retry fails, report as "review failed" with the error. The range review continues.

**Stop conditions** (any one stops iteration):
- **Clean** — a complete topic pass produces no new issues.
- **Converged** — two consecutive passes produce the same issue set with no new findings.
- **Human-only** — only issues requiring user decisions remain; further iteration won't resolve them.
- **Limit** — `--iterations` maximum reached.
- **Quality degradation** — later iterations produce fewer issues but with weaker reasoning, vaguer evidence, or recycled findings. Treat as convergence and stop early rather than continuing with diminishing returns.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue. Examples:
- "entry criteria too vague" and "phase gate conditions unclear" → same issue if they stem from the same criteria section.
- "system coverage gap" and "missing system in scope" → same issue if about the same system.

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
| **Accept → edit phase** | Apply change immediately. The issue is valid and the fix is within phase scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or the issue is out of scope. |
| **Escalate to user** | Requires planning judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag ambiguous phase scope** | Phase scope permits multiple valid interpretations of entry/exit criteria or system coverage. Not incorrect — genuinely ambiguous. Escalate to user for scoping decision rather than forcing one reading. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- Prefer fixing the phase over escalating — most issues are clarity or consistency.
- Never "half-accept" — choose exactly one outcome per issue.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of phase scope, entry/exit criteria, or coverage exist → flag ambiguous phase scope for user decision. Do not treat ambiguity as a defect or force a single reading at review level.

### Scope Collapse Guard

Before accepting any change to a phase, enforce these three tests to prevent phase-layer expansion into design, system, or implementation territory:

**1. Upward Leakage Test:**
Does this change introduce design decisions, system behavior, or architectural choices that belong in Steps 1-3?
- If YES → reject. Phases define when and what scope of work is done, not what the game is or how systems work.
- Phases may: define entry/exit criteria, system coverage scope, risk assessments, and milestone goals.
- Phases must NOT: redefine features, alter system responsibilities, or introduce architectural requirements not already in Steps 1-3.

**2. Downward Leakage Test:**
Does this change prescribe slice decomposition, spec-level behavior, or task-level implementation detail?
- If YES → reject. Phases set scope boundaries; slices, specs, and tasks fill in the detail.
- Phases may: describe what capability the phase delivers at a high level.
- Phases must NOT: dictate how slices are cut, what specific behaviors specs must define, or how tasks should implement.

**3. "Would This Survive System Redesign?" Test:**
If a system design changed tomorrow, would this phase scope still be valid?
- If NO → the phase is encoding a system design assumption, not a scope decision. Reject or rewrite as a dependency.
- If YES → safe scope decision. Accept.

These tests apply to both reviewer-proposed changes AND existing phase content flagged during review.

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-phase-P#-###-<YYYY-MM-DD>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

```
## Phase Review Complete: P#-### — [Name]

### Most Dangerous Thing
[The single issue most likely to cause re-scoping or blocked implementation.]

### Undetected Failure Risk
[What failures could exist if all exit criteria pass?]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Scope Quality & Milestone Clarity | N | N | N |
| 2. Entry/Exit Chain & Sequencing | N | N | N |
| 3. System Coverage & Authority | N | N | N |
| 4. Risk Awareness & Decision Currency | N | N | N |

**Phase Strength Rating:** N/5 — [one-line reason]
**Slice Readiness:** Ready / Ambiguous / Not ready — [brief explanation if not Ready]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Issue types:** N mechanical wording / N scope design / N chain/sequencing / N authority/ownership / N risk/staleness
**Review log:** scaffold/decisions/review/ITERATE-phase-P#-###-YYYY-MM-DD.md
```

## Rules

- **Project documents and authority order win.** Claude adjudicates conflicts using document authority — higher-ranked documents decide disputes, not Claude's preference.
- **Phases describe SCOPE, not IMPLEMENTATION.** If the reviewer suggests implementation details, reject and propose scope-level alternatives.
- **Only edit the phase file.** Never edit the roadmap, slices, specs, tasks, or other phases during review.
- **Changes must not introduce new systems into In Scope.** The adversarial loop may tighten, clarify, or remove scope — but adding systems expands the phase, which is a planning decision for the user.
- **Edits must not remove systems from In Scope unless the behavior they support is also removed from the phase capability.** Removing a system while keeping the behavior it enables creates an undeliverable phase. If a system appears unnecessary, the capability or deliverables that depend on it must also be adjusted.
- **Edits may clarify or tighten scope but must not broaden phase objectives.** Even without adding systems, rewording can silently expand what the phase delivers (e.g., "storms damage structures" → "storms damage structures and containment"). If an edit would make the phase deliver more than it originally claimed, reject it.
- **Never apply changes that violate document authority.** Higher-ranked documents win.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Pushback is expected and healthy.**
- **Reappearing material issues escalate to the user.** Escalate when the same material issue persists for 2 outer iterations, or when the reviewer and Claude remain split after max-exchanges on a topic. Present escalated issues using the Human Decision Presentation pattern (see WORKFLOW.md) — numbered, with concrete options (a/b/c).
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Upward leakage — does this introduce design, system, or architecture decisions belonging in Steps 1-3? If yes, reject. (2) Downward leakage — does this prescribe slice decomposition, spec behavior, or task implementation? Phases set scope, not detail. (3) "Would this survive system redesign?" — if a system design changed, would this phase still hold? If no, it's encoding system assumptions, not scope.
- **Ambiguous phase scope is not a defect.** When a phase genuinely permits multiple valid scope boundaries, entry/exit criteria, or coverage interpretations, do not treat ambiguity as an error. Flag for user decision. The reviewer's preferred scoping is not automatically correct — scope flexibility may reflect intentional design optionality.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the phase harder to use as a planning gate? (b) does this improve clarity for implementation planning, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving planability, optimize for review criteria over practical development guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing phases that are hyper-consistent but less actionable or flexible. The goal is phases the team can implement against, not ones that score perfectly on an internal consistency audit.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "entry criteria vague" and "phase gate unclear" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.

---
name: scaffold-iterate-roadmap
description: Adversarial per-topic roadmap review using an external LLM. Reviews the roadmap across 5 topics (vision coverage, phase sequencing, milestone quality, risk distribution, player experience evolution) with back-and-forth discussion. Use for deep roadmap review beyond what fix-roadmap catches.
argument-hint: [--focus "concern"] [--iterations N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Roadmap Review

Run an adversarial per-topic review of the project roadmap using an external LLM reviewer: **$ARGUMENTS**

This skill reviews `scaffold/phases/roadmap.md` across 4 sequential topics, each with its own back-and-forth conversation. It uses the same Python infrastructure as iterate-phase/iterate-slice/iterate-spec/iterate-task but with roadmap-optimized topics.

## Topics

| # | Topic | What It Evaluates |
|---|-------|-------------------|
| 1 | Vision Coverage & Scope Alignment | Does the roadmap cover everything the design doc promises? **Cross-check Core Fantasy, Core Loop, Secondary Loops, and Content Structure** — every major feature should map to at least one phase. Is the total scope realistic given the design doc's Scope Reality Check? Are there design doc promises no phase delivers? Are there phases that deliver things the design doc doesn't mention? **System coverage** — is every gameplay-facing or roadmap-relevant system assigned to at least one phase or explicitly deferred? Internal support systems don't need roadmap-level coverage. **Roadmap internal consistency** — does the Capability Ladder match the Phase Overview? Do Phase Boundaries align with phase goals? Does Current Phase match the earliest non-complete phase? Do Upcoming Phases align with Phase Overview order? **Cross-system interaction timing** — do phases introduce system interactions early enough? If systems are introduced in isolation across 3+ phases before any interactions occur, flag as late integration risk — vertical gameplay requires systems talking to each other, not operating in silos. Core question: *does this roadmap deliver the game described in the design doc?* |
| 2 | Phase Sequencing & Dependency Logic | Do phases build logically? Early phases should establish the smallest playable proof first; later phases should build on prior capabilities without introducing avoidable rework. **Does each phase's goal depend only on capabilities delivered by earlier phases?** Are there circular dependencies or phases that assume work not yet done? Is the first phase the smallest playable proof of the core loop? **Phase count** — too few phases (< 3) may mean each is over-scoped; too many (> 12) may mean the roadmap is too granular. Does the sequence minimize rework — are high-uncertainty systems addressed early? **Phase size consistency** — does any phase contain >40% of the roadmap's systems? That phase is likely too large. Flag significant size imbalances between phases. **Roadmap resilience** — if a single phase fails or changes significantly, does the rest of the roadmap collapse? If most later phases depend on one critical phase's exact output, the roadmap is fragile. Risk should be isolated early. Core question: *if you implement these phases in order, does each one have what it needs to start?* |
| 3 | Milestone Quality & Capability Progression | Is each phase a real milestone — does it unlock a new demonstrable capability? **Check that phase goals are outcome-oriented, not task-oriented.** "Prove the core loop works" is a milestone. "Implement 5 systems" is a task list. **Behavior-not-systems test** — are any phases named after systems rather than behaviors? Apply the actor test: can the goal be phrased as "[Actor] can now [do something new]"? Phases named after systems ("Event System", "Morale System") produce horizontal engineering slices, not vertical gameplay slices — flag for reframing. **Capability independence (skip test)** — if a phase were skipped, would the next phase still make sense? If yes, the skipped phase may not unlock a meaningful capability on its own. **Demo realism** — is each phase's demo achievable with the systems assigned to that phase? If the demo requires systems not in scope, the roadmap is internally inconsistent. **Sliceability stress test** — can each phase plausibly decompose into multiple vertical slices without collapsing into horizontal engineering work? If the goal can't produce slices that each deliver observable behavior, the phase may be too abstract or system-oriented. Does each phase build meaningfully on the previous one — is there visible progress after every phase? **Phase boundaries** — does each phase clearly define what it defers? Phases without explicit boundaries tend to expand until unfinishable. Core question: *after each phase, can you show something new that works?* |
| 4 | Risk Distribution & ADR Currency | Are high-risk systems (architecturally novel, untested, cross-cutting) addressed early in the roadmap? **Is risk spread across phases, or concentrated?** A roadmap that defers all risky work to later phases is fragile. Are known issues from `known-issues.md` reflected in phase planning? Are accepted ADRs absorbed — if an ADR changes scope, does the roadmap reflect it? Are playtest patterns (if any) accounted for? **ADR Feedback Log** — are all ADRs from completed phases logged? Core question: *is this roadmap planning against current reality, or the original assumptions?* |
| 5 | Player Experience Evolution | Does the roadmap produce a game, or just a collection of systems? **Core loop validation timing** — when does the core loop become playable? If meaningful player decisions don't emerge until late phases, the roadmap delays validation of the game's core promise. **Player agency progression** — does each phase expand what the player can meaningfully decide, not just what mechanics exist? Good: "player responds to storms" → "player manages colonist reactions" → "player chooses long-term strategy." Bad: "system A" → "system B" → "system C." **Emergent gameplay timing** — when do systems begin influencing each other to produce unplanned outcomes? Delayed emergence means delayed product validation. **Ship definition convergence** — if every phase succeeds, does the roadmap actually deliver the game described in the Ship Definition? Or does it approach it without arriving? **Playtest opportunities** — are phases structured to allow meaningful external feedback cycles early enough to course-correct? **Feature gravity** — are there design doc features (factions, economy, procedural generation, generational systems) that will naturally grow far larger than the roadmap assumes? Flag features treated as small milestones that are likely to expand. Core question: *if we execute this roadmap perfectly, will the result actually be the game we designed?* |

**After all topics complete**, the reviewer must answer three final questions and provide a rating:

1. **What is the single most dangerous thing about this roadmap?** — the structural issue most likely to cause major re-planning or blocked phases.

2. **What could go wrong that this roadmap wouldn't catch?** — list the project failures that could exist even if every phase completes successfully. Short list = strong roadmap. Long list = gaps in coverage.

3. **Is any phase not worth existing?** — identify phases that should merge with adjacent ones, or that don't deliver a meaningful milestone.

4. **Roadmap Strength Rating (1–5):**
   - 1 = fundamentally broken (vision disconnected, critical gaps, impossible sequencing)
   - 2 = major restructuring needed (phases don't build logically, risk concentrated late)
   - 3 = workable but weak (vague milestones, coverage gaps, some ordering issues)
   - 4 = solid plan (clear progression, good coverage, minor gaps)
   - 5 = strong plan (every phase is a real milestone, risk distributed, full coverage)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--focus` | No | — | Narrow the review within each topic to a specific concern |
| `--iterations` | No | 10 | Maximum outer loop iterations (full 4-topic cycles). Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | all | Review only a specific topic (1-4) |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic |

## Preflight

Before running external review:

1. **Check roadmap exists.** If `scaffold/phases/roadmap.md` doesn't exist or is at template defaults, stop: "No roadmap to review. Run `/scaffold-new-roadmap` first."
2. **Check structure.** Verify the roadmap has required sections: Vision Checkpoint, Design Pillars, Ship Definition, Capability Ladder, Phase Overview, Phase Boundaries, System Coverage Map, Current Phase, Upcoming Phases. If any are structurally missing, stop and instruct the user to run `/scaffold-fix-roadmap` first. Without these sections the reviewer must infer too much, producing low-quality feedback.

## Context Files

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| `scaffold/design/design-doc.md` | Vision alignment and scope coverage — the primary authority |
| `scaffold/design/systems/_index.md` | System coverage check |
| `scaffold/design/architecture.md` | Foundation decision awareness |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| `scaffold/decisions/known-issues.md` | Known constraint awareness |
| ADRs with status `Accepted` | Decision compliance and currency |
| Phase files referenced by the roadmap (compact subset) | Phase content verification — goals, scope, sequencing. If many phases exist, include only those needed to verify goals, statuses, and sequencing rather than loading all files. |

Only include context files that exist — skip missing ones silently.

## Execution

Follow the same topic loop, inner loop (exchanges), consensus, and apply-changes pattern as `/scaffold-iterate-slice`. The iteration mechanics, stop conditions, and review log creation are identical.

**Stop conditions** (any one stops iteration):
- **Clean** — a complete topic pass produces no new issues.
- **Converged** — two consecutive passes produce the same issue set with no new findings.
- **Human-only** — only issues requiring user decisions remain; further iteration won't resolve them.
- **Limit** — `--iterations` maximum reached.
- **Quality degradation** — later iterations produce fewer issues but with weaker reasoning, vaguer evidence, or recycled findings. Treat as convergence and stop early rather than continuing with diminishing returns.

**Verification pass rule:** A pass that found issues and applied fixes is NOT clean — it is a "fixed" pass. After a fixed pass, you MUST run at least one more full pass on the updated document to verify no new issues were introduced by the fixes and no previously-hidden issues are now exposed. Only a pass that finds ZERO new issues counts as **Clean**. Stopping after fixing issues without a verification pass is a skill failure.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue. Examples:
- "phase ordering is wrong" and "sequencing creates dependency gaps" → same issue if they stem from the same phase relationship.
- "milestone too vague" and "success criteria unclear" → same issue.

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
| **Accept → edit roadmap** | Apply change immediately. The issue is valid and the fix is within roadmap scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or the issue is out of scope. |
| **Escalate to user** | Requires planning judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag ambiguous scope intent** | Roadmap permits multiple valid phase sequencing or scope interpretations. Not incorrect — genuinely ambiguous. Escalate to user for planning decision rather than forcing one reading. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- Prefer fixing the roadmap over escalating — most issues are clarity or consistency.
- Never "half-accept" — choose exactly one outcome per issue.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of roadmap scope or sequencing exist → flag ambiguous scope intent for user decision. Do not treat ambiguity as a defect or force a single reading at review level.

### Scope Collapse Guard

Before accepting any change to the roadmap, enforce these three tests to prevent roadmap-layer expansion into design or system territory:

**1. Layer Test:**
Does this change introduce design decisions or system behavior that belongs in the design doc or system designs?
- If YES → reject. The roadmap defines when things are built and in what order, not what the game is or how systems behave.
- Roadmap may: define phase goals, ordering, milestones, entry/exit criteria, and risk assessments.
- Roadmap must NOT: redefine game features, alter system responsibilities, or introduce behavioral requirements. Those belong in Steps 1-2.

**2. Scope Boundary Test:**
Does this change tighten phase scope beyond what the design doc and system designs define?
- If the roadmap adds requirements not present in the design doc → it's design leakage into scheduling.
- If the roadmap restricts system behavior beyond what system designs specify → it's system leakage into planning.
- The roadmap sequences existing design decisions; it does not create new ones.

**3. "Would This Survive Design Change?" Test:**
If the design doc changed a feature tomorrow, would this roadmap decision still be valid?
- If NO → the roadmap is encoding a design assumption, not a planning decision. Reject or rewrite as a dependency on the design decision.
- If YES → safe planning decision. Accept.

These tests apply to both reviewer-proposed changes AND existing roadmap content flagged during review.

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-roadmap-<YYYY-MM-DD>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

```
## Roadmap Review Complete

### Most Dangerous Thing
[The structural issue most likely to cause re-planning or blocked phases.]

### Undetected Failure Risk
[What project failures could exist if every phase completes?]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Vision Coverage & Scope Alignment | N | N | N |
| 2. Phase Sequencing & Dependency Logic | N | N | N |
| 3. Milestone Quality & Capability Progression | N | N | N |
| 4. Risk Distribution & ADR Currency | N | N | N |
| 5. Player Experience Evolution | N | N | N |

**Roadmap Strength Rating:** N/5 — [one-line reason]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/ITERATE-roadmap-YYYY-MM-DD.md
```

## Rules

- **Project documents and authority order win.** Claude adjudicates conflicts using document authority — higher-ranked documents decide disputes, not Claude's preference.
- **The roadmap describes WHAT to deliver and WHEN, not HOW.** If the reviewer suggests implementation details, reject and propose planning-level alternatives.
- **Only edit the roadmap file.** Never edit phase files, indexes, design docs, or ADRs during review.
- **Edits may clarify or tighten scope but must not add new phases.** The adversarial loop may sharpen goals, reword milestones, flag gaps, or suggest reordering — but creating new phases is a planning decision for the user.
- **Edits must not remove phases.** Flagging a phase as potentially unnecessary is fine; deleting it is not.
- **Edits must not materially change a phase's promised capability without user confirmation.** Rewording for clarity is fine; "clarifying" a phase goal into a substantially different capability is scope mutation. If an edit would change what the phase delivers, require user confirmation.
- **Never apply changes that violate document authority.** Higher-ranked documents win.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Pushback is expected and healthy.**
- **Reappearing material issues escalate to the user.** Escalate when the same material issue persists for 2 outer iterations, or when the reviewer and Claude remain split after max-exchanges on a topic. Present escalated issues using the Human Decision Presentation pattern (see WORKFLOW.md) — numbered, with concrete options (a/b/c).
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Ambiguous scope intent is not a defect.** When the roadmap genuinely permits multiple valid phase orderings, scope boundaries, or milestone definitions, do not treat ambiguity as an error. Flag for user decision. The reviewer's preferred sequencing is not automatically correct — roadmap flexibility often reflects intentional optionality.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the roadmap harder to use as a planning reference? (b) does this improve clarity for development planning, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving planability, optimize for review criteria over practical scheduling guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing roadmaps that are hyper-consistent but less actionable or flexible. The goal is a roadmap the team can plan from, not one that scores perfectly on an internal consistency audit.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Layer — does this introduce design decisions or system behavior belonging in the design doc or system designs? If yes, reject. (2) Scope boundary — does this tighten phase scope beyond what design doc and system designs define? The roadmap sequences decisions, it doesn't create them. (3) "Would this survive design change?" — if the design doc changed tomorrow, would this roadmap decision still hold? If no, it's design leakage into planning.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "phase ordering wrong" and "sequencing creates gaps" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.

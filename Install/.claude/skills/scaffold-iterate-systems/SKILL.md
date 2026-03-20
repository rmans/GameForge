---
name: scaffold-iterate-systems
description: Adversarial per-topic system design review using an external LLM. Reviews system designs across 5 topics (ownership correctness, behavioral completeness, design governance compliance, cross-system coherence, simulation fitness) with back-and-forth discussion. Consumes design signals from fix-systems. Supports single system or range.
argument-hint: SYS-### or SYS-###-SYS-### [--focus "concern"] [--iterations N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial System Review

Run an adversarial per-topic review of system designs using an external LLM reviewer: **$ARGUMENTS**

This skill reviews system design docs across 5 sequential topics, each with its own back-and-forth conversation. It uses the same Python infrastructure as iterate-design/iterate-roadmap/iterate-references but with system-design-optimized topics.

This is the **design reviewer** — not the formatter. It runs after `fix-systems` has normalized the docs and detected design signals. It evaluates whether the system's design is *good* — whether its boundaries are correct, its behavior is complete, its ownership is defensible, and its role in the simulation is sound.

The real question this review answers: **does this system own the right things, in the right way, without stepping on other systems or violating the design?**

## Topics

| # | Topic | What It Evaluates |
|---|-------|-------------------|
| 1 | Ownership Correctness | Does this system own what it should — and only what it should? |
| 2 | Behavioral Completeness | Does the system describe enough behavior for specs to be written against it? |
| 3 | Design Governance Compliance | Does the system respect invariants, boundaries, control model, and simulation depth? |
| 4 | Cross-System Coherence | Does this system interact correctly with others — dependencies, consequences, authority? |
| 5 | Simulation Fitness | Does this system earn its existence in the simulation? |

### Topic 1 — Ownership Correctness

Does this system own what it should — and only what it should?

- **Simulation responsibility clarity** — is it immediately obvious what state this system uniquely owns? If someone asked "who owns [X]?", does this system's Simulation Responsibility and Owned State answer it unambiguously?
- **Owned State legitimacy** — is every Owned State entry genuinely this system's to write? Could any entry more naturally belong to another system? If another system also needs to update this state, is the boundary clear?
- **Non-Responsibilities honesty** — do the Non-Responsibilities actually name things the system *could* plausibly own but *shouldn't*? Generic exclusions ("doesn't own rendering") are useless. Specific exclusions ("doesn't own colonist mood — owned by NeedsSystem") are valuable.
- **Scope creep detection** — does the system's described behavior extend beyond what its Purpose and Simulation Responsibility claim? If Player Actions or System Resolution describe behaviors not implied by the Purpose, the system is drifting.
- **Authority alignment** — if authority.md exists, does the system's ownership match? If not, which is wrong?
- **Ownership minimality** — does the system own only the state required to fulfill its purpose, or has it accumulated adjacent concerns that belong elsewhere? Example: a ConstructionSystem that also owns mood penalties is exhibiting state sprawl.

Core question: *if you removed this system, what state would become unowned? That set should exactly match what this system claims to own.*

### Topic 2 — Behavioral Completeness

Does the system describe enough behavior for specs to be written against it?

- **Player Actions completeness** — can a spec writer derive atomic behavior specs from the Player Actions section? Are there obvious actions the system should support that aren't listed? Are the actions specific enough to be testable?
- **System Resolution chain** — does every Player Action have a corresponding resolution? Are the consequences observable? If a player performs Action 3, what exactly happens? If the resolution says "the system processes it," that's too vague.
- **Failure path coverage** — does the system describe what happens when things go wrong? Not just "errors occur" but specific failure states with player-visible consequences. What does the player see when placement is invalid, when resources are insufficient, when a job is interrupted?
- **State Lifecycle coverage** — does the lifecycle capture all major phases the system goes through? Are transitions between states clear? Can you trace a complete lifecycle from creation to completion/destruction?
- **Edge case quality** — do the edge cases answer real questions a spec writer or implementer would ask? Vague edge cases ("what if something unusual happens?") don't count. Specific ones ("what if the target tile is destroyed mid-construction?") do.
- **Visibility to Player alignment** — does what's visible match what the player needs to know to make decisions? If the system tracks 10 states but the player can only see 3, are the right 3 visible?
- **Temporal resolution** — when does the system process updates — per tick, per event, per player action, or on demand? If multiple systems respond to the same event, is the order of resolution clear from the doc? Could two systems attempt to update the same state in the same simulation step? If a programmer implemented this behavior, would they know *when* it happens — not just *what* happens?

Core question: *could a spec writer produce complete behavioral specs from this system doc alone, without guessing?*

### Topic 3 — Design Governance Compliance

Does the system respect the design doc's governance mechanisms?

- **Invariant compliance** — does the system's behavior respect every Design Invariant? Check each invariant against the system's Player Actions, System Resolution, and Owned State. If an invariant says "no direct control" and the system offers direct commands, that's a violation.
- **Boundary compliance** — does the system stay within Design Boundaries? Does it accidentally describe features the design doc explicitly excluded?
- **Control model alignment** — do the system's Player Actions match the Player Control Model? If the design says "indirect control through policy," do the actions reflect that? Or do they secretly describe direct manipulation?
- **Simulation depth alignment** — is the system's complexity proportional to the Simulation Depth Target? A system with 20 state transitions and 15 failure modes in a "moderate depth" game may be over-engineered.
- **Design constraint coverage** — does the system's Design Constraints section actually reference the relevant invariants and boundaries? An empty or generic constraints section means governance isn't being tracked.
- **Decision anchor alignment** — when the system faces an ambiguous design choice, do Decision Anchors resolve it? If the system makes a tradeoff that contradicts an anchor, flag it.

Core question: *does this system build the game described in the design doc, or a different game?*

### Topic 4 — Cross-System Coherence

Does this system interact correctly with other systems?

- **Dependency legitimacy** — does each upstream dependency represent a genuine functional requirement? Could the system work without any of its listed dependencies? Phantom dependencies create unnecessary coupling.
- **Consequence completeness** — does the system acknowledge all the downstream effects its behavior creates? If the Construction system reserves resources and creates jobs, both the Resource system and the Task system should appear in Downstream Consequences.
- **Handoff clarity** — at each system boundary, is it clear who does what? If System A "requests" and System B "resolves," is the boundary described well enough to assign ownership? Note: detailed exchange mechanics belong in interfaces.md and specs, not system docs. System docs must define the boundary and consequence clearly enough to assign responsibility.
- **Information flow clarity** — are the system's inputs explicit? What information does it require from other systems to function? Are the system's outputs explicit? What state changes or signals do other systems rely on? Could another system implement against this one without guessing what information is exchanged?
- **Authority at boundaries** — at each cross-system interaction, who writes state? If both systems might update shared state, flag it. The single-writer rule must hold at every boundary.
- **Orphan detection** — if the system has no dependencies and no consequences, is that intentional or a sign of missing connections? Simulation systems should participate in the system graph. Oversight systems may legitimately stand alone.
- **Dependency cycle interpretation** — if fix-systems detected dependency cycles in the cross-system pass, are they legitimate feedback loops (e.g., needs → behavior → consequences → needs) or signs of design confusion? Legitimate cycles should be documented as intentional feedback loops. Confused cycles should be untangled.

Core question: *if you replaced this system with a perfect black box that exposes the same inputs and outputs, would the rest of the simulation still work?*

### Topic 5 — Simulation Fitness

Does this system earn its existence in the simulation?

- **Purpose justification** — does the system exist because it owns unique simulation state that no other system can own? Or does it exist because someone thought the game "should have" this feature?
- **Player decision impact** — does this system create or enable meaningful player decisions? A system that runs silently in the background without affecting player choices may be unnecessary simulation complexity.
- **Stable-state contribution** — what does this system do when things are going well? If the system only matters during crises or failures, it may be reactive rather than generative. Strong simulation systems create decisions during stability, not just during problems.
- **Granularity check** — is this system the right size? Too broad: a single system owning unrelated concerns (construction + mood + economy). Too narrow: a system that only manages one tiny state with one action. Either suggests restructuring.
- **Category fit** — using the 9 system categories (Actors, World State, Resources & Economy, Tasks & Coordination, Construction & Transformation, Conflict & Consequences, Progression & Meta, Events & Pressure, Player Oversight), which category does this system primarily serve? Does its behavior match that category's expectations?
- **Colony sim fitness** — does this system handle the interruption-heavy, reservation-dependent reality of a colony sim? Does it describe what happens when the happy path breaks (target disappears, resource unavailable, actor dies mid-task), or does it only describe success flows? A system designed only for clean completion paths will fail in a game where interruption is the normal state.
- **Redundancy check** — does this system duplicate functionality available in another system? If two systems both track "colonist availability" or both manage "build priority," one may be redundant.

**Evidence rule:** Every fitness criticism must cite specific evidence from the system doc (purpose, owned state, player actions, dependencies/consequences) or the design doc (core loop, major mechanics, simulation depth). Vague taste-based observations ("this system seems unnecessary") are not acceptable without grounding.

Core question: *if you deleted this system entirely, what player-facing capability would be lost? If the answer is vague, the system may not justify its existence.*

**After all topics complete**, the reviewer must answer final questions and provide a rating:

**For single-system review:**

1. **What is the single biggest ownership problem?** — the boundary most likely to cause implementation confusion. If no problem exists, say so.

2. **Primary rework risk** — what part of this system is most likely to need significant rework during specs or implementation? Why?

3. **Most likely spec pain point** — where will spec writers struggle because the system doc is insufficient or ambiguous?

**For range review:**

1. **What is the single biggest ownership problem across the reviewed systems?** — the boundary most likely to cause implementation confusion or authority conflicts. If no problem exists, say so explicitly.

2. **Which system is weakest?** — the system most likely to need significant rework during specs or implementation. Why?

3. **Are there systems that should merge or split?** — based on ownership overlap, granularity issues, or dependency patterns. If the system set looks correct, say so.

### System Identity Check

Before assigning the final rating, the reviewer must answer these questions for each system. They cut through polished wording and expose systems that exist without a clear reason.

1. **If this system stopped running entirely, what simulation state would become incorrect or frozen?** — this is the most important question. If the answer is vague ("decisions become worse") rather than concrete ("colonist hunger levels freeze, reserved resources stay locked forever"), the system may not own real simulation truth.

2. **What player decision does this system create or shape?** — if a system cannot clearly answer this, it often shouldn't exist independently. Systems that run silently without affecting player choices may be unnecessary complexity or policy layers that belong inside another system.

3. **What other systems must trust this system's state as authoritative?** — a system is only truly authoritative if other systems rely on it. If nothing depends on the system's outputs, it may be a policy layer, not a simulation owner.

4. **Which system is allowed to change this system's core state?** — if the answer is "only this system," ownership is clean. If the answer involves multiple writers, there's an authority conflict. If the answer is unclear, the ownership boundary is soft.

5. **What part of the game experience would feel different if this system were removed?** — the player-facing sanity test. If the answer is vague or requires explaining internal mechanics, the system may not have clear player-facing impact.

If answers to questions 1-3 are vague or overlapping with another system, flag a **system identity weakness** — the system may need to merge, split, or be reframed as a policy within another system.

**Rating (1-5):**
- 1 = fundamentally broken (ownership unclear, behaviors undefined, governance ignored)
- 2 = major issues (significant ownership overlaps, missing behaviors, governance violations)
- 3 = workable but soft (some fuzzy boundaries, incomplete behavior coverage, minor governance gaps)
- 4 = solid design (clear ownership, good behavioral coverage, governance respected)
- 5 = strong design (ownership is unambiguous, behaviors are spec-ready, governance actively shapes the system)

Ratings must be justified by the highest-severity accepted issues. A 4 or 5 requires no major unresolved ownership or governance problems. A 1 or 2 requires major issues in ownership clarity, behavioral completeness, or governance compliance.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SYS-###` or `SYS-###-SYS-###` | Yes | — | Single system or range to review. |
| `--focus` | No | — | Narrow the review within each topic to a specific concern |
| `--iterations` | No | 10 | Maximum outer loop iterations. Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | all | Review only a specific topic (1-5) |
| `--topics` | No | all | Comma-separated topic numbers to review (e.g., `"1,2,5"`). Used by the revision loop when fix-systems signals indicate only certain topics need adversarial review. Topic mapping from signal types: ownership signals → Topics 1,4; governance signals → Topic 3; behavioral gaps → Topic 2; cross-system signals → Topic 4; fitness/granularity signals → Topic 5. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic |
| `--signals` | No | — | Design signals from fix-systems to focus the review on known issues. Format: comma-separated signal descriptions. When provided, the reviewer is instructed to prioritize these signals within the selected topics. |

## Parallelization

For range reviews, Topics 1-3 and 5 (per-system topics) can run in parallel across systems that don't list each other in Upstream Dependencies or Downstream Consequences. Edits to one system's doc during review could conflict with concurrent edits to an interacting system — so interacting pairs must be reviewed sequentially.

Topic 4 (Cross-System Coherence) always runs as a batch after all per-system topics complete, since it evaluates the interaction graph.

**Practical approach:**
1. Build dependency graph from all systems in the range.
2. Systems with no mutual edges → review Topics 1-3, 5 in parallel.
3. Systems with mutual edges → review sequentially within their group.
4. After all per-system reviews complete → run Topic 4 as a batch across the full range.

## Preflight

Before running external review:

1. **Check systems exist.** Glob `design/systems/SYS-###-*.md` for the requested range. If none found, stop.
2. **Check fix-systems has run.** Verify the systems are structurally clean. Template default = section contains only HTML comments, `<!-- SEEDED -->` markers with no authored prose, copied template instructions not replaced, or placeholder text. Critical sections that must have authored content: Purpose, Simulation Responsibility, Player Actions, Owned State. If any critical section is still at template defaults, stop: "Systems are too incomplete for adversarial review. Run `/scaffold-fix-systems` first to normalize structure."
3. **Check design doc exists.** The reviewer needs Design Invariants, Control Model, and Boundaries as context. If the design doc doesn't exist, stop.

## Context Files

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| The system file(s) being reviewed | Primary targets |
| `design/design-doc.md` | Design Invariants, Control Model, Boundaries, Simulation Depth Target — governance context |
| `design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| `design/systems/_index.md` | Full system set context — what other systems exist |
| Other system files that interact with the reviewed system(s) | Cross-system coherence (dependency/consequence targets) |
| `design/authority.md` (if exists) | Ownership verification |
| `design/interfaces.md` (if exists) | Cross-system contract verification |
| `decisions/known-issues.md` | Known constraints |
| ADRs with status `Accepted` that reference these systems | Decision compliance |
| Design signals from fix-systems (if `--signals` provided) | Focus areas for the reviewer |

Only include context files that exist — skip missing ones silently. When reviewing a range, include all systems in the range plus their direct interaction partners.

## Reviewer Bias Pack

Include these detection patterns in the reviewer's system prompt. They represent the most common failure modes in system design docs — the issues that look fine on the surface but cause implementation pain.

1. **Fake ownership clarity** — the Owned State table is filled out but the boundary is functionally soft. Multiple systems shape the same decision through technically non-overlapping but functionally tangled state. "Read-only influence" that is really disguised write authority. Look for systems where 2-3 systems all affect the same player-visible outcome through different state names.

2. **Hidden two-step behavior gaps** — the doc jumps from player input to final outcome, skipping the operational middle that specs will need. Missing: reservation, validation persistence, interruption handling, retries, cancellation cleanup, partial progress rules. These gaps become spec blockers.

3. **Documentation furniture state** — Owned State entries that are vague umbrella terms (`current_status`, `processing_flag`, `active_mode`) rather than crisp simulation truth. These mask missing lifecycle thinking and will not survive spec derivation.

4. **Policies pretending to be systems** — a "system" that is really a rule set, prioritization layer, tuning policy, or modifier framework. These should usually be owned by another system, not exist independently. Check: does it own enough unique state to justify independent existence?

5. **One-way dependency lies** — dependency tables show neat one-directional flow, but the real conceptual dependency is bidirectional. Feedback loops disguised as linear handoffs. "Clean" boundaries that only work because important reverse influence is omitted.

6. **Internal section contradictions** — Purpose says one thing, Player Actions imply another. Owned State doesn't match what Lifecycle describes. Visibility to Player doesn't match Decision Types. These are the highest-value findings — section-by-section consistency is often assumed but rarely verified.

7. **Imaginary supporting infrastructure** — the system only works because an unstated scheduler, resolver, priority arbiter, or state broker must exist. A boundary only makes sense assuming an interface contract not yet defined. "Another system handles that" but no credible owner is named. Flag all phantom dependencies.

8. **False spec-readiness** — the doc is well-written but not precise enough to derive specs from. The ultimate test: **if two engineers independently wrote specs from this system doc, would they write the same specs?** If not, the doc needs more precision regardless of how polished it reads.

## Execution

### Single-System Review

For a single system (e.g., `SYS-005`), follow the same topic loop, inner loop (exchanges), consensus, and apply-changes pattern as `/scaffold-iterate-design`. Run Topics 1-5 sequentially for that system.

### Range Review

For a range (e.g., `SYS-001-SYS-043`), **every system in the range must be reviewed**. The range is not a suggestion — it is a work list. Skipping systems is not acceptable.

**Step 1 — Build the work list.**
1. Glob all system files matching the range: `design/systems/SYS-*.md` where the ID falls within the specified range.
2. Sort by ID number.
3. Log the full work list: "Reviewing N systems: SYS-001, SYS-002, ..., SYS-043"
4. If any IDs in the range have no matching file, note them as missing and continue with the rest.

**Step 2 — Per-system review (Topics 1-3, 5).**
For EACH system in the work list, sequentially:
1. Load the system file and its context files (interaction partners, design doc, glossary, authority, interfaces).
2. Run Topics 1, 2, 3, and 5 — each with its own back-and-forth exchange loop.
3. Adjudicate and apply changes.
4. Log progress: "Completed SYS-### (N of M) — Rating: X/5, Issues: Y accepted, Z rejected"
5. Move to the next system. **Do not stop after one system.**

Systems with no mutual dependency edges (per the Parallelization section) may be reviewed in parallel where the Python infrastructure supports it. Systems that list each other in Upstream Dependencies or Downstream Consequences must be reviewed sequentially.

**Step 3 — Cross-system batch review (Topic 4).**
After ALL per-system reviews in Step 2 are complete:
1. Run Topic 4 (Cross-System Coherence) as a single batch across the full range.
2. This evaluates the interaction graph — dependency symmetry, authority conflicts, handoff clarity, orphan detection, dependency cycles.
3. Topic 4 findings may reference any system in the range.

**Step 4 — Convergence check.**
After the full pass (Steps 2-3), check convergence:
- If no new issues were found across the entire range → stop.
- If new issues exist → run another iteration, but only on systems that had accepted changes or unresolved escalations.
- Maximum `--iterations` outer loops across the full range.

**Stop conditions** (any one stops iteration):
- **Clean** — a complete pass across all systems produces no new issues.
- **Converged** — two consecutive passes produce the same issue set with no new findings.
- **Human-only** — only issues requiring user decisions remain; further iteration won't resolve them.
- **Limit** — `--iterations` maximum reached.

**Critical rule for ranges:** The skill MUST process every system in the work list before stopping. Reviewing one system and stopping is a skill failure, not convergence. Convergence is checked after a complete pass through the entire range, not after a single system.

### Issue Adjudication

Every issue raised by the reviewer must be classified into exactly one outcome:

| Outcome | Action |
|---------|--------|
| **Accept and fix** | Issue is valid. Apply the fix to the system doc. |
| **Reject with reasoning** | Issue is incorrect, out of scope, implementation-level, or contradicted by a higher-authority doc. |
| **Escalate to user** | Requires design judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag ambiguous design authority** | Design doc or higher-ranked doc permits multiple valid interpretations and the system design chose one. Not incorrect — genuinely ambiguous upstream. Flag for user decision to lock the interpretation. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- Prefer fixing system docs over escalating — most issues are system-level clarity.
- Never "half-accept" — choose exactly one outcome per issue.
- If the issue depends on a missing or ambiguous design-doc decision → escalate or flag ambiguous, not system fix.
- If the issue is system-specific clarity or behavioral precision → accept and fix.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of a design-doc decision or authority boundary exist and the system design chose a reasonable one → flag ambiguous design authority for user decision. Do not treat ambiguity as a defect or force a single reading at system level.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue. Examples:
- "ownership boundary unclear" and "system writes to another system's state" → same issue if they stem from the same authority conflict.
- "behavior incomplete" and "missing edge case handling" → same issue if about the same behavior gap.

**Lock enforcement:**
- The reviewer must NOT reintroduce a resolved issue in a different form.
- The reviewer must NOT raise stricter variants of a resolved issue unless: (a) new evidence exists that wasn't available when the issue was resolved, OR (b) the fix itself introduced a new problem.
- If a previously resolved issue reappears: classify it as a **review inconsistency**, not a new issue. Prefer rejecting the reappearance unless the reviewer provides materially different evidence.

**Cross-topic lock:** If Topic 1 resolves an issue, later topics may not re-raise it under a different name. The cross-topic consistency check catches this retroactively, but the lock prevents wasted exchanges proactively.

**Tracking:** Maintain a running resolved-issues list in the review log during execution. Before engaging with any new reviewer claim, check it against the resolved list by root cause. If it matches, reject with "previously resolved — see [iteration N, topic M]."

### Scope Collapse Guard

Before accepting any change to a system design, enforce these three tests to prevent system-layer expansion into design or architecture territory:

**1. Upward Leakage Test:**
Does this change introduce or modify game-level design decisions that belong in the design doc?
- If YES → reject or flag for revise-design. System designs implement the design doc's vision for a specific domain; they don't redefine the game.
- System designs may: define player-visible behavior, system-specific rules, state descriptions, and behavioral invariants.
- System designs must NOT: change core game vision, alter player experience goals, or redefine features owned by the design doc.

**2. Downward Leakage Test:**
Does this change introduce architectural, interface, or implementation detail that belongs in Step 3 (architecture, authority, interfaces) or Step 4 (engine docs)?
- If YES → reject. System designs describe behavior, not structure.
- System designs must NOT: specify signals, methods, node names, class hierarchies, data structures, or communication patterns. Those belong in architecture.md, interfaces.md, or engine docs.
- Test: does this read like "the player sees X happen" (correct) or "SystemA calls method Y on SystemB" (wrong layer)?

**3. "Would This Survive Architecture Change?" Test:**
If the architecture changed how systems communicate tomorrow, would this system design still be valid?
- If NO → the system design is encoding an architecture assumption, not a behavioral description. Reject or rewrite as behavior.
- If YES → safe behavioral description. Accept.

These tests apply to both reviewer-proposed changes AND existing system design content flagged during review.

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-systems-SYS-###[-SYS-###]-<YYYY-MM-DD>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

For a single system:
```
## System Review Complete: SYS-### — [Name]

### Biggest Ownership Problem
[Boundary most likely to cause confusion, or "None detected."]

### Primary Rework Risk
[Part of this system most likely to need significant rework during specs or implementation.]

### Most Likely Spec Pain Point
[Where spec writers will struggle because the system doc is insufficient or ambiguous.]

### System Identity
[Answers to the 5 identity check questions — summarized in 2-3 sentences.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Ownership Correctness | N | N | N |
| 2. Behavioral Completeness | N | N | N |
| 3. Design Governance Compliance | N | N | N |
| 4. Cross-System Coherence | N | N | N |
| 5. Simulation Fitness | N | N | N |

**System Design Strength Rating:** N/5 — [one-line reason]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/ITERATE-systems-SYS-###-YYYY-MM-DD.md
```

For a range:
```
## System Review Complete: SYS-###–SYS-###

### Biggest Ownership Problem
[The boundary most likely to cause implementation confusion across the system set.]

### Weakest System
[System most likely to need rework, and why.]

### Merge/Split Recommendations
[Systems that should merge or split based on review findings, or "System boundaries look correct."]

### Per-System Summary

| System | Rating | Key Issue |
|--------|--------|-----------|
| SYS-### — Construction | 4/5 | Minor: failure paths incomplete |
| SYS-### — Colony Needs | 3/5 | Ownership overlap with SYS-### on mood state |
| ... | ... | ... |

### Cross-System Coherence (Topic 4 batch results)
| Issue | Systems | Detail |
|-------|---------|--------|
| Dependency asymmetry | SYS-###, SYS-### | A→B exists, B→A undocumented |
| Authority conflict | SYS-###, SYS-### | Both claim write access to mood |
| ... | ... | ... |

**Overall System Design Strength Rating:** N/5 — [one-line assessment of the full system set]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/ITERATE-systems-SYS-###-SYS-###-YYYY-MM-DD.md
```

## Rules

- **Project documents and authority order win.** Claude adjudicates conflicts using document authority — higher-ranked documents decide disputes.
- **Systems describe BEHAVIOR, not IMPLEMENTATION.** If the reviewer suggests implementation details, signal contracts, engine patterns, or code structures, reject and redirect to design-level alternatives.
- **Only edit system files in the reviewed range.** Never edit design doc, authority.md, interfaces.md, glossary, or other upstream documents during review.
- **Edits are limited to clarification and restructuring.** Auto-edits may only: reword existing content for clarity (preserving the same meaning), restructure existing content for readability, replace vague wording with more explicit wording when the intent is already directly supported elsewhere in the same doc. Auto-edits must NOT: add new Player Actions, lifecycle phases, failure states, or Owned State entries; narrow or broaden ownership scope; resolve ambiguous boundaries; add new downstream consequences. All of those require user confirmation.
- **Do not invent missing behavior to solve a review issue.** If the system appears weak because behavior is missing, flag the gap. Do not silently add content.
- **Ownership changes are always escalated.** Moving state between systems, changing authority claims, or merging/splitting systems requires user confirmation.
- **Respect the formatter/reviewer boundary.** fix-systems handles mechanical issues. This skill handles design quality. If the reviewer raises a formatting issue, note it but don't prioritize it — fix-systems should have caught it.
- **Design signals from fix-systems are prioritized.** When `--signals` are provided, the reviewer should examine those areas first before moving to general topic review.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Pushback is expected and healthy.**
- **Reappearing material issues escalate to the user.** Escalate when the same material issue persists for 2 outer iterations, or when the reviewer and Claude remain split after max-exchanges on a topic. Present escalated issues using the Human Decision Presentation pattern (see WORKFLOW.md) — numbered, with concrete options (a/b/c).
- **Cross-topic soft weaknesses escalate.** If the same issue (e.g., vague ownership) materially degrades 2 or more topics, escalate it even if it's not a direct conflict. A material issue is one that affects ownership boundary, spec-writability, governance compliance, cross-system authority clarity, or system necessity/granularity.
- **Deduplicate cross-topic findings.** When the same root issue affects multiple topics, record it once as a primary finding and reference it in later topics — don't restate it as a new issue each time.
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Ambiguous upstream design is not a system defect.** When the design doc or higher-ranked docs genuinely permit multiple valid interpretations of ownership, behavior, or boundaries and the system design chose a reasonable one, do not treat the system design as incorrect. Flag for user decision to lock the interpretation upstream. The reviewer's preferred reading is not automatically correct — design ambiguity often means the design doc needs tightening, not the system.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the system design harder to implement? (b) does this improve behavioral clarity, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving implementability, optimize for review criteria over practical development guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing system designs that are hyper-consistent but less practical, readable, or flexible. The goal is system designs a developer can implement from, not ones that score perfectly on an internal consistency audit.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "ownership boundary unclear" and "writes to wrong system's state" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Upward leakage — does this introduce game-level design decisions belonging in the design doc? If yes, reject or flag for revise-design. (2) Downward leakage — does this introduce architecture, interface, or implementation detail belonging in Steps 3-4? System designs describe behavior, not structure — no signals, methods, or class names. (3) "Would this survive architecture change?" — if the architecture changed tomorrow, would this system design still hold? If no, it's encoding architecture, not behavior.

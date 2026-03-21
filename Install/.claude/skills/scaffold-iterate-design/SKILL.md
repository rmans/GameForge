---
name: scaffold-iterate-design
description: Adversarial per-topic design doc review using an external LLM. Reviews the design document across 6 topics — 5 structural (vision coherence, player experience model, world & presentation integrity, governance mechanism quality, scope & content realism) plus 1 design interrogation (design stress test — tries to break the game design itself). Use for deep design review beyond what fix-design catches.
argument-hint: [--focus "concern"] [--iterations N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Design Review

Run an adversarial per-topic review of the design document using an external LLM reviewer: **$ARGUMENTS**

This skill reviews `design/design-doc.md` across 5 sequential topics, each with its own back-and-forth conversation. It uses the same Python infrastructure as iterate-roadmap/iterate-references/iterate-phase but with design-doc-optimized topics.

The design doc is the highest authority for player-facing intent and non-breakable design rules. This review operates in two modes:

**Mode 1 — Structural Review (Topics 1-5):** Evaluates whether the document is internally consistent, well-governed, and honestly scoped. Catches contradictions, drift, and governance gaps. The question: *will this document keep the project building the same game six months from now?*

**Mode 2 — Design Interrogation (Topic 6):** Tries to break the game design itself. Not "is this document well-formed?" but "will this game actually work?" Targets gameplay quality, player frustration, dominant strategies, engagement gaps, and emotional failure modes. The question: *where does this design fail in practice even if the document is perfect?*

Both modes run every pass. Topics 1-5 validate the document. Topic 6 attacks the design.

## Topics

| # | Topic | Mode | What It Evaluates |
|---|-------|------|-------------------|
| 1 | Vision Coherence & Identity Clarity | Structural | Does the design doc describe one game or several conflicting ones? |
| 2 | Player Experience Model | Structural | Do the loops, control model, and decision architecture produce the intended experience? |
| 3 | World & Presentation Integrity | Structural | Does the world, tone, camera, and information model support the core fantasy? |
| 4 | Governance Mechanism Quality | Structural | Are invariants testable, anchors actionable, pressure tests realistic, gravity directions clear? |
| 5 | Scope & Content Realism | Structural | Does the design doc describe a game with honest scope and believable player-facing complexity? |
| 6 | Design Stress Test | Interrogation | Where does this design break, bore, frustrate, or fail under real player behavior? |

### Topic 1 — Vision Coherence & Identity Clarity

Does the design doc describe one game, or several conflicting ones?

- **Core Fantasy alignment** — does every section reinforce the same player fantasy? If Core Fantasy says "manage a colony through indirect AI control" but Player Verbs lists direct unit commands, the vision is split.
- **Player role stability** — does the player's role stay consistent across all sections? Identity sections, control sections, loop sections, and world sections must all describe the same player. If Identity says "distant overseer" but systems imply "tactical commander", the role is drifting.
- **Pillar coverage** — does each Core Pillar appear in at least one concrete section (a loop, a mechanic, a system domain)? Pillars that exist only as aspirations are decorative, not structural.
- **Invariant-pillar consistency** — do Design Invariants protect the Core Pillars? If a pillar claims "emergent storytelling" but no invariant prevents scripted narrative override, the pillar is undefended.
- **Tension integrity** — does the Core Design Tension actually produce hard choices? A tension where one side always wins isn't a tension — it's a default. Check whether the loops, decisions, and failure philosophy force the player to navigate the tension. Can the player realistically choose either side? Do mechanics push both directions?
- **Elevator Pitch fidelity** — does the Elevator Pitch accurately summarize the game described in the rest of the document? Pitch drift is common when sections evolve independently.
- **USP traceability** — are the Unique Selling Points traceable to specific mechanics or invariants in the doc? USPs that describe genre conventions ("base building", "survival mechanics") are not differentiators. Lower priority than identity coherence — flag but don't dwell.
- **Shadow identity detection** — does the document describe two different games depending on which sections you read? Common pattern: Identity sections describe game A, Shape sections describe game B, neither realizes the mismatch.
- **Optimization resistance** — if the player optimizes purely for efficiency, does the resulting play still resemble the intended experience? If optimal play bypasses the fantasy entirely, the design relies on voluntary role-play instead of mechanical reinforcement. Strong designs make optimal play and the intended fantasy converge — the best strategy should feel like the core experience, not a shortcut around it.

Core question: *if five different developers each read only one section group, would they all build the same game?*

### Topic 2 — Player Experience Model

Do the loops, control model, and decision architecture produce the intended experience?

- **Core Loop completeness** — does the Core Loop describe a full cycle (input → action → feedback → new state → new decision)? Loops that end at "feedback" are missing the re-engagement hook.
- **Loop-control alignment** — does the Core Loop match the Player Control Model? If control is indirect but the loop describes direct actions, one of them is wrong.
- **Decision architecture** — do Decision Types match the loops? If the core loop produces tactical decisions but Decision Types claims strategic depth, where do strategic decisions actually emerge?
- **Decision density calibration** — does the described decision cadence match the session shape? A 30-minute session with only 2 meaningful decisions is a watching game, not a management game. Is the claimed density plausible given the loop structure?
- **Goal ladder coherence** — do short-term, mid-term, and long-term Player Goals build on each other? Short-term goals should feed mid-term progress; mid-term goals should create long-term trajectory. Disconnected goals produce grind.
- **Feedback loop coverage** — does every player action have a described feedback path? Actions without feedback are invisible to the player. Are positive and negative feedback loops balanced?
- **Mental model match** — does the Player Mental Model align with what's actually described in the loops and systems? If the mental model says "manage a living colony" but the loops describe clicking buttons on timers, the player will feel deceived.
- **Secondary loop integration** — do Secondary Loops wrap around the Core Loop, or are they parallel tracks? Parallel secondary loops create scope without depth. Good secondary loops recontextualize core loop decisions. Loops that don't feed the core loop, don't change core decisions, and just add content surface area are scope traps.
- **Progression arc validation** — does the Progression Arc describe genuine capability growth, or just number inflation? "Unlock new building types" is capability growth. "Buildings get +10% efficiency" is number inflation dressed as progression.
- **Accidental experience check** — based on the loops, controls, decisions, and feedback described, what will the player *actually* do moment-to-moment? Does that match the Core Fantasy, or does the fantasy describe one experience while the mechanics produce another?
- **Stable-state engagement** — what does the player do when things are going well? If the answer is "wait for the next disruption", the design depends on crises for engagement and the core loop is weak between emergencies. Strong designs generate new decisions during stability — planning, expansion, tradeoffs, future investment. If stability produces no meaningful decisions, the design depends on disruption for engagement. If the "good state" is passive (watch timers, check panels, wait for resources), the game is only interesting when it's breaking.

- **Failure-state engagement** — when things go badly, does the player get meaningful decisions, or just punishment and cleanup? Good designs give the player agency during failure — triage, recovery choices, sacrifice decisions. If crises produce only damage reports and repair queues, failure is noise, not gameplay.

Core question: *does a player following these loops actually experience the Core Fantasy, or just perform adjacent actions?*

### Topic 3 — World & Presentation Integrity

Does the world, tone, camera, and information model support the core fantasy?

- **Tone-fantasy alignment** — does the Tone match the Core Fantasy? A grim tone with a whimsical core fantasy creates dissonance. A lighthearted tone with life-or-death stakes undermines tension.
- **Camera-control coherence** — does the Camera perspective match the Player Control Model? Top-down suits oversight/management. Close third-person suits direct control. Mismatch between camera and control creates disconnect.
- **Information model-transparency alignment** — does the Player Information Model match the Simulation Transparency Policy? If transparency promises "players understand consequences" but the information model hides critical state, the policies contradict.
- **Information clarity-decision alignment** — does the Information Clarity Principle actually enable the Decision Types described? If decisions require strategic planning but information is hidden, the player can't plan — they can only react. Does the player have the information required for the decisions the game asks them to make?
- **Narrative wrapper load-bearing check** — does the Narrative Wrapper carry gameplay weight, or is it only flavor? If factions exist in the narrative but have no mechanical expression, they're decoration. If the narrative explains why the player has limited control, it's load-bearing.
- **Faction mechanical expression** — do Factions/Forces have mechanical impact described elsewhere in the doc (loops, systems, decisions)? Factions without mechanics are worldbuilding without gameplay.
- **Aesthetic-tone consistency** — do Aesthetic Pillars reinforce the Tone? Visual identity should amplify the emotional register, not contradict it.
- **Audio-world alignment** — does the Audio Direction support the Place & Time? Audio that doesn't match the setting breaks immersion.
- **Information framing clarity** — does the UI/visualization implied by the design make important game state understandable? If critical state exists but the design provides no way for the player to perceive it clearly, decisions become guesswork. State that exists but cannot be understood is functionally hidden.

Core question: *does the world make the player believe in the game, or does it fight against the mechanics?*

### Topic 4 — Governance Mechanism Quality

Are the governance mechanisms well-formed, internally consistent, and actually useful for downstream decisions?

- **Invariant testability** — can each Design Invariant be tested with a binary yes/no? Invariants that use words like "generally", "mostly", "when appropriate" are untestable. An untestable invariant is a suggestion, not a rule.
- **Invariant coverage** — do the invariants protect the core design? Check each Core Pillar and the Core Design Tension — is there at least one invariant guarding each? Unprotected pillars will erode during implementation.
- **Invariant conflict detection** — do any two invariants contradict each other in a realistic scenario? If Invariant A says "no direct control" and Invariant B says "player must be able to respond instantly to threats", there's a hidden conflict.
- **Anchor actionability** — does each Decision Anchor resolve a real ambiguity? Test: can you construct a plausible design question where the anchor determines the answer? Anchors that state obvious preferences ("fun over boring") are wasted slots.
- **Anchor conflict detection** — do any two Decision Anchors contradict in a realistic scenario? With 3-5 anchors, pairwise conflicts are testable. Surface any tension between anchors.
- **Pressure test realism** — is each Pressure Test scenario plausible? Tests against impossible conditions ("what if 10 million entities spawn") don't validate the design. Tests should stress the design at realistic extremes.
- **Pressure test coverage** — do Pressure Tests stress the Core Design Tension? The tension is where the design is most likely to break. If no test targets the tension, the most vulnerable point is unexamined.
- **Pressure test-invariant alignment** — would violating any invariant cause a pressure test to fail? If not, either the invariants don't protect enough, or the tests don't stress enough.
- **Gravity-pillar distinction** — does Design Gravity describe evolution directions distinct from Core Pillars? Gravity that restates pillars is redundant. Pillars = what the game IS. Gravity = where it DEEPENS.
- **Gravity feasibility** — are the Design Gravity directions achievable given the systems, mechanics, and content structure described in the doc? Gravity pointing toward systems or content not described anywhere is aspirational, not actionable.
- **Boundary specificity** — do Design Boundaries name specific things the game is NOT, or just generic disclaimers? "Not a first-person shooter" is obvious. "Not a game where the player directly commands colonists" is specific and useful.
- **Governance survivability** — if a downstream author is tired, rushed, or optimizing locally, which governance mechanisms will still hold and which will be ignored because they are too vague, too abstract, or too disconnected from actual decisions? Mechanisms that survive real workflow pressure are strong. Mechanisms that only work when everyone is paying full attention are fragile.
- **Governance mechanism count** — are governance mechanisms within their target ranges? Invariants: 3-7. Anchors: 3-5. Pressure Tests: 3-6. Gravity: 3-4. Too few = underspecified. Too many = decision paralysis.

Core question: *if a downstream developer faces an ambiguous design choice, do these mechanisms actually resolve it?*

### Topic 5 — Scope & Content Realism

Does the design doc describe a game with honest scope and believable player-facing complexity?

This topic evaluates the design doc's own scope claims at the design level — not architecture feasibility, system decomposition, or engine constraints (those belong in Steps 3, 6, and 7).

- **Content structure-replayability alignment** — does the Content Structure support the Replayability Model? If replayability claims procedural variation but content is mostly authored, the replay model is aspirational.
- **Procedural-authored boundary clarity** — is the boundary between procedural and authored content explicit? Fuzzy boundaries create scope creep when "just a bit more procedural generation" keeps expanding.
- **Scope Reality Check honesty** — does the Scope Reality Check accurately reflect the document's ambition? If the design describes 15 interconnected systems with deep simulation and procedural generation, a scope check that says "achievable for a solo developer" is dishonest.
- **MVP contains the core loop** — is the minimum viable product described, and does it include the Core Loop? An MVP that defers core gameplay validates nothing.
- **Learning curve-complexity alignment** — does the Learning Curve Strategy match the actual complexity described in the loops, decisions, and systems? Simple strategies for complex systems will frustrate players. Elaborate strategies for simple systems waste development time.
- **Platform-control consistency** — do Target Platforms impose high-level constraints the design doesn't acknowledge? Console targets need controller navigation. Mobile targets need simpler interaction. Do any platforms conflict with the described Player Control Model?
- **Simulation depth honesty** — does the Simulation Depth Target match the scope commitment? Deep simulation of many domains is expensive. Does the doc acknowledge the depth-vs-breadth tradeoff, or does it claim both?
- **Feature gravity detection** — identify design features that appear small in the document but are structurally central and likely to expand (e.g., factions, procedural generation, generational simulation). Flag when the design doc treats them as minor additions instead of core systems.
- **Accessibility-design alignment** — do Accessibility Goals conflict with core mechanics? If the game requires fast reaction but accessibility commits to "no time pressure", there's a conflict.
- **Scope concentration** — is the design's complexity concentrated in a few load-bearing areas, or scattered across too many medium-sized ambitions? A design can fail scope realism even without any single insane feature, when complexity is distributed everywhere and nothing is simple.
- **Genre-fit pressure** — does this design describe a game where interruption, stale targets, multi-system causality, and continuous world churn are normal? Or does it implicitly assume clean execution paths and rare state changes? A colony sim design that doesn't explicitly acknowledge interruption-heavy workflows is designing for a different genre.

Core question: *does this design doc describe a game whose complexity matches what it claims, or does it promise more than its structure can support?*

**After all topics complete**, the reviewer must complete two synthesis checks, answer final questions, and provide a rating:

### Design Identity Check

1. **If all downstream docs were lost, what game would this design doc cause the team to rebuild?** — the answer should be immediately clear. If it's ambiguous, the doc isn't governing strongly enough.
2. **What is the player actually spending most of their time doing, based on this document?** — not what the Core Fantasy claims, but what the loops, decisions, and mechanics actually demand.
3. **What part of the game is mechanically load-bearing vs aspirational flavor?** — which design promises are protected by governance and mechanics, and which are just descriptive language?
4. **What design promise is most at risk of erosion during implementation?** — the commitment most likely to be quietly dropped when it becomes hard to build.
5. **What would a new team member most likely misunderstand after reading this doc once?** — if the answer is easy to identify, the doc has a clarity gap there.

### Design Choice Examination

1. **What major design choices define this game?** — identify the structural choices (e.g., indirect control, systemic simulation, emergent storytelling, specific camera model).
2. **What problem or experience goal does each choice solve?** — why was this approach chosen over alternatives?
3. **What tradeoff does each choice impose?** — every structural choice closes off other possibilities. Are those tradeoffs acknowledged?
4. **Is any major choice unsupported by mechanics or governance?** — the document claims the choice, but the rest of the design doesn't enforce it.
5. **Which design choice most constrains the game's future evolution, and is that constraint intentional?** — deep commitments (indirect control, procedural worlds, generational progression) shape everything downstream. If the doc doesn't acknowledge them, the design may not understand its own constraints.

### Final Questions

1. **What is the single biggest internal contradiction in this design?** — the place where the document most fights against itself. If no contradiction exists, say so explicitly.

2. **What player experience does this design accidentally create?** — based on the loops, controls, decisions, and feedback described, what will the player *actually* experience vs. what the Core Fantasy *claims* they'll experience? Agreement = strong design. Divergence = design drift.

3. **Which governance mechanism is weakest?** — identify the invariant, anchor, pressure test, or gravity statement most likely to fail in practice, and why.

4. **What part of this design is most likely to be misbuilt even if the team follows the document in good faith?** — catches "clear to the author, fuzzy to everyone else" areas.

5. **Design Strength Rating (1-5):**
   - 1 = fundamentally incoherent (vision split, loops don't produce the fantasy, governance absent)
   - 2 = major issues (significant internal contradictions, weak governance, scope disconnected from reality)
   - 3 = workable but soft (some misalignment between sections, governance mechanisms present but undertested)
   - 4 = solid design (internally consistent, governance works, minor soft spots)
   - 5 = strong design (sections reinforce the same vision, governance resolves real ambiguities, scope claims are honest)

### Topic 6 — Design Stress Test

**Mode: Design Interrogation.** The reviewer shifts from document auditor to game design attacker. The goal is to find where the design breaks, bores, or frustrates under real player behavior — even if the document is perfectly consistent.

**Reviewer instruction:** "You are NOT checking documentation. You are trying to break the game design. Think as a player, a critic, and a rival designer simultaneously. Every issue must describe a concrete gameplay scenario, not a document structure concern."

- **Control model stress** — Construct a specific scenario where the player desperately wants direct control but cannot have it. Does the design provide enough indirect tools to make the player feel satisfied rather than helpless? What is the emotional recovery path? If the design cannot answer "the player still feels agency here," the control model has a hole.
- **Stable-state boredom test** — What does the player do for 10 uninterrupted minutes when nothing is going wrong? No crises, no alerts, no cascades. List the moment-to-moment decisions available. If the answer is "wait for something to break," the design depends on disruption for engagement and the core loop is weak between emergencies. Colony sims live or die on this question.
- **Consequence tracing apathy** — The design promises traceable cause chains. What happens when the player doesn't care enough to trace? Most players won't dig into logs unless forced or rewarded. If traceability is intellectually strong but emotionally weak — if the player can ignore the logs and still play effectively — is the traceability a player experience or a developer safety net?
- **Irreversibility tipping point** — Permanent scars, permanent deaths, irreversible power progression. At what point does the player feel locked out instead of invested? Identify the specific decision or accumulation threshold where irreversibility shifts from "meaningful weight" to "I should restart." If the design cannot describe that boundary, it doesn't know where its own punishment system breaks.
- **Cognitive load ceiling** — The design claims high transparency and high data density. At what point does transparency become overload? More data does not equal more clarity. Describe the late-game information state: how many simultaneous systems must the player monitor, how many overlays, how many trends? Is this playable, or is it a full-time job?
- **Dominant strategy search** — What is the most efficient strategy a min-maxer would find? Does it invalidate other systems? Does it bypass the core tension? If an optimizing player can avoid the instability loop entirely, or reduce it to a solved formula, the design's central conflict is decorative.
- **Corporate loop dominance test** — Can the player ignore the corporate funding loop and still succeed? If yes, it's optional flavor. If no, it dominates the game and every other system is subordinate to evaluation optimization. Where does this loop actually sit in the priority hierarchy during play?
- **Emotional failure mode** — When does the game stop being "tense and engaging" and become "exhausting and demoralizing"? Describe the specific colony state where the player's emotional experience crosses from the intended "dread + mastery" into "I don't want to play anymore." What recovery mechanism prevents this?
- **Fantasy-mechanics convergence** — Based purely on the mechanics described (not the flavor text), what does the player actually spend 80% of their time doing? Does that activity match the Core Fantasy, or does the fantasy describe one experience while the mechanics produce another? If the answer is "reading panels and adjusting numbers" but the fantasy says "custodial dread," is there enough dread in the panel-reading to carry the fantasy?
- **New player cliff** — The design says "familiar problems, unfamiliar tools." At what exact moment does the unfamiliar tool set stop feeling like a fresh challenge and start feeling like a missing feature? When does "I can't click on colonists" go from "oh interesting" to "why can't I just tell them what to do"? What keeps the player past that moment?

Core question: *would you actually play this game for 20 hours, and if you'd stop before that, why?*

**Topic 6 adjudication rules:**
- Issues from Topic 6 are gameplay concerns, not document defects. They should be classified as:
  - **Design risk** — a real concern the design should acknowledge (add to known issues or pressure tests)
  - **Already mitigated** — the design addresses this but the reviewer missed it (cite the specific section)
  - **Escalate to user** — a genuine design question only the designer can answer
- Topic 6 issues do NOT result in design doc edits unless the user explicitly accepts a design change. They result in awareness, known issues, or new pressure tests.
- Do not reject Topic 6 issues for being "not a document problem." That's the point — they're design problems.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--focus` | No | -- | Narrow the review within each topic to a specific concern |
| `--iterations` | No | 10 | Maximum outer loop iterations (full 6-topic cycles). Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | all | Review only a specific topic (1-6) |
| `--sections` | No | all | Comma-separated section groups that changed (e.g., `"Identity,Shape"`). Automatically selects only the topics relevant to those sections instead of running all 6. Used by the revision loop to scope iterate to just the changed areas. Section-to-topic mapping: Identity → Topics 1,4,6; Shape → Topics 1,2,6; Control → Topics 2,3,6; World → Topic 3; Presentation → Topic 3; Content → Topic 5; System Domains → Topics 2,5; Philosophy → Topics 4,5; Scope → Topic 5. Topic 6 runs whenever any gameplay-affecting section changes. Deduplicates — if multiple sections map to the same topic, it runs once. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic |

## Preflight

Before running external review:

1. **Check design doc exists.** If `design/design-doc.md` doesn't exist or is at template defaults, stop: "No design doc to review. Run `/scaffold-init-design` first."
2. **Check design health.** The design doc must have at least 50% of sections with non-placeholder content. If below 50%, stop: "Design doc is too incomplete for adversarial review. Run `/scaffold-init-design --mode fill-gaps` to fill remaining sections, then `/scaffold-fix-design` to clean up mechanical issues."
3. **Check governance readiness.** Verify Design Invariants and Decision Anchors sections exist. If governance sections are empty or at template defaults:
   - **Do not hard-stop.** Continue the review, but skip Topic 4 (Governance Mechanism Quality).
   - Report in the output: "Topic 4 skipped — governance sections are empty. Run `/scaffold-init-design --mode fill-gaps --sections Philosophy` to populate governance mechanisms."
   - Topics 1-3 and 5 can still surface valuable issues without governance being complete.

## Context Files

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| `design/design-doc.md` | The primary target — this IS the document being reviewed |
| `design/glossary.md` | Canonical terminology — reviewer should use correct terms |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| `design/systems/_index.md` | Context for system-domain assumptions referenced in the design doc |
| `decisions/known-issues.md` | Known constraints the design must accommodate |
| ADRs with status `Accepted` | Decisions that may have changed design assumptions |
| Theory docs relevant to the game's genre (if identifiable) | Advisory context for the reviewer — clearly labeled as non-authoritative |

Only include context files that exist — skip missing ones silently. Theory docs are advisory — instruct the reviewer that theory observations are secondary to internal consistency checks.

## Execution

Follow the same topic loop, inner loop (exchanges), consensus, and apply-changes pattern as `/scaffold-iterate-roadmap`. The iteration mechanics, stop conditions, and review log creation are identical.

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
- "vision statement too vague" and "core fantasy unclear" → same issue if they stem from the same section's lack of specificity.
- "player motivation loop missing" and "no engagement driver defined" → same issue.

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
| **Accept → edit design doc** | Apply change immediately. The issue is valid and the fix is within design-doc scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or the issue is out of scope. |
| **Escalate to user** | Requires design judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag ambiguous design intent** | Design doc permits multiple valid interpretations and the reviewer favors one. Not incorrect — genuinely ambiguous. Escalate to user for design decision rather than forcing one reading. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- Prefer fixing the design doc over escalating — most issues are clarity or consistency.
- Never "half-accept" — choose exactly one outcome per issue.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of a design intent exist → flag ambiguous design intent for user decision. Do not treat ambiguity as a defect or force a single reading at review level.

### Scope Collapse Guard

Before accepting any change to the design doc, enforce these three tests to prevent design-layer expansion into implementation-layer responsibility:

**1. Layer Test:**
Does this change introduce implementation detail that belongs in system designs, architecture, or engine docs?
- If YES → reject. The design doc defines what the game is and how it feels, not how systems work internally.
- Design doc may: define player-visible behavior, game feel, creative direction, invariants, and constraints.
- Design doc must NOT: specify system internals, architectural patterns, data structures, signal flows, or engine mechanics. Those belong in Steps 2-4.

**2. Abstraction Level Test:**
Is this change written at the right level of abstraction for a design doc?
- Design doc language: "colonists become unhappy when hungry" (player-visible behavior).
- System design language: "NeedsSystem decrements mood when hunger exceeds threshold" (system internals).
- If the change reads like a system design or architecture decision → reject or rewrite at design-doc abstraction level.

**3. "Would This Constrain Implementation?" Test:**
Does this change lock implementation options that should remain open?
- If the change would force a specific system decomposition, data model, or architectural pattern → it's implementation leakage. Reject or rewrite as a constraint/invariant rather than a prescription.
- If the change expresses intent without prescribing implementation → safe design decision. Accept.

These tests apply to both reviewer-proposed changes AND existing design doc content flagged during review.

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-design-<YYYY-MM-DD>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

```
## Design Review Complete

### Biggest Internal Contradiction
[Where the document most fights against itself, or "None detected."]

### Accidental Player Experience
[What the player will actually experience vs. what Core Fantasy claims.]

### Weakest Governance Mechanism
[Which invariant/anchor/test/gravity is most likely to fail in practice, and why. Or "Topic 4 skipped — governance not yet populated."]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Vision Coherence & Identity Clarity | N | N | N |
| 2. Player Experience Model | N | N | N |
| 3. World & Presentation Integrity | N | N | N |
| 4. Governance Mechanism Quality | N (or "skipped") | N | N |
| 5. Scope & Content Realism | N | N | N |
| 6. Design Stress Test | N | N | N |

**Design Strength Rating:** N/5 — [one-line reason]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/ITERATE-design-YYYY-MM-DD.md
```

## Rules

- **Project documents and authority order win.** Claude adjudicates conflicts using document authority — higher-ranked documents decide disputes, not Claude's preference.
- **The design doc describes WHAT the game is, not HOW to build it.** If the reviewer suggests implementation details, system ownership, signal contracts, or engine patterns, reject and redirect to design-level alternatives.
- **Only edit the design doc.** Never edit system designs, reference docs, glossary, engine docs, or ADRs during review.
- **Edits may clarify or tighten wording but must not change what the game is.** The adversarial loop may sharpen language, surface contradictions, strengthen governance mechanisms, and flag gaps — but changing the Core Fantasy, adding new mechanics, or removing design commitments requires user confirmation.
- **Do not invent missing mechanics to solve a review issue.** If the design appears weak because a mechanic, loop, or governance rule is missing, flag the gap. Do not silently add new design content unless it is a wording clarification of already-implied intent and the user explicitly accepts it. Topics 2 and 5 especially can tempt the reviewer into feature design — resist this.
- **Diagnose, don't prescribe.** The reviewer may identify missing support for a design promise, but must not prescribe new features unless the existing design already clearly implies them. "This loop lacks stable-state engagement" is a valid diagnosis. "You need a trading system" is feature invention disguised as critique.
- **Governance edits must preserve intent.** Rewording an invariant for testability is fine. Changing what the invariant protects is a design decision requiring user confirmation.
- **Never weaken governance mechanisms without user confirmation.** Removing an invariant, softening an anchor, or reducing pressure test coverage must be escalated.
- **Scope judgments are flagged, not imposed.** The reviewer may flag scope concerns but must not unilaterally cut scope. Scope decisions are human-required.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Layer — does this introduce implementation detail belonging in system designs, architecture, or engine docs? If yes, reject. (2) Abstraction level — is this written as player-visible behavior (correct) or system internals (wrong layer)? (3) "Would this constrain implementation?" — does this lock implementation options that should remain open? Design docs express intent and constraints, not prescriptions. The design doc defines what the game is, not how to build it.
- **Stay at the design layer.** This is Step 1 review. Do not drift into system decomposition (Step 3), engine constraints (Step 6), or foundation architecture (Step 7). If a review issue implies work in those layers, note it as a downstream concern — don't try to solve it here.
- **Theory observations are clearly labeled.** If the reviewer cites genre conventions, design patterns, or academic game design principles, these are advisory — not authority. Flag them separately from internal consistency issues.
- **ADR supersedence is rare and explicit.** ADRs only override the design doc where the ADR explicitly changes design intent — not where it merely imposes implementation constraints. Technical ADRs do not override game design decisions.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Pushback is expected and healthy.**
- **Reappearing material issues escalate to the user.** Escalate when the same material issue persists for 2 outer iterations, or when the reviewer and Claude remain split after max-exchanges on a topic. Present escalated issues using the Human Decision Presentation pattern (see WORKFLOW.md) — numbered, with concrete options (a/b/c).
- **Cross-topic soft weaknesses escalate.** If the same non-contradiction issue (e.g., vague Player Mental Model) materially degrades 2 or more topics, escalate it even if it is not a direct conflict. Repeated soft weaknesses are structural problems.
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Ambiguous design intent is not a defect.** When the design doc genuinely permits multiple valid readings (creative direction, tone, scope boundaries), do not treat ambiguity as an error. Flag for user decision. The reviewer's preferred interpretation is not automatically correct — design ambiguity often reflects intentional flexibility.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the design doc harder to use as a development reference? (b) does this improve clarity for the team, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving usability, optimize for review criteria over practical development guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing docs that are hyper-consistent but less inspiring, readable, or flexible. The goal is a design doc the team can build from, not one that scores perfectly on an internal consistency audit.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "vision too vague" and "core fantasy unclear" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.

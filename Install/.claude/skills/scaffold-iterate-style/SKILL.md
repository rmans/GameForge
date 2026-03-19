---
name: scaffold-iterate-style
description: Adversarial per-topic review of Step 5 docs using an external LLM. Each of the 6 docs gets its own specialized review lens, then a cross-doc integration topic checks the seams. Consumes design signals from fix-style. Supports --target for single-doc focus and --topics for scoped review.
argument-hint: [--target doc.md] [--topics "1,3,7"] [--focus "concern"] [--iterations N] [--signals "..."]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Style Review

Run an adversarial per-topic review of Step 5 visual/UX docs using an external LLM reviewer: **$ARGUMENTS**

This skill reviews the 6 Step 5 docs across 7 sequential topics — one per doc plus a cross-doc integration topic. Each doc gets its own specialized review lens targeting its unique failure modes, then Topic 7 checks whether the docs work together as one system.

This is the **design reviewer** for Step 5 — not the formatter. It runs after `fix-style` has normalized the docs and detected design signals. It evaluates whether the visual/UX model is *sound*.

The real question this review answers: **do these 6 docs, taken together, give a developer everything they need to build the game's visual presentation, player interaction, system feedback, and audio — without guessing, contradicting each other, or leaving critical UX decisions implicit?**

## Topics

| # | Topic | Doc | Core Question |
|---|-------|-----|---------------|
| 1 | Visual Identity & Readability | style-guide | Can this world be seen clearly and consistently? |
| 2 | Color Semantics & Accessibility | color-system | Does color carry stable meaning without breaking accessibility? |
| 3 | UI Component Model | ui-kit | Are the UI building blocks sufficient and properly bounded? |
| 4 | Input Clarity & Command Structure | interaction-model | Can the player act clearly and consistently? |
| 5 | Response Coverage & Priority Logic | feedback-system | Does the game answer every action and event correctly? |
| 6 | Audio Tone & Boundary Discipline | audio-direction | Does sound reinforce tone and information without overstepping? |
| 7 | Cross-Doc Integration | All 6 docs | Do these six docs work as one usable system? |

**Budget priority:** When `--topics` is omitted and `--iterations` is low (≤ 3), run Topic 7 first instead of last. Topic 7 is the highest-value topic — it catches seam failures that per-doc reviews miss. With tight budgets, per-doc topics can be truncated but Topic 7 must run.

### Topic 1 — Visual Identity & Readability

**Doc:** style-guide.md
**Attacks:** identity coherence, readability at scale, production realism

This doc gets hammered on whether the visual identity holds together and supports gameplay — not on component mechanics or feedback timing.

**Review pressure points:**
- **Pillar coherence** — do the aesthetic pillars reinforce each other, or do they pull in conflicting directions? "Readable at a glance" and "dense, detailed art" are in tension. Flag contradictions the doc doesn't acknowledge.
- **Tone register completeness** — do registers cover the full emotional range the design doc describes (calm, tension, crisis, transition)? Are transitions between registers described — what triggers the shift, how fast?
- **Rendering approach fitness** — does the rendering approach serve the actual gameplay camera and information density? Top-down pixel art for a game that needs "cinematic character moments" is a mismatch.
- **Entity readability at scale** — are visual descriptions specific enough to distinguish entity types at the game's actual camera distance? A description that sounds beautiful in prose but is unreadable at 1080p zoom-out is a design failure.
- **Animation budget realism** — do the animation principles imply a production scope that matches the project? "Unique idle animations per colonist personality" in a solo-dev project is a scope trap.
- **Reference specificity** — are visual references concrete ("Rimworld's icon language for status indicators") or vague ("clean and modern")? Vague references provide no implementation guidance.
- **Iconography testability** — could an artist produce icons from these rules alone? Are size constraints, color restrictions, and state variant rules concrete enough?
- **Visual hierarchy vs player information model** — does the visual hierarchy support what the design doc says the player needs to see? If the player must monitor 8 systems simultaneously, does the style enable that?

**Questions the reviewer must answer:**
1. Can the player distinguish entities, statuses, and priorities at the real camera distance?
2. Do the tone registers cover calm, tension, crisis, and transition states?
3. Are the visual pillars operational, or just moodboard language?
4. Would two artists produce assets that look like the same game from this doc alone?

---

### Topic 2 — Color Semantics & Accessibility

**Doc:** color-system.md
**Attacks:** semantic discipline, accessibility rigor, palette-to-tone alignment

This doc gets attacked on whether color carries stable, learnable meaning — not on general visual identity or interaction behavior.

**Review pressure points:**
- **Palette-to-tone alignment** — does the palette actually evoke the mood described in style-guide tone registers? A "warm, organic" tone register with a cold blue palette is incoherent.
- **Token coverage** — does every important gameplay state have a corresponding token? Are there gameplay states without color representation?
- **Signal color reservation** — are signal colors (health, danger, alert) truly reserved, or are they also used decoratively? Decorative reuse of signal colors destroys player-learned associations.
- **Accessibility rigor** — are contrast ratios concrete numbers, not aspirational language? "We aim for good contrast" is worthless. "WCAG AA 4.5:1 minimum for body text" is testable.
- **Theme variant coherence** — if themes exist, do they maintain token semantics? A "desert biome" theme where the danger color shifts from red to orange breaks learned associations.
- **Color count discipline** — is the total palette size manageable? Too many colors create visual noise. Too few create monotony. Is there a stated principle?
- **State-transitions coverage** — do entity states from state-transitions.md all have corresponding color tokens? Flag unmapped states.

**Questions the reviewer must answer:**
1. Does every important gameplay state have a token?
2. Are danger/warning/success/error reserved and learnable?
3. Do theme variants preserve meaning?
4. Is critical information ever color-only?
5. Are contrast targets concrete and enforceable?

---

### Topic 3 — UI Component Model

**Doc:** ui-kit.md
**Attacks:** component completeness, composition discipline, boundary control

This doc gets attacked on whether the building blocks are sufficient and properly bounded — not on player verbs or overall feedback escalation logic.

**Review pressure points:**
- **Component sufficiency** — for each player-visible system, what component shows it? Are there systems that surface player data with no corresponding ui-kit component?
- **State table completeness** — does every interactive component have the states needed by the interaction model (default, hover, pressed, focused, disabled, error, selected)? Are there interaction patterns that imply states ui-kit doesn't define?
- **Typography/spacing fitness** — does the type scale and spacing system serve the game's actual information density? A game that shows 20 stats on one panel needs different typography rules than one with minimal HUD.
- **Composition logic** — are composition rules (how components combine into panels) described at the right abstraction level? Too abstract = unusable. Too concrete = engine leakage.
- **Resource/entity representation** — do resources from resource-definitions.md and entities from entity-components.md have icon or display components?
- **Scope guard** — has the doc drifted into screen maps, scene hierarchies, modal graphs, or HUD structure? Those belong in engine docs.
- **Color token compliance** — do all component states reference color-system tokens? Are there raw hex values?
- **Sound feedback boundary** — are per-component sounds clearly distinct from feedback-system coordination? Is there overlap?

**Questions the reviewer must answer:**
1. For each player-visible system, what component shows it?
2. Does every interactive component have the states needed by the interaction model?
3. Is the kit sufficient to build all major panels without inventing new atoms?
4. Does the doc stay at component level instead of drifting into screen layout?
5. Would two UI devs build the same kinds of panels from this kit?

---

### Topic 4 — Input Clarity & Command Structure

**Doc:** interaction-model.md
**Attacks:** input ambiguity, command completeness, modal clarity

This doc gets attacked on whether the player can act clearly and consistently — not on coordinated audiovisual response logic.

**Review pressure points:**
- **Player verb coverage** — does every player verb from the design doc have a concrete interaction expression? Are there verbs with no defined input mechanism?
- **Selection model ambiguity** — could two developers implement the same selection behavior from this doc? Single-select, multi-select, drag-select, deselection, persistence across mode changes — all unambiguous?
- **Command model completeness** — are commands specific enough for implementation? "The player can issue orders" is insufficient. "Click entity → right-click target → command issued if valid, error feedback if not" is implementable.
- **Modal structure coherence** — are game modes (build, zone, inspect, etc.) clearly defined? What persists and what resets on mode switch? Are transitions documented?
- **Input feedback mapping** — does every interactive element have a defined hover, press, and select response? Are these consistent with ui-kit component states and color-system tokens?
- **UI affordance assumptions** — does the interaction model assume components (context menus, drag ghosts, selection rings) that ui-kit doesn't define?
- **Boundary enforcement** — does the doc strictly define player input? If it describes what happens after a command is issued (beyond immediate input feedback), that content belongs in feedback-system.
- **Invalid action handling** — when the player tries something that can't be done, is the immediate feedback expectation clear? Not the full system response (feedback-system owns that), but the input-layer signal that "this isn't valid."

**Questions the reviewer must answer:**
1. Can a developer implement selection exactly from this doc?
2. Does every player verb have a concrete interaction path?
3. Are build/zone/inspect/command mode transitions clear?
4. What persists when switching context?
5. Where would two developers diverge most when implementing the same interaction?

---

### Topic 5 — Response Coverage & Priority Logic

**Doc:** feedback-system.md
**Attacks:** response completeness, priority realism, cross-modal coordination

This doc gets attacked under realistic gameplay conditions, not tidy table checks. It should be the most brutally reviewed doc because feedback coordination failures are the hardest to fix after implementation.

**Review pressure points:**
- **Event coverage** — does every major player action and game event have defined feedback? Are there important events with no response at all?
- **Priority hierarchy realism** — test the priority ordering against realistic simultaneous-event scenarios. Two events fire at once — what wins and why? A colonist dying during building placement, a critical alert during a modal dialog. The priority system was designed for one event at a time in a game that produces many.
- **Event-response table completeness** — for each entry, are visual, audio, and UI responses all specified? Are there events with only one channel?
- **Timing realism** — are timing rules consistent with the simulation model? "Instant" feedback for tick-confirmed actions will feel wrong.
- **Failure messaging quality** — when the player tries something invalid, is the feedback specific enough to explain WHY? "Can't do that" vs "Not enough iron (need 5, have 3)."
- **Cross-modal coordination specificity** — are coordination rules specific enough that two developers would implement the same behavior? "Visual and audio fire together" is vague. Concrete timing and sequencing is implementable.
- **Redundancy enforcement** — is gameplay-critical information conveyed through at least two channels? Are there critical events with only one feedback channel?
- **Boundary enforcement** — does the doc define system responses only? If it contains input mapping, that belongs in interaction-model.
- **Interaction loop closure** — does every interaction pattern opened by interaction-model end with a defined response here? No dead ends where the player acts and nothing happens.

**Questions the reviewer must answer:**
1. Does every major player action or game event have defined feedback?
2. If multiple events occur at once, what wins and why?
3. Is the timing believable relative to the simulation model?
4. Are critical failures explained clearly enough for recovery?
5. Does every critical event use redundant channels?

---

### Topic 6 — Audio Tone & Boundary Discipline

**Doc:** audio-direction.md
**Attacks:** tone alignment, category coverage, boundary control

This doc gets attacked on whether sound reinforces the visual experience — not on trigger timing or event choreography.

**Review pressure points:**
- **Philosophy-to-tone alignment** — does the audio identity match the visual identity from style-guide? If visual tone is "clinical, precise, cold" but audio says "warm ambient organic soundscape," they fight each other.
- **Category completeness** — do sound categories cover all feedback types from feedback-system? Are there feedback events that need audio but have no corresponding category?
- **Music direction vs gameplay pacing** — does the music direction serve the game's actual pacing? If the game has long quiet stretches, does music account for that? If the game depends on hearing escalating alerts, can music duck or yield?
- **Music vs alert readability** — can critical audio signals (alerts, warnings, state changes) be heard over music? Is the relationship between music and gameplay audio explicitly defined, or does the doc assume music and alerts never conflict?
- **Silence as design** — is silence used intentionally? Does the doc define when the game should be quiet and what quiet communicates? Or is silence just "no sounds playing"?
- **Feedback hierarchy consistency** — does the audio priority ordering match feedback-system's priority hierarchy? Divergence means two different stacking/suppression behaviors.
- **Accessibility compliance** — does the doc acknowledge the no-audio-only-information rule? Are there audio events that carry gameplay info not available through any other channel?
- **Boundary enforcement** — does the doc define what the game sounds like (philosophy, categories, aesthetic rules)? Or does it drift into defining when sounds fire and how they coordinate with visual/UI (feedback-system's domain)?

**Questions the reviewer must answer:**
1. Does the game sound like it looks?
2. Are all needed sound categories actually covered?
3. Does silence mean anything, or is it accidental?
4. Can music coexist with alert readability?
5. Does audio-direction define character, while feedback-system defines timing?

---

### Topic 7 — Cross-Doc Integration

**Docs:** All 6 Step 5 docs
**Attacks:** seam failures, accessibility coherence, implementation readiness

This is the integration test. It evaluates whether the 6 docs work together as one usable system. Run this topic first when budget is tight.

**Cross-doc consistency checks:**
- **Style-guide → Color-system** — do palette choices evoke the mood described in tone registers? Do tone register shifts have corresponding palette shifts?
- **Color-system → UI-kit** — do all component state tokens exist in color-system? Any raw hex values in ui-kit? Do states use semantically correct tokens (error = danger color, not accent)?
- **Style-guide → UI-kit** — do animation timings match? Does icon style match iconography rules? Does typography match the visual tone?
- **UI-kit → Interaction-model** — does interaction-model assume components ui-kit defines? Does ui-kit define interaction behavior it shouldn't?
- **Interaction-model → Feedback-system** — every input has a response. Every response corresponds to a real input. No gaps, no overlap.
- **Feedback-system → Audio-direction** — priority hierarchies agree. Sound categories cover feedback types. Timing coordination belongs in feedback-system only.
- **Feedback-system → Color-system** — feedback visual treatments use correct severity tokens.
- **Audio-direction → Style-guide** — audio aesthetic matches visual aesthetic. Tone registers align.
- **All → Design doc** — aesthetic pillars, tone, player verbs, failure philosophy, and player information model are consistently reflected.
- **All → State-transitions** — entity states are mapped to colors, visual states, feedback triggers, and audio responses consistently.
- **Canonical drift detection** — is any downstream doc more detailed or more current-looking than its upstream source? This is a signal, not an automatic defect — downstream docs may legitimately operationalize upstream intent. The defect is when they appear to become the de facto source of truth, displacing the upstream doc's authority.
- **Abstraction-level consistency** — are all 6 docs at the same abstraction level? Or has one drifted into implementation while others remain high-level?

**Accessibility coherence (cross-doc):**
- **Color-only information** — are there gameplay states communicated only through color? (color-system + ui-kit)
- **Audio-only information** — is there gameplay-critical info conveyed only through audio? (audio-direction + feedback-system)
- **Hover-only interaction** — are there interaction cues available only through hover, inaccessible to keyboard/gamepad? (interaction-model + ui-kit)
- **Redundant channel coverage** — does every critical gameplay event have at least two feedback channels? (feedback-system + ui-kit + audio-direction)

**Player experience readiness:**
- **Spec derivation readiness** — could behavior specs be written against these docs? Can you specify "when the player places a building" in terms of interaction-model input, feedback-system response, ui-kit components, color-system tokens, and audio-direction sound?
- **Implementation path clarity** — for each major player interaction, is the full path clear? Input mechanism → component representation → system response → visual treatment → audio response?
- **Gap detection** — what's the biggest thing missing? Not "this could be improved" but "a developer would get stuck here."
- **Ambiguity detection** — where could two developers legitimately build incompatible presentations?
- **Multi-developer divergence test** — if two UI developers independently built the same panel, where would they diverge?

**Questions the reviewer must answer:**
1. Does style-guide mood actually map into color-system and audio-direction?
2. Does ui-kit support everything interaction-model assumes?
3. Does feedback-system close every loop interaction-model opens?
4. Does audio-direction cover the sound roles feedback-system expects?
5. Do state changes map consistently across color, UI, feedback, and audio?
6. Are accessibility promises enforced across all docs, not just mentioned locally?
7. Where would two developers still diverge?

**After all topics complete**, the reviewer must answer final questions and provide a rating:

1. **What is the single most dangerous cross-doc inconsistency?** — the mismatch most likely to produce a confusing player experience.

2. **What could a developer get wrong despite reading all 6 docs?** — the implicit assumption most likely to produce inconsistent presentation.

3. **Which doc is weakest?** — the doc that contributes least to implementation clarity.

4. **Blocker classification** — for each issue found, classify its downstream impact:
   - **Blocks engine UI doc** — can't write engine UI implementation without this resolved
   - **Blocks specs** — can't derive behavior specs involving UI/interaction without this resolved
   - **Blocks slice/spec approval confidence** — Step 5 ambiguity will undermine spec/slice review quality
   - **Blocks art/audio production** — can't generate consistent assets without this resolved
   - **Does not block, increases risk** — implementation can proceed but UX inconsistency will grow

5. **Visual/UX Model Strength Rating (1–5):**
   - 1 = fundamentally broken (major cross-doc contradictions, critical docs mostly TBD)
   - 2 = major gaps (interaction model incomplete, feedback system missing, visual identity unclear)
   - 3 = workable but risky (some cross-doc drift, several TBD areas, ambiguity in key UX decisions)
   - 4 = solid visual/UX model (docs mostly consistent, minor gaps bounded, implementation path clear)
   - 5 = strong visual/UX model (all docs consistent, no contradictions, developer could implement from docs alone)

## Reviewer Bias Pack

Include these detection patterns in the reviewer's system prompt.

1. **Aesthetic coherence without operational precision** — the docs describe a beautiful vision but lack the concrete rules needed to implement it. "Warm, organic feel" with no color tokens, timing values, or spacing rules. Test: could you build a UI panel from this description alone?

2. **Boundary erosion** — interaction-model starts defining system responses. Feedback-system starts defining input behavior. Audio-direction starts defining coordination timing. UI-kit starts defining screen layout. Each doc drifts into its neighbor's domain.

3. **Priority hierarchy fantasy** — feedback priority ordering looks clean on paper but fails under realistic gameplay scenarios. Two simultaneous events, three overlapping audio cues, a critical alert during a modal dialog.

4. **Component-level completeness, interaction-level gaps** — every component is beautifully defined but the interaction patterns connecting them are underspecified. Or vice versa. The docs look complete individually but the seam is the gap.

5. **Accessibility as afterthought** — accessibility sections exist in individual docs but no cross-doc check ensures the principle is enforced. Color-only health indicators. Audio-only alerts. Hover-only inspection. Each doc passes; the system fails.

6. **Tone register orphaning** — style-guide defines tone registers but color-system, audio-direction, and feedback-system don't reference them. The registers exist in isolation — they describe mood shifts no other doc implements.

7. **Feedback coordination gap** — feedback-system describes coordinated responses, but the individual docs it coordinates were written independently without referencing the coordination rules.

8. **Scope creep into engine territory** — UI-kit defines screen maps. Interaction-model defines input routing. Feedback-system defines signal dispatch. Audio-direction defines audio middleware. Each drifts from "what" into "how."

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--target` | No | all | Target a single doc by filename (e.g., `--target ui-kit.md`). When set, runs the targeted doc's topic plus Topic 7. |
| `--topics` | No | all | Comma-separated topic numbers to review (e.g., `"1,4,7"`). |
| `--focus` | No | — | Narrow the review within each topic to a specific concern. |
| `--iterations` | No | 10 | Maximum outer loop iterations. Stops early on convergence. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic. |
| `--signals` | No | — | Design signals from fix-style to focus the review. Format: comma-separated signal descriptions. |

### --target to --topics mapping

When `--target` is set without explicit `--topics`:

| Target | Auto-selected Topics |
|--------|---------------------|
| `style-guide.md` | 1, 7 |
| `color-system.md` | 2, 7 |
| `ui-kit.md` | 3, 7 |
| `interaction-model.md` | 4, 7 |
| `feedback-system.md` | 5, 7 |
| `audio-direction.md` | 6, 7 |

Topic 7 is always included. Explicit `--topics` overrides this mapping.

## Preflight

Before running external review:

1. **Check docs exist.** Verify at least style-guide.md, ui-kit.md, interaction-model.md, and feedback-system.md exist and are not at template defaults. If fewer than 4 Step 5 docs exist, stop: "Style docs not ready. Run `/scaffold-bulk-seed-style` first."
2. **Check fix-style has run.** Look for the most recent `FIX-style-*` log in `scaffold/decisions/review/`. If no log exists, or the most recent log reports FAIL-level structural issues that were not resolved, stop: "Run `/scaffold-fix-style` first to normalize structure." If no log exists but docs appear structurally clean (all required sections present, no invalid token references), proceed with a warning.
3. **Check design doc exists.** The reviewer needs Design Invariants, Aesthetic Pillars, and Player Control Model as context.

## Context Files

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| All 6 Step 5 docs in `scaffold/design/` | Primary targets |
| `scaffold/design/design-doc.md` | Aesthetic Pillars, tone, player verbs, failure philosophy, accessibility |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution |
| `scaffold/design/systems/_index.md` + system files with player-visible behavior | What the UI must display and what events the game produces |
| `scaffold/design/state-transitions.md` | Entity states for color/visual/feedback/audio mapping |
| `scaffold/reference/entity-components.md` | Entity types for component and icon coverage |
| `scaffold/reference/resource-definitions.md` | Resources for UI representation coverage |
| `scaffold/decisions/known-issues/_index.md` | Known gaps and constraints |
| Accepted ADRs in `scaffold/decisions/architecture-decision-record/` (canonical: internal `Status: Accepted` field) | Decision compliance |
| Design signals from fix-style (if `--signals` provided) | Focus areas for the reviewer |

Only include context files that exist — skip missing ones silently.

## Execution

### Loop Structure

```
Outer Loop (iterations — fresh review of updated doc)
└── Per Topic:
    └── Inner Loop (exchanges — back-and-forth conversation)
        ├── Reviewer raises issues (structured JSON via doc-review.py)
        ├── Claude evaluates each: AGREE / PUSHBACK / PARTIAL
        ├── Reviewer counter-responds
        └── ... until consensus or max-exchanges
    └── Consensus: reviewer summarizes final position
    └── Apply changes: accepted issues are applied to the doc
```

Each topic gets its own review → respond → consensus cycle via the Python `doc-review.py` script. After all topics in one outer iteration, re-read updated docs and start the next outer iteration if issues remain.

**Stop conditions** (any one stops iteration):
- **Clean** — a complete topic pass produces no new issues.
- **Converged** — two consecutive passes produce the same issue set (same doc + category + section) with no new findings.
- **Human-only** — only issues requiring user decisions remain; further iteration won't resolve them.
- **Limit** — `--iterations` maximum reached.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue.

**Lock enforcement:**
- The reviewer must NOT reintroduce a resolved issue in a different form.
- The reviewer must NOT raise stricter variants unless: (a) new evidence exists, OR (b) the fix itself introduced a new problem.
- If a previously resolved issue reappears: classify it as a **review inconsistency**, not a new issue.

**Cross-topic lock:** If Topic 1 resolves an issue, later topics may not re-raise it under a different name.

**Tracking:** Maintain a running resolved-issues list in the review log. Before engaging with any new reviewer claim, check it against the resolved list by root cause.

**Edit scope:**
- When `--target` is set, only edit the targeted doc. Flag cross-doc issues for fix-style.
- When `--target` is not set, edit any of the 6 Step 5 docs.
- Never edit Step 1–4 docs or planning docs.

### Issue Adjudication

Every issue raised by the reviewer must be classified into exactly one outcome:

| Outcome | Action |
|---------|--------|
| **Accept → edit Step 5 doc** | Apply change immediately. The issue is valid and within Step 5 scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or out of scope. |
| **Escalate to user** | Requires design judgment, unclear authority, or unresolved after adjudication attempts across 2 outer iterations. |
| **Flag for revise-design** | Design doc is likely incomplete or ambiguous on visual/UX direction. |
| **Defer (valid TBD)** | Correctly blocked by an unresolved design decision. Not a gap — an honest wait. |
| **Flag ambiguous design intent** | Design doc permits multiple valid interpretations and the Step 5 doc chose one. Flag for user decision. |

**Adjudication rules:**
- Prefer fixing Step 5 docs over escalating — most issues are presentation-level clarity.
- Never "half-accept" — choose exactly one outcome per issue.
- If the issue depends on a missing design decision → flag for revise-design, not Step 5 fix.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- Escalate only if the issue remains unresolved after adjudication attempts across 2 outer iterations. Bad reviewer repetition alone does not force escalation — if you've already adjudicated it, the lock holds.

### Scope Collapse Guard

Before accepting any change:

**1. Upward Leakage Test:**
Does this change introduce decisions belonging in system designs or the design doc?
- Step 5 docs may: define visual identity, component behavior, interaction patterns, feedback coordination, audio direction.
- Step 5 docs must NOT: change what systems do, alter gameplay mechanics, or redefine system responsibilities.

**2. Downward Leakage Test:**
Does this change introduce engine-specific implementation detail?
- Step 5 docs must NOT: specify scene tree structure, node types, signal wiring, render pipelines, or engine-specific APIs.
- Test: could this rule be implemented in any engine? If engine-specific → wrong layer.

**3. Lateral Leakage Test:**
Does this change belong in a different Step 5 doc?
- Interaction-model must not define system responses (→ feedback-system).
- Feedback-system must not define input behavior (→ interaction-model).
- Audio-direction must not define coordination timing (→ feedback-system).
- UI-kit must not define screen maps or modal hierarchies (→ engine docs).

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-style-[target-or-all]-<YYYY-MM-DD-HHMMSS>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

```
## Style Review Complete [target / all]

### Most Dangerous Cross-Doc Inconsistency
[The mismatch most likely to produce a confusing player experience.]

### What Could a Developer Get Wrong
[The implicit assumption most likely to produce inconsistent presentation.]

### Weakest Doc
[The doc that contributes least to implementation clarity.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Visual Identity & Readability | N | N | N |
| 2. Color Semantics & Accessibility | N | N | N |
| 3. UI Component Model | N | N | N |
| 4. Input Clarity & Command Structure | N | N | N |
| 5. Response Coverage & Priority Logic | N | N | N |
| 6. Audio Tone & Boundary Discipline | N | N | N |
| 7. Cross-Doc Integration | N | N | N |

### Per-Doc Issues
| Document | Issues Found | Accepted Changes | Key Finding |
|----------|-------------|-----------------|-------------|
| style-guide.md | N | N | ... |
| color-system.md | N | N | ... |
| ui-kit.md | N | N | ... |
| interaction-model.md | N | N | ... |
| feedback-system.md | N | N | ... |
| audio-direction.md | N | N | ... |

**Visual/UX Model Strength Rating:** N/5 — [one-line reason]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/ITERATE-style-[target]-YYYY-MM-DD-HHMMSS.md
```

## Rules

- **Design doc and system designs are the primary authority.** Step 5 docs interpret and present; they do not override.
- **Step 5 docs describe PRESENTATION, not IMPLEMENTATION.** Reject engine constructs, node types, or rendering pipeline details.
- **Edit only Step 5 docs.** Never edit design-doc, system designs, architecture, reference docs, engine docs, planning docs, or ADRs during review.
- **Authority flows downstream within Step 5.** style-guide → color-system → ui-kit. Interaction-model and feedback-system are peers. Audio-direction derives priority from feedback-system. On mismatch, upstream is canonical. Downstream issues may reveal upstream incompleteness — report both directions. Peer conflicts are reported, not auto-resolved, unless one side only contains stale copied text.
- **Each doc has its own failure modes.** Do not ask the same generic questions of all 6 docs. Style-guide gets attacked on readability and identity. Color-system on semantics and accessibility. UI-kit on completeness and scope. Interaction-model on input clarity. Feedback-system on response coverage and priority realism. Audio-direction on tone alignment and boundaries.
- **Topic 7 is the highest-value topic.** When budget is tight, run Topic 7 first. It catches seam failures that per-doc reviews miss.
- **Never blindly accept.** Every issue gets evaluated against project context and design doc intent.
- **Pushback is expected and healthy.** The reviewer is adversarial — disagreement is normal.
- **Escalate only after real adjudication failure.** The same material issue must remain unresolved after adjudication attempts across 2 outer iterations. Reviewer repetition of a locked issue is not an adjudication failure.
- **When --target is set, respect edit scope.** Cross-doc issues found during targeted review are flagged for fix-style, not fixed directly.
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Ambiguous upstream design is not a Step 5 defect.** When the design doc permits multiple valid interpretations and a Step 5 doc chose a reasonable one, do not treat it as incorrect. Flag for user decision.
- **Canonical drift is a signal, not an automatic defect.** Downstream docs may legitimately operationalize upstream intent. The defect is when they displace the upstream doc's authority — becoming the de facto source of truth.
- **Practicality check before finalizing changes.** Before accepting any change: would this make the doc harder to use during implementation? Does this improve clarity for developers and artists, or just enforce consistency for the review system's benefit? Reject changes that increase rigidity without improving usability.
- **Scope collapse guard.** Before accepting any change: (1) Upward — does this change gameplay or system behavior? (2) Downward — does this introduce engine-specific detail? (3) Lateral — does this belong in a different Step 5 doc? If any test fails, reject or flag.
- **Resolved issues are locked across iterations.** Once accepted+fixed or rejected with reasoning, an issue is closed. Only new evidence or a regression can reopen. Issues are identified by root cause, not phrasing.

---
name: scaffold-bulk-seed-style
description: Seed style-guide, color-system, ui-kit, interaction-model, feedback-system, and audio-direction from the design doc and system designs. Auto-writes high-confidence content, leaves low-confidence as TODO, asks only on ambiguous or high-impact decisions.
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Seed Visual & UX Documents

Seed all 6 Step 5 docs from upstream context: **$ARGUMENTS**

Reads the design doc, system designs, and supporting docs to pre-fill style-guide, color-system, ui-kit, interaction-model, feedback-system, and audio-direction. Phases are processed in order for consistency. Auto-writes where upstream evidence is strong; flags ambiguity for user input.

## Prerequisites

1. **Read the design doc** at `scaffold/design/design-doc.md`.
2. **Verify it's sufficiently filled out.** The following sections must have content (not just TODO markers):
   - Core Fantasy
   - Design Invariants
   - Core Loop
   - Player Control Model
   - Player Mental Model
   - Player Information Model
   - Failure Philosophy
3. If the design doc is too empty, stop and tell the user to run `/scaffold-init-design` first.
4. **Check existing doc state.** For each of the 6 docs:
   - **Exists and authored** (substantive content beyond template defaults) → skip that phase entirely.
   - **Exists but incomplete** (template defaults, mostly TODOs, or only a few sections filled) → seed missing sections only, preserve existing content.
   - **Does not exist** → create from template, then seed all sections.
   Report which docs are being skipped, partially seeded, or fully seeded.

## Confidence Model

Every section you seed gets a confidence tag:

| Confidence | Criteria | Action |
|-----------|---------|--------|
| **High** | Directly supported by a single upstream doc with clear, unambiguous content | Auto-write. No confirmation needed. |
| **Medium** | Reasonable synthesis from multiple sources, or a single source with some interpretation | Auto-write. Record rationale in the Changelog entry and the final report — not inline in the doc. |
| **Low** | Speculative, conflicting sources, or insufficient upstream evidence | Leave as TODO with `<!-- LOW: [what's missing] -->`. Include in report. |

**Confirmation pause** — only stop and ask the user when:
- The design doc is ambiguous on visual/audio tone and multiple valid interpretations exist
- A choice would materially change downstream docs (e.g., selection model affects everything below it)
- Two upstream sources contradict each other on a player-facing behavior
- A major UX model decision has no clear upstream support (e.g., modal vs non-modal)

For everything else: write it, tag it, report it.

## Context Files

Read these before starting. They provide the full upstream context for Step 5.

### Primary Sources (design intent — what the game is)

| Context File | Why |
|-------------|-----|
| `scaffold/design/design-doc.md` | Core vision, loops, pillars, player experience model, failure philosophy, target platforms |
| `scaffold/design/glossary.md` | Canonical terminology — use correct terms in all seeded content |
| `scaffold/design/systems/_index.md` + individual SYS-### docs | System list, player-visible behavior, events, state changes |
| `scaffold/design/state-transitions.md` | Entity states — map to colors, visual states, feedback triggers |

### Secondary Sources (constraints — how it must work)

| Context File | Why |
|-------------|-----|
| `scaffold/design/architecture.md` | Scene tree patterns, data flow rules — constrains what's feasible |
| `scaffold/design/authority.md` | Data ownership — constrains command model |
| `scaffold/design/interfaces.md` | Cross-system contracts — constrains interaction model |
| `scaffold/reference/entity-components.md` | Entity data shapes — what the UI needs to display |
| `scaffold/reference/resource-definitions.md` | Resources — what items need UI representation |
| `scaffold/reference/signal-registry.md` | Signal names and levels — what events the game fires |
| `scaffold/engine/_index.md` + engine UI/input/scene docs | Implementation constraints — what the engine supports |

### Advisory Sources (rationale — not authoritative)

| Context File | Why |
|-------------|-----|
| `scaffold/theory/` (if relevant docs exist) | UX heuristics, visual design principles, audio design. Read for rationale and anti-pattern awareness. |
| Accepted ADRs | Decisions that may affect visual/UX choices |

Only include context files that exist — skip missing ones silently.

## Phase Order

Phases are processed in order for consistency. Each doc reads the previous ones as context.

```
style-guide → color-system → ui-kit ↔ interaction-model → feedback-system → audio-direction
```

If ui-kit and interaction-model reveal a tension between them (e.g., interaction-model needs a component ui-kit didn't define, or ui-kit assumed a selection model that interaction-model changes), note the tension in the report and flag the earlier doc for follow-up rather than silently rewriting it.

## Phase 1 — Seed Style Guide

1. **Read** `scaffold/design/style-guide.md`. If already authored, skip to Phase 2.
2. **If file doesn't exist**, create from `scaffold/templates/style-guide-template.md`.
3. **Extract visual identity cues** from upstream context:
   - **Art Direction** ← Design doc: Aesthetic Pillars + Genre & Reference Points
   - **Visual Tone** ← Design doc: Tone section + Failure Philosophy (how mood shifts with game state)
   - **Rendering Approach** ← Design doc: Camera/Perspective
   - **Character & Entity Style** ← Design doc: entity descriptions + System designs: what entities exist
   - **Environment Style** ← Design doc: Place & Time + Rules of the World
   - **Lighting Model** ← Design doc: atmosphere + Tone section
   - **Animation Style** ← Design doc: Input Feel + Aesthetic Pillars
   - **Iconography Style** ← Design doc: Player Information Model (what info must be visible at a glance)
4. **Auto-write** all High/Medium sections. Leave Low sections as TODO.
5. **Pause only** if the design doc's visual tone is ambiguous (e.g., "stylized" with no further direction).
6. **Write content**, set Created/Last Updated dates, add Changelog entry.

## Phase 2 — Seed Color System

1. **Read** `scaffold/design/color-system.md`. If already authored, skip to Phase 3. If file doesn't exist, create from `scaffold/templates/color-system-template.md`.
2. **Read the style-guide** (just seeded in Phase 1) for visual identity context.
3. **Extract color cues** from upstream context:
   - **Palette** ← Style-guide: Art Direction + Visual Tone (colors that match the mood)
   - **Color Tokens** ← Design doc: game mechanics + State-transitions: entity states (map states to semantic colors)
   - **Usage Rules** ← Style-guide: Visual Tone + Design doc: Player Information Model (readability rules)
   - **UI vs World Colors** ← Style-guide: Rendering Approach
   - **Accessibility** ← Design doc: Accessibility Philosophy and targets
   - **Theme Variants** ← Design doc: factions, biomes, modes, escalation states
4. **Auto-write** all High/Medium sections. Leave Low sections as TODO.
5. **Pause only** if competing visual interpretations exist (e.g., design doc references both "warm" and "clinical" tones).
6. **Write content**, set dates, add Changelog entry.

## Phase 3 — Seed UI Kit

1. **Read** `scaffold/design/ui-kit.md`. If already authored, skip to Phase 4. If file doesn't exist, create from `scaffold/templates/ui-kit-template.md`.
2. **Read the style-guide and color-system** (just seeded) for context.
3. **Read system designs that surface player-visible information.** Scan `scaffold/design/systems/_index.md` and read the Purpose + Player Actions + Visibility to Player sections of systems that directly affect what the UI must show.
4. **Extract UI cues** from upstream context:
   - **Component Definitions** ← Design doc: Player Verbs + Core Loop + Player Control Model + System designs: what info each system surfaces to the player + Resource-definitions: what items/resources need UI representation
   - **Component States** ← Color-system: color tokens (hover = accent, disabled = muted, error = danger) + State-transitions: entity states needing visual representation
   - **Typography** ← Style-guide: Visual Tone + Design doc: Player Information Model (data density needs)
   - **Iconography** ← Style-guide: Iconography Style + Entity-components: entity types needing icons
   - **Spacing & Layout Conventions** ← Style-guide: Visual Tone + Design doc: Camera/Perspective (data density vs breathing room)
   - **Animation & Transitions** ← Style-guide: Animation Style
   - **Sound Feedback** ← Design doc: Audio Identity (basic per-component sounds — detailed coordination is in feedback-system)
5. **Auto-write** all High/Medium sections. Leave Low sections as TODO.
6. **Pause only** if the component set implies a UX model that isn't clear from the design doc.
7. **Write content**, set dates, add Changelog entry.

**Scope guard:** UI kit defines components, component states, composition patterns, and spacing/layout conventions at the component level. It does not define screen maps, scene hierarchies, modal graphs, or full HUD structure — those belong in engine docs or later planning.

## Phase 4 — Seed Interaction Model

1. **Read** `scaffold/design/interaction-model.md`. If file doesn't exist, create from `scaffold/templates/interaction-model-template.md`.
2. **Read style-guide, color-system, and ui-kit** (just seeded) for context.
3. **Read system designs for player-interactive entities.** Scan system designs and read Purpose + Player Actions sections to identify: what entities the player can select, what commands each system exposes, what modes exist, what information the player queries.
4. **Extract interaction cues** from upstream context:
   - **Selection Model** ← Design doc: Player Control Model + System designs: what entities are player-interactive
   - **Command Model** ← Design doc: Core Loop + Player Verbs + System designs: what actions each system exposes to the player
   - **Secondary Actions** ← Design doc: Player Control Model + Interfaces: what cross-system interactions the player triggers
   - **Drag Behaviors** ← Design doc: zone/build/placement mechanics
   - **Interaction Patterns** ← Design doc: Core Loop (the canonical sequence of actions per game cycle)
   - **Modal vs Non-Modal** ← Design doc: layer/mode descriptions + UI kit: layout rules
   - **Input Feedback** ← Color-system: hover/selection colors + Style-guide: animation for hover/press
   - **Camera Interaction** ← Design doc: Camera/Perspective
   - **Accessibility** ← Design doc: Accessibility Philosophy
5. **Auto-write** all High/Medium sections. Leave Low sections as TODO.
6. **Pause and ask** if:
   - Selection model is ambiguous (single-select vs multi-select vs marquee)
   - Modal structure is unclear
   - Authority constraints make a player verb impossible as described
7. **Write content**, set dates, add Changelog entry.
8. **Back-check ui-kit.** If the interaction model implies components ui-kit didn't define (e.g., a context menu, a drag ghost, a selection ring), note the gap in the report for follow-up. Do not silently edit ui-kit.

## Phase 5 — Seed Feedback System

1. **Read** `scaffold/design/feedback-system.md`. If file doesn't exist, create from `scaffold/templates/feedback-system-template.md`.
2. **Read all prior Step 5 docs** (style-guide, color-system, ui-kit, interaction-model) for context.
3. **Read system designs for events and state changes.** Scan system designs and read Purpose + Downstream Consequences + State Lifecycle sections to identify: what events each system produces, what state changes the player should be notified about, what failure/warning conditions exist per system.
4. **Extract feedback cues** from upstream context:
   - **Feedback Types** ← Design doc: Failure Philosophy (Pre-Failure Warning Contract, no silent failures) + System designs: what events each system produces
   - **Timing Rules** ← Interaction-model: input timing expectations + Design doc: simulation tick model awareness
   - **Priority & Stacking** ← Design doc: alert escalation model + UI kit: any alert, notification, or severity-display component definitions
   - **Cross-Modal Coordination** ← UI kit: component states + Sound Feedback section + Color-system: semantic color meanings + Style-guide: animation timing
   - **Event-Response Table** ← System designs: major events per system + State-transitions: state change triggers. Map each to visual + audio + UI response. Use signal-registry as a secondary check for event naming, signal granularity, and cross-system event coverage.
5. **Auto-write** all High/Medium sections. The Event-Response Table will likely be mostly Medium confidence — synthesized from multiple system designs.
6. **Pause only** if the priority hierarchy is ambiguous or multiple events compete for the same feedback channel.
7. **Write content**, set dates, add Changelog entry.

## Phase 6 — Seed Audio Direction

1. **Read** `scaffold/design/audio-direction.md`. If file doesn't exist, create from `scaffold/templates/audio-direction-template.md`.
2. **Read style-guide, feedback-system, and ui-kit** for context. Feedback-system informs timing hierarchy and priority coordination. UI-kit informs local component sound expectations only (click, hover, toggle) — not audio policy.
3. **Extract audio cues** from upstream context:
   - **Audio Philosophy** ← Design doc: Tone + Core Fantasy + Aesthetic Pillars + Style-guide: Visual Tone registers
   - **Sound Categories** ← Feedback-system: feedback types (each type needs a sound category) + UI kit: Sound Feedback (component-level sounds already defined)
   - **Music Direction** ← Design doc: Tone + pacing references + Style-guide: Visual Tone registers
   - **Silence & Space** ← Design doc: atmosphere + Failure Philosophy (does silence mean danger?)
   - **Feedback Hierarchy** ← Feedback-system: priority hierarchy (audio stacking aligns with cross-modal priority)
   - **Asset Style Rules** ← Style-guide: Art Direction (audio aesthetic should match visual aesthetic) + Design doc: Target Platforms (audio format constraints)
   - **Accessibility** ← Design doc: Accessibility Philosophy + Feedback-system: redundancy principle (no audio-only information)
4. **Auto-write** all High/Medium sections. Leave Low sections as TODO.
5. **Pause only** if the design doc's audio tone is genuinely ambiguous.
6. **Write content**, set dates, add Changelog entry.

## Phase 7 — Report

```
## Step 5 Seed Complete

### Documents Seeded
| Document | High | Medium | Low/TODO | Status |
|----------|------|--------|----------|--------|
| style-guide.md | N | N | N | Draft / Skipped (already authored) |
| color-system.md | N | N | N | Draft / Skipped |
| ui-kit.md | N | N | N | Draft / Skipped |
| interaction-model.md | N | N | N | Draft / Skipped |
| feedback-system.md | N | N | N | Draft / Skipped |
| audio-direction.md | N | N | N | Draft / Skipped |

### Assumptions Made
[List every Medium-confidence decision and the reasoning behind it.
These are the sections most likely to need user review.]

### Unresolved Questions
[List every Low-confidence TODO and what upstream information is missing.
Include which doc would need to be filled in to resolve it.]

### Cross-Doc Tensions
[Any inconsistencies discovered between the 6 docs during seeding.
Include back-propagation needs (e.g., "interaction-model implies a context menu component not defined in ui-kit").]

### Recommended Next Steps
- Run `/scaffold-sync-glossary --scope style` to register new domain terms (color tokens, UI component names, interaction patterns) in the glossary
- Review Medium-confidence sections (listed above) — these are reasonable but unverified
- Fill remaining TODOs where upstream docs are missing information
- Run `/scaffold-fix-systems` or `/scaffold-fix-references` if tensions reveal upstream gaps
- Run `/scaffold-validate --scope all` to check cross-references
```

## Rules

- **Auto-write when confidence is high.** If upstream evidence is strong and unambiguous, write the section directly. Do not turn bulk seeding into six interviews.
- **Pause only on ambiguous or high-impact decisions.** Ambiguous style direction, competing visual interpretations, major UX model choices, or anything that would materially change downstream docs.
- **Leave TODOs for low-confidence content.** Don't force content where upstream docs don't provide enough context. Tag what's missing so the user can fill it.
- **Phases are processed in order for consistency.** Style-guide → color-system → ui-kit → interaction-model → feedback-system → audio-direction. If a later phase reveals a missing assumption in an earlier doc, note the tension in the report and flag the earlier doc for follow-up rather than silently rewriting it.
- **Design doc and system designs are the primary sources.** Architecture, reference, and engine docs are secondary constraint sources. Don't let Step 5 docs overweight low-level technical references at the expense of player experience.
- **Be specific, not generic.** Proposed content should reference the actual game described in the design doc, not boilerplate. Use system names, entity types, and mechanics from the project.
- **Use canonical terminology.** All content must use terms from `scaffold/design/glossary.md`. Never use NOT-column synonyms.
- **Preserve any existing content.** If a section is already filled, skip it — don't overwrite.
- **Created documents start with Status: Draft.** Set Created and Last Updated to today's date. Add initial Changelog entry referencing this skill as trigger.
- **Engine-aware, not engine-bound.** Step 5 docs define what must exist, how it behaves, and how it feels. They may reference engine capabilities for context, but must not prescribe specific node hierarchies, signal wiring, or engine patterns. Those belong in Step 4 engine docs.
- **UI kit stays at component level.** Components, component states, composition patterns, spacing conventions. Not screen maps, scene hierarchies, modal graphs, or full HUD structure.
- **Feedback-system is the coordination layer.** UI kit defines component-level feedback. Audio-direction defines sound character. Feedback-system defines when and how they fire together. Don't duplicate — cross-reference.
- **Interaction-model owns input, feedback-system owns response.** Interaction-model defines what the player does. Feedback-system defines what the system does back. Don't mix these.
- **Audio-direction owns philosophy, not timing.** Audio-direction defines what the game sounds like — categories, aesthetic rules, hierarchy, silence meaning. Feedback-system decides when sounds fire and how they coordinate with visual/UI responses. UI-kit may mention local component sounds (click, hover) but does not own audio policy.
- **Read theory docs for advisory context.** If `scaffold/theory/` contains docs on UX design, visual design, audio design, or game feel — read them for rationale and anti-pattern awareness. Theory never overrides design-doc decisions.
- **Step 5 never edits Step 1–4 docs.** If seeding reveals upstream gaps (missing system designs, incomplete architecture, absent engine docs), flag them in the report. Do not back-fill or modify upstream documents — that's the job of revise-* skills.

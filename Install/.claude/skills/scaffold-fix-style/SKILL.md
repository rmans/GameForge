---
name: scaffold-fix-style
description: Mechanical cleanup pass for Step 5 docs (style-guide, color-system, ui-kit, interaction-model, feedback-system, audio-direction). Auto-fixes structural issues, cross-doc inconsistencies, and terminology drift. Detects design signals for adversarial review. Supports --target for single-doc focus.
argument-hint: [--target doc.md] [--iterate N]
allowed-tools: Read, Edit, Grep, Glob
---

# Fix Style

Mechanical cleanup and signal detection for Step 5 visual/UX docs: **$ARGUMENTS**

This skill is the **formatter and linter** for Step 5 docs — not the design reviewer. It normalizes structure, repairs mechanical inconsistencies across the 6 Step 5 docs, and detects design signals. It does not interpret or resolve design issues — that is the job of `iterate-style` (adversarial review) which runs immediately after this skill.

**What fix-style does:** normalize docs so adversarial review doesn't waste time on trivial issues.
**What fix-style does NOT do:** evaluate whether the visual direction is good, resolve interaction model disputes, or make UX decisions.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--target` | No | all | Target a single doc by filename (e.g., `--target style-guide.md`, `--target ui-kit.md`). When omitted, processes all 6 Step 5 docs. |
| `--iterate N` | No | `10` | Maximum review-fix passes before stopping. Stops early on convergence. |

### Valid --target values

| Target | Doc Path | Template |
|--------|----------|----------|
| `style-guide.md` | `design/style-guide.md` | `templates/style-guide-template.md` |
| `color-system.md` | `design/color-system.md` | `templates/color-system-template.md` |
| `ui-kit.md` | `design/ui-kit.md` | `templates/ui-kit-template.md` |
| `interaction-model.md` | `design/interaction-model.md` | `templates/interaction-model-template.md` |
| `feedback-system.md` | `design/feedback-system.md` | `templates/feedback-system-template.md` |
| `audio-direction.md` | `design/audio-direction.md` | `templates/audio-direction-template.md` |

When `--target` is specified, cross-doc checks still run (reading other docs for consistency) but only the targeted doc is edited.

## Missing Doc Handling

If a target Step 5 doc does not exist, report it as **missing** in the per-doc status and do not attempt to create or edit it. Missing Step 5 docs are seeded by `/scaffold-bulk-seed-style`, not fix-style. Continue processing any remaining docs.

## Step 1 — Gather Context

Always read (regardless of `--target`):
1. `scaffold/design/design-doc.md` — core vision, pillars, tone, player experience model, failure philosophy.
2. `scaffold/design/glossary.md` — canonical terminology.
3. `scaffold/doc-authority.md` — document authority ranking, same-rank conflict resolution.
4. `scaffold/design/systems/_index.md` — registered system IDs and names.
5. All accepted ADR files in `scaffold/decisions/architecture-decision-record/` (canonical: internal `Status: Accepted` field. Filename `_accepted` suffix is secondary — if status field and filename conflict, status field wins).
6. `scaffold/decisions/known-issues/_index.md` — open issues that may affect visual/UX.

Read the target doc(s) and their templates:
7. Each target doc from `scaffold/design/`.
8. Corresponding template from `scaffold/templates/` (see mapping in --target table above).

Read cross-reference docs (for consistency checks, not editing):
9. All 6 Step 5 docs (even when targeting one — cross-doc consistency requires reading neighbors).
10. `scaffold/design/state-transitions.md` — entity states that should map to colors and feedback.
11. `scaffold/reference/entity-components.md` — entity types for icon coverage and component definitions.
12. `scaffold/reference/resource-definitions.md` — resources for UI representation coverage.

## Section Health Classification

For each section in each doc, classify its health:

| Health | Criteria |
|--------|---------|
| **Complete** | Substantive authored content — specific to this project, not template text |
| **Partial** | Some authored content but TODOs, placeholders, or template text remain |
| **Empty** | Only template/default text, or section heading with no content |

Report per-doc health as weighted percentage: Complete = 1.0, Partial = 0.5, Empty = 0. Health = `(sum of weights / total required sections) × 100`. This is advisory — it helps iterate-style prioritize and helps fix-style decide when to stop.

## Step 2 — Per-Doc Checks

### style-guide.md

#### Section Structure
Compare against `templates/style-guide-template.md`. Required sections:
- Art Direction (with Aesthetic Pillars, Reference Points)
- Visual Tone (with Tone Registers, Mood Communication)
- Rendering Approach (with Resolution & Scale)
- Character & Entity Style (with Entity Visual Hierarchy)
- Environment Style
- VFX & Particles
- Animation Style (with Motion Principles, Feedback Animations)
- Iconography Style (with Icon Design Rules, Icon Categories)
- Rules

#### Mechanical Checks
- **Aesthetic pillars populated** — at least 3 concrete pillars, not template text.
- **Tone registers defined** — at least 2 named registers with visual descriptions.
- **Rendering approach concrete** — camera perspective and art style specified, not just "TBD."
- **Entity types covered** — entity types from `entity-components.md` have corresponding visual descriptions. Flag missing entity types.
- **Animation timing stated** — motion principles include at least one concrete timing value (e.g., "< 200ms").
- **Iconography categories present** — icon categories align with what `entity-components.md` and `resource-definitions.md` need represented.
- **Design doc alignment** — aesthetic pillars trace to design doc Aesthetic Pillars. Tone registers trace to design doc Tone section. Rendering approach matches Camera/Perspective.
- **Terminology compliance** — glossary canonical terms throughout.
- **Template text / TODOs** — no remaining placeholder content in populated sections.

#### Design Signals
- **Tone register gap** — design doc describes mood shifts but style-guide has no corresponding registers.
- **Entity coverage gap** — entity types exist in entity-components but have no visual description.
- **Pillar contradiction** — aesthetic pillars conflict with each other or with design doc.

---

### color-system.md

#### Section Structure
Compare against `templates/color-system-template.md`. Required: Palette (Base, Signal, Identity), Color Tokens (State, UI), Usage Rules, UI vs World Colors, Accessibility, Theme Variants, Rules.

#### Mechanical Checks
- **Token table columns complete** — every row has: Token, State/Purpose, Hex, Usage.
- **State tokens cover state-transitions.md** — entity states from state-transitions.md have corresponding color tokens. Flag missing states.
- **UI tokens present** — at minimum: primary, secondary, accent, background, surface, text, disabled, error, success, warning.
- **Hex values valid** — all hex values are well-formed (#RRGGBB or #RRGGBBAA).
- **No duplicate tokens** — same token name doesn't appear twice.
- **Signal palette completeness** — health, danger, and alert states have assigned colors.
- **Accessibility section populated** — contrast ratio targets stated, not just "TBD."
- **Style-guide alignment** — palette mood matches style-guide tone registers.
- **Terminology compliance.**
- **Template text / TODOs.**

#### Design Signals
- **State-color ambiguity** — two visually similar colors assigned to different states.
- **Missing theme variants** — design doc describes factions/biomes/modes but no theme variants defined.
- **Accessibility gap** — no contrast ratios stated, or stated ratios below WCAG AA.

---

### ui-kit.md

#### Section Structure
Compare against `templates/ui-kit-template.md`. Required: Component Definitions, Component States, Typography, Iconography, Spacing & Layout Conventions, Animation & Transitions, Sound Feedback, Responsive & Resolution Scaling, Rules.

#### Mechanical Checks
- **Component state table complete** — every row has: State, Visual Treatment, Color Token, Example.
- **Color tokens reference color-system.md** — state table tokens exist in color-system.md. Flag missing tokens.
- **Sound feedback table present** — at least button click, panel open/close, and alert appear.
- **Typography scale defined** — heading sizes, body text, and label sizes stated with concrete values.
- **Spacing scale defined** — base unit stated (e.g., 4px).
- **Component coverage** — systems that surface player-visible information (from system designs) have corresponding UI components. Flag systems with player-facing data but no component.
- **Resource representation** — resources from `resource-definitions.md` have icon or display components.
- **Style-guide alignment** — animation timing matches style-guide motion principles.
- **Terminology compliance.**
- **Template text / TODOs.**
- **Scope guard** — flag if doc contains screen maps, scene hierarchies, modal graphs, or HUD layout. These belong in engine docs, not ui-kit.

#### Design Signals
- **Component gap** — system surfaces player-visible data but no ui-kit component exists for it.
- **Scope creep** — doc contains implementation-level UI structure (scene tree, node types, panel management).
- **Sound-feedback overlap** — sound definitions here conflict with or duplicate audio-direction.md categories.

---

### interaction-model.md

#### Section Structure
Compare against `templates/interaction-model-template.md`. Required sections:
- Selection Model (Selectable Entities, Selection Mechanics, Selection Persistence)
- Command Model
- Secondary Actions
- Drag Behaviors
- Interaction Patterns
- Modal vs Non-Modal
- Input Feedback
- Camera Interaction
- Accessibility
- Rules

#### Mechanical Checks
- **Selectable entities listed** — at least one entity type explicitly listed as selectable.
- **Selection mechanics concrete** — single/multi/drag-select behavior stated, not just "TBD."
- **Command model populated** — at least 3 concrete player commands described.
- **Interaction patterns present** — at least one full interaction sequence described (select → command → feedback).
- **Design doc alignment** — player verbs match design doc Player Verbs / Core Loop. Commands trace to system designs Player Actions.
- **UI-kit alignment** — interaction feedback references ui-kit component states (hover, selected, disabled). Flag if interaction-model assumes components ui-kit doesn't define.
- **Color-system alignment** — hover/selection/error colors reference color-system tokens.
- **No response definitions** — interaction-model defines what the player DOES. System responses belong in feedback-system.md. Flag any event-response coordination content.
- **Terminology compliance.**
- **Template text / TODOs.**

#### Design Signals
- **Missing player verb** — design doc lists a player verb with no corresponding interaction-model entry.
- **UI-kit gap** — interaction-model assumes a component (context menu, drag ghost, selection ring) not defined in ui-kit.
- **Boundary violation** — doc defines system responses instead of just player input behavior.

---

### feedback-system.md

#### Section Structure
Compare against `templates/feedback-system-template.md`. Required sections:
- Feedback Types (Action Confirmation, Action Failure, State Change, Warning/Escalation, Critical Alert, Selection/Hover, Sustained State)
- Timing Rules
- Priority & Stacking
- Cross-Modal Coordination
- Event-Response Table
- Rules

#### Mechanical Checks
- **Feedback types complete** — at least 5 of the 7 template types have substantive content.
- **Priority hierarchy stated** — explicit ordering of feedback types by priority.
- **Event-response table present** — at least 10 entries mapping game events to coordinated responses.
- **Event-response table columns complete** — every row has: Event, Visual, Audio, UI, Timing, Priority.
- **Cross-modal coordination present** — at least one concrete example of visual + audio + UI firing together.
- **Interaction-model alignment** — every player action type in interaction-model has a corresponding feedback type here.
- **Style-guide alignment** — visual feedback references style-guide animation timing and tone registers.
- **Color-system alignment** — feedback visual treatments reference color-system tokens.
- **Audio-direction alignment** — feedback audio categories exist in audio-direction sound categories.
- **No input definitions** — feedback-system defines system RESPONSES. Player input behavior belongs in interaction-model.md. Flag any input mapping content.
- **Terminology compliance.**
- **Template text / TODOs.**

#### Design Signals
- **Missing system coverage** — system produces events (from system designs) but no feedback-system entry exists.
- **Priority ambiguity** — two feedback types have the same priority level.
- **Boundary violation** — doc defines input behavior instead of system responses.
- **Audio-direction gap** — feedback references sound categories not defined in audio-direction.

---

### audio-direction.md

#### Section Structure
Compare against `templates/audio-direction-template.md`. Required sections:
- Audio Philosophy (Core Audio Identity, Audio as Information, Restraint Principle)
- Sound Categories
- Music Direction
- Silence & Space
- Feedback Hierarchy
- Asset Style Rules
- Accessibility
- Rules

#### Mechanical Checks
- **Audio philosophy concrete** — core audio identity stated in specific terms, not just "ambient."
- **Sound categories listed** — at least 4 categories (feedback, ambient, music, UI).
- **Music direction stated** — when music plays and what it communicates.
- **Feedback hierarchy present** — priority ordering of audio signals.
- **Feedback-system alignment** — feedback hierarchy matches feedback-system priority ordering. If audio-direction priority order conflicts with feedback-system, do not rewrite audio-direction priority content unless it is clearly a copied stale list; otherwise flag as user-pending.
- **UI-kit alignment** — component sound expectations here don't contradict ui-kit Sound Feedback section.
- **Style-guide alignment** — audio tone matches visual tone registers from style-guide.
- **Accessibility populated** — redundancy principle stated (no audio-only gameplay information).
- **No timing coordination** — audio-direction defines what the game SOUNDS like. When sounds fire and how they coordinate with visual/UI is in feedback-system.md. Flag coordination content.
- **Terminology compliance.**
- **Template text / TODOs.**

#### Design Signals
- **Tone mismatch** — audio philosophy doesn't match style-guide visual tone.
- **Category gap** — feedback-system references sound events with no corresponding audio-direction category.
- **Boundary violation** — doc defines when/how sounds coordinate with visual feedback instead of just audio character.

---

## Step 3 — Classify Issues

### Auto-Fixable (apply immediately)

Auto-fix may normalize:

| Category | Fix | Condition |
|----------|-----|-----------|
| **Missing sections** | Add section heading and minimal template stub only — do not fabricate section body content beyond the template scaffold | Section required by template and genuinely absent |
| **Missing table columns** | Add column headers to existing tables — only when the existing table is clearly intended to match the template table (same heading, same context). Do not mutate custom tables that serve a different purpose | Template has columns the doc doesn't |
| **Template text / TODOs** | Remove placeholder text in populated sections | Section has authored content beyond template markers |
| **Terminology drift** | Replace NOT-column terms with canonical terms | Used as authoritative terminology, not in examples/quotes |
| **Stale ADR references** | Update to current ADR status | ADR status changed since doc was last edited |
| **Token name normalization** | Normalize token names to consistent format | Inconsistent casing or naming convention within color-system |
| **Hex value normalization** | Normalize hex values to consistent format (#RRGGBB) | Mixed formats within same doc |
| **Duplicate entries** | Merge duplicate rows, keeping the more complete version — only when duplicates are mechanically equivalent. If duplicate rows differ semantically, flag as user-pending instead of merging | Same token, component, or event name appears twice |
| **Raw hex replacement** | Replace raw hex with token reference | Color-system defines a token for that exact hex value |

Auto-fix may **not** invent:
- New components, theme variants, or event-response entries
- New interaction behaviors or audio categories
- New state mappings without explicit upstream support
- Content for Empty sections — those are user-pending, not auto-fillable

### Mechanically Detected, User-Confirmed

| Category | Action |
|----------|--------|
| **Template defaults remaining** | Section still at template/default level. Report for human completion. |
| **Scope creep detected** | UI-kit contains screen maps or scene hierarchy. Report for relocation to engine docs. |
| **Boundary violation** | Interaction-model defines responses, or feedback-system defines inputs, or audio-direction defines timing coordination. Report for relocation. |
| **Component gap** | System surfaces player data but no ui-kit component exists. Report for human decision. |
| **Missing state-color mapping** | Entity states exist in state-transitions but have no color token. Report for human decision. |
| **Missing doc** | A target Step 5 doc does not exist. Report for seeding via bulk-seed-style. |
| **Priority hierarchy conflict** | Audio-direction priority order conflicts with feedback-system and is not clearly a stale copy. Report for human resolution. |

### Design Signals (for adversarial review)

These feed into `iterate-style`. Detected and reported, not resolved.

| Signal | Context |
|--------|---------|
| Tone mismatch | Visual tone and audio tone don't align |
| Priority conflict | Feedback-system and audio-direction disagree on priority ordering |
| Entity coverage gap | Entity types have no visual description in style-guide |
| Component gap | System surfaces player data with no ui-kit component |
| UI-kit scope creep | Doc contains implementation-level structure |
| Boundary violation | Doc content belongs in a different Step 5 doc |
| Pillar contradiction | Aesthetic pillars conflict with each other or design doc |
| Missing theme variants | Design doc factions/biomes exist but no color theme variants |
| Accessibility gap | No contrast ratios or redundancy principle stated |
| Cross-doc accessibility hole | Gameplay-critical info relies on a single channel (color-only, audio-only, or hover-only) |

## Step 4 — Apply Auto-Fixes

**Safety rules:**
- **When `--target` is set, only edit the targeted doc.** Cross-doc mismatches are flagged but other docs are not edited.
- **When `--target` is not set, edit all 6 docs.** Cross-doc auto-fixes are limited to normalization only (see auto-fix boundaries above). Invention of new content is never auto-fixed.
- **Never edit Step 1–4 docs.** Step 5 docs never auto-edit design-doc, system designs, architecture, reference docs, or engine docs. Flag mismatches for human resolution.
- **Never change design decisions.** Only fix how clearly they're expressed and how consistently they're reflected across the 6 docs.
- **Never relocate content across docs.** fix-style may identify misplaced content (boundary violations, scope creep) but must not move content between docs automatically. Flag for human relocation.
- **Authority hierarchy within Step 5:** style-guide → color-system → ui-kit. Interaction-model and feedback-system are peers. Audio-direction derives from feedback-system for priority hierarchy. On mismatch, the upstream doc is canonical.
- **No speculative fixes.** When multiple plausible interpretations exist, report instead of auto-fixing.

## Step 5 — Cross-Doc Pass

After all per-doc checks and fixes, run one cross-doc consistency pass:

1. **Style-guide → Color-system** — tone registers have corresponding palette shifts. Visual mood words match color temperature.
2. **Color-system → UI-kit** — component state table tokens exist in color-system. No raw hex values in ui-kit.
3. **Style-guide → UI-kit** — animation timing in ui-kit matches style-guide motion principles. Icon style matches style-guide iconography rules.
4. **Interaction-model → Feedback-system** — every player action type has a corresponding feedback type. No gaps.
5. **Feedback-system → Audio-direction** — priority hierarchy is consistent. Sound categories in feedback-system exist in audio-direction.
6. **Feedback-system → UI-kit** — feedback visual treatments reference components defined in ui-kit. Flag missing components.
7. **UI-kit ↔ Interaction-model** — interaction-model doesn't assume components ui-kit doesn't define. UI-kit doesn't define interaction behavior.
8. **Audio-direction → UI-kit** — component sounds in ui-kit don't contradict audio-direction category rules.
9. **All → Design doc** — aesthetic pillars, tone, player verbs, and failure philosophy are consistently reflected.
10. **All → State-transitions** — entity states are mapped to colors (color-system), visual states (ui-kit), and feedback triggers (feedback-system).
11. **Accessibility coherence** — visual warnings are not color-only (check color-system + ui-kit). Critical feedback has redundant channels (check feedback-system). Interaction cues are not hover-only (check interaction-model). Audio-only information is not gameplay-critical (check audio-direction).

Cross-doc pass results are:
- Auto-fixable alignment issues → applied (respecting `--target` scope and auto-fix boundaries)
- Design signals → reported for iterate-style

## Step 6 — Re-review and Iterate

After applying fixes, re-review. Continue iterating until:
- **Clean** — no issues remain.
- **Human-only** — only human-required issues and design signals remain.
- **Stable** — same issues persist across two consecutive passes. An issue is considered the same across passes if it has the same doc, category, and affected section or table.
- **Limit** — `--iterate N` reached.

## Step 7 — Report

```
## Fix-Style Summary

### Configuration
| Field | Value |
|-------|-------|
| Target | [all / specific doc] |
| Passes | N completed / M max [early stop: yes/no] |
| Auto-fixed | N issues |
| User-confirmed pending | N issues |
| Design signals | N issues |
| Final status | Clean / Human-only / Stable / Limit |

### Per-Doc Status
| Document | Health | Auto-fixed | User-pending | Design Signals | Status |
|----------|--------|-----------|-------------|----------------|--------|
| style-guide.md | N% weighted (Complete X, Partial Y, Empty Z) | N | N | N | Clean / Human-only / Missing |
| color-system.md | N% | N | N | N | Clean / Human-only / Missing |
| ui-kit.md | N% | N | N | N | Clean / Human-only / Missing |
| interaction-model.md | N% | N | N | N | Clean / Human-only / Missing |
| feedback-system.md | N% | N | N | N | Clean / Human-only / Missing |
| audio-direction.md | N% | N | N | N | Clean / Human-only / Missing |

### Auto-Fixes Applied
| # | Document | Category | What Changed |
|---|----------|----------|-------------|
| 1 | color-system.md | Hex normalization | Normalized #fff to #FFFFFF |
| 2 | ui-kit.md | Terminology | Replaced "worker" with "colonist" |
| ... | ... | ... | ... |

### User-Confirmed Actions Pending
| # | Document | Category | Action Required |
|---|----------|----------|----------------|
| 1 | ui-kit.md | Scope creep | Screen map section should move to engine UI doc |
| 2 | color-system.md | Missing state mapping | injury states from state-transitions have no color token |
| ... | ... | ... | ... |

### Design Signals (for iterate-style)
| # | Documents | Signal | Detail |
|---|----------|--------|--------|
| 1 | style-guide.md, audio-direction.md | Tone mismatch | Visual tone is "warm" but audio direction is "clinical" |
| 2 | interaction-model.md, ui-kit.md | Component gap | Interaction-model assumes context menu not in ui-kit |
| ... | ... | ... | ... |

### Cross-Doc Consistency
| Check | Result | Issues |
|-------|--------|--------|
| Style-guide → Color-system | N issues | ... |
| Color-system → UI-kit | N issues | ... |
| Interaction-model → Feedback-system | N gaps | ... |
| Feedback-system → Audio-direction | N issues | ... |
| All → State-transitions | N unmapped | ... |
| Accessibility coherence | N holes | ... |
```

Update each edited doc's `Last Updated` date and add **one** Changelog entry per doc per run (not per pass): `- YYYY-MM-DD: Mechanical cleanup (fix-style).` If multiple passes edited the same doc, collapse into a single entry.

## Rules

- **This skill is a formatter and linter, not a design reviewer.** It normalizes docs and detects signals. Design evaluation belongs to iterate-style.
- **Authority flows downstream within Step 5.** style-guide → color-system → ui-kit. Interaction-model and feedback-system are peers (input vs response). Audio-direction derives priority hierarchy from feedback-system. On mismatch, the upstream doc is canonical — but downstream issues may reveal upstream incompleteness rather than downstream drift. Report both directions; don't over-blame the downstream doc. Peer conflicts are reported, not auto-resolved, unless one side only contains stale copied terminology or reference formatting.
- **--target restricts edits, not reads.** When targeting one doc, all 6 docs are still read for cross-doc checks, but only the target is edited. Mismatches in other docs are flagged, not fixed.
- **Never change design decisions.** Auto-fixes clarify expression and fix consistency. They never alter what the visual/UX direction says.
- **Never edit Step 1–4 docs.** Step 5 docs never auto-edit design-doc, system designs, architecture, reference docs, or engine docs. Flag mismatches for human resolution.
- **Never relocate content across docs.** Boundary violations and scope creep are flagged for human relocation, not moved automatically.
- **Never invent content.** Auto-fix normalizes what exists. It does not create new components, theme variants, event-response entries, interaction behaviors, audio categories, or state mappings.
- **Missing docs are reported, not created.** If a Step 5 doc doesn't exist, report it and skip. Creation belongs to bulk-seed-style.
- **No speculative fixes.** When multiple plausible interpretations exist, report — do not auto-fix.
- **Design signals are detected, not resolved.** Tone mismatches, priority conflicts, and coverage gaps are reported for iterate-style — not acted on by this skill.
- **Terminology fixes respect context.** Only replace NOT-column terms when used as authoritative design terminology.
- **Boundary enforcement is mechanical.** If interaction-model contains system response content, or feedback-system contains input mapping, or audio-direction contains timing coordination — flag for relocation. Don't interpret whether the content is "close enough."
- **Scope guard for ui-kit is strict.** Components, component states, composition patterns, spacing conventions. Screen maps, scene hierarchies, modal graphs, and HUD layout are flagged for relocation to engine docs.
- **One changelog entry per doc per run.** Multiple passes that edit the same doc collapse into a single changelog entry.

# Document Authority

> **Rule:** When documents conflict, the higher-ranked document wins. Lower documents must conform to higher documents. Code must never "work around" higher-level intent.

## Precedence Chain (highest wins)

| Rank | Step | Document | Layer |
|------|------|----------|-------|
| 1 | S1 | [design/design-doc.md](design/design-doc.md) | Canon — core vision, non-negotiables |
| 2 | S5 | [design/style-guide.md](design/style-guide.md) | Canon — visual identity |
| 2 | S5 | [design/color-system.md](design/color-system.md) | Canon — color palette |
| 2 | S5 | [design/ui-kit.md](design/ui-kit.md) | Canon — UI components |
| 2 | S2 | [design/glossary.md](design/glossary.md) | Canon — terminology |
| 2 | S5 | [design/interaction-model.md](design/interaction-model.md) | Canon — interaction patterns |
| 2 | S5 | [design/feedback-system.md](design/feedback-system.md) | Canon — feedback coordination |
| 2 | S5 | [design/audio-direction.md](design/audio-direction.md) | Canon — audio direction |
| 3 | S6 | [inputs/action-map.md](inputs/action-map.md) | Canon — action IDs |
| 3 | S6 | [inputs/default-bindings-kbm.md](inputs/default-bindings-kbm.md) | Canon — keyboard/mouse bindings |
| 3 | S6 | [inputs/default-bindings-gamepad.md](inputs/default-bindings-gamepad.md) | Canon — gamepad bindings |
| 3 | S6 | [inputs/ui-navigation.md](inputs/ui-navigation.md) | Canon — focus flow |
| 3 | S6 | [inputs/input-philosophy.md](inputs/input-philosophy.md) | Canon — input principles |
| 4 | S3 | [design/architecture.md](design/architecture.md) | Canon — engineering conventions, structural constraints |
| 4 | S3 | [design/interfaces.md](design/interfaces.md) | Canon — system contracts |
| 4 | S3 | [design/authority.md](design/authority.md) | Canon — data ownership |
| 5 | S2 | design/systems/SYS-### | Canon — system designs |
| 5 | S3 | [design/state-transitions.md](design/state-transitions.md) | Canon — state machines |
| 6 | S3 | [reference/entity-components.md](reference/entity-components.md) | Reference — entity data shapes |
| 6 | S3 | [reference/resource-definitions.md](reference/resource-definitions.md) | Reference — resources and chains |
| 6 | S3 | [reference/signal-registry.md](reference/signal-registry.md) | Reference — signals and intents |
| 6 | S3 | [reference/balance-params.md](reference/balance-params.md) | Reference — tunable numbers |
| 6 | S3 | [reference/enums-and-statuses.md](reference/enums-and-statuses.md) | Reference — shared vocabulary |
| 7 | S8 | [phases/roadmap.md](phases/roadmap.md) | Scope — project roadmap |
| 7 | S9 | phases/PHASE-### | Scope — phase gates |
| 8 | S10 | slices/SLICE-### | Integration — vertical slice contracts |
| 9 | S11–12 | specs/SPEC-### | Behavior — atomic specs |
| 10 | S4 | engine/* | Implementation — engine constraints |
| 11 | S11–12 | tasks/TASK-### | Execution — implementation steps |
| — | Any | theory/* | Advisory only — no authority |
| — | Any | decisions/* | Pipeline influence — decision docs don't carry rank, but they drive changes to ranked docs through specific mechanisms. See **Decision Influence Model** below. |
| — | Any | decisions/review/* | Tooling — review findings trigger edits to ranked docs during iterate-* passes. |

---

## Decision Influence Model

Decision docs don't carry rank in the precedence chain, but they all drive changes to ranked documents through specific mechanisms. No ranked doc changes without a traceable decision path.

| Decision Doc | Influence Mechanism | What It Can Change | How |
|-------------|--------------------|--------------------|-----|
| **ADR-###** | Direct authorization | Any Rank 1–11 doc | The **only** way to change a higher-ranked doc from below. Accepted ADR authorizes the edit; the updated authoritative doc becomes the source of truth. The ADR records reasoning. |
| **KI-###** | Blocking | Downstream ranked docs that depend on the unresolved question | A KI with `Blocking: SLICE-009` prevents that slice's specs/tasks from proceeding. Resolution updates the authoritative doc (often via ADR). |
| **DD-###** | Scheduled correction | The ranked doc containing the compromised content | Payoff plan triggers a task/spec that corrects the ranked doc. Until then, the compromise is documented and accepted. |
| **PF-###** | Scope pressure | Phases, slices, specs (Rank 7–9) | Patterns (3+ reports) feed `/scaffold-revise-phases` and `/scaffold-revise-slices` as scope input. A pattern can add scope, reprioritize slices, or trigger new specs. |
| **XC-###** | Pipeline enforcement | Any ranked doc that failed a cross-cutting check | Decision-closure findings force TODOs to be resolved. Staleness findings force restabilization. Workflow findings force missing pipeline steps. |
| **Triage logs** | Planning changes | Specs, tasks (Rank 9, 11) | Upstream actions create, split, merge, reassign, or defer specs and tasks. Decisions that affect system designs or architecture produce ADR stubs. |
| **Revision logs** | Drift correction | Systems, references, engine docs, style docs (Rank 2, 5–6, 10) | Auto-updates fix stale references and alignments in ranked docs. Escalations require user decisions (which may produce ADRs). |
| **Code review logs** | Code + doc correction | Code files + engine docs + style docs (Rank 2, 10) | Accepted findings directly edit code. Engine doc drift detected during review feeds `/scaffold-revise-engine`. Style doc drift feeds `/scaffold-revise-style`. |
| **Review logs (iterate)** | Quality enforcement | The ranked doc being reviewed | Accepted issues are edited into the ranked doc. Consensus determines approval (Draft → Approved). |

**Key principle:** Decision docs create *pressure* on ranked docs to change, but ranked docs only actually change through: (a) an accepted ADR editing a higher-ranked doc, (b) a skill (fix/revise/iterate) editing the doc it's responsible for, or (c) direct user edit. Decision docs are the *reason* for the change, not the *authority* for it.

---

## Document Influence Map

This table defines what each document reads (influenced by) and what reads it (influences). Skills use this to determine context files when creating, reviewing, or revising documents. Theory docs are listed here so they get read when relevant — their advisory status doesn't mean they should be ignored.

| Document | Influenced By (reads these) | Influences (read by these) |
|----------|---------------------------|---------------------------|
| **design-doc.md** | (foundation — self-contained) | Everything. Every doc, every skill, every decision traces back here. |
| **style-guide.md** | design-doc, architecture (scene tree), engine UI doc, system designs | color-system, ui-kit, feedback-system, audio-direction, art skills, engine UI/post-processing/asset-import docs, tasks |
| **color-system.md** | design-doc, style-guide, state-transitions (state→color mapping) | ui-kit, feedback-system, art skills, engine UI doc, tasks |
| **ui-kit.md** | design-doc, style-guide, color-system, system designs (what info to surface), architecture (UI panel pattern), engine UI doc | feedback-system, interaction-model, engine UI/scene-architecture docs, tasks |
| **glossary.md** | design-doc | Every doc (terminology compliance). validate checks all docs against glossary NOT column. |
| **interaction-model.md** | design-doc, system designs, architecture, engine input doc, style-guide, color-system, ui-kit | feedback-system, input docs (action-map, bindings, navigation), engine input doc, specs, tasks |
| **feedback-system.md** | design-doc, system designs, interaction-model, style-guide, color-system, ui-kit, audio-direction, signal-registry, state-transitions, engine UI doc | audio-direction (priority coordination), engine UI/post-processing docs, specs, tasks |
| **audio-direction.md** | design-doc, style-guide, feedback-system (priority hierarchy), system designs | engine audio doc (if exists), audio skills, feedback-system (sound categories), tasks |
| **action-map.md** | design-doc, interaction-model | bindings (KBM, gamepad), ui-navigation, engine input doc, tasks |
| **default-bindings-kbm.md** | design-doc, action-map, input-philosophy | engine input doc, tasks |
| **default-bindings-gamepad.md** | design-doc, action-map, input-philosophy | engine input doc, tasks |
| **ui-navigation.md** | design-doc, interaction-model, action-map, engine UI doc | engine input doc, tasks |
| **input-philosophy.md** | design-doc, interaction-model | action-map, bindings, ui-navigation, specs |
| **architecture.md** | design-doc, system designs | interfaces, authority, all reference docs, all engine docs, specs, tasks, code review |
| **interfaces.md** | design-doc, system designs, architecture | signal-registry, engine coding/simulation-runtime docs, specs, tasks |
| **authority.md** | design-doc, system designs, architecture | entity-components, engine coding doc, specs, tasks |
| **systems/SYS-###** | design-doc, glossary | architecture, interfaces, authority, all reference docs, all Step 5 docs, engine docs, roadmap, specs, tasks |
| **state-transitions.md** | design-doc, system designs, architecture | enums-and-statuses, entity-components, feedback-system (state→response), specs, tasks |
| **entity-components.md** | architecture, authority (ownership), state-transitions | engine coding/save-load docs, specs, tasks, code review |
| **resource-definitions.md** | design-doc, system designs, architecture | style-guide, ui-kit, feedback-system, balance-params, engine data-pipeline doc, specs, tasks |
| **signal-registry.md** | architecture, interfaces, system designs | engine coding/scene-architecture/simulation-runtime docs, feedback-system, specs, tasks, code review |
| **balance-params.md** | design-doc, system designs, resource-definitions | specs, tasks, playtesting |
| **enums-and-statuses.md** | state-transitions, entity-components | engine coding doc, specs, tasks |
| **phases/roadmap.md** | design-doc, system designs, architecture, ADRs, playtest patterns | phases, revision loop |
| **phases/PHASE-###** | design-doc, system designs, architecture, roadmap, ADRs | slices, tasks |
| **slices/SLICE-###** | design-doc, system designs, architecture, interfaces, phases, ADRs | specs, tasks, revision loop |
| **specs/SPEC-###** | system designs, architecture, interfaces, authority, references, state-transitions, interaction-model, feedback-system, slices, ADRs, triage decisions | tasks, code review, completion tracking |
| **engine/coding-best-practices** | architecture, authority, interfaces, signal-registry, entity-components, enums-and-statuses | All other engine docs (convention source), tasks, code review |
| **engine/ui-best-practices** | style-guide, color-system, ui-kit, interaction-model, feedback-system, architecture, coding-best-practices, scene-architecture | tasks, code review |
| **engine/input-system** | interaction-model, action-map, bindings, ui-navigation, architecture, coding-best-practices | tasks, code review |
| **engine/scene-architecture** | architecture, interfaces, signal-registry, ui-kit, coding-best-practices | tasks, code review |
| **engine/simulation-runtime** | architecture, signal-registry, coding-best-practices | tasks, code review |
| **engine/save-load-architecture** | architecture, entity-components, coding-best-practices | tasks, code review |
| **engine/ai-task-execution** | architecture, signal-registry, coding-best-practices | tasks, code review |
| **engine/performance-budget** | design-doc, architecture | tasks, code review |
| **engine/data-and-content-pipeline** | architecture, resource-definitions, coding-best-practices | tasks, code review |
| **engine/localization** | glossary, style-guide, coding-best-practices | tasks, code review |
| **engine/post-processing** | style-guide, feedback-system, architecture | tasks, code review |
| **engine/asset-import-pipeline** | style-guide, color-system, ui-kit | tasks, code review |
| **engine/debugging-and-observability** | architecture, coding-best-practices | tasks, code review |
| **engine/build-and-test-workflow** | architecture | tasks, CI |
| **engine/implementation-patterns** | implementation experience, code review findings | tasks, code review |
| **tasks/TASK-###** | specs, architecture, interfaces, authority, all engine docs, references, slices, ADRs, triage decisions | code implementation, completion tracking, reference doc sync |
| **theory/*** | external knowledge, design experience | All creation and review skills (advisory context). Read during init-design, iterate-*, bulk-seed-*. Not authoritative but should not be ignored — they provide design rationale and anti-pattern warnings. |
| **ADR-###** | any conflicting docs, implementation discoveries | the authoritative doc it changes, all downstream docs, revise-* skills |
| **KI-###** | design/implementation contradictions | revise-* skills, blocks downstream work when marked Blocking |
| **DD-###** | intentional compromises | phase transitions (payoff triggers), revise-* skills |
| **PF-###** | playtester observations | revise-phases, revise-slices (patterns feed scope) |
| **XC-###** | validate checks | fix-cross-cutting, authoritative docs (via resolution) |

---

## Document Table — 5W+1H

### Rank 1 — Vision

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **design-doc.md** | Core vision, loops, pillars, governance mechanisms, non-negotiable design rules | Defines WHAT the game IS — everything else flows from this | Everyone | init-design, revise-design | Step 1 | Every skill reads it. Every conflict traces back here. The highest authority for player-facing intent. |

### Rank 2 — Player Experience Definition

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **style-guide.md** | Visual identity, rendering style, lighting model, animation style, iconography | Defines what the game LOOKS like | Art skills, UI skills, engine UI doc | seed style, revise-style | Step 5 | Visual decisions that all presentation must follow. |
| **color-system.md** | Color palette, semantic colors, accessibility rules | Defines the color LANGUAGE | Art skills, UI skills | seed style, revise-style | Step 5 | Every color choice traces back here. |
| **ui-kit.md** | UI component definitions, panel patterns, layout rules, theme conventions | Defines how UI is STRUCTURED | Engine UI doc, task implementations | seed style, revise-style | Step 5 | Governs all UI implementation. |
| **glossary.md** | Canonical terminology, NOT-column forbidden synonyms | Defines what things are CALLED | Every skill (terminology compliance) | seed systems | Step 2 | All docs must use canonical terms. validate checks compliance. |
| **interaction-model.md** | Selection model, command model, drag behaviors, input feedback, layer navigation, camera interaction | Defines how the player INTERACTS with the game — input→intent mapping | Input docs, engine input doc, UI skills, specs | seed style, revise-style | Step 5 | Governs what inputs implement and what UI presents. Scoped to player input, not system response. |
| **feedback-system.md** | Feedback types, timing rules, priority/stacking, cross-modal coordination, event-response table | Defines how the SYSTEM RESPONDS to events and player actions — coordinated visual + audio + UI | All presentation docs, engine docs, specs, tasks | seed style, revise-style | Step 5 | Governs the "feel" layer. Bridges interaction-model (what player does) and presentation docs (what player sees/hears). |
| **audio-direction.md** | Audio philosophy, sound categories, music direction, silence rules, asset style rules | Defines what the game SOUNDS like | Audio skills, engine docs, feedback-system | seed style, revise-style | Step 5 | Governs all audio implementation. Sound priority coordination is in feedback-system.md. |

### Rank 3 — Input Bindings

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **action-map.md** | Canonical action IDs and their purposes | Maps player VERBS to action names | Engine input doc, binding docs | seed input | Step 6 | Source of truth for what actions exist. |
| **default-bindings-kbm.md** | Keyboard/mouse binding assignments | Concrete KEY → ACTION mapping | Engine input doc, tasks | seed input | Step 6 | Implementation reads this to wire InputMap. |
| **default-bindings-gamepad.md** | Gamepad binding assignments | Concrete BUTTON → ACTION mapping | Engine input doc, tasks | seed input | Step 6 | Same as KBM for gamepad. |
| **ui-navigation.md** | Focus flow, tab order, navigation rules | How the player NAVIGATES UI without mouse | Engine UI doc, tasks | seed input | Step 6 | Governs focus/navigation implementation. |
| **input-philosophy.md** | Input design principles, accessibility goals | WHY inputs are designed the way they are | All input docs, specs | seed input | Step 6 | Advisory within the input layer — principles that govern binding choices. |

### Rank 4 — Technical Enforcement

Architecture, interfaces, and authority are all the same category: technical enforcement layers that constrain implementation of design intent. They should never override design intent — if they conflict with Rank 1-2 docs, file an ADR to change the enforcement layer, not the design.

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **architecture.md** | Scene tree, dependency graph, tick order, simulation update semantics, data flow rules, forbidden patterns, identity model, boot order, failure/recovery patterns, code patterns | Defines HOW systems connect — the structural constraints that implementation must follow | Every technical skill, all system/reference/engine docs | seed references, fix-references, revise-references | Step 3 | Constrains implementation of design. If architecture says "no cross-system mutation," implementation must comply. If design requires behavior that conflicts, file an ADR to update architecture — not the other way. |
| **interfaces.md** | Cross-system contracts: source, target, data, direction, realization path, timing, failure guarantees | Defines WHAT flows between systems and under what guarantees | System designs, signal-registry, engine docs, specs | seed references, revise-references | Step 3 | Canonical for contracts. signal-registry conforms to this. |
| **authority.md** | Single-writer ownership table: variable, owning system, write mode, authority type, persistence owner, readers, cadence | Defines WHO WRITES each piece of game data | Entity-components, system designs, engine docs, specs | seed references, revise-references | Step 3 | Canonical for ownership. entity-components derives from this. |

### Rank 5 — System Behavior

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **systems/SYS-###** | Per-system: purpose, simulation responsibility, player actions, system resolution, owned state, dependencies, consequences, state lifecycle, edge cases | Defines WHAT each system owns and does — player-visible behavior only | Authority, interfaces, references, specs, tasks | seed systems, revise-systems | Step 2 | Source of truth for individual system behavior. Specs derive from these. |
| **state-transitions.md** | State machines: states, transitions, triggers, timing, authorities, invariants, illegal transitions | Defines VALID STATES and how entities move between them | Entity-components, enums, system designs, specs | seed references, revise-references | Step 3 | Canonical for state names. enums-and-statuses conforms to this. |

### Rank 6 — Reference Data

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **entity-components.md** | Entity data shapes: fields, types, components, authority, cadence, persistence | Defines the DATA SHAPE of every entity | Engine docs, specs, tasks | seed references, revise-references | Step 3 | Implementation reads this for struct/class definitions. Authority column derived from authority.md. |
| **resource-definitions.md** | Resources: tiers, categories, production chains, stations, fungibility, storage types | Defines WHAT RESOURCES exist and how they transform | System designs, specs, tasks | seed references, revise-references | Step 3 | Implementation reads this for resource handling. |
| **signal-registry.md** | Signals and intents: names, levels, payloads, emitters, consumers, delivery expectations | Defines EVERY cross-system notification and request | Engine docs, architecture signal wiring, specs, tasks | seed references, revise-references | Step 3 | Implementation reads this for signal wiring. Conforms to interfaces.md. |
| **balance-params.md** | Tunable numbers: parameter, type, value, unit, range, system, dependencies | Defines EVERY gameplay-affecting number | Specs, tasks, playtesting | seed references, revise-references | Step 3 | Implementation reads this for constants. Playtesting tunes values. |
| **enums-and-statuses.md** | Shared cross-system vocabulary: states, meanings, used by, owning authority, source of truth | Defines SHARED STATE TERMS used across multiple systems | System designs, entity-components, state-transitions | seed references, revise-references | Step 3 | Prevents vocabulary drift. Conforms to state-transitions.md. |

### Rank 7 — Scope

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **phases/roadmap.md** | Vision checkpoint, phase overview, capability ladder, system coverage, phase boundaries, transition protocol | Defines the PROJECT PLAN from start to ship | Phases, revise-roadmap, revise-phases | new-roadmap, revise-roadmap | Step 8 | Controls phase sequencing. Updated after each phase completes. |
| **phases/PHASE-###** | Phase scope gates: goal, capability unlocked, in/out scope, entry/exit criteria, systems covered | Defines WHEN behavior gets built and what milestone it proves | Slices, roadmap | seed phases, revise-phases | Step 9 (planning) | Controls implementation order. Only one phase is Approved at a time. |

### Rank 8 — Integration

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **slices/SLICE-###** | Vertical slice contracts: goal, proof value, integration points, done criteria, specs included, tasks table | Defines WHAT end-to-end chunk to build and what it proves | Specs, tasks, revise-slices | seed slices, revise-slices | Step 10 (planning) | Organizes implementation into provable vertical chunks. Only one slice is Approved at a time per phase. |

### Rank 9 — Behavior Specs

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **specs/SPEC-###** | Atomic behavior descriptions: acceptance criteria, preconditions, postconditions, systems involved | Defines WHAT the system must DO — testable behavior | Tasks, engine docs | seed specs, triage-specs | Step 11 (planning) | Tasks are derived from these. Describes final product behavior. |

### Rank 10 — Engine Constraints

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **engine/[prefix]-coding-best-practices.md** | C++/scripting boundary, naming, signals, lifetime, serialization, testing, allowed/forbidden patterns | Defines HOW to write code correctly in this engine | Tasks, code review | seed engine, revise-engine | Step 4 | Every code change must follow these conventions. Convention source for all engine docs. |
| **engine/[prefix]-ui-best-practices.md** | UI rendering approach, themes, layout, focus, scaling, performance | Defines HOW to build UI correctly | Tasks, code review | seed engine | Step 4 | Every UI implementation follows these rules. |
| **engine/[prefix]-input-system.md** | Input routing, device handling, remapping, pause behavior | Defines HOW input is handled at the engine level | Tasks | seed engine | Step 4 | Input implementation follows these patterns. |
| **engine/[prefix]-scene-architecture.md** | Scene tree patterns, lifecycle, pooling, singleton policy, communication paths | Defines HOW scenes and nodes are structured | Tasks, code review | seed engine | Step 4 | Every scene/node decision follows these rules. |
| **engine/[prefix]-performance-budget.md** | Frame/memory/render budgets, profiling, escalation criteria | Defines PERFORMANCE LIMITS code must respect | Tasks, code review | seed engine | Step 4 | Budget violations are bugs. |
| **engine/[prefix]-simulation-runtime.md** | Tick orchestration, fixed/variable step, queued work, pause/speed | Defines HOW the simulation loop executes | Tasks, code review | seed engine | Step 4 | Translates architecture.md timing rules into engine implementation. |
| **engine/[prefix]-save-load-architecture.md** | Serialization boundaries, entity restoration, handle rebind, versioning | Defines HOW live simulation state is persisted and restored | Tasks, code review | seed engine | Step 4 | Every save/load decision follows these patterns. |
| **engine/[prefix]-ai-task-execution.md** | Task reservation lifecycle, interruption, stale-handle cleanup, arbitration | Defines HOW AI task selection and execution work at the engine level | Tasks, code review | seed engine | Step 4 | Task/reservation implementation follows these patterns. |
| **engine/[prefix]-data-and-content-pipeline.md** | Content vs runtime boundary, definition loading, ID mapping, validation | Defines HOW authored content flows into runtime | Tasks, code review | seed engine | Step 4 | Content loading and validation follows these rules. |
| **engine/[prefix]-localization.md** | Translation keys, tr() usage, CSV pipeline, formatting, fallback | Defines HOW player-visible text is translated | Tasks, code review | seed engine | Step 4 | Every string follows these conventions. |
| **engine/[prefix]-post-processing.md** | Effects, cost limits, readability safeguards, overlay interaction | Defines HOW visual effects are applied | Tasks, code review | seed engine | Step 4 | Post-processing implementation follows these rules. |
| **engine/[prefix]-asset-import-pipeline.md** | Import presets, source vs runtime boundary, data table import | Defines HOW assets flow from source to engine | Tasks | seed engine | Step 4 | Asset import follows these rules. |
| **engine/[prefix]-debugging-and-observability.md** | Overlays, event tracing, state inspection, [DIAG] warnings | Defines HOW to debug the simulation | Tasks, code review | seed engine | Step 4 | Debugging and diagnostics follow these patterns. |
| **engine/[prefix]-build-and-test-workflow.md** | Build configurations, test framework, CI/headless testing | Defines HOW to build and test the project | Tasks, CI | seed engine | Step 4 | Build and test pipeline follows these rules. |
| **engine/implementation-patterns.md** | Project-specific patterns: problem, when to use, structure, anti-pattern | Records HOW specific implementation challenges were solved | Tasks, code review | Grows during implementation | Implementation | Prevents repeating solved problems. Not pre-filled — grows from experience. |

### Rank 11 — Implementation Steps

| Doc | What | Why | Who reads | Who writes | When created | How it's used |
|-----|------|-----|-----------|------------|-------------|---------------|
| **tasks/TASK-###** | Implementation steps: objective, files touched, acceptance criteria, dependencies | Defines HOW to build a specific piece of behavior | Developers, code review | seed tasks, triage-tasks | Step 12 (planning) | Must follow engine constraints (Rank 10), specs (Rank 9), and everything above. |

### Unranked — Advisory, Decisions & History

These documents do not appear in the rank chain, but decision docs actively drive changes to ranked documents. See the **Decision Influence Model** above for the full mechanism table.

| Doc | What | Why | How it's used |
|-----|------|-----|---------------|
| **theory/*** | Game design principles, UX heuristics, architecture patterns | Provides CONTEXT for decisions — never dictates them | Read when creating/reviewing docs. Never overrides any ranked document. |
| **decisions/architecture-decision-record/ADR-###** | Why a decision was made, what changed, what alternatives were rejected | **The only mechanism that can change a higher-ranked doc from below.** Accepted ADR authorizes the edit; updated authoritative doc becomes source of truth. | Filed when implementation conflicts with design, contracts change, or lower docs need to deviate from higher docs. |
| **decisions/known-issues/KI-###** | TBDs, gaps, conflicts, ambiguities | Tracks UNRESOLVED QUESTIONS | Read by revise-* skills as drift signals. Resolution updates authoritative docs. |
| **decisions/design-debt/DD-###** | Intentional compromises with payoff plans | Tracks ACCEPTED SHORTCUTS | Read at phase boundaries. Payoff triggers spec/task creation. |
| **decisions/playtest-feedback/PF-###** | Playtester observations and patterns | Records PLAYER BEHAVIOR | Patterns (3+ reports) feed revise-phases, revise-slices, and revise-style as scope input. |
| **decisions/cross-cutting-finding/XC-###** | Cross-document integrity issues from validate | Tracks PIPELINE HEALTH | Read by fix-cross-cutting. Resolution updates authoritative docs. |
| **decisions/code-review/** | Adversarial code review session logs | Records CODE QUALITY findings | Engine doc drift detected here feeds revise-engine. Style doc drift feeds revise-style. |
| **decisions/revision-log/** | Revision session records | Records DRIFT DETECTION and resolution | Baseline timestamps used by subsequent revision runs. |
| **decisions/triage-log/** | Triage session decision records | Records PLANNING DECISIONS | Upstream actions feed revise-* skills. |
| **decisions/review/*** | Adversarial review logs from iterate-* skills | Records REVIEW FINDINGS | Freshness checked by validate. Consensus determines doc approval. |

---

## Conflict Resolution

When two documents at the same rank conflict:
- **Same layer** (e.g., two Rank 2 docs): resolve based on which doc is more specific to the question. Style-guide wins on visual identity, glossary wins on terminology, interaction-model wins on player input behavior, feedback-system wins on system response coordination (timing, priority, cross-modal), audio-direction wins on sound character and music, ui-kit wins on component structure, color-system wins on color meaning.
- **Within Rank 4** (technical enforcement): architecture.md wins on structural rules, timing model, data flow, identity, and boot order. interfaces.md wins on contract semantics (direction, timing, realization path, failure guarantees). authority.md wins on ownership and write responsibility. If two Rank 4 docs conflict outside their domains, file an ADR.
- **Within Rank 10** (engine): coding-best-practices wins on conventions that other engine docs reference (naming, signals, error handling, language boundary). For domain-specific conflicts (UI vs input, save-load vs simulation-runtime), the more specific doc wins for its domain.
- **Cross-layer at same rank**: file an ADR — the conflict indicates a design gap.

When a higher-ranked document conflicts with a lower-ranked one:
- The higher-ranked document wins. Always.
- The lower document must be updated to conform.
- If the lower document's content is actually correct and the higher is wrong, file an ADR to change the higher document first — never silently override.

## Rules

1. **No work-arounds.** If code would violate a higher-authority document, the code is wrong, not the document. Raise a decision (ADR) to change the document instead.
2. **No implicit overrides.** A lower document cannot silently redefine something from a higher document. Conflicts must be resolved explicitly via an ADR.
3. **Architecture constrains implementation, not design intent.** architecture.md (Rank 4) defines engineering structural constraints. Systems, references, and engine docs must conform to architecture rules. But if design intent (Rank 1-2) requires behavior that conflicts with architecture, file an ADR to update architecture — architecture adapts to design, not the other way.
4. **Engine adapts to design.** The `engine/` layer describes *how* to implement, never *what* to implement. If an engine constraint conflicts with design intent, file an ADR.
5. **Tasks follow engine constraints.** Tasks (Rank 11) must respect engine conventions (Rank 10). A task that violates an engine coding standard, performance budget, or scene architecture rule is wrong.
6. **Specs require behavior, engine constrains implementation strategy.** Specs (Rank 9) outrank engine docs (Rank 10) — behavior wins over feasibility until an ADR says otherwise. But engine docs are not advisory: they define real constraints that implementation must respect. When a spec requires behavior that an engine doc says is unsafe, too expensive, or violates runtime rules, architecture and ADRs resolve the conflict. Neither side is silently dropped.
7. **Theory is advisory.** Documents in `theory/` inform decisions but never dictate them. They carry no authority.
8. **Decision docs drive change, ranked docs hold truth.** All decision docs (ADRs, KIs, DDs, PFs, XCs, triage/revision/code-review logs) create pressure on ranked docs to change — through authorization (ADRs), blocking (KIs), scheduled correction (DDs), scope pressure (PFs), enforcement (XCs), or drift correction (revision logs). But ranked docs only change through accepted ADRs, pipeline skills, or direct user edits. Once changed, the ranked doc is the source of truth — read the doc for current state, read the decision doc for why it changed.
9. **IDs are stable.** Renaming a document does not change its authority rank — the rank is determined by its directory and type, not its filename.

## Deprecation

When a document is no longer active (system removed, spec superseded, phase cancelled):

1. Set Status to `Deprecated`.
2. Add `> **Superseded by:** [replacement doc or "N/A"]` to the blockquote header.
3. Keep the document in its directory and index — IDs are permanent.
4. Review skills flag references to deprecated documents as warnings.
5. To deprecate, file an ADR explaining why and update the ADR's Updated Documents table.

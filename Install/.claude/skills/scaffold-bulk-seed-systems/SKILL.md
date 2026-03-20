---
name: scaffold-bulk-seed-systems
description: Read the design doc, seed the glossary with key terms, and bulk-create system design stubs from simulation responsibilities. Uses design invariants, control model, system domains, and simulation depth to propose systems by ownership — not raw verbs. Audits for overlap, missing coverage, and invariant conflicts before creation.
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Seed Systems from Design Doc

Read the completed design doc and use it to seed the glossary and bulk-create system design files: **$ARGUMENTS**

Systems are the simulation layer — they own player-visible state and behavior. This skill proposes systems from **simulation responsibilities and owned player-facing concerns**, not from raw verbs, UI surfaces, or implementation details.

## Prerequisites

1. **Read the design doc** at `design/design-doc.md`.
2. **Verify Step 1 pipeline completed.** The design doc should have completed the Step 1 stabilization loop: fix and iterate logs exist in `scaffold/decisions/review/`, and the design doc has substantive content (not template defaults). If no review logs exist and the doc is mostly placeholders, stop: "Run the Step 1 pipeline (init → fix → iterate → validate) before seeding systems."
3. **Verify design doc health.** The following sections must have substantive content (not TODO/placeholder):

   **Required (FAIL if missing):**
   - Core Fantasy
   - Core Loop
   - Player Control Model
   - Player Verbs
   - Design Invariants
   - Major System Domains

   **Strongly recommended (WARN if missing):**
   - Core Pillars
   - Secondary Loops
   - Player Mental Model
   - Simulation Depth Target
   - Design Boundaries
   - Content Structure
   - Decision Types
   - Failure Philosophy

4. **Read supporting context:**
   - `design/glossary.md` (if exists) — avoid duplicating existing terms
   - `design/architecture.md` (if exists) — detect conflicts with existing architecture decisions
   - `decisions/known-issues.md` (if exists) — constraints that affect system scope
   - `decisions/playtest-feedback.md` (if exists) — playtest patterns may affect system scope
   - `doc-authority.md` — document authority ranking and influence map
   - Accepted ADRs — decisions that may have changed system boundaries:
     - `ADR-001-traits-as-behavioral-drivers` — affects colonist/actor system design
     - `ADR-002-satisfaction-coordinator-pattern` — affects needs/mood system boundaries
     - `ADR-003-rate-multipliers-deferred` — defers rate tuning from system scope
     - `ADR-004-manual-tick-orchestration` — constrains simulation tick ownership
     - `ADR-005-flat-scene-tree` — constrains scene/architecture structure
     - `ADR-007-natural-terrain-as-room-boundary` — affects room/zone system boundaries
     - `ADR-008-work-ai-continuity-pre-pass` — affects work AI system design
     - `ADR-010-berry-bushes-as-harvestable-food-source` — affects resource/food system scope
     - `ADR-011-tile-layer-stacking` — affects world/terrain system design
     - `ADR-012-task-group-skill-schedule-rework` — affects task system design
     - `ADR-013-two-actor-medical-task-model` — affects medical/task system design
     - `ADR-014-medical-task-per-colonist-granularity` — affects medical/task system granularity
     - `ADR-016-utility-based-intent-resolution` — affects AI/decision system design
     - `ADR-017-hybrid-work-discovery-model` — affects work AI discovery boundaries
     - `ADR-018-auto-generated-zone-model` — affects zone system design
     - `ADR-022-data-driven-game-economy` — affects resource/economy system design
     - `ADR-024-encyclopedia-panel` — affects UI/oversight system scope
     - `ADR-025-ui-shared-style-constants` — affects UI layer boundary checks
     - `ADR-029-generational-handles-dynamic-storage` — affects entity handle architecture

## Phase 1 — Seed Glossary

1. **Read** `design/glossary.md` (create if it doesn't exist).
2. **Extract candidate terms** from the design doc. Look for:
   - Game-specific nouns (entities, locations, resources, mechanics)
   - Terms that appear multiple times with a consistent meaning
   - Terms that could be confused with synonyms (these need a NOT column entry)
   - Terms from Design Invariants (invariant ShortNames should be glossary-referenceable)
3. **Present proposed terms as a batch confirmation.** Include the Authority and Criticality columns introduced in the glossary format:

   ```
   ## Proposed Glossary Terms

   | # | Term | Definition | NOT (suggested) | Authority | Criticality | Source Section |
   |---|------|-----------|-----------------|-----------|-------------|---------------|
   | 1 | Colonist | An autonomous agent in the colony | Settler, Worker, Unit | design-doc | Core | Core Fantasy |
   | 2 | Blueprint | A placed but unbuilt structure | Plan, Ghost | design-doc | Shared | Core Loop |

   **Options:** Confirm all / Edit specific rows by # / Reject specific rows by # / Add missing terms
   ```

   - **Authority** at this stage is always `design-doc` (the only source). Later steps may shift authority to system docs or reference docs via `/scaffold-sync-glossary`.
   - **Criticality**: Core for terms referenced by Design Invariants or cross-system mechanics; Shared for terms used across multiple system domains; Local for single-domain terms.

4. **Write confirmed terms** into the glossary table with all five columns (Term, Definition, NOT, Authority, Criticality), preserving alphabetical order.

## Phase 2 — Propose System Domains

### 2a. Analyze design inputs

Read these design doc sections systematically to identify simulation responsibilities:

| Design Input | What it reveals about systems |
|-------------|-------------------------------|
| **Major System Domains** | Explicitly named gameplay domains — strongest signal for system candidates |
| **Core Loop** | Each step implies state ownership — who tracks progress through the loop? |
| **Secondary Loops** | Longer cycles that wrap the core loop — may imply additional systems or extend existing ones |
| **Player Verbs** | Actions the player performs — group by shared simulation responsibility, not one verb per system |
| **Player Control Model** | What the player directly/indirectly/never controls — shapes system boundaries |
| **Content Structure** | Content categories that need runtime management (resources, structures, events) |
| **Failure Philosophy** | What can go wrong — implies damage, health, morale, or consequence tracking systems |
| **Decision Types** | What kinds of decisions exist — implies the state systems must expose for those decisions |
| **Simulation Depth Target** | What is simulated vs deliberately NOT simulated — prevents over-scoping systems |

### 2b. Propose systems by simulation responsibility

For each proposed system, define:

| Field | What to fill |
|-------|-------------|
| **Name** | Concise noun-based: "Construction", "Colony Needs", "Work AI" |
| **Purpose** | One-line: what player-visible behavior this system owns |
| **Simulation responsibility** | What state this system uniquely owns and updates |
| **Player-facing concern** | What the player sees, decides, or reacts to because of this system |
| **Likely dependencies** | Systems this one requires to function (upstream) |
| **Likely downstream effects** | Systems this one affects or feeds state to |
| **Likely out of scope** | Adjacent concerns this system explicitly does NOT own — name the system that does if possible |
| **Design constraints** | Any Design Invariants, Boundaries, or Control Model rules that constrain this system |

**Grouping heuristic:** Systems should be defined by *what state they own*, not by *what verbs the player uses*. Multiple verbs often map to one system (build/place/demolish → Construction). One verb may touch multiple systems (assign colonist → Work AI + Task System).

### 2b-ii. Check system category coverage

Evaluate whether the proposed systems cover the major simulation categories relevant to the game. Categories are a coverage heuristic, not a forced structure — not every game needs every category, but missing a needed category is a likely design gap.

| Category | What it covers | Example systems |
|----------|---------------|-----------------|
| **Actors** | Autonomous agents or player-controlled entities that act in the world | Colonist AI, Creature AI, Faction Agents |
| **World State** | Persistent world conditions, terrain, weather, zones, hazards, environmental simulation | Terrain, Weather, Region Instability |
| **Resources & Economy** | Production, storage, transfer, consumption, markets, logistics | Inventory, Resource Flow, Trade |
| **Tasks & Coordination** | Assignment, prioritization, work routing, scheduling, queues | Task System, Work Assignment, Job Arbitration |
| **Construction & Transformation** | Building, crafting, upgrading, demolition, world modification | Construction, Crafting, Terraforming |
| **Conflict & Consequences** | Damage, combat, injury, death, failure, collapse, recovery | Combat, Health, Incident Resolution |
| **Progression & Meta** | Unlocks, research, long-term advancement, reputation, campaign state | Research, Tech Progression, Faction Standing |
| **Events & Pressure** | External events, incidents, crises, escalation, pacing pressure | Event System, Raid Pressure, Disaster System |
| **Player Oversight** | Gameplay-facing state that supports decision-making — alerts, summaries, surfaced priorities | Alerts, Colony Status, Risk Tracking |

**Rules:**
- Categories are coverage heuristics, not required one-to-one systems. One system may cover multiple categories. Multiple systems may exist within one category.
- Only include categories relevant to the game's design. Do not force a category if the design doc clearly excludes it (check Design Boundaries and Simulation Depth Target).
- If a core loop step or major mechanic implies a category with no owning system, flag a coverage gap.

### 2c. Audit the proposal

Before presenting to the user, run these checks:

**Overlap detection** — do any two proposed systems appear to own the same state or concern? If "Colonist AI" and "Work Assignment" both claim to own task selection, flag the overlap and suggest merge or boundary clarification.

**Coverage gaps** — ensure every Core Loop step is supported by at least one system (multiple steps may map to the same system). Does every player verb have a system that enables it? Does every content category have a system that manages it? Flag uncovered areas.

**Category coverage** — which relevant simulation categories (from 2b-ii) are represented by proposed systems, and which appear missing? Flag categories the design implies but no system covers.

**Invariant conflicts** — does any proposed system imply a mechanic that violates a Design Invariant or Design Boundary? Example: if Invariant says "no direct control" but a proposed system's purpose implies direct unit commands, flag the conflict.

**Authority check** — ensure each piece of gameplay state has a single owning system responsible for updating it. If two proposed systems both claim write authority over the same state (e.g., both update mood), flag the conflict and suggest which one should own it.

**Granularity check** — if multiple proposed systems operate on the same entity type and share lifecycle/state transitions, consider merging them. Example: ColonistMovement + ColonistWork + ColonistNeeds may be one ColonistSimulation system, not three.

**Layer boundary check** — is any proposed system actually a presentation concern (UI rendering, HUD layout), input concern (key bindings, controller mapping), or engine concern (scene management, performance)? If so, flag it: "This may belong to Step 4 (Engine), Step 5 (Visual/UX), or Step 6 (Input) rather than Step 2 (Systems)."

**Scope check** — is the total system count reasonable? Prefer broad, responsibility-based systems over narrow feature slices. For many games, 8–15 systems is a healthy early draft. Simulation-heavy games may need more, but if exceeding ~20, verify you are not splitting by feature instead of ownership.

### 2d. Present for confirmation

```
## Proposed Systems

| # | Name | Purpose | Owns | Interacts With | Constraints |
|---|------|---------|------|---------------|-------------|
| 1 | Construction | Manages structure placement, building progress, and demolition | Build state, blueprints | Resources, Map, Work AI | Invariant: IndirectControl |
| 2 | Colony Needs | Tracks colonist vital needs and satisfaction | Need levels, mood | Colonist AI, Resources, Alerts | Boundary: no micromanagement |
| ... | ... | ... | ... | ... | ... |

### Audit Results
- **Overlaps detected:** [list or "None"]
- **Coverage gaps:** [list or "None"]
- **Category coverage:** Covered: [list]. Missing: [list or "None — all relevant categories represented"]
- **Invariant conflicts:** [list or "None"]
- **Authority conflicts:** [list or "None — each state has a single owner"]
- **Granularity concerns:** [list or "None"]
- **Layer boundary concerns:** [list or "None"]
- **System count:** N (target: 8–20 for this game's simulation depth)

**Options:** Confirm all / Merge # and # / Split # / Rename # / Remove # / Add missing system
```

Wait for user confirmation before creating any files.

## Phase 3 — Create System Stubs

For each confirmed system:

1. **Read the system template** at `scaffold/templates/system-template.md`.
2. **Assign the next sequential SYS-### ID** (starting from SYS-001 or the next available).
3. **Create the file** at `design/systems/SYS-###-name_draft.md`:
   - Replace `SYS-###` with the actual ID
   - Replace `[System Name]` with the confirmed name
   - **Write substantive content** for the 8 pre-fill sections listed below. "Pre-fill" means writing real prose derived from the design doc analysis in Phase 2 — not copying the template HTML comments, not writing TODO, not leaving placeholders. Every pre-filled section must contain authored content that a downstream reviewer could evaluate.

   | Section | What to write | Minimum content |
   |---------|--------------|-----------------|
   | **Purpose** | 1-2 sentences describing what player-visible behavior this system owns, derived from the confirmed proposal | Must be a complete sentence, not a fragment or TODO |
   | **Simulation Responsibility** | What state this system uniquely owns and updates — the reason this system exists as a separate entity | 2-3 sentences explaining what this system simulates and why no other system can own it |
   | **Player Intent** | Bullet list of what the player is trying to accomplish when engaging with this system, derived from player verbs and the control model | At least 3 bullet points |
   | **Design Constraints** | Invariants, boundaries, anchors, and control model rules that constrain this system — referenced by name from the design doc | At least 1 named constraint with explanation of how it applies |
   | **Owned State** | Table of gameplay-facing state this system exclusively manages, derived from design doc content categories, entities, and resources. Gameplay state only — not caches, scene nodes, engine objects, or data-structure choices | At least 2 state entries in the table with Description and Persistence columns filled |
   | **Upstream Dependencies** | Table of systems this one requires to function, with what each provides — derived from the "Likely dependencies" column | At least 1 entry if dependencies exist, or explicit "None — this system has no upstream dependencies" |
   | **Downstream Consequences** | Table of systems this one feeds state to, with what each receives — derived from the "Likely downstream effects" column | At least 1 entry if downstream effects exist, or explicit "None — this system does not feed other systems" |
   | **Non-Responsibilities** | Bullet list of adjacent concerns this system explicitly does NOT own, naming the system that does where possible | At least 2 bullet points |

   **Pre-fill quality standard:** If a downstream reviewer reads only the pre-filled sections, they should understand what this system does, what it owns, what constrains it, and what it does NOT do. A file where every pre-filled section is a single generic sentence or a rephrased template prompt has failed the pre-fill — go back to the design doc analysis and write specific content.

   - After the authored content in each pre-filled section, append `<!-- SEEDED: derived from design doc. Verify and expand. -->` so reviewers know what was inferred vs authored.
   - Remove the template's HTML comment prompts from pre-filled sections — replace them with the authored content. Do not leave the template instruction comments alongside the real content.
   - Leave remaining sections (Visibility to Player, Player Actions, System Resolution, State Lifecycle, Failure / Friction States, Edge Cases, Feel & Feedback, Observability, Performance Characteristics, Open Questions) as template prompts with their HTML comments intact.

4. **Register in both indexes:**
   - Add a row to `design/systems/_index.md`
   - Add a row to the System Design Index in `design/design-doc.md`
   - Set Status to `Draft`

## Phase 4 — Report

```
## Systems Seeded

### Glossary
| Metric | Value |
|--------|-------|
| Terms proposed | N |
| Terms confirmed | N |
| Terms rejected | N |

### Systems
| Metric | Value |
|--------|-------|
| Systems proposed | N |
| Systems confirmed | N |
| Systems merged | N |
| Systems removed | N |
| Final system count | N |

### Audit Summary
| Check | Result |
|-------|--------|
| Overlap | N flagged, N resolved |
| Coverage gaps | N flagged, N addressed |
| Category coverage | N / M relevant categories represented |
| Invariant conflicts | N flagged, N resolved |
| Authority conflicts | N flagged, N resolved |
| Granularity | N merges suggested, N accepted |
| Layer boundary | N flagged, N moved out |

### Created Files
| ID | Name | Status |
|----|------|--------|
| SYS-001 | Construction | Draft |
| SYS-002 | Colony Needs | Draft |
| ... | ... | ... |

### Next Steps
- Fill in each system design (ownership, dependencies, state transitions, interfaces)
- Run `/scaffold-fix-systems` after systems are complete to check cross-system consistency
- Run `/scaffold-bulk-seed-references` once systems are stable
```

## Rules

- **Never create systems the user hasn't confirmed.** Always present the proposal and audit results first.
- **Systems are simulation responsibilities, not verb lists.** Group verbs by shared state ownership. "Build", "place", and "demolish" are one Construction system — not three.
- **Do not seed presentation, input, or engine systems.** Engine/service architecture belongs to Step 4. UI component rules belong to Step 5. Input mappings belong to Step 6. Only seed systems that own gameplay simulation state. Exception: if a system has genuine gameplay-facing simulation ownership (e.g., an Alert system that tracks alert state and priority), it belongs here even though it has UI implications.
- **Respect Design Invariants.** Every proposed system must be checked against invariants and boundaries. A system that implies a mechanic violating an invariant is a contradiction, not a valid proposal.
- **Respect the Simulation Depth Target.** If the design doc says "moderate simulation", don't propose 25 deeply interconnected systems. Match system complexity to stated depth.
- **Owned State is gameplay state, not implementation structures.** Do not seed caches, engine nodes, scene references, registries, service locators, or data-structure choices. List only player-facing or simulation-facing state (blueprint placement, construction progress, need levels, mood scores).
- **Pre-fill means write real content, not copy template prompts.** Every pre-fill section must contain substantive authored prose derived from the design doc analysis. A system file where pre-fill sections are TODO, single generic sentences, or rephrased template comments is a failed seed. Go back to the Phase 2 proposal data and write specific content about THIS system. Template HTML comments must be removed from pre-filled sections and replaced with the authored content.
- **Mark seeded content clearly.** Append `<!-- SEEDED -->` comments after authored content so fix/iterate/review passes know what was inferred vs authored. The SEEDED marker goes after the content, not instead of it.
- **System names are nouns, not verbs.** "Construction" not "Building things." "Combat" not "Fighting."
- **IDs are sequential and permanent.** Never skip or reuse.
- **Preserve existing systems.** If SYS-### files already exist, start numbering after the highest existing ID and don't overwrite. Present existing systems alongside new proposals so the user can see the full picture.
- **Existing systems are the baseline.** If systems already exist, audit them first against the design doc before proposing new ones. Prefer expanding or clarifying existing systems over proposing new ones unless a genuine ownership gap exists. Flag if existing systems now overlap with new proposals. Don't re-propose existing systems.
- **Created documents start with Status: Draft.**
- **Glossary uses batch confirmation.** Don't ask about each term individually — present the full table and let the user confirm/edit/reject in bulk.

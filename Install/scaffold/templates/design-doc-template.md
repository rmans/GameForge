# [Game Name] — Design Document

> **Authority:** Rank 1
> **Layer:** Canon — core vision
> **Status:** Draft
> **Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Changelog:**
> - YYYY-MM-DD: Initial creation from template.

---

## Identity

### Core Fantasy
<!-- What experience does the player have? Not what they do — what they feel. -->

### Design Invariants
<!-- Non-breakable rules the game must always obey. If a feature breaks an invariant, the feature is wrong. 3-7 invariants. Each follows this format:

Invariant: <ShortName>
Rule: <single sentence non-breakable rule>
Reason: <why this rule exists>
Implication: <high-level design impact>

Downstream docs cite them using `Invariant: <ShortName>`. -->

### Elevator Pitch
<!-- 1-2 sentences that sell the game to someone who has never heard of it. -->

### Core Pillars
<!-- 3-5 guiding design principles. These inspire, but do not enforce like invariants do. -->

### Core Design Tension
<!-- The opposing forces that drive player decisions. What makes choices hard? -->

### Unique Selling Points
<!-- What makes this game different from similar games? -->

---

## Shape

### Core Loop
<!-- The primary repeated player action cycle. What does the player do every minute? -->

### Secondary Loops
<!-- Longer cycles that wrap around the core loop. What emerges over 10-30 minutes? -->

### Session Shape
<!-- What does a typical play session look like from start to save? -->

### Progression Arc
<!-- How does the player's experience change from first hour to endgame?

Describe at least three phases:
- **Early game** (first 1-2 hours) — what is the player learning? What mechanics are available?
- **Mid game** — what new decisions emerge? What changes from the early game?
- **Late game / endgame** — what does mastery look like? What keeps the player engaged?

What stays the same across the arc? What fundamentally changes? -->

### Player Goals
<!-- Short-term, mid-term, and long-term motivations. Why does the player keep playing? -->

### Decision Types
<!-- What kinds of decisions does the game demand? Tactical, strategic, economic, risk, information? -->

### Decision Density
<!-- How often is the player asked to make meaningful decisions? Micro/strategic/major cadence. -->

---

## Control

### Player Control Model
<!-- What the player directly controls, indirectly influences, and cannot control.
For each category, explain WHY it's in that category — what design goal does the control level serve?

- **Direct control** — player acts, world responds immediately. Why direct?
- **Indirect influence** — player sets policy/priority, simulation executes. Why indirect?
- **No control** — happens regardless of player action. Why uncontrollable? -->

### Control Philosophy
<!-- How does control feel? Steering a system, commanding units, managing policy? -->

### Player Verbs
<!-- The actions the player performs. Build, assign, research, explore, etc.

| Verb | Input | Target | Outcome |
|------|-------|--------|---------|

Examples:
| Build | Click placement grid | Empty tile | Structure begins construction |
| Assign | Drag colonist to task | Task queue slot | Colonist prioritizes that task |
| Zone | Paint area on map | Tile region | Area gains type and permissions | -->

### Player Mental Model
<!-- How should the player conceptually understand the world? What do they believe is happening? -->

### Feedback Loops
<!-- How does the game communicate the results of player actions? -->

---

## World

### Place & Time
<!-- Where and when does the game take place? -->

### Tone
<!-- What emotional register does the game operate in? -->

### Narrative Wrapper
<!-- What story or context frames the gameplay? -->

### Factions / Forces
<!-- What opposing or allied groups exist in the world? -->

---

## Presentation

### Camera
<!-- Perspective, movement, zoom, rotation rules. -->

### Aesthetic Pillars
<!-- Visual identity principles. What does the game look like? -->

### Audio Direction
<!-- Sound design philosophy. What does the game sound like? -->

### Entity Presentation
<!-- How do the major content categories look and sound? Not style guide detail — design-level identity.
Describe the visual and audio character of each major entity type so downstream docs (style guide, system designs, specs) know what assets are needed.

| Entity / Category | Visual Identity | Animation Set | Sound Identity |
|-------------------|----------------|---------------|----------------|

Examples:
| Colonists | 3D low-poly humanoids, distinct silhouettes per role | Walk, run, idle, 2H gun fire, axe side swing, overhead mining, carry, collapse | Footsteps (surface-aware), tool impacts, voice barks (effort, pain, idle chatter) |
| Buildings | Modular grid-snapped structures, construction scaffolding phase | Build-up sequence (foundation → frame → complete), damage states, destruction | Construction hammering, ambient hum (powered), creak/groan (damaged) |
| Environment | Procedural terrain with biome-specific vegetation | Wind sway (vegetation), weather particles | Biome ambience loops, weather layers, wildlife | -->

### Player Information Model
<!-- What information is always visible, partially visible, hidden, or must be discovered?

Information Hierarchy — categorize every major piece of game state:
- **Critical** (always visible) — state the player needs for core loop decisions
- **Supplementary** (available on demand) — state that enriches understanding but isn't required moment-to-moment
- **Discoverable** (hidden until earned/triggered) — state the player uncovers through play
- **Opaque** (deliberately hidden) — state the simulation uses but the player never sees directly

Explanation Depth — how deep can the player drill into any piece of information?
- Surface: what is the current state? (e.g., mood icon: unhappy)
- Reason: why is it this way? (e.g., tooltip: "hungry, overworked")
- Detail: what are the exact numbers? (e.g., expanded panel: hunger 72/100, work hours 14/8)

History & Logs — what can the player look back at?
- What events are logged and for how long?
- What information is ephemeral (gone once dismissed)?
- What historical data helps the player spot trends? -->

---

## Content

### Content Structure
<!-- How is content organized? What are the major content categories? -->

### Content Categories
<!-- Player-facing content types: structures, colonists, resources, events, biomes, etc. -->

### Procedural vs Authored
<!-- What is generated, what is hand-crafted, what is hybrid? -->

### Replayability Model
<!-- What drives replay value? Procedural variation, faction dynamics, strategic diversity? -->

---

## Simulation Requirements

### State That Matters
<!-- What persistent state does the game track that the player can observe or that drives gameplay?
List the major state domains — not system names, but WHAT is being simulated and WHY it matters.

| State Domain | What Changes | Player Sees | Consequence If Ignored |
|-------------|-------------|-------------|----------------------|

Examples:
| Colonist needs | hunger, rest, morale over time | mood indicators, behavior changes | work slowdowns, breakdowns, abandonment |
| Power grid | generation vs consumption balance | surplus/deficit meter | brownouts disable rooms, cascade failures |
| Structural integrity | damage accumulates from events | cracks, warnings, visual damage | breaches, room loss, exposure risk | -->

### Behaviors That Need Rules
<!-- What gameplay behaviors require persistent, rule-driven simulation?
These are the interactions and dynamics that can't be hand-scripted — they need systems to govern them.

Example:
- Colonists autonomously select tasks based on skill and priority → requires task assignment logic
- Damage propagates through connected rooms → requires structural integrity tracking
- Weather events escalate based on biome instability → requires environmental hazard modeling -->

### Player Actions That Need Governance
<!-- What player actions affect the simulation and need rules to resolve?
Focus on actions where the outcome isn't trivial — where the game must evaluate, schedule, or constrain.

Example:
- Player assigns zones → game must track zone types, permissions, and enforce boundaries
- Player queues construction → game must schedule workers, track materials, resolve conflicts
- Player dispatches expeditions → game must simulate off-map progress, risk, and return -->

### Interaction Patterns
<!-- How do different parts of the simulation affect each other?
Describe the causal chains and feedback loops, not which systems talk to which.

Example:
- Low power → rooms go dark → colonist stress rises → work slows → less maintenance → more breakdowns
- Storm damage → breaches → exposure risk → medical demand spikes → diverts workers from repair -->

### Simulation Depth Target
<!-- What is simulated because it creates player decisions? What is deliberately NOT simulated?
Be explicit about where you draw the line.

Example:
Simulated: individual colonist needs, room-level power, per-tile damage
NOT simulated: individual colonist pathfinding decisions, fluid dynamics, realistic physics -->

### Simulation Boundaries
<!-- What does the player NOT need a system for? What should be handled by simple rules, data tables, or UI?

Example:
- Tooltips and info panels are UI, not systems — they read state, they don't own it
- Save/load is infrastructure, not gameplay — no persistent state to govern
- Difficulty settings are data transforms, not behavioral domains -->

---

## Philosophy

### Failure Philosophy
<!-- How should failure feel? Traceable causes, fair consequences, learning opportunities.

Address each:
- **Consequence severity** — how bad can things get? Setback, loss, or game over?
- **Recovery cost** — how long does recovery take? Is it proportional to the mistake?
- **Cascading failure** — can one failure trigger others? How far does a cascade go before stabilizing?
- **Teaching through failure** — does the player learn something useful from every failure, or are some just punitive?
- **Failure signals** — how does the player know things are going wrong BEFORE catastrophic failure? -->

### Risk / Reward Philosophy
<!-- How are risk and reward linked? Safe play vs aggressive play tradeoffs. -->

### Simulation Transparency Policy
<!-- How understandable should the simulation be? Transparent, partially opaque, or narrative? -->

### Information Clarity Principle
<!-- Can the player understand the likely consequences of decisions before committing? -->

### Decision Anchors
<!-- 3-5 tie-breaker rules for ambiguous design choices. Format: "X over Y". Keep to 3-5 to remain actionable. -->

### Design Pressure Tests
<!-- 3-6 stress scenarios. Each follows this format:

Pressure Test: <name>
Scenario: <extreme condition>
Expectation: <what must remain true>
Failure Signal: <what indicates the design is breaking> -->

### Design Gravity
<!-- 3-4 directions the game should deepen over time. Core Pillars define what the game IS. Design Gravity defines where it should DEEPEN. Pillars = identity. Gravity = evolution. -->

### Design Boundaries
<!-- What this game is NOT. Anti-scope to prevent drift. -->

### Learning Curve Strategy
<!-- How are complex systems introduced? Gradual reveal through play? -->

---

## Scope

### Scope Reality Check
<!-- Is the total scope achievable? What's the minimum viable product? -->

### Target Platforms
<!-- PC, console, mobile, Steam Deck? -->

### Accessibility Goals
<!-- What accessibility features are committed vs aspirational? -->

### Performance Targets
<!-- Frame rate, entity count, map size targets. -->

### Technical Stack

<!-- Project-level technical context. Captured during init so all downstream docs know what's available. -->

#### Engine
<!-- Which engine and version? e.g., Godot 4.3, Unity 2024, Unreal 5.4 -->

#### Languages
<!-- What languages are used? e.g., GDScript, C++ via GDExtension, C#, Rust -->

#### Build System
<!-- How is the project built? e.g., SConstruct, CMake, dotnet build, cargo -->

#### Test Frameworks
<!-- What testing tools are available? e.g., GUT (GDScript), regression tests (C++), gdlint -->

#### CI/CD
<!-- What's the CI setup? e.g., GitHub Actions, none yet -->

#### Key Dependencies
<!-- Major plugins, addons, or libraries the project relies on. e.g., GDExtension addon, navigation plugin -->

---

## System Design Index

<!-- Populated by Step 3. Links to all system design files. -->

| ID | System | Status |
|----|--------|--------|
| — | — | — |

---

## Rules

1. This document is the highest authority for game intent, player experience, and design rules.
2. Sections marked Complete are locked canon — use `/scaffold-seed design --mode refresh` to change them.
3. Design Invariants are non-breakable. Features that violate invariants are wrong.
4. Decision Anchors resolve ambiguous design choices without debate.
5. System truth, reference truth, and engine truth live in their own documents, not here.

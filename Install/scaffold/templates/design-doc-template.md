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
<!-- How does the player's experience change from first hour to endgame? -->

### Player Goals
<!-- Short-term, mid-term, and long-term motivations. Why does the player keep playing? -->

### Decision Types
<!-- What kinds of decisions does the game demand? Tactical, strategic, economic, risk, information? -->

### Decision Density
<!-- How often is the player asked to make meaningful decisions? Micro/strategic/major cadence. -->

---

## Control

### Player Control Model
<!-- What the player directly controls, indirectly influences, and cannot control. -->

### Control Philosophy
<!-- How does control feel? Steering a system, commanding units, managing policy? -->

### Player Verbs
<!-- The actions the player performs. Build, assign, research, explore, etc. -->

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

### Player Information Model
<!-- What information is always visible, partially visible, hidden, or must be discovered? -->

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

## System Domains

### Major System Domains
<!-- High-level gameplay domains the design requires. Not a full ownership map — that's Step 3. -->

### Major Mechanics
<!-- The primary mechanics that support the core loop. -->

### System Interaction Philosophy
<!-- How should systems interact? Emergent problems from interaction, not isolated mechanics. -->

### Simulation Depth Target
<!-- What is simulated because it creates player decisions? What is deliberately NOT simulated? -->

---

## Philosophy

### Failure Philosophy
<!-- How should failure feel? Traceable causes, fair consequences, learning opportunities. -->

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

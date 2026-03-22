---
name: scaffold-bulk-seed-references
description: Read all system designs and bulk-populate all Step 3 docs — architecture, authority, interfaces, state transitions, entity components (with identity semantics), resource definitions, signal registry (with event taxonomy), balance parameters, and enums/statuses. Use after system designs are filled out.
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Seed References + Architecture from System Designs

Read all completed system designs and use them to bulk-populate all 9 Step 3 output documents.

## Confidence Classes

Every seeded entry has a confidence class that determines whether it is written immediately or escalated:

| Class | Meaning | Action |
|-------|---------|--------|
| **Direct** | Explicitly stated in system docs (Owned State, Simulation Responsibility, explicit dependency declaration) | Write immediately |
| **Derived** | Inferred from consistent patterns across multiple system docs | Write immediately with `<!-- Derived from SYS-###, SYS-### -->` provenance comment |
| **TBD** | Ambiguous, contested, or requires judgment beyond what system docs provide | Write as TBD placeholder, add to Decision Queue in report |

**Bulk-write all Direct and Derived entries without stopping.** Only escalate TBD items — collected in the Phase 10 report for user follow-up. The skill should not stop between phases for confirmation unless it encounters a blocking conflict (two systems claiming write authority over the same variable with no clear resolution).

## Prerequisites

1. **Read** `scaffold/design/systems/_index.md` to get the list of registered systems.
2. **Read every system file** in `scaffold/design/systems/`.
3. **Read** `scaffold/design/design-doc.md` — needed for architecture seeding (vision, core loop, system domains, simulation depth, governance).
4. **Read** `scaffold/doc-authority.md` — needed for document authority ranking and influence map. When seeding entries or resolving conflicts, the precedence chain in this file determines which source wins.
5. **Verify systems are sufficiently filled out.** Each system should have content (not just template defaults) in at least:
   - Purpose / Simulation Responsibility
   - Player Actions
   - System Resolution
   - Upstream Dependencies
   - Downstream Consequences
   - Owned State
6. If fewer than 2 systems are filled out, stop and tell the user to design more systems first.
7. **Read templates** for any docs that don't exist yet — all 9 templates in `scaffold/templates/`.
8. **Read engine docs** if they exist (`scaffold/engine/`) — needed for architecture Phase 1d and 1f. If engine docs don't exist yet (Step 4 hasn't run), note this and mark timing/representation decisions as TBD.

## Phase Order

Phases must run in this order — later phases depend on earlier ones:

```
1. Architecture (scene tree, dependencies, tick order, update semantics, identity model)
   ↓
2. Authority (single-writer ownership)
   ↓
3. Interfaces (cross-system contracts)
   ↓
4. State Transitions (state machines, invariants)
   ↓
5. Entity Components (data shapes, identity semantics from Phase 1)
   ↓
6. Resource Definitions (items, tiers, chains)
   ↓
7. Signal Registry (signals with event taxonomy, intents — realizes Phase 3 contracts)
   ↓
8. Balance Parameters (tunable numbers)
   ↓
9. Enums & Statuses (shared cross-system vocabulary)
   ↓
10. Report (summary + Decision Queue)
```

---

## Phase 1 — Architecture

**Output:** `scaffold/design/architecture.md`

If the file doesn't exist, create it from the template. If it exists, seed missing sections.

### 1a. Scene Tree Layout

Extract from system designs:
- Which systems exist (one node per system in SimulationLayer)
- **WorldLayer entries** — seed only entries directly implied by a system's explicit Visibility to Player or Feel & Feedback sections. Do not speculatively create renderers/overlays from general system descriptions. Mark uncertain UI surfaces as `<!-- TBD: renderer for SYS-### -->`.
- **UILayer entries** — same rule. Only seed panels/HUD elements with explicit system-doc support.

Include **System Representation** — are systems scene tree nodes, pure objects, autoloads, or hybrids? Derive from engine docs if they exist (`scaffold/engine/godot4-scene-architecture.md`). If engine docs don't exist, mark as **TBD — requires Step 4 engine doc input**.

### 1b. System Dependency Graph

Extract from each system's Upstream Dependencies section:
- Build the dependency table: System → Tier → Depends On
- Assign tiers by dependency depth (Tier 0 = no dependencies, Tier 1 = depends only on Tier 0, etc.)
- Flag any upward dependencies (Tier N depending on Tier N+1) — these are architecture bugs
- **Cycle handling:** if dependency cycles prevent clean tier assignment, mark affected systems as **TBD — dependency cycle blocks tier placement** and add to Decision Queue. Do not force a bad tier assignment to resolve a cycle.

### 1c. Tick Processing Order

Extract from system dependencies and data flow patterns:
- Systems that produce data others consume must tick first
- Time/clock systems first, emergency/alert systems last
- Draft the position table with justifications
- Where ordering requires judgment beyond explicit dependencies, mark as **TBD — tick position requires user decision** and explain the trade-off
- **Ambiguity handling:** if explicit dependencies do not produce a clean partial order, or if two systems both appear to require earlier freshness from each other, mark as **TBD — mutually dependent freshness, requires user decision**. Do not force a contradictory ordering.

### 1d. Simulation Update Semantics

**Never infer timing decisions from system docs alone.** These are foundation-level choices.

- **If engine docs exist:** derive timestep model, signal dispatch timing, and intent processing from engine docs.
- **If engine docs don't exist:** seed the section structure from the template but mark ALL timing decisions as **TBD — requires Step 4 engine doc input**. Do not guess fixed vs variable timestep or immediate vs deferred dispatch.
- **Exception:** if the design doc or an accepted ADR explicitly states a timing model, use that as Direct confidence.

### 1e. Signal Wiring Map

Extract from system Downstream Consequences and interfaces:
- Which signals are behavioral (gameplay effect) vs logging (observe-only)?
- Draft the two wiring tables (behavioral + logging)
- Provenance: note which system's Downstream Consequences each wiring entry derives from

### 1f. Data Flow Rules

**Do not invent architecture rules from weak evidence.** Seed from the architecture template defaults. Adapt only when:
- A pattern appears consistently across **3+ systems**, or
- A convention is already explicitly stated in the design doc, an accepted ADR, or an existing engine doc

Otherwise leave template rules as-is for later refinement during fix-references and iterate-references.

Seed the Forbidden Patterns section from the template — these are universal and do not require project-specific evidence.

### 1g. Entity Identity & References

Extract from system designs:
- What entities exist? (scan system Owned State for entity nouns — preview for Phase 5)
- Do systems reference entities by ID, handle, name, or position?
- Are there patterns suggesting generational handles, UUIDs, or bare integers?
- What content types exist? (items, structures, recipes, traits)

Draft the Identity section with options where ambiguous:
- **Runtime identity** — handle format, uniqueness scope, invalidation, reuse policy
- **Persistent identity** — save format, load validation, cross-reference survival
- **Content identity** — ID format, runtime resolution, mod extensibility

**Identity model decisions are rewrite-multipliers.** If the answer isn't clear from system designs + existing ADRs, draft options and mark as **TBD** for Step 7 resolution. Never silently pick one.

### 1h. Initialization & Boot Order

Derive from system dependencies and scene tree layout:
- What order do systems initialize in? (scene tree position determines `_ready()` order)
- When does signal wiring happen relative to system initialization?
- When is the simulation safe to start ticking?

If engine docs exist, derive from scene architecture conventions. Otherwise mark as **TBD — requires Step 4 engine doc input** and seed the section structure from the template.

### 1i. Failure & Recovery Patterns

Seed the section structure from the template. For each pattern category (missing dependency, stale reference, invalid state, data corruption on load), note any explicit handling mentioned in system designs. Most entries will be template defaults at this stage — concrete patterns emerge during implementation.

### 1j. Code Patterns

Scan system designs for recurring structural patterns. Seed pattern stubs only for patterns with explicit system-doc support. Full patterns are fleshed out during implementation.

**Write the architecture draft. Add `<!-- Seeded from SYS-###, SYS-### -->` provenance comments to derived sections.**

---

## Phase 2 — Authority Table

**Output:** `scaffold/design/authority.md`

### Source hierarchy for ownership inference

Ownership must be inferred in this strict order. Lower sources cannot override higher sources:

1. **Owned State section** — primary source. If a system's Owned State lists a variable, that system owns it. (Direct confidence)
2. **Simulation Responsibility** — secondary clarification. Confirms or disambiguates ownership scope. (Direct confidence)
3. **System Resolution / Player Actions** — detect candidate mismatches or missing entries only. Not a primary ownership source. (Derived confidence if consistent with #1-2)
4. **Upstream Dependencies / Downstream Consequences** — supporting context only. Never infer ownership from "System A reads X from System B." (Not an ownership source)

### Steps

1. **Read** `scaffold/design/authority.md` (or create from template).
2. **Extract ownership claims** using the source hierarchy above.
3. **Group by domain** — organize entries into domain subsections (Time & Calendar, Colonist — Lifecycle, etc.)
4. **Draft entries** using the full template columns:
   ```
   | Variable / Property | Owning System | Write Mode | Authority Type | Persistence Owner | Readers | Update Cadence | Notes |
   ```
   - **Write Mode:** direct owner write / delegated setter / event-driven update. Derive from how the system describes updating the variable.
   - **Authority Type:** Authoritative (source of truth, saved) / Derived (computed, not saved) / Cache (performance copy, not saved). Default to Authoritative unless system doc explicitly describes it as derived or cached.
   - **Persistence Owner:** the system responsible for save/load of this variable. For Derived/Cache entries, enter "—".
5. **Write Direct entries immediately.** For conflicts where two systems' Owned State sections claim the same variable, mark as **TBD** and add to Decision Queue. Do not guess.
6. **Add provenance:** `<!-- Owned State: SYS-### -->` for each entry.

---

## Phase 3 — Interface Contracts

**Output:** `scaffold/design/interfaces.md`

1. **Read** `scaffold/design/interfaces.md` (or create from template).
2. **Extract system-to-system communication** from every system's Upstream Dependencies and Downstream Consequences tables. For each pair of systems that exchange data:
   - Identify the data exchanged
   - Determine the direction: Push (source notifies target), Pull (target reads from source), or Request (source asks target to act). If the data exchange is clear but the direction is not explicit in system docs, write the contract with **Direction: TBD** rather than guessing from prose tone.
   - Draft guarantees and notes
3. **Group by domain** — organize into domain subsections matching authority table domains.
4. **Draft entries:**
   ```
   | Source System | Target System | Data Exchanged | Direction | Notes |
   ```
5. **Write entries.** Flag conflicts where systems disagree about data flow direction as **TBD**.
6. **Add provenance:** `<!-- SYS-### Downstream → SYS-### Upstream -->` for each entry.

---

## Phase 4 — State Transitions

**Output:** `scaffold/design/state-transitions.md`

1. **Read** `scaffold/design/state-transitions.md` (or create from template).
2. **Extract state machines** from system designs. Only draft state machines for **discrete named states with explicit transitions**. Continuous variables and thresholds (hunger level, morale score, HP) do not become state machines unless the system doc explicitly models them as discrete bands with named transitions (e.g., morale bands: Excellent → Good → Neutral → Low → Critical). Look for:
   - State Lifecycle sections in system docs (primary source)
   - Entities with discrete lifecycle states (idle, active, dead, etc.)
   - Entities that change discrete mode (blueprint → built, raw → refined)
   - Explicit named-state enums in system designs
3. **For each proposed state machine**, draft:
   - Sequential number, name, and owning system (Authority)
   - Entity type
   - State table: `| State | Transitions To | Trigger | Notes |`
   - Invariants (testable rules that must always hold)
   - Terminal states marked with `*(terminal)*`
4. **Write state machines.** Add provenance: `<!-- Derived from SYS-### State & Lifecycle > State Lifecycle -->`.

---

## Phase 5 — Entity Components

**Output:** `scaffold/reference/entity-components.md`

### Entity extraction criteria

Not every noun is an entity. **Candidate entities must have at least one of:**
- **Persistent identity** — the noun has an ID, handle, or name that persists across ticks
- **Lifecycle** — the noun is created, exists, and is destroyed/removed
- **Cross-system reference** — multiple systems read or write fields on this noun

**Not entities:**
- Transient actions or intents (hauling_request, sleep_request)
- Status values or enums (morale_state, lifecycle_state) — these are fields ON entities
- Abstract metrics or derived views (colony_mood_average)
- Resources as quantities (iron_ore count) — though individual items may be entities

### Steps

1. **Read** `scaffold/reference/entity-components.md` (or create from template).
2. **Extract entities** using the criteria above.
3. **Seed identity conventions** at the top of the doc:
   - **Entity Reference Convention** — from Phase 1g (architecture identity model)
   - **Content Identity Convention** — from Phase 1g
   - If Phase 1g marked these as TBD, note that here too — conventions will be locked in Step 7
4. **For each entity**, draft a component table:
   - Group fields by component (Identity, Lifecycle, Needs, Health, Skills, Work, etc.)
   - Types: string, int, float, bool, enum, list, dict, ref, Vector2i, etc.
   - Authority: from authority table (Phase 2). Must match — if it doesn't, flag the mismatch.
   - Cadence: Once, Per tick, On event, On change
5. **Include singleton entities** — entities with exactly one instance (PowerGrid, Colony, World, etc.)
6. **Write entities.** Add provenance: `<!-- Fields from SYS-### State & Lifecycle > Owned State, authority from Phase 2 -->`.

---

## Phase 6 — Resource Definitions

**Output:** `scaffold/reference/resource-definitions.md`

1. **Read** `scaffold/reference/resource-definitions.md` (or create from template).
2. **Extract resources** from system designs. Look for:
   - Anything consumed, produced, stored, or traded in system descriptions
   - Materials mentioned in Player Actions
   - Items in Upstream Dependencies/Downstream Consequences tables
3. **Distinguish fungible resources from item entities:**
   - **Fungible resources** (iron ore, food, fuel) — interchangeable units defined here in resource-definitions.md
   - **Unique item entities** (a specific weapon, a named artifact) — defined in entity-components.md, not here
   - If a noun appears to be both (e.g., "items" that are both stackable resources and individually tracked entities), flag the modeling choice as **TBD** instead of duplicating across both docs
4. **For each fungible resource**, draft:
   - Category, tier (1-4 per tier definitions), source, storage type, notes
5. **Organize into categories** — one section per category with a summary table at the top.
5. **Draft production chains** if multi-step resource transformations exist.
6. **Draft production station registry** if crafting stations are mentioned.
7. **Write resources.** Add provenance: `<!-- From SYS-### Player Experience > Player Actions / System Resolution -->`.

---

## Phase 7 — Signal Registry

**Output:** `scaffold/reference/signal-registry.md`

1. **Read** `scaffold/reference/signal-registry.md` (or create from template).
2. **Extract signals** from system Downstream Consequences tables:
   - If a system **notifies** others that something happened → Signal (past tense: `structure_completed`)
   - If a system **requests** another system to act → Intent (noun form: `hauling_request`)
3. **For each proposed signal**, draft with the **Level** column:
   ```
   | Signal Name | Level | Payload | Emitter | Consumer(s) | Notes |
   ```
   Level values: Entity, Room, System, Colony, Global
4. **For each proposed intent**, draft:
   ```
   | Intent Object | Payload | Requester | Handler | Notes |
   ```
5. **Cross-reference with interfaces.md (Phase 3).** Every interface contract should have a defined **realization path**: signal, intent, query API, or direct sanctioned interface call. Flag contracts with no clear realization path as **TBD** — but do not assume every interface must be a signal. Pull/query interfaces are realized through API calls, not signals.
6. **Write signals and intents.** Add provenance: `<!-- SYS-### Relationships > Downstream Consequences -->`.

---

## Phase 8 — Balance Parameters

**Output:** `scaffold/reference/balance-params.md`

### Extraction criteria

Only extract numbers that define **gameplay behavior**: thresholds, rates, durations, capacities, or formulas intended for tuning. Ignore:
- Purely illustrative numbers in prose ("about 10 colonists")
- Temporary scaffolding or examples
- Narrative approximations not intended as design targets

When uncertain whether a number is a tunable parameter, register it with **TBD** value and note the source ambiguity.

### Steps

1. **Read** `scaffold/reference/balance-params.md` (or create from template).
2. **Extract tunable numbers** from system designs using the criteria above.
3. **For each parameter**, draft:
   ```
   | Parameter | Value | Unit | Range | System | Notes |
   ```
4. **Organize by system** — one subsection per system in ascending SYS-### order.
5. **Write parameters.** Add provenance: `<!-- SYS-### Player Experience > System Resolution / State & Lifecycle > Failure States -->`.

---

## Phase 9 — Enums & Statuses

**Output:** `scaffold/reference/enums-and-statuses.md`

1. **Read** `scaffold/reference/enums-and-statuses.md` (or create from template).
2. **Extract shared state vocabulary** from system designs and state transitions (Phase 4). A state belongs here if:
   - It is referenced by **two or more systems** (cross-system vocabulary)
   - It appears in state-transitions.md AND is read by systems other than the authority
3. **Normalize against existing canonical sources:**
   - State names must match `state-transitions.md` entries for cross-system states
   - Terms must not conflict with `glossary.md` terminology
   - If a seeded term conflicts with either canonical source, use the canonical name and flag the drift — do not silently normalize synonyms
4. **Classify into categories:**
   - Job / Task States, Construction States, Colonist Activity States, Need / Vital States, Alert / Severity Levels, Resource States, Damage / Health States, Ownership / Control States, Custom categories as needed
5. **For each shared enum**, draft:
   ```
   | State | Meaning | Used By |
   ```
6. **Single-system enums stay out.** If only one system uses a state value, it belongs in that system's doc, not here.
7. **Write enums.** Add provenance: `<!-- Cross-system: SYS-###, SYS-### via state-transitions.md #N -->`.

---

## Phase 10 — Report

```
## Seed Report

### Documents Seeded
| Document | Status | Entries | Direct | Derived | TBD |
|----------|--------|---------|--------|---------|-----|
| architecture.md | Created / Updated | ... | N | N | N |
| authority.md | Created / Updated | ... | N | N | N |
| interfaces.md | Created / Updated | ... | N | N | N |
| state-transitions.md | Created / Updated | ... | N | N | N |
| entity-components.md | Created / Updated | ... | N | N | N |
| resource-definitions.md | Created / Updated | ... | N | N | N |
| signal-registry.md | Created / Updated | ... | N | N | N |
| balance-params.md | Created / Updated | ... | N | N | N |
| enums-and-statuses.md | Created / Updated | ... | N | N | N |

### Identity Model
- Runtime handle: [format or TBD]
- Content identity: [format or TBD]
- Persistence: [format or TBD]

### Decision Queue — Blocking Conflicts
These prevented high-confidence seeding. Two or more systems disagree and the skill could not resolve it.

| # | Phase | Item | Contenders | Source |
|---|-------|------|------------|--------|
| 1 | Authority | colonist.mood ownership | SYS-004 vs SYS-009 — both claim in Owned State | SYS-004, SYS-009 |
| ... | ... | ... | ... | ... |

### Decision Queue — Non-Blocking TBDs
These were safely deferred as TBD placeholders. Seeding continued.

| # | Phase | Item | Options | Source |
|---|-------|------|---------|--------|
| 1 | Architecture | Simulation timestep model | Fixed / Variable / Fixed+interpolation | No engine doc yet |
| ... | ... | ... | ... | ... |

### Gaps Detected
- Systems that didn't contribute to any reference doc (may be underdesigned)
- Variables with no clear owner
- Entities referenced but not fully defined
- Interface contracts with no realization path (no signal, intent, or API)
- State values used cross-system but not in enums-and-statuses
- Terminology drift between seeded enums and glossary/state-transitions

### Confidence Hot Spots
- Systems with highest TBD count: SYS-### (N TBDs), SYS-### (N TBDs)
- Docs with highest Derived density: [doc] (N% derived), [doc] (N% derived)
- Areas most likely to need Step 7 locking: [identity model / timing semantics / etc.]

### Provenance Summary
- Direct entries: N (from explicit Owned State, Simulation Responsibility, State Lifecycle)
- Derived entries: N (from consistent cross-system patterns, marked with source comments)
- TBD entries: N (in Decision Queue above)
```

### Next Steps
- Run `/scaffold-sync-glossary --scope references` to register new domain terms (entity names, resource names, signal names, state names) in the glossary
- Resolve Decision Queue items (user decisions or defer to Step 7)
- Run `/scaffold-fix-references` to auto-fix cross-doc inconsistencies
- Run `/scaffold-iterate references` for adversarial architecture review
- Run `/scaffold-validate --scope refs` for cross-reference integrity check

---

## Rules

- **Seeded content must be substantive, not template placeholders.** Every Direct and Derived entry must have real authored content derived from system designs. Each reference template (architecture, authority, interfaces, state-transitions, entity-components, resource-definitions, signal-registry, balance-params, enums-and-statuses) defines its own sections and table columns — every section that receives seeded content must have populated tables with real entries (all columns filled, not placeholder dashes). Remove template HTML comments from sections that receive authored content — replace them with the actual entries. Do not leave pre-filled tables as empty template structures, TODO markers, or placeholder rows. TBD items are collected in the Decision Queue, not left as inline TODOs in the doc body. A reference doc where seeded tables contain only the template example row has failed the seed.
- **Bulk-write Direct and Derived entries without stopping.** Only stop for blocking conflicts (two systems claiming write authority over the same variable with no resolution). Collect all TBD items in the Decision Queue for user follow-up after seeding completes.
- **Work phase by phase.** Complete one phase before starting the next — later phases build on earlier ones.
- **Architecture comes first** because it establishes the scene tree, dependency graph, identity model, and update semantics that all other docs reference.
- **Authority table comes before interfaces** because interfaces reference ownership.
- **Interfaces come before signals** because signal-registry realizes interface contracts.
- **State transitions come before entity-components** because entity state fields reference registered state machines.
- **Enums come last** because they extract shared vocabulary from all prior phases.
- **Preserve existing content.** If a doc already has entries, add to them — don't overwrite.
- **Flag conflicts, don't resolve them.** If two systems claim the same variable or entity field, write as TBD and add to Decision Queue. Don't guess.
- **"TBD" is a valid value.** For balance params, identity decisions, and timing semantics where no answer exists yet, use TBD. The point is to register the question, not to answer it prematurely.
- **Authority extraction follows a strict source hierarchy.** Owned State → Simulation Responsibility → System Resolution/Player Actions (mismatch detection only) → Dependencies/Consequences (context only, never ownership source).
- **Entity extraction requires persistent identity, lifecycle, or cross-system reference.** Not every noun is an entity. Transient actions, status values, abstract metrics, and resource quantities are not entities.
- **Balance param extraction is conservative.** Only register numbers that define gameplay behavior (thresholds, rates, durations, capacities). Ignore illustrative prose numbers.
- **Interface realization is not always signals.** Pull/query interfaces are realized through API calls. Push interfaces are realized through signals. Request interfaces are realized through intents. Flag contracts with no clear realization path.
- **Enums must match canonical sources.** State names match state-transitions.md. Terms must not conflict with glossary.md. Flag drift, don't silently normalize.
- **Data flow rules are not invented from weak evidence.** Seed from template defaults. Only adapt when a pattern appears across 3+ systems or is explicitly stated in design doc / engine doc / accepted ADR.
- **Timing decisions are never inferred from system docs alone.** Timestep model, signal dispatch timing, and same-tick cascading require engine doc or explicit design doc/ADR support. Mark as TBD otherwise.
- **Identity model decisions are rewrite-multipliers.** Draft options and mark as TBD for Step 7. Never silently pick one.
- **Add provenance to derived content.** Use `<!-- Source: SYS-###, SYS-### -->` HTML comments so later audits can trace seeded entries back to their source. Prefer section-level or block-level provenance comments preceding the seeded block. Use row-level provenance only where the doc format already has a Notes column. Do not clutter dense tables with inline HTML comments.
- **No duplicate seeding.** Before writing a seeded entry, check whether an equivalent entry already exists in the target doc. If it does, update or annotate the existing entry rather than creating a duplicate row. Equivalence definitions:
  - Authority: same Variable/Property name
  - Interface: same Source + Target + Data Exchanged
  - Signal: same Signal Name
  - Resource: same canonical Resource name
  - Entity field: same Entity + Component + Field name
  - Enum: same canonical State value
  - Balance param: same Parameter name + System
- **Resource state variants vs enums.** Resource state variants that change the identity or category of a resource (raw → refined, fresh → spoiled) belong in resource-definitions.md. Cross-system shared status values (job states, alert levels) belong in enums-and-statuses.md. Do not duplicate across both docs.
- **Created documents start with Status: Draft.**
- **Use templates for new docs.** If a doc doesn't exist, create it from the corresponding template in `scaffold/templates/`.

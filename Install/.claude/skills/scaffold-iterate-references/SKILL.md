---
name: scaffold-iterate-references
description: Adversarial per-topic review of Step 3 docs using an external LLM. Reviews architecture, authority, interfaces, state-transitions, entity-components, resource-definitions, signal-registry, balance-params, and enums-and-statuses across 6 topics (architectural coherence, ownership & authority model, contract & interface quality, data model fitness, cross-doc consistency, simulation readiness). Consumes design signals from fix-references. Supports --target for single-doc focus and --topics for scoped review.
argument-hint: [--target doc.md] [--topics "1,2,5"] [--focus "concern"] [--iterations N] [--signals "..."]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial References Review

Run an adversarial per-topic review of Step 3 reference and architecture docs using an external LLM reviewer: **$ARGUMENTS**

This skill reviews the 9 Step 3 docs across 6 sequential topics, each with its own back-and-forth conversation. It uses the same Python infrastructure as iterate-design/iterate-systems but with reference-doc-specific topics.

This is the **design reviewer** for Step 3 — not the formatter. It runs after `fix-references` has normalized the docs and detected design signals. It evaluates whether the reference model is *sound* — whether the architecture is coherent, the authority model is defensible, the contracts are complete, the data model is fit for purpose, and the docs are consistent with each other.

The real question this review answers: **do these 9 docs, taken together, give a system implementer everything they need to build correctly — without guessing, contradicting each other, or leaving critical decisions implicit?**

## Topics

| # | Topic | What It Evaluates | Primary Docs |
|---|-------|-------------------|-------------|
| 1 | Architectural Coherence | Is the architecture internally consistent and complete? | architecture.md |
| 2 | Ownership & Authority Model | Is the authority model defensible and unambiguous? | authority.md, entity-components.md |
| 3 | Contract & Interface Quality | Are cross-system contracts complete and realizable? | interfaces.md, signal-registry.md |
| 4 | Data Model Fitness | Is the data model sound for the game's needs? | entity-components.md, resource-definitions.md, balance-params.md |
| 5 | Cross-Doc Consistency | Do all 9 docs agree with each other? | All 9 docs |
| 6 | Simulation Readiness | Could a developer implement from these docs without guessing? | All 9 docs |

### Topic 1 — Architectural Coherence

Is the architecture internally consistent and complete?

**architecture.md focus:**
- **Scene tree vs dependency graph** — does every system in the scene tree have correct tier placement? Do tier assignments match actual dependency direction? Are there phantom dependencies (listed but never used) or hidden dependencies (used but not listed)?
- **Dependency graph honesty** — is the graph actually real or just neat-looking? Are any listed dependencies decorative? Is some omitted reverse dependency actually load-bearing? Does a supposedly downward-only graph hide feedback loops that matter operationally?
- **Tick order freshness hazards** — is there a clear rationale for every position? Could a developer predict where a new system goes? Are there stale-freshness traps where a consumer ticks before its producer? Do any systems require same-tick freshness from each other?
- **Timing model precision** — are the timing rules complete and unambiguous? Does signal dispatch timing match what system designs assume? Would two developers implement the same timing behavior from these rules? Are there places where "immediate" vs "queued" is left vague? Do state transitions silently depend on end-of-tick cleanup not documented anywhere?
- **Boot order and startup races** — is initialization sequencing explicit enough to prevent startup races? Can signal wiring happen before systems are ready? Are data stores initialized before readers? Can the first tick run before all required state is legal? Does load-from-save change the startup sequence in a way the doc ignores?
- **Data flow rules vs forbidden patterns** — do the positive rules and negative rules cover the same ground? Are there gaps where something is neither allowed nor forbidden? Do the forbidden patterns actually close the loopholes left by the positive rules? Does the doc describe what happens when a rule collides with convenience or performance pressure?
- **Identity model precision** — does the entity identity model (handles, content IDs, persistence mapping) hang together? What exactly is an entity reference? What does invalidation mean? Can handles be reused? What survives save/load? How are cross-references repaired or rejected on load? If the identity section sounds polished but leaves these questions open, flag it hard.
- **Failure/recovery coverage** — are the documented recovery patterns sufficient for the game's failure modes? Are there entity lifecycle paths that could lead to unrecoverable states? What happens when assumptions break at runtime?
- **Code pattern sufficiency** — do the documented patterns cover the actual recurring structures in the codebase? Are there patterns being used that aren't documented?
- **Fragility detection** — is the architecture technically coherent but operationally brittle? Look for: too many same-tick dependencies creating fragile ordering pressure, overloaded orchestrators, signal fan-out that creates debugging opacity, or ownership boundaries so fragmented that normal gameplay flows require excessive cross-system coordination.
- **New system insertion test** — could a developer place a new system into the scene tree, dependency graph, tick order, signal model, and authority model using the documented rules alone? Or would they need to copy an existing system by intuition and hope it's right?
- **Mid-tick visibility rules** — when one system mutates authoritative state during its tick, which later systems see the new value this tick, and which earlier systems see last tick's value? Are these rules explicit or assumed?
- **Resume-path architecture** — does architecture.md distinguish cold boot, load-from-save, and resume-from-pause? Are they the same path or different? What about reconnect/reload scenarios?
- **Eventual consistency boundaries** — what must be exact this tick? What may lag one tick? What may be recomputed lazily? What may be stale for UI only? What absolutely cannot lag without changing gameplay?
- **Causal debuggability** — if a gameplay outcome goes wrong (colonist starved, task abandoned, resource vanished), can a developer trace the cause across authority, interfaces, state transitions, and signals without guessing? Is the decision path for actor behavior reconstructable from the docs? Do the docs identify where arbitration, interruption, rejection, and cleanup decisions happen? A model that is implementable but not diagnosable will fail in production.
- **Coordination cost** — does a representative gameplay flow require too many system hops, contracts, or signals to reason about safely? As systems grow, does the number of required cross-system coordination points per flow grow faster than a solo developer can maintain?
- **Architecture weight vs scope** — is this architecture more complex than the gameplay requires? Are there layers, abstractions, or contracts that introduce coordination cost without enabling meaningful gameplay? Would a simpler model produce the same behavior with less cognitive overhead? This catches premature abstraction, enterprise-style overdesign in a solo-dev sim, and systems that exist because they're clean rather than because they're needed.
- **Operational middle** — does the doc bridge high-level rules and implementable behavior? Can a developer determine: how systems obtain what they need, when they react, what is synchronous vs deferred, who triggers transitions, and how recovery works? Or is there a gap between principles and reality that forces developers to infer unwritten conventions?

**state-transitions.md focus (timing layer):**
- **Transition timing vs tick order** — do immediate transitions happen within the owning system's tick? Do queued transitions respect tick boundaries? Could a transition's timing conflict with architecture.md's update semantics?
- **Boot-time state validity** — are initial states defined for every state machine? Can all state machines reach a valid state during boot before the first tick?

**Exemplar findings** (the kind of concrete, divergence-exposing output the reviewer should produce):
- "Your tick model is underspecified. Two developers would implement different signal timing."
- "Your dependency graph is formally downward but functionally cyclic — system X depends on system Y's output from the same tick."
- "Your boot order is hand-waved. Nothing says what happens if system A's _ready() fires before system B exists."
- "Your identity section sounds clean but doesn't answer: what happens when slot 47 is reused?"
- "Your forbidden patterns don't close the loopholes. Rule 3 says no ad hoc calls, but nothing prevents caching a pointer obtained during init and calling it directly forever."
- "A new developer could not add a system without copying an existing one by feel."

Core question: *if you built a new system using only architecture.md, would you build it correctly — or would you make assumptions that contradict undocumented rules?*

### Topic 2 — Ownership & Authority Model

Is the authority model defensible and unambiguous?

**authority.md focus:**
- **Single-writer completeness** — does every piece of mutable gameplay state have exactly one owner? Are there states that fall between systems — owned by neither or tacitly shared?
- **Write mode accuracy** — are the Write Mode classifications (direct/delegated/event-driven) accurate? Does "delegated setter" actually mean the owner validates, or is it a backdoor for shared writes?
- **Derived/cache discipline** — are Derived and Cache entries truly derivable from their sources? Would removing a cache and recomputing from source produce identical results?
- **Persistence ownership** — for every Saved field, is it clear who serializes it and who reconstructs it on load? Are there fields with ambiguous save responsibility?
- **Conflict/TBD resolution trajectory** — are the entries in authority.md's Conflict/TBD section actually resolvable, or are they structural disagreements that indicate deeper design issues?
- **Lifecycle-split authority** — does one system initialize a value, another update it, and a third clear it, with no single system owning the full lifecycle? That pattern looks clean in slices but the value has no true authority across time.
- **Reservation/claim ownership** — who owns assignments, reservations, claims, locks, and pending intents? What invalidates them? When do they expire? What happens on interruption, entity death, or load? These temporary ownership objects are central to sim correctness but often owned nowhere.
- **Arbitration clarity** — when multiple systems influence the same actor or outcome (hunger vs danger, reservation vs reassignment, job priority vs self-preservation), is it clear where final arbitration happens? Perfect ownership with no decision-composition point still produces chaos.
- **Recovery source of truth** — when recovery happens after interruption, corruption, or stale references, which doc layer defines the legal repaired end-state? Authority says who owns, state-transitions says allowed states, interfaces says who was talking. But after breakage, which layer is canonical for determining "what is the correct state now"?
- **Functional ownership overlap** — even if variables differ by name, do multiple systems materially control the same gameplay outcome in a way that makes authority.md technically clean but operationally misleading? Example: three systems all shape colonist work speed through different variables, but no one owns the final player-visible value.
- **Domain grouping quality** — are domains logically organized? Could a developer find any variable's owner within 10 seconds by scanning domain headings?

**entity-components.md focus:**
- **Authority column alignment** — does every Authority column entry match authority.md? When they disagree, is authority.md actually correct (as documented), or has the entity evolved past what authority.md tracks?
- **Convention section quality** — are Entity Reference Convention, Content Identity Convention, Reference Type Conventions, Singleton Conventions, and Derived/Cache Field Policy sections complete enough to guide implementation? Could a developer define a new entity using only these conventions?
- **Component grouping logic** — do component groupings (Identity, Lifecycle, Health, etc.) reflect real data ownership boundaries? Or do components group fields by thematic similarity while ownership is split across systems?
- **Persistence model coherence** — is the Saved/Derived/Transient split consistent with authority.md's Authority Type (Authoritative/Derived/Cache)? Do all Saved fields have authoritative owners?

**Exemplar findings:**
- "Three systems all shape colonist work speed through different variables, but no one owns the final value. Technically no overlap, functionally tangled."
- "Delegated setter on variable X — does the owner actually validate, or is this a backdoor for shared writes?"
- "Derived field Y claims to be recomputable from source Z, but source Z is updated per-tick while Y is cached on-event. They will diverge."
- "Your Conflict/TBD section has 4 entries from 3 months ago. Are these actually resolvable or are they structural?"
- "Persistence Owner is missing for 12 Authoritative fields. Who saves them?"
- "Entity Reference Convention says generational handles, but 4 entities still use bare int in their ref fields."
- "Colonist has 68 fields across 12 components. 3 components are owned by the same system. Should those merge?"
- "Persistence column is empty for 15 fields. A save system developer would not know what to serialize."
- "TraitProfile entity has no lifecycle — it's created once and never destroyed. Is it really an entity or just a data bag?"

Core question: *if two systems both tried to update a value, could authority.md resolve the conflict immediately and unambiguously — or would you need to "ask someone"?*

### Topic 3 — Contract & Interface Quality

Are cross-system contracts complete and realizable?

**interfaces.md focus:**
- **Direction accuracy** — are Push/Pull/Request classifications correct? Are there "Pull" interfaces where the consumer actually reacts to events (should be Push)? Are there "Push" interfaces where the receiver ignores the signal (phantom push)?
- **Realization path completeness** — does every contract have a defined realization (signal/intent/query API/direct call)? Are there contracts with Realization Path: TBD that should be resolved by now?
- **Timing consistency** — does the interface Timing (immediate/deferred/next tick) match what the signal-registry Dispatch Timing Conventions say? Do system designs assume different timing than what's documented?
- **Failure guarantee realism** — are Failure Guarantee classifications accurate? Does "can fail" actually have failure handling documented? Does "no-op" silently swallow errors that should be visible?
- **Contract sufficiency** — do contracts carry enough detail for implementation? Or are they just "System A talks to System B" without specifying what, when, and what guarantees hold?
- **Missing/TBD contracts** — are the entries in the Missing/TBD section actually being tracked, or has the section become stale?
- **Fallback path sufficiency** — when contracts fail, data is missing, references are stale, or handlers reject requests, is the fallback behavior documented clearly enough that two developers would implement the same recovery path? Check: rejection paths for intents, startup/readiness behavior before systems are fully initialized, stale-data handling.
- **Degraded-mode contract behavior** — when required data is missing, stale, or rejected, does the contract define consistent behavior? Not just "can fail" but: does the simulation remain sane when assumptions break? What remains authoritative during degraded operation?
- **Mechanism duplication** — is the same interaction documented as both a query contract and a signal path? Or both an intent and a direct sanctioned call? Multiple mechanisms for the same interaction create "works in two places, breaks in edge cases" behavior. Each interaction should have one canonical mechanism.
- **Authority-to-trigger clarity** — for state-changing contracts, is it clear who detects the condition vs who owns the state vs who performs the transition? If one system detects and another owns, is the handoff explicit (signal → owner transitions) or ambiguous (either could do it)?
- **Contract stability** — are any contracts already showing signs they want to split into two narrower contracts? A contract that covers "all resource movement" may actually be hiding separate hauling, storage, and trade contracts with different timing and failure guarantees.
- **Contract granularity** — are contracts too vague to implement, or too over-specified for a reference doc? A Step 3 contract should define required data, timing, and guarantees without drifting into engine-level implementation. Underfit: "System A sends data to System B." Overfit: "System A calls B.process_update(dict) at line 42 of tick handler."

**signal-registry.md focus:**
- **Interface-to-signal traceability** — does every Push interface have a signal? Does every Request interface have an intent? Flag any interface with no signal/intent counterpart.
- **Payload sufficiency** — do signal payloads carry enough information for consumers to act? Do consumers need to make follow-up queries because the payload is too thin?
- **Consumer completeness** — is every system that could reasonably need a signal actually listed as a consumer? Are there systems that read related state but aren't wired to the notification?
- **Intent handling guarantees** — for intent objects, is it clear what happens when the handler rejects the request? Does the requester have a fallback?
- **Level classification accuracy** — are Entity/Room/System/Colony/Global classifications correct? Does the level match the actual scope of impact?
- **Delivery expectation realism** — are fire-and-forget signals actually acceptable to lose? Are "reliable" signals actually implemented with delivery guarantees?
- **Dispatch timing convention alignment** — do individual signal entries respect the project-wide timing conventions?
- **Payload schema compliance** — do payloads follow the documented conventions (snake_case, entity handles not raw pointers, Vector2i for grid positions, enums from enums-and-statuses)?
- **Semantic signal duplication** — are two signals expressing almost the same event with slightly different payloads or names? Event-model bloat creates wiring confusion and consumer ambiguity.

**Exemplar findings:**
- "Interface between TaskSystem and WorkAI says Pull, but WorkAI actually reacts to task_state_changed signals. That's Push, not Pull."
- "5 contracts have Realization Path: TBD. Engine docs exist. These should be resolved."
- "Failure Guarantee says 'no-op' for 8 contracts. That means 8 places where errors are silently swallowed. Is that intentional?"
- "Contract says 'immediate' timing but architecture.md says signals are queued. Which is true?"
- "grid_quality_changed has 15 consumers. That is signal fan-out that will be debugging hell. Should some consumers pull instead?"
- "8 signals have Delivery Expectation: fire-and-forget but are consumed by systems that make gameplay decisions. If the signal is lost, the decision is wrong."
- "Intent objects have no rejection path documented. What happens when a hauling_request is rejected because no colonist is available?"
- "Dispatch Timing Conventions section says 'during tick' for most signals but architecture.md's Simulation Update Semantics is still TBD. These can't both be right."

Core question: *could you implement all cross-system communication using only interfaces.md and signal-registry.md, without needing to read individual system docs to figure out what's actually exchanged?*

### Topic 4 — Data Model Fitness

Is the data model sound for the game's needs?

**authority.md supporting context:**
- Topic 4 reviews data model fitness, but much of that depends on authority. When reviewing entity-components, resource-definitions, or balance-params, cross-check whether ownership and persistence claims are consistent with authority.md. Flag cases where component grouping implies ownership boundaries that authority.md doesn't confirm.

**entity-components.md focus:**
- **Entity completeness** — does every entity have all the fields it needs for the behaviors described in system designs? Are there system behaviors that would require fields not yet in entity-components?
- **Type precision** — are field types specific enough for implementation? Are there `dict` or `list` types that should have inner types documented? Are enum fields backed by registered state machines?
- **Singleton modeling** — are singleton entities (Colony, World, PowerGrid) correctly identified and documented? Is it clear how they differ from pooled entities?
- **Over-entityfication check** — are there entities with fewer than 3 fields and no lifecycle that shouldn't be entities? Are there abstract concepts modeled as entities that should be simple values?
- **Data lifecycle fit** — do entities/resources/states/params reflect not just what exists, but when it comes into existence, when it becomes invalid, and when it is removed or recomputed? Bad lifecycle modeling causes silent bugs even when types and fields look correct.
- **Container schema sharpness** — are `list`, `dict`, `map`, and `set` fields challenged when inner types are underspecified? A field typed `dict` without documenting key type and value type forces implementers to guess.
- **Cross-field invariants** — are there fields that only make sense in combination? Fields that must be updated together, or that have implicit constraints between them (e.g., hp <= hp_max, morale_value drifts toward morale_target) should have those relationships documented, not just individually listed.
- **In-flight object lifecycle** — are queued jobs, reservations, pending actions, claims, and temporary locks modeled anywhere? These objects are central to sim correctness but often fall between entity-components, state-transitions, and authority — owned nowhere. If the game has reservations, assignments, or pending intents, they need explicit lifecycle rules.
- **Global runtime invariants** — are there cross-field or cross-entity truths that should be documented? Examples: a reservation cannot exist without a valid reserving actor and target; an entity cannot be both destroyed and reachable; an owned value cannot be updated by two systems in the same tick; every queued intent must end in handled/rejected/expired.

**resource-definitions.md focus:**
- **Resource coverage** — do resource definitions cover everything system designs consume, produce, or store? Are there resources mentioned in system designs but missing from this doc?
- **Production chain completeness** — can every Tier 2+ resource be traced back to Tier 1 sources through documented chains? Are station assignments correct?
- **Fungibility accuracy** — are fungible/unique classifications correct? Could a system accidentally treat a unique item as fungible? Are there resources that should be unique (quality variants, named items) but are marked fungible?
- **Storage type coverage** — do storage types cover all resource handling needs? Are refrigerated/secure classifications correct for gameplay?
- **Resource state variants** — are transformation states (raw→refined, fresh→spoiled) tracked? Do they overlap with state-transitions.md state machines?
- **Economic closure** — can every produced resource be sourced, transformed, consumed, stored, decayed, or sunk somewhere? Are there resources defined but not meaningfully used by any system or chain (dead definitions)?
- **Logistics truth** — can the documented storage types, transportability values, and production chains actually support movement through the simulation? Are there resources that are economically defined but operationally impossible to move, store, or consume under the current contracts and system designs?

**balance-params.md focus:**
- **Parameter coverage** — do balance params exist for all tunable system behaviors? Are there system designs that describe thresholds, rates, or capacities without corresponding params?
- **Type accuracy** — are parameter types (threshold/rate/duration/capacity/multiplier) correct? Is a "rate" actually a threshold? Is a "multiplier" actually a capacity?
- **Dependency accuracy** — do dependency notes capture real parameter relationships? Are there interacting parameters with empty dependency notes?
- **Range realism** — are min-max ranges plausible? Are there ranges so wide they're meaningless (0-999999) or so narrow they prevent tuning?
- **TBD density** — what percentage of parameters are still TBD? For systems that have been implemented, are params still TBD?
- **Behavioral anchor** — for each parameter, is it clear what player-visible behavior this governs? A parameter without a clear gameplay effect is either misplaced or a sign that the behavior itself isn't well understood.
- **Tuning isolation** — is tuning this value in isolation actually meaningful, or does it only make sense when tuned together with other parameters? Interdependent parameters documented in isolation become tuning traps.
- **Hidden constants outside doc** — are important behavioral constants still embedded implicitly in system designs, state-transition triggers, or interface assumptions instead of registered here? Fragmented tuning authority means real numbers live in prose instead of the params doc.

**state-transitions.md focus:**
- **State machine coverage** — do state machines cover all discrete states described in system designs? Are there system behaviors that imply state transitions not documented here?
- **Trigger specificity** — are transition triggers specific enough for implementation? "Condition changes" is too vague; "HP reaches zero" is concrete.
- **Timing accuracy** — are timing values (immediate/queued/end-of-tick) consistent with architecture.md's simulation update semantics?
- **Invariant testability** — could each invariant be checked at runtime? Vague invariants ("system behaves correctly") don't count.
- **Illegal transition coverage** — for complex state machines (5+ states), are illegal transitions documented? Are there obviously dangerous transitions that aren't listed as illegal?
- **Interrupted/invalidated transition handling** — what happens when a transition is interrupted, invalidated mid-flow, or triggered on a stale entity? If a colonist starts transitioning to Working but the task is cancelled during the same tick, which state wins? This is a classic sim bug seam.

**enums-and-statuses.md focus:**
- **Shared vocabulary completeness** — does the doc capture all genuinely cross-system states? Are any single-system states leaking into shared vocabulary?
- **Name consistency** — do state names exactly match state-transitions.md? Are there synonyms or near-duplicates?
- **Authority accuracy** — does each enum's Owning Authority match authority.md and state-transitions.md?
- **Source of Truth clarity** — is it clear for each enum whether the canonical definition lives in state-transitions, authority, interfaces, or UI?
- **Deprecated synonym tracking** — are historical synonyms tracked to prevent terminology regression?
- **Simulation truth vs presentation** — does each enum represent simulation truth (authoritative state), interpretation (derived band/classification), or presentation (UI label)? That boundary gets muddy fast. Simulation-facing vocab belongs here; player-facing display labels belong in glossary or UI docs.

**Exemplar findings:**
- "Colonist lifecycle has 5 states but no illegal transitions listed. Can a Dead colonist transition to Sleeping?"
- "State machine 7 says timing is 'immediate' for all transitions, but the owning system ticks at position 15. 'Immediate' means 'within that system's tick', not 'globally immediate'. That's confusing."
- "Production job lifecycle has no entry conditions. Can a job enter this state machine before the station exists?"
- "Spectral Filaments are Tier 3 / expedition-only but have no production chain entry and no exemption in Source."
- "Iron Ore is fungible but entity-components has an Item entity with individual identity. Are iron ore items tracked individually or as a count?"
- "Resource State Variants section is empty. But system designs describe raw→refined, fresh→spoiled transformations."
- "40% of parameters are TBD. For implemented systems, 12 params are still TBD. Those should have values by now."
- "hunger_decay_rate and fatigue_decay_rate have identical ranges but no dependency note connecting them."
- "Colonist lifecycle states here say Idle/Working/Sleeping/Downed/Dead but state-transitions also includes 'Eating' as a transition target. Which is canonical?"
- "3 enums have Owning Authority blank. Who decides what 'Brownout' means?"
- "Construction states are listed here AND as resource state variants in resource-definitions. Blueprint→Placed→UnderConstruction overlaps both docs."

Core question: *could you write all the data structures and state machines from these docs alone, and have them be correct for the game described in the design doc?*

### Topic 5 — Cross-Doc Consistency

Do all 9 docs agree with each other?

This topic is the most important and should receive the most scrutiny. It reviews the seams between documents — the places where two docs describe the same thing and might disagree.

**Doc-pair checks:**
- **Architecture ↔ Authority** — do architecture.md's ownership rules match authority.md's table? Does the single-writer rule in data flow rules match the actual authority entries?
- **Authority ↔ Entity-Components** — Authority column derivation is correct. Persistence columns are consistent. No orphan fields in one but not the other.
- **Interfaces ↔ Signal Registry** — every Push interface has a signal. Signal consumers match interface targets. Timing matches. Payload is consistent with data exchanged.
- **State-Transitions ↔ Enums-and-Statuses** — state names match exactly. Owning authorities agree. Cross-system states appear in both docs.
- **State-Transitions ↔ Entity-Components** — every state machine's entity has corresponding enum fields. State names match field type.
- **Architecture ↔ State-Transitions** — tick order doesn't create state-transition timing violations. Boot order doesn't allow transitions before authority systems are ready.
- **Resource-Definitions ↔ Entity-Components** — fungible resources are not duplicated as entities. Unique items that are also resources have clear modeling boundaries.
- **Balance-Params ↔ System Designs** — every parameterized system behavior has balance params. No orphan params referencing nonexistent systems.
- **Architecture ↔ Interfaces** — interfaces respect the data flow rules and forbidden patterns. No interface implies a forbidden communication pattern.
- **Architecture ↔ Signal Registry** — signals in the wiring map exist in signal-registry. Gameplay/Logging classification matches wiring location (behavioral vs logging).
- **All ↔ Glossary** — canonical terminology used consistently across all 9 docs.
- **Canonical drift by detail gravity** — is a lower-rank doc more detailed, more current-looking, or more implementation-shaped than its canonical higher-rank source? Flag places where the practical source of truth is drifting downward even if the formal authority order is documented correctly. This is the most dangerous form of drift because it looks justified.
- **Abstraction-level drift** — is the same concept defined as authoritative state in one doc, derived classification in another, and UI/display vocabulary in a third, without anyone noticing they're at different abstraction levels? Example: `morale_value` (entity-components) vs `morale_band` (enums) vs `morale_state_changed` (signal-registry) vs `mood` (glossary/UI). Not just terminology drift — abstraction drift.
- **Practical reading order vs formal authority** — if a developer moving fast opens entity-components.md before authority.md, or signal-registry.md before interfaces.md, does the practical reading order produce correct understanding? If lower-rank docs are easier to read and more detailed, they become the de facto canon regardless of rank.

**Exemplar findings:**
- "authority.md says SystemA owns mood, entity-components shows SystemB in the Authority column, and interfaces shows SystemC pushing mood updates. Terminology is consistent; meaning is not."
- "entity-components has 8 fields with no matching authority.md entry. Are those fields authoritative, derived, or orphaned?"
- "interfaces.md says Push for contract X but signal-registry lists the signal with 0 consumers. Phantom push."
- "State-transitions uses 'Brownout' but enums-and-statuses uses 'PowerLow'. Which is canonical?"
- "Resource-definitions and entity-components both model items — fungible ore is tracked as both a resource count and an Item entity. Double-modeling."
- "entity-components is more detailed and current than authority.md. Developers will trust entity-components as the source of truth even though authority.md formally outranks it."

Core question: *if you read all 9 docs in sequence, would you encounter any contradictions — or would they tell one consistent story?*

### Topic 6 — Simulation Readiness

Could a developer implement from these docs without guessing?

This is the integration test. It evaluates whether the complete Step 3 doc set is sufficient for downstream work. Review each doc for its contribution to implementation clarity.

**Per-doc readiness:**
- **architecture.md** — could a developer set up the scene tree, wire signals, and integrate a new system using only this doc?
- **authority.md** — could a developer resolve any "who owns this?" question using only this table?
- **interfaces.md** — could a developer implement a cross-system interaction using only this contract?
- **state-transitions.md** — could a developer implement a state machine using only this definition?
- **entity-components.md** — could a developer define all data structures using only this registry?
- **resource-definitions.md** — could a developer implement resource handling using only this doc?
- **signal-registry.md** — could a developer wire all signals using only this registry?
- **balance-params.md** — could a developer parameterize a system using only this doc?
- **enums-and-statuses.md** — could a developer use shared vocabulary correctly using only this doc?

**Integration checks:**
- **Spec derivation readiness** — could behavior specs be written against these docs? Are there system behaviors documented in system designs that have no corresponding authority, interface, state machine, or signal backing them?
- **Implementation path clarity** — for each major system, is the implementation path clear? Does the developer know: what data to store (entity-components), who owns it (authority), what signals to emit (signal-registry), what contracts to honor (interfaces), what states to track (state-transitions), what numbers to use (balance-params)?
- **Gap detection** — what's the biggest thing missing? Not "this could be improved" but "a developer would get stuck here and not know what to do."
- **Ambiguity detection** — where could two developers legitimately interpret these docs differently and build incompatible implementations?
- **Foundation decision coverage** — are all 6 foundation areas (identity, content-definition, storage, save/load, spatial, API boundaries) addressable from these docs? Are any still effectively Undefined despite having content?
- **Downstream handoff readiness** — could Step 4 engine docs be written from this architecture? Could Step 7 foundation locking proceed? Could specs be derived without inventing missing contracts, ownership assignments, or state semantics? If any downstream step would need to invent information this step should have provided, that's a gap.
- **Multi-developer divergence test** — if two competent developers independently implemented the same system from these 9 docs, where are they most likely to diverge? That divergence point is the highest-priority ambiguity to resolve.
- **Interrupted-path test** — trace a representative flow where the target disappears mid-process (e.g., colonist walking to food, food gets consumed by another colonist). Does every doc involved handle the interruption? Authority, state machine, signal, interface, entity lifecycle? Critically: who cleans up? Who clears stale reservations, removes invalid queued intents, releases references to destroyed entities, and reconciles half-complete transitions? Not just "is it handled" but "which system is responsible for cleanup." Without that, everybody assumes somebody else does it.
- **Resume-path test** — trace a representative flow across save/load. Are handles revalidated? Are in-flight tasks/reservations/intents restored or cleaned up? Does the simulation reach a consistent state after load without manual intervention?
- **Minimum implementable path test** — pick one representative gameplay flow (e.g., colonist gets hungry → chooses food task → reserves food → walks → food becomes unavailable → task fails → state recovers → hunger keeps updating → UI reflects it) and trace it through all 9 docs. Does every step have authority, interface, signal, state machine, and entity coverage? This exposes missing seams faster than any per-doc review.

**Genre / Simulation Fit:**

Does this architecture fit the needs of a stateful, simulation-heavy colony/management game with persistent world state, interruption-heavy workflows, and multi-system causality?

- **Simulation-first vs application-first** — does this reference model treat time, interruption, stale targets, and continuous world churn as first-class concerns? Or does it assume rare, discrete state changes like a CRUD/business app?
- **Interruption as default, not exception** — in a colony sim, the normal flow is: colonist starts task → something changes → task is interrupted → state must recover. Does the architecture make that the primary design path, or is happy-path completion the assumed default with interruption bolted on?
- **Long-lived entity fitness** — entities in this game live a long time and accumulate state (injuries, memories, relationships, skills, trait effects). Does the data model support growing entity complexity without becoming fragile?
- **Multi-system causality** — a single gameplay outcome (colonist refuses to work) may result from morale + needs + traits + injuries + zone restrictions + task availability. Does the architecture make that causal chain traceable, or does it fragment across so many systems/signals that debugging emergent behavior becomes impossible?
- **Reservation/claim centrality** — colony sims depend heavily on reservations, assignments, and claims (food reserved, bed assigned, task claimed, resource locked). Is that lifecycle explicit and well-owned, or is it an afterthought?
- **Save/load of live world** — this game saves a running simulation with in-flight tasks, partial construction, active needs, queued jobs. Does the architecture support saving and restoring that mid-flow state, not just static configuration?
- **Scalability of sim layers** — as more systems are added (combat, expeditions, research, diplomacy), does the architecture stay understandable? Or is it already at the edge of what one developer can reason about?
- **Determinism and debuggability** — can a developer trace why a colonist starved, why a task was abandoned, why a resource disappeared? Or does the architecture make emergent behavior opaque?
- **Genre-hostile patterns** — is anything in the current model elegant on paper but hostile to the kind of gameplay the game actually needs? Too much event indirection for a sim that needs deterministic sequencing? Too much ownership fragmentation for a game where one actor's behavior depends on many systems?

**Genre fit exemplar findings:**
- "This architecture is coherent, but it is too event-fragmented for a sim where deterministic sequencing matters."
- "Ownership is technically clean, but actor behavior is spread across too many systems for the gameplay style."
- "The model handles happy-path task execution better than disruption, which is backwards for this genre."
- "The design assumes state changes are rare and discrete, but this game depends on constant continuous world churn."
- "Reservation lifecycle is not modeled as a first-class concern anywhere. For a colony sim, that is a structural gap."

**Exemplar findings:**
- "System designs describe morale affecting work speed, but no interface contract, signal, or balance parameter captures this interaction. A spec writer would have to invent it."
- "A developer implementing TaskSystem would know what data to store and who owns it, but would not know when intent objects are processed relative to the tick — the timing path is undocumented."
- "The biggest gap is startup behavior. No doc describes what happens on game load — the identity model says handles are validated, but no doc says what happens to in-flight tasks whose worker handle is stale."
- "Two developers would diverge on signal timing. One would implement immediate dispatch, the other queued. Architecture.md's Simulation Update Semantics is TBD."
- "Step 4 engine docs cannot be written without first deciding the identity model. That's still TBD in architecture.md. Step 3 is blocking Step 4."

Core question: *are these 9 docs, combined with the system designs from Step 2, sufficient to begin planning — or are there gaps that would make downstream specs or tasks ambiguous?*

**After all topics complete**, the reviewer must answer final questions and provide a rating:

1. **What is the single most dangerous cross-doc inconsistency?** — the mismatch most likely to cause implementation bugs if not caught.

2. **What could a developer get wrong despite reading all 9 docs?** — the implicit assumption or undocumented rule most likely to cause a subtle implementation error.

3. **Which doc is weakest?** — the doc that contributes least to implementation clarity or has the most unresolved content.

4. **Blocker classification** — for each issue found, classify its downstream impact:
   - **Blocks Step 4 (Engine)** — can't write engine docs without this resolved
   - **Blocks specs** — can't derive behavior specs without this resolved
   - **Blocks tasks** — can't write implementation tasks without this resolved
   - **Does not block, increases risk** — implementation can proceed but this will cause pain later

5. **Reference Model Strength Rating (1–5):**
   - 1 = fundamentally broken (major cross-doc contradictions, critical docs mostly TBD)
   - 2 = major gaps (authority unclear, interfaces incomplete, identity model unresolved)
   - 3 = workable but risky (some cross-doc drift, several TBD areas, ambiguity in key spots)
   - 4 = solid reference model (docs mostly consistent, minor gaps bounded, implementation path clear)
   - 5 = strong reference model (all docs consistent, no contradictions, developer could implement from docs alone)

## Reviewer Bias Pack

Include these detection patterns in the reviewer's system prompt. They represent the most common failure modes in reference doc sets.

1. **Surface consistency, deep contradiction** — all docs use the same terms and system IDs, but the actual semantic content disagrees. Authority.md says System A owns mood, but entity-components shows System B in the Authority column, and interfaces.md shows System C pushing mood updates. The terminology is consistent; the meaning is not.

2. **Phantom completeness** — every section has content and every table has rows, but the content is template-level or mechanically derived without real design thinking. Well-structured emptiness. Test: could you derive a non-trivial spec from this content?

3. **Missing middle** — high-level rules exist (architecture.md) and low-level data exists (entity-components), but the operational middle is missing. No one documented *how* the rules apply to the data. Interfaces list what flows but not what guarantees hold. State machines list states but not timing.

4. **Optimistic contract design** — interfaces assume everything works. No failure guarantees. No "what if the handler rejects." No "what if the source doesn't have the data yet." Real systems fail; contracts that don't account for failure are incomplete.

5. **Identity hand-waving** — the identity section exists but doesn't answer the hard questions: what happens on reuse? What survives save/load? How do cross-references validate? A well-written identity section that doesn't answer these questions is more dangerous than an empty one (because it implies the questions are answered).

6. **Circular derivation** — entity-components says "Authority: per authority.md." Authority.md says "derived from system Owned State." System Owned State says "see entity-components for field list." Each doc defers to the others, but no doc is the actual source. One doc must be the canonical anchor for each piece of information.

7. **Silent temporal assumptions** — system designs assume a timing model that architecture.md doesn't explicitly define. Signals are assumed immediate but the dispatch model says queued. State transitions are assumed atomic but tick ordering creates one-tick delays. The most common source of implementation bugs in simulation games.

8. **Vocabulary fragmentation** — the same concept has different names across different docs. "morale_state" in entity-components, "morale_band" in state-transitions, "mood_level" in authority.md. All refer to the same thing. The glossary is clean, but the reference docs aren't.

## Per-Doc Mandatory Interrogation

For every Step 3 doc in scope, the reviewer must run the doc's specialized failure-mode check **in addition to** the topic questions. This is not optional — it is mandatory. Each doc owns a different dimension of the simulation contract.

### architecture.md

**Unique responsibility:** How systems are structured, ordered, and wired — the engineering skeleton.

**Attack surface:**
- **Ordering bugs** — where would tick-ordering bugs appear first? Which system pairs have the tightest freshness dependency?
- **Timing assumptions** — what assumption about "same tick" vs "next tick" is most likely wrong or undocumented?
- **Identity edge cases** — what happens when a handle slot is reused? When a reference survives save/load but the target doesn't? When two systems hold references to the same entity and one destroys it?
- **Boot races** — can any system's init depend on another system that hasn't initialized yet? Can signals fire before wiring is complete?
- **Mid-tick visibility** — when System A mutates state during its tick, which later systems see the new value this tick? Is this rule explicit or assumed?
- **Operational middle gap** — does the doc bridge high-level rules and implementable behavior, or is there a gap developers must fill by convention?

**Questions the reviewer must answer:**
1. Where would ordering bugs appear first?
2. What assumption about timing is most likely wrong?
3. What behavior depends on undocumented "same tick" guarantees?

---

### authority.md

**Unique responsibility:** Who owns what — single-writer discipline for every piece of mutable state.

**Attack surface:**
- **Functional overlap** — can two systems both effectively control the same player-visible outcome through different variables, making authority technically clean but operationally misleading?
- **Lifecycle-split authority** — does one system initialize a value, another update it, and a third clear it? That pattern has no true single owner across time.
- **Reservation/claim ownership** — who owns assignments, reservations, claims, locks, and pending intents? What invalidates them? Who cleans up on interruption or entity death?
- **Arbitration clarity** — when multiple systems influence the same outcome (hunger vs danger, job priority vs self-preservation), where does final arbitration happen?
- **Recovery source of truth** — after interruption or corruption, which doc layer determines "what is the correct state now"?

**Questions the reviewer must answer:**
1. Where can two systems still both effectively control the same outcome?
2. What lifecycle has no single owner across time?
3. What breaks during interruption or cleanup — who clears stale state?

---

### interfaces.md

**Unique responsibility:** Cross-system contracts — what data flows between systems, with what guarantees.

**Attack surface:**
- **Fallback path sufficiency** — when contracts fail, data is missing, or handlers reject, is the fallback behavior documented clearly enough that two developers implement the same recovery?
- **Mechanism duplication** — is the same interaction documented as both a signal and a query, or both an intent and a direct call? Multiple mechanisms for the same thing create edge-case divergence.
- **Authority-to-trigger clarity** — for state-changing contracts, is it clear who detects the condition vs who owns the state vs who performs the transition?
- **Contract stability** — are any contracts already showing signs they want to split into narrower contracts?
- **Contract granularity** — are contracts too vague to implement ("System A sends data to System B") or too engine-specific ("calls B.process_update(dict)")?

**Questions the reviewer must answer:**
1. Which contract is most likely to fail in real gameplay?
2. Where is fallback behavior undefined?
3. Which contract will be implemented differently by two developers?

---

### state-transitions.md

**Unique responsibility:** Discrete state machines — what states exist, what transitions are legal, and what timing governs them.

**Attack surface:**
- **Interrupted transitions** — what happens when a transition is interrupted mid-flow? If a colonist starts transitioning to Working but the task is cancelled during the same tick, which state wins?
- **Missing illegal transitions** — for complex state machines (5+ states), which obviously dangerous transitions are not explicitly listed as illegal?
- **Timing ambiguity** — does "immediate" mean within the owning system's tick, or globally instant? Could a developer get this wrong?
- **Boot-time validity** — are initial states defined for every state machine? Can all machines reach a valid state before the first tick?
- **Cross-machine coordination** — when two state machines interact (entity lifecycle + task lifecycle), are the coordination points explicit?

**Questions the reviewer must answer:**
1. Which transition is ambiguous under interruption?
2. Which state machine is missing illegal transitions?
3. Which transitions depend on timing not guaranteed by architecture.md?

---

### entity-components.md

**Unique responsibility:** Entity data shapes — what fields exist, who owns them, how they persist.

**Attack surface:**
- **Irrecoverable data** — which fields, if lost or corrupted, cannot be reconstructed from other state? Those are the highest-risk persistence targets.
- **Lifecycle gaps** — are there fields with unclear creation/destruction timing? Fields that are written once and never updated but also never explicitly frozen?
- **Stale reference accumulation** — which `ref`-type fields are most likely to hold stale handles? Are validation rules documented for each?
- **Container schema sharpness** — are `list`, `dict`, `set` fields challenged when inner types are unspecified?
- **Cross-field invariants** — are there fields that only make sense in combination (hp ≤ hp_max, morale drifts toward target)? Are those relationships documented?
- **In-flight objects** — are reservations, queued jobs, pending intents, and claims modeled here? Or do they fall between entity-components and authority?

**Questions the reviewer must answer:**
1. What data cannot be reconstructed if lost?
2. Which fields have unclear lifecycle — created but never explicitly managed?
3. Where will stale references accumulate fastest?

---

### resource-definitions.md

**Unique responsibility:** Resources, production chains, and the economic model.

**Attack surface:**
- **Operational viability** — can every defined resource actually flow through the simulation? Are there resources that are economically defined but operationally impossible to move, store, or consume under current contracts?
- **Dead resources** — are there resources defined but not meaningfully used by any system, chain, or gameplay mechanic?
- **Production chain completeness** — can every Tier 2+ resource be traced back to Tier 1 sources? Are there broken chains?
- **Logistics realism** — do storage types, transportability values, and hauling contracts support real movement through the sim?
- **Fungible/unique confusion** — are any resources modeled as both fungible counts and unique item entities?

**Questions the reviewer must answer:**
1. Which resource cannot actually flow through the sim as designed?
2. Which production chain is incomplete or broken?
3. Which resource is defined but unused by any system?

---

### signal-registry.md

**Unique responsibility:** The event vocabulary — what signals exist, what they carry, who fires them, who consumes them.

**Attack surface:**
- **Fan-out risk** — which signals have too many consumers? High fan-out creates debugging opacity and ordering sensitivity.
- **Semantic duplication** — are two signals expressing almost the same event with slightly different payloads? Event model bloat creates wiring confusion.
- **Delivery guarantee realism** — are fire-and-forget signals actually safe to lose? Are "reliable" signals actually reliable in the engine?
- **Missing critical events** — are there gameplay-critical state changes with no corresponding signal? Systems that need to know but aren't wired?
- **Payload sufficiency** — do consumers need follow-up queries because the payload is too thin?
- **Redundancy** — for critical gameplay events, is there a backup channel if the signal is missed?

**Questions the reviewer must answer:**
1. Which signals are overloaded (too many consumers, too broad)?
2. Which critical events are missing signal coverage entirely?
3. Which signals should not exist (duplicates, unused, or misclassified)?

---

### balance-params.md

**Unique responsibility:** Tunable numbers — rates, thresholds, capacities, multipliers.

**Attack surface:**
- **Tuning coupling** — which parameters cannot be tuned independently? Interdependent parameters documented in isolation become tuning traps.
- **Hidden constants** — are important behavioral numbers still embedded in system designs, state-transition triggers, or interface assumptions instead of registered here?
- **Player-visible mapping** — for each parameter, is it clear what player-visible behavior it governs? A parameter without a clear gameplay effect is misplaced or a sign the behavior isn't understood.
- **Behavioral anchoring** — does each parameter have a testable impact? "Mood decay rate" should predictably affect visible mood over a known time period.
- **TBD density** — for systems that have been designed and are ready for implementation, are their parameters still TBD?

**Questions the reviewer must answer:**
1. Which parameters cannot be tuned independently?
2. Which parameters don't map to player-visible behavior?
3. Which important numbers are secretly defined elsewhere (in prose, in system docs, in state-transition triggers)?

---

### enums-and-statuses.md

**Unique responsibility:** Shared cross-system vocabulary — state names that must mean the same thing everywhere.

**Attack surface:**
- **Abstraction layer split** — is each enum simulation truth (authoritative state), derived interpretation (computed band/classification), or presentation (UI label)? That boundary gets muddy. Simulation vocab belongs here; display labels belong in glossary.
- **Naming drift** — do enum values exactly match state-transitions.md? Are there near-synonyms that will cause bugs?
- **Enum explosion** — are there enums that are growing unbounded? Enums with 15+ values may be masking a data model problem.
- **Single-system leaks** — are there enums only used by one system that shouldn't be in the shared vocabulary?
- **Authority gaps** — does every shared enum have an explicit owning authority? Who decides what "Brownout" means?

**Questions the reviewer must answer:**
1. Where is vocabulary split across abstraction layers (simulation vs interpretation vs UI)?
2. Which enums are presentation, not simulation — and shouldn't be here?
3. Where will naming drift reappear first?

---

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--target` | No | all | Target a single doc by filename (e.g., `--target architecture.md`). When set, topics are scoped to the targeted doc's concerns — but cross-doc topics (5, 6) still read all docs. |
| `--topics` | No | all | Comma-separated topic numbers to review (e.g., `"1,5,6"`). Used by revise-foundation when only certain areas need adversarial review. |
| `--focus` | No | — | Narrow the review within each topic to a specific concern. |
| `--iterations` | No | 10 | Maximum outer loop iterations. Stops early on convergence. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic. |
| `--signals` | No | — | Design signals from fix-references to focus the review on known issues. Format: comma-separated signal descriptions. |

### --target to --topics mapping

When `--target` is set without explicit `--topics`, the skill automatically selects the relevant topics:

| Target | Auto-selected Topics |
|--------|---------------------|
| `architecture.md` | 1, 5, 6 |
| `authority.md` | 2, 5, 6 |
| `interfaces.md` | 3, 5, 6 |
| `state-transitions.md` | 4, 5, 6 |
| `entity-components.md` | 2, 4, 5, 6 |
| `resource-definitions.md` | 4, 5, 6 |
| `signal-registry.md` | 3, 5, 6 |
| `balance-params.md` | 4, 6 |
| `enums-and-statuses.md` | 4, 5, 6 |

Topics 5 (Cross-Doc Consistency) and 6 (Simulation Readiness) are always included because they evaluate doc interactions.

Explicit `--topics` overrides this mapping.

## Preflight

Before running external review:

1. **Check docs exist.** Verify at least architecture.md, authority.md, interfaces.md, and entity-components.md exist and are not at template defaults. If fewer than 4 Step 3 docs exist, stop: "Reference docs not ready. Run `/scaffold-bulk-seed-references` first."
2. **Check fix-references has run.** Verify the docs are structurally clean — no missing required sections, no invalid enumerated values. If structural issues remain, stop: "Run `/scaffold-fix-references` first to normalize structure."
3. **Check design doc exists.** The reviewer needs Design Invariants and governance as context.

## Context Files

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| All 9 Step 3 docs | Primary targets |
| `design/design-doc.md` | Design Invariants, governance, vision — high-authority context |
| `design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| `design/systems/_index.md` + system files | System design cross-check |
| `decisions/known-issues/_index.md` | Known gaps and constraints |
| Engine docs (if they exist) | Viability verification for architecture decisions |
| ADRs with status `Accepted` | Decision compliance |
| Design signals from fix-references (if `--signals` provided) | Focus areas for the reviewer |

Only include context files that exist — skip missing ones silently.

## Execution

### Loop Structure

```
Outer Loop (iterations — fresh review of updated docs)
├── Per Topic (6 topic questions):
│   └── Inner Loop (exchanges — back-and-forth conversation)
│       ├── Reviewer raises issues (structured JSON via doc-review.py)
│       ├── Claude evaluates each: AGREE / PUSHBACK / PARTIAL
│       ├── Reviewer counter-responds
│       └── ... until consensus or max-exchanges
│   └── Consensus: reviewer summarizes final position
│   └── Apply changes: accepted issues applied to Step 3 docs
│
├── Per Doc in scope (mandatory interrogation):
│   └── Reviewer answers doc-specific failure-mode questions
│   └── Claude evaluates findings against existing topic results
│   └── Deduplicate: merge with topic findings by root cause
│
└── Cross-topic consistency check → resolve contradictions
```

Each topic gets its own review → respond → consensus cycle via the Python `doc-review.py` script. After topics complete, the per-doc mandatory interrogation runs for each doc in scope. Findings are deduplicated against topic results by root cause. After all topics and per-doc checks in one outer iteration, re-read updated docs and start the next outer iteration if issues remain.

**Stop conditions** (any one stops iteration):
- **Clean** — a complete topic pass produces no new issues.
- **Converged** — two consecutive passes produce the same issue set with no new findings.
- **Human-only** — only issues requiring user decisions remain; further iteration won't resolve them.
- **Limit** — `--iterations` maximum reached.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying concern count as the same issue. Examples:
- "authority boundary unclear" and "ownership conflict between systems" → same issue if they stem from the same authority gap.
- "interface contract incomplete" and "missing return type on contract" → same issue if about the same contract.

**Lock enforcement:**
- The reviewer must NOT reintroduce a resolved issue in a different form.
- The reviewer must NOT raise stricter variants of a resolved issue unless: (a) new evidence exists that wasn't available when the issue was resolved, OR (b) the fix itself introduced a new problem.
- If a previously resolved issue reappears: classify it as a **review inconsistency**, not a new issue. Prefer rejecting the reappearance unless the reviewer provides materially different evidence.

**Cross-topic lock:** If Topic 1 resolves an issue, later topics may not re-raise it under a different name. The cross-topic consistency check catches this retroactively, but the lock prevents wasted exchanges proactively.

**Tracking:** Maintain a running resolved-issues list in the review log during execution. Before engaging with any new reviewer claim, check it against the resolved list by root cause. If it matches, reject with "previously resolved — see [iteration N, topic M]."

**Edit scope:**
- When `--target` is set, only edit the targeted doc. Flag cross-doc issues for fix-references.
- When `--target` is not set, edit any of the 9 Step 3 docs.
- Never edit system designs, design-doc, engine docs, or planning docs.

### Issue Adjudication

Every issue raised by the reviewer must be classified into exactly one outcome:

| Outcome | Action |
|---------|--------|
| **Accept → edit Step 3 doc** | Apply change immediately. The issue is valid and the fix is within Step 3 doc scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or the issue is out of scope. |
| **Escalate to user** | Requires design judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag for revise-design** | Design doc (Rank 1-2) is likely incomplete or incorrect. The Step 3 doc may be right; design needs updating. |
| **Defer (valid TBD)** | The section is correctly blocked by an unresolved design decision. Not a gap — an honest wait. |
| **Flag ambiguous design intent** | Design doc (Rank 1-2) permits multiple valid architectural interpretations and the Step 3 doc chose one. Not incorrect — genuinely ambiguous upstream. Flag for user decision to lock the interpretation in the design doc. Do NOT treat ambiguity as an error. |

**Adjudication rules:**
- Prefer fixing Step 3 docs over escalating — most issues are reference-level clarity.
- Never "half-accept" — choose exactly one outcome per issue.
- If the issue depends on a missing design decision → flag for revise-design, not Step 3 fix.
- If the issue is reference-specific clarity or convention → accept and fix.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of a design-doc decision exist and the Step 3 doc chose a reasonable one → flag ambiguous design intent for user decision. Do not treat ambiguity as a defect or force a single reading at architecture level.

### Scope Collapse Guard

Before accepting any change to a Step 3 doc, enforce these three tests to prevent reference-layer expansion into system or engine territory:

**1. Upward Leakage Test:**
Does this change introduce or modify behavioral decisions that belong in system designs or the design doc?
- If YES → reject or flag for revise-systems/revise-design. Step 3 docs implement system designs as engineering contracts; they don't define what systems do.
- Step 3 docs may: define architecture patterns, ownership assignments, interface contracts, state machines, entity schemas, and signal registries.
- Step 3 docs must NOT: change system behavior, alter what players see, or redefine system responsibilities. Those belong in Steps 1-2.

**2. Downward Leakage Test:**
Does this change introduce engine-specific implementation detail that belongs in engine docs?
- If YES → reject. Step 3 docs are engine-agnostic engineering contracts.
- Step 3 docs must NOT: specify Godot node types, GDScript patterns, C++ class implementations, or engine-specific APIs. Those belong in Step 4 engine docs.
- Test: could this contract be implemented in any engine (Godot, Unity, Unreal), or does it assume a specific engine? If engine-specific → wrong layer.

**3. "Would This Survive Engine Change?" Test:**
If the project switched engines tomorrow, would this Step 3 decision still be valid?
- If NO → the Step 3 doc is encoding an engine assumption, not an architecture decision. Reject or rewrite as engine-agnostic.
- If YES → safe architecture decision. Accept.

These tests apply to both reviewer-proposed changes AND existing Step 3 content flagged during review.

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-references-[target-or-all]-<YYYY-MM-DD-HHMMSS>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

```
## Reference Review Complete [target / all]

### Most Dangerous Cross-Doc Inconsistency
[The mismatch most likely to cause implementation bugs.]

### What Could a Developer Get Wrong
[The implicit assumption most likely to cause subtle errors.]

### Weakest Doc
[The doc that contributes least to implementation clarity.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Architectural Coherence | N | N | N |
| 2. Ownership & Authority Model | N | N | N |
| 3. Contract & Interface Quality | N | N | N |
| 4. Data Model Fitness | N | N | N |
| 5. Cross-Doc Consistency | N | N | N |
| 6. Simulation Readiness | N | N | N |

### Per-Doc Issues
| Document | Issues Found | Accepted Changes | Key Finding |
|----------|-------------|-----------------|-------------|
| architecture.md | N | N | ... |
| authority.md | N | N | ... |
| interfaces.md | N | N | ... |
| state-transitions.md | N | N | ... |
| entity-components.md | N | N | ... |
| resource-definitions.md | N | N | ... |
| signal-registry.md | N | N | ... |
| balance-params.md | N | N | ... |
| enums-and-statuses.md | N | N | ... |

**Reference Model Strength Rating:** N/5 — [one-line reason]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/ITERATE-references-[target]-YYYY-MM-DD.md
```

## Rules

- **Project documents and authority order win.** Claude adjudicates conflicts using document authority. Higher-ranked docs are always right when they disagree with lower-ranked docs.
- **Reference docs describe DATA CONTRACTS, not IMPLEMENTATION.** If the reviewer suggests specific code patterns, class structures, or engine constructs, reject and propose contract-level alternatives. Step 3 docs define what must be true, not how to build it.
- **Edit only Step 3 docs.** Never edit system designs, design-doc, engine docs, planning docs, or ADRs during review.
- **Edits may clarify or tighten contracts but must not change architectural direction without user confirmation.** Rewording for clarity is fine; changing the identity model or authority structure is not.
- **Never apply changes that violate document authority.** authority.md wins over entity-components. interfaces.md wins over signal-registry. state-transitions.md wins over enums-and-statuses.
- **Never resolve cross-doc contradictions by weakening the higher-rank doc.** If the lower-rank doc looks more complete or more current but conflicts with the canonical source, either align the lower doc or escalate to the user. Never "split the difference" between ranks.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Pushback is expected and healthy.** The reviewer is adversarial — disagreement is normal.
- **Escalate only after real adjudication failure.** The same material issue must remain unresolved after adjudication attempts across 2 outer iterations. Reviewer repetition of a locked issue is not an adjudication failure — the lock holds. Escalate immediately (skip the 2-iteration wait) if the issue depends on a missing or contradictory Step 1-2 decision.
- **When --target is set, respect edit scope.** Cross-doc issues found during targeted review are flagged for fix-references, not fixed directly.
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Cross-doc consistency (Topic 5) is the highest-value topic.** If time or iteration budget is limited, prioritize Topics 5 and 6 over per-doc topics.
- **Ambiguous upstream design is not an architecture defect.** When the design doc genuinely permits multiple valid architectural interpretations and a Step 3 doc chose a reasonable one, do not treat the Step 3 doc as incorrect. Flag for user decision to lock the interpretation in the design doc. The reviewer's preferred reading is not automatically correct — design ambiguity often means the design doc needs tightening, not the architecture.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the reference doc harder to use during implementation? (b) does this improve clarity for developers, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving implementability, optimize for review criteria over practical development guidance, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing reference docs that are hyper-consistent but less practical, readable, or flexible. The goal is reference docs developers can implement from, not ones that score perfectly on an internal consistency audit.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Upward leakage — does this introduce behavioral decisions belonging in system designs or the design doc? If yes, reject or flag upstream. (2) Downward leakage — does this introduce engine-specific implementation detail? Step 3 docs are engine-agnostic contracts — no Godot nodes, GDScript patterns, or engine APIs. (3) "Would this survive engine change?" — if the project switched engines, would this decision still hold? If no, it's engine leakage, not architecture.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "authority boundary unclear" and "ownership conflict" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.

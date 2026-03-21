---
name: scaffold-iterate-engine
description: Adversarial per-topic review of engine docs using an external LLM. Reviews 15 engine docs across 6 topics (architecture implementation fidelity, authority & contract compliance, engine convention quality, cross-engine consistency, implementation sufficiency, simulation-layer fitness). Consumes alignment signals from fix-engine. Supports --target for single-doc focus and --topics for scoped review.
argument-hint: [--target doc-stem] [--topics "1,2,5"] [--focus "concern"] [--iterations N] [--signals "..."]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Engine Review

Run an adversarial per-topic review of engine docs using an external LLM reviewer: **$ARGUMENTS**

This skill reviews the 15 engine docs across 6 sequential topics, each with its own back-and-forth conversation. It uses the same Python infrastructure as iterate-design/iterate-systems/iterate-references but with engine-doc-specific topics.

This is the **design reviewer** for Step 4 — not the formatter. It runs after `fix-engine` has normalized the docs and detected alignment signals. It evaluates whether the engine docs correctly and completely implement the decisions made in Steps 1-3, using sound engine patterns, without contradicting higher-ranked docs or leaving implementation gaps.

The real question this review answers: **do these engine docs give a developer everything they need to implement correctly in the chosen engine — without guessing, contradicting Step 3, or reinventing decisions that should already be locked?**

## Topics

| # | Topic | What It Evaluates | Primary Docs |
|---|-------|-------------------|-------------|
| 1 | Architecture Implementation Fidelity | Does the engine doc faithfully implement Step 3 architecture decisions? | simulation-runtime, scene-architecture, coding-best-practices |
| 2 | Authority & Contract Compliance | Does the engine doc respect ownership, interface contracts, signal timing? | simulation-runtime, ai-task-execution, save-load-architecture |
| 3 | Engine Convention Quality | Are the engine patterns, APIs, and naming sound for the chosen engine? | coding-best-practices, ui-best-practices, input-system, scene-architecture |
| 4 | Cross-Engine Consistency | Do all engine docs agree on shared conventions? | All 15 docs |
| 5 | Implementation Sufficiency | Could a developer implement from this engine doc without guessing? | All 15 docs |
| 6 | Simulation-Layer Fitness | Does the engine approach handle the colony sim's needs? | simulation-runtime, save-load, ai-task-execution, debugging-and-observability |

### Topic 1 — Architecture Implementation Fidelity

Does the engine doc faithfully implement Step 3 architecture decisions?

Engine docs are Rank 9 — they implement, not define. Every engine decision must trace back to a Step 3 decision or be a pure engine convention that doesn't constrain design.

**Tick model implementation:**
- Does simulation-runtime's tick orchestration match architecture.md's Simulation Update Semantics exactly? Not "roughly" — exactly. Same timing model, same tick boundaries, same update order semantics.
- Does the engine doc distinguish fixed-step simulation from variable-step rendering? Does architecture.md? If architecture.md is silent on this, the engine doc is inventing a decision it shouldn't own.
- Are there timing assumptions in the engine doc that architecture.md doesn't explicitly authorize? "Process physics at 60Hz" is an engine decision only if architecture.md says "fixed timestep." If architecture.md says "tick-based," the engine doc can't unilaterally decide the rate.
- Does the engine doc's tick orchestration create ordering constraints not present in architecture.md? If architecture.md defines tick order A→B→C, does the engine doc silently add D between B and C?

**Identity model implementation:**
- Does coding-best-practices or save-load describe handle semantics that match architecture.md's Entity Identity section? Same generation model, same invalidation rules, same reuse policy?
- Does the engine doc add identity constraints beyond what architecture.md specifies? If architecture.md says "generational handles," does the engine doc add slot pooling, type-specific handle spaces, or other constraints without flagging them as engine-specific extensions?
- Does save-load's entity restoration process match the identity model? Are handles rebound correctly? Is the generation counter preserved or reset on load?

**Boot order implementation:**
- Does scene-architecture's initialization sequence match architecture.md's Boot Order? Same init phases, same dependency direction, same "ready before first tick" guarantees?
- Does the engine doc handle the distinction between cold boot and load-from-save? Does architecture.md? If architecture.md distinguishes them, the engine doc must too. If architecture.md doesn't, the engine doc can't invent different boot paths.
- Are there startup race conditions the engine doc doesn't address? Can signal wiring happen before all systems exist? Can a system's `_ready()` call a method on a system that hasn't initialized yet?

**Data flow compliance:**
- Does the engine doc describe any communication pattern that violates architecture.md's Forbidden Patterns? Check all 7 forbidden patterns against every engine doc's described interactions.
- Does the engine doc establish data flow rules beyond what architecture.md permits? If architecture.md says "signals only for cross-system communication," does the engine doc introduce "except we also use direct calls for performance"?
- Does the engine doc's signal wiring pattern match architecture.md's Signal Dispatch location rules?

**Failure & recovery implementation:**
- Does the engine doc's error handling match architecture.md's Failure & Recovery Patterns? Same recovery categories, same escalation rules?
- Are there failure modes the engine doc handles that architecture.md doesn't mention? Those are either engine-specific (fine) or design decisions the engine doc is making (flag).

**simulation-runtime focus:**
- Tick orchestration matches architecture.md Simulation Update Semantics exactly — same timing, same boundaries, same order
- Fixed/variable step distinction matches architecture.md or is honestly Constrained TODO
- Queued work draining handles interruption cascades per architecture.md failure patterns
- Cleanup phase is either engine-specific or traceable to architecture.md

**scene-architecture focus:**
- Init sequence matches architecture.md Boot Order — same phases, same direction
- Cold boot vs load-from-save distinction matches architecture.md (or both, if architecture.md distinguishes)
- Signal wiring location matches architecture.md's dispatch rules
- Autoload vs instanced decisions don't create startup races

**coding-best-practices focus:**
- Handle/reference patterns match architecture.md Entity Identity section exactly
- Data flow patterns comply with all 7 Forbidden Patterns
- Signal wiring conventions match architecture.md's Signal Dispatch location rules
- Error handling categories match architecture.md's Failure & Recovery Patterns

**save-load-architecture focus:**
- Entity restoration process matches identity model — generations preserved or reset per architecture.md
- Handle rebinding follows architecture.md's cross-reference validation rules
- Boot-from-save path matches architecture.md Boot Order (if distinguished)

**Exemplar findings:**
- "simulation-runtime says variable timestep with delta accumulator, but architecture.md's Simulation Update Semantics says fixed-step at simulation tick rate. These are different models."
- "scene-architecture adds a pre-tick initialization phase not in architecture.md's Boot Order. Is that an engine necessity or an unauthorized design decision?"
- "coding-best-practices says 'direct method calls between adjacent systems for performance' but architecture.md Forbidden Pattern #3 says no ad hoc direct calls."
- "save-load resets handle generations on load, but architecture.md's Identity section says generations are preserved across save/load. Which is correct?"
- "simulation-runtime adds a cleanup phase after all system ticks. Architecture.md doesn't mention post-tick cleanup. Is this engine-specific or an undocumented architecture decision?"

Core question: *if you diff'd the engine doc against architecture.md, would every difference be a pure engine convention — or would some be unauthorized design decisions?*

### Topic 2 — Authority & Contract Compliance

Does the engine doc respect ownership, interface contracts, and signal timing?

Engine docs describe HOW to implement cross-system interactions — but they must not redefine WHO owns what, WHAT contracts exist, or WHEN signals fire. Those are Step 3 decisions.

**Ownership compliance:**
- Does the engine doc assume any system owns something that authority.md assigns to a different system? This is the most common engine-doc error: implementing a feature and implicitly reassigning ownership.
- Does the engine doc describe "helper" or "manager" patterns that create de facto second writers? If authority.md says SystemA owns mood, but the engine doc introduces a MoodUpdateHelper that also writes mood, that's a hidden authority violation.
- Does the engine doc respect the Persistence Owner column in authority.md? If authority.md says SystemA persists field X, does the save-load engine doc agree?

**Contract implementation:**
- Does the engine doc implement interfaces.md contracts faithfully? Same direction (Push/Pull/Request), same data, same guarantees?
- Does the engine doc add implementation-level contracts not in interfaces.md? Engine docs may add engine-specific implementation details (Godot signals, method signatures), but the semantic contract must match interfaces.md.
- Does the engine doc change failure guarantees? If interfaces.md says a contract "can fail with fallback," does the engine doc silently drop the fallback?

**Signal timing compliance:**
- Does the engine doc's signal dispatch timing match signal-registry.md's Dispatch Timing Conventions? If the registry says "queued end-of-tick" but the engine doc implements "immediate emit," that's a timing violation.
- Does the engine doc's signal payload match signal-registry.md's documented payloads? Same fields, same types, same conventions (snake_case, handles not pointers, Vector2i for grid)?
- Does the engine doc add signals not in the registry? Engine-internal signals are fine; gameplay-facing signals must be registered.

**State transition implementation:**
- Does the engine doc implement state transitions matching state-transitions.md? Same entry/exit conditions, same timing (immediate/queued/end-of-tick)?
- Does the engine doc add engine-specific transition validation not in state-transitions.md? Validation that prevents illegal transitions per the state machine is correct. Validation that restricts legal transitions is an authority violation.

**Reservation/claim lifecycle:**
- Does ai-task-execution's reservation lifecycle match what authority.md and interfaces.md define? Same ownership, same invalidation triggers, same cleanup responsibility?
- Does the engine doc handle reservation expiry, stale-reference cleanup, and interrupted-task recovery as defined in Step 3? Or does it invent its own rules?

**ai-task-execution focus:**
- Task lifecycle states match state-transitions.md task state machine exactly
- Reservation ownership matches authority.md — who creates, who invalidates, who cleans up
- Interruption handling doesn't write to state owned by other systems (mood, needs, position)
- Stale-handle cleanup on every code path that touches entity references

**save-load-architecture focus:**
- Persistence Owner matches authority.md for every serialized field
- Does not reassign persistence responsibility to "convenient" systems
- In-flight state (tasks, reservations, queued intents) persistence respects authority ownership

**simulation-runtime focus:**
- Signal dispatch timing matches signal-registry.md Dispatch Timing Conventions
- Does not introduce "optimization" patterns that bypass interfaces.md contracts
- Queued work draining respects authority boundaries (systems only drain their own work)

**data-and-content-pipeline focus:**
- Content ID mapping matches architecture.md Content Identity Convention
- Does not establish new ownership over content that authority.md assigns elsewhere

**Exemplar findings:**
- "ai-task-execution describes TaskSystem clearing colonist mood on task failure. authority.md says NeedsSystem owns mood. TaskSystem can't write mood."
- "simulation-runtime implements signal dispatch as immediate emit, but signal-registry says Dispatch Timing is 'queued, processed end-of-tick.' These produce different behavior."
- "save-load assigns persistence responsibility to StorageSystem for inventory data. authority.md's Persistence Owner says InventorySystem. Mismatch."
- "coding-best-practices introduces a ServiceLocator pattern for cross-system access. interfaces.md doesn't define a ServiceLocator contract — this is a hidden new interface."
- "ai-task-execution adds a 'task_timeout' transition not in state-transitions.md's Task lifecycle state machine."

Core question: *does the engine doc implement Step 3 contracts — or does it quietly rewrite them?*

### Topic 3 — Engine Convention Quality

Are the engine patterns, APIs, and naming sound for the chosen engine?

This topic evaluates whether the engine doc uses the engine correctly — not whether it matches Step 3. This is the one topic where engine-specific expertise matters more than architecture compliance.

**API correctness:**
- Does the engine doc use the engine's actual APIs, classes, and patterns? Not pseudocode, not generic patterns, but real Godot 4 / Unity / Unreal conventions.
- Are deprecated or anti-pattern APIs recommended? Does the doc recommend patterns the engine documentation explicitly discourages?
- Are engine version-specific features assumed? Does the doc use APIs only available in a specific version without noting the requirement?

**Performance pattern quality:**
- Does performance-budget set realistic targets for the engine and platform? Are the per-system budgets achievable with the described patterns?
- Does the engine doc recommend patterns with known performance pitfalls? (e.g., per-frame allocations in GDScript, excessive signal fan-out, deep scene tree traversal)
- Are the documented profiling tools and techniques correct for the engine version?

**Scene/node architecture:**
- Does scene-architecture's tree layout follow engine best practices? Node types, composition patterns, signal wiring location?
- Are lifecycle patterns correct? (_ready, _enter_tree, _exit_tree, _process vs _physics_process in Godot; Start, Awake, OnEnable in Unity)
- Does the engine doc handle engine-specific gotchas? (e.g., Godot's `_ready()` order is children-first, parent-last; Unity's execution order is non-deterministic by default)

**UI framework fitness:**
- Does ui-best-practices use the engine's UI system correctly? Control nodes in Godot, UGUI/UI Toolkit in Unity, UMG in Unreal?
- Are the recommended UI patterns achievable with the engine's layout system? Or do they fight the framework?
- Does the doc handle dynamic content, scrolling, localization interaction, and resolution scaling using engine-native approaches?

**Input system fitness:**
- Does input-system use the engine's input framework correctly? InputMap in Godot, Input System in Unity, Enhanced Input in Unreal?
- Are rebinding, action maps, and device-switching handled using engine-native patterns?

**Build/test quality:**
- Does build-and-test-workflow describe correct build configurations for the engine?
- Are the test patterns appropriate? (GUT in Godot, NUnit in Unity, Automation in Unreal)
- Does the CI configuration account for the engine's specific build requirements?

**Exemplar findings:**
- "coding-best-practices recommends `get_node()` with string paths, but Godot best practice is `@onready var` with exported NodePaths or unique names."
- "performance-budget says 'keep all systems under 2ms per tick' but simulation-runtime describes 15 systems. At 60fps that's 30ms for systems alone — over half the frame budget."
- "scene-architecture uses multiple inheritance of packed scenes, but Godot 4 scenes don't support multiple inheritance. Composition via child scenes is the pattern."
- "ui-best-practices describes a React-style reactive binding model. Godot's Control system is imperative, not reactive. This will fight the framework."
- "input-system recommends polling Input.is_action_pressed() every frame, but for UI actions, InputEvent propagation via _input() is more correct."

Core question: *would an experienced engine developer read this doc and say "yes, this is how you'd actually build it" — or would they see anti-patterns, misunderstandings, or framework fights?*

### Topic 4 — Cross-Engine Consistency

Do all engine docs agree on shared conventions?

This topic compares engine docs against each other, looking for internal contradictions. It's the engine-layer equivalent of iterate-references Topic 5 (Cross-Doc Consistency).

**Naming convention consistency:**
- Do all engine docs use the same naming conventions for signals, methods, classes, nodes, and files?
- Does coding-best-practices define naming rules that other engine docs violate?
- Are there engine docs that use different case conventions for the same concept?

**Signal wiring consistency:**
- Do all engine docs agree on where signals are wired? (e.g., all in `_ready()`, or via autoload, or via scene tree?)
- Does simulation-runtime's signal dispatch model match what coding-best-practices describes?
- Does ai-task-execution wire signals the same way as scene-architecture?

**Error handling consistency:**
- Do all engine docs use the same error handling patterns? Same logging levels, same recovery approaches?
- Does debugging-and-observability describe diagnostics that other engine docs don't implement?
- Are there engine docs with conflicting error escalation (one says log-and-continue, another says assert-and-crash)?

**Data access pattern consistency:**
- Do all engine docs use the same patterns for accessing cross-system data? Same query approach, same caching policy?
- Does one engine doc use direct node references while another uses signals for the same kind of interaction?

**Pattern duplication vs reference:**
- Are there patterns described in full in multiple engine docs that should reference a single canonical source (coding-best-practices or implementation-patterns)?
- When one engine doc establishes a convention, do other engine docs reference it or silently redefine it?

**Constrained TODO alignment:**
- Are engine docs that share the same Step 3 dependency consistently constrained? If simulation-runtime is constrained on "tick model TBD," are ai-task-execution and save-load also constrained on the same dependency?
- Are there engine docs that pre-fill sections that other docs correctly mark as constrained? That's a consistency error — one doc is guessing while another correctly waits.

**Practical source-of-truth drift:**
- Is any downstream or sibling engine doc becoming the de facto source of truth because it is more detailed, more actionable, or more current-looking than the doc that should own the convention? This is the most common form of cross-engine drift because it looks justified.
- Example: coding-best-practices is more detailed and current than scene-architecture. Developers start following coding-best-practices for node lifecycle patterns even when scene-architecture should be canonical. Now practical truth has drifted.
- Flag when: a doc is more detailed than its peer on a topic the peer should own; developers would naturally read doc A instead of doc B for a convention doc B is supposed to define; two docs both describe the same pattern at different levels of detail without cross-referencing.

**Exemplar findings:**
- "coding-best-practices says signal names use snake_case, but ai-task-execution uses camelCase for 3 signals."
- "scene-architecture wires signals in `_ready()`, but simulation-runtime uses an autoload SignalBus. Two wiring patterns for the same project."
- "simulation-runtime is constrained on tick model (architecture.md TBD), but coding-best-practices pre-fills a fixed-step pattern. One is honest about the gap; the other guesses."
- "Error handling in save-load says 'return null on failure' but coding-best-practices says 'push_error() and return default.' Inconsistent."
- "The handle validation pattern is described in full in coding-best-practices, save-load, and ai-task-execution. Should be in one place with references."

Core question: *if you read all 15 engine docs, would they tell one consistent implementation story — or would you find contradictions that mean different docs would produce different code?*

### Topic 5 — Implementation Sufficiency

Could a developer implement from this engine doc without guessing?

This topic evaluates whether the engine doc is complete enough to be useful. Not architecturally correct (Topics 1-2) or engine-appropriate (Topic 3), but *sufficient*.

**Section completeness:**
- Are there sections that are still TODO or template-default that should be authored by now?
- Are Constrained TODO sections correctly blocked, or has the blocking Step 3 decision been resolved (making the constraint stale)?
- Is the Purpose section clear enough that a developer knows what this doc governs?

**Decision coverage:**
- Does every section that describes a convention or pattern actually make a decision? Or are there sections that describe the problem space without committing to an approach?
- Are there "depends on project needs" or "choose one of the following" sections that should have a concrete choice by now?
- Are there engine-specific decisions that the doc should make but doesn't? (e.g., "how do we handle hot-reload?" for a development workflow doc)

**Gap classification:**
When a developer would need to guess, classify the gap to determine the correct action:
- **Local implementation gap** — this engine doc should contain the answer but doesn't. Fix: author the section.
- **Cross-doc navigation gap** — another engine doc has the answer, but this doc doesn't reference it. Fix: add cross-reference.
- **Upstream design gap** — Step 3 never defined it. Fix: mark as Constrained TODO and flag for revise-references.

**Implementability test:**
- Could a developer read this doc and write code without opening any other engine doc? If not, are the cross-references explicit?
- Are there implicit assumptions about engine knowledge that should be documented? (e.g., "assumes familiarity with Godot's scene tree" when the project owner has zero Godot experience)
- Does the doc bridge the gap between Step 3 decisions and engine-specific implementation? Or does it restate Step 3 at the architecture level without providing engine-level guidance?

**Rules section quality:**
- Does the Rules section contain enforceable, testable rules? Or are the rules vague ("keep things clean")?
- Could a code reviewer use these rules to accept or reject a PR? If not, they're too vague.
- Do the rules cover the most common implementation mistakes for this engine doc's domain?

**Project Overrides section:**
- Is the Project Overrides table populated where the project deviates from engine defaults?
- Are there conventions described in the main body that should be overrides instead?

**Final-product design vs temporary scaffolding:**
- Does this engine doc implement the final architecture defined in Step 3, or does it describe temporary workarounds that will require rework? An engine doc that says "for now we use polling until the signal system is ready" is introducing temporary scaffolding. The engine doc should either implement the final design or mark the section as Constrained TODO.
- Does the engine doc contain "TODO: replace with proper implementation" or "temporary until X is built"? These are temporary-scaffolding markers. Either commit to the final approach or use Constrained TODO.
- Is there a mismatch between what Step 3 defines and what the engine doc implements, justified by "we'll fix it later"? That is temporary design, not incremental implementation. An engine doc that implements half the ownership model correctly is incremental. An engine doc that implements the wrong ownership model because "the real one isn't built yet" is temporary design.

**Exemplar findings:**
- "simulation-runtime's Tick Orchestration section says 'TODO: Define tick execution pattern.' This is the most critical section and it's empty."
- "save-load describes 3 approaches to handle rebinding but doesn't choose one. A developer would have to decide on their own."
- "coding-best-practices assumes familiarity with GDExtension C++ that the project owner doesn't have. Needs more explanatory context."
- "Rules section says 'follow SOLID principles' — that's not enforceable in a code review. What specific patterns are required or forbidden?"
- "ui-best-practices has no Project Overrides, but the project uses a non-standard panel system described in the design doc's UI Kit."

**Minimum implementable path test (mandatory):**

Pick one representative gameplay flow and trace it through the engine docs end-to-end. Choose a flow that involves interruption, not just happy path.

Example: *"Colonist gets hungry → task system chooses food task → food reserved → walk begins → food consumed by another colonist → task interrupted → state recovers → UI updates → debug trace explains it → save/load mid-flow still works"*

Trace through:
1. **simulation-runtime** — does the tick model handle this flow's ordering and timing?
2. **ai-task-execution** — does task discovery, reservation, interruption, and recovery all work?
3. **save-load-architecture** — if saved mid-walk, does the sim restore correctly?
4. **scene-architecture** — are all nodes in the right lifecycle state during each step?
5. **coding-best-practices** — do handle validation and error handling cover the interruption?
6. **debugging-and-observability** — can a developer trace why the colonist is now idle?
7. **ui-best-practices** — does the UI reflect the state change at each step?

If any step is unclear, undefined, or contradictory across engine docs → **fail**. Report which doc and which step broke. This catches seam failures faster than any per-doc review.

Core question: *if you handed this doc to a new developer on their first day, could they write correct code — or would they need to ask questions the doc should have answered?*

### Topic 6 — Simulation-Layer Fitness

Does the engine approach handle the colony sim's needs?

This topic applies the same genre-fit lens as iterate-references Topic 6, but from the engine implementation side. A technically correct engine doc can still be wrong for the game.

**Interruption handling:**
- Does the engine approach treat interruption as the default case? In a colony sim, tasks are interrupted more often than they complete. Does ai-task-execution's implementation handle interruption as a primary path, not an error path?
- Does save-load handle saving mid-interruption? What happens when a save triggers while a colonist is between task states?
- Does simulation-runtime's tick model handle state that changes mid-tick due to interruption cascades?

**Save/load of live simulation:**
- Does save-load handle in-flight tasks, partial construction, active needs, queued jobs? Not just static entity state, but dynamic simulation state?
- Does the engine approach handle entity references that may be invalid on load (destroyed entities, reused slots)?
- Does save-load preserve or reconstruct reservation/claim/assignment state? These temporary ownership objects are central to sim correctness.

**Scalability under system growth:**
- As more systems are added (combat, expeditions, research, diplomacy), do the engine conventions scale? Or are they already at the edge of what's manageable?
- Does the debugging/observability approach handle 15+ systems with cross-system causality?
- Does the performance budget account for system growth beyond the current set?

**Determinism and debuggability:**
- Can a developer trace why a colonist starved, why a task was abandoned, why a resource disappeared using the debugging-and-observability tools described?
- Does the engine approach support deterministic replay or event logging for debugging emergent behavior?
- Are simulation diagnostics ([DIAG] warnings, state validators) sufficient for the game's complexity?

**Data pipeline fitness:**
- Does data-and-content-pipeline handle the volume and variety of content definitions a colony sim needs (items, structures, recipes, traits, research, etc.)?
- Does asset-import-pipeline handle the art and audio needs of a top-down 2D sim?
- Does localization handle the quantity of dynamic strings a colony sim generates (status messages, tooltips, event descriptions)?

**Genre / Simulation Fit:**

Does this engine approach treat the game as a stateful, simulation-heavy colony/management game — or as a generic application that happens to have some game logic?

- **Simulation-first vs application-first** — does the engine approach treat time, interruption, stale targets, and continuous world churn as first-class concerns? Or does it assume rare, discrete state changes like a CRUD app? The implementation patterns should reflect that this is a live simulation, not a request-response system.
- **Interruption as default, not exception** — the normal flow in a colony sim is: colonist starts task → something changes → task is interrupted → state must recover. Does the engine approach make that the primary design path? Or is happy-path completion the assumed default with interruption bolted on?
- **Long-lived entity fitness** — entities in this game live a long time and accumulate state (injuries, memories, relationships, skills, trait effects). Do the engine patterns support growing entity complexity without becoming fragile?
- **Multi-system causality** — a single gameplay outcome (colonist refuses to work) may result from morale + needs + traits + injuries + zone restrictions + task availability. Do the engine patterns make that causal chain traceable across systems, or do they fragment it across so many signals and callbacks that debugging emergent behavior becomes impossible?
- **Reservation/claim centrality** — colony sims depend heavily on reservations, assignments, and claims (food reserved, bed assigned, task claimed, resource locked). Does the engine approach treat that lifecycle as a first-class implementation concern, or is it an afterthought?
- **Save/load of live world** — this game saves a running simulation with in-flight tasks, partial construction, active needs, queued jobs. Does the engine approach support saving and restoring that mid-flow state, not just static configuration?

**Colony sim anti-patterns:**
- Are there engine patterns that look clean but are hostile to colony sim needs? Too much event indirection for a sim that needs deterministic sequencing? Too much loose coupling for a game where one actor's behavior depends on many systems?
- Does the UI approach handle the information density a colony sim requires (many panels, overlays, contextual info)?
- Does the input approach handle the colony sim's input complexity (selection, placement, camera, context menus, zone painting)?

**Exemplar findings:**
- "ai-task-execution implements task interruption as an exception path with error logging. In a colony sim, interruption is the normal path — it should be as clean as task completion."
- "save-load serializes entity components but not in-flight task state. After load, all tasks restart from scratch. That's a gameplay regression for long tasks (mining, construction)."
- "simulation-runtime's tick model is clean but doesn't account for cascading state changes within a single tick. In a colony sim, one event can trigger a chain of reactions."
- "debugging-and-observability has no way to trace a causal chain across systems. When a colonist starves, you'd need to check 5 different system logs to find why."
- "performance-budget allocates 0.5ms per system at 60fps. With 15 systems that's 7.5ms. But the budget doesn't account for GC pauses, rendering, or input processing."
- "coding-best-practices uses a pure ECS approach with no entity-level encapsulation. Colony sim entities (colonists) have complex, interconnected state that may benefit from some grouping."

Core question: *does this engine approach make building a colony sim easier — or does it add implementation overhead that fights the game's natural structure?*

**Cross-Topic Consistency Check:**

Before finalizing results, reconcile findings across all 6 topics. Independent topic conversations can produce contradictions:
- Topic 1 says tick model is incorrect, but Topic 5 says implementation is sufficient → contradiction
- Topic 2 says contracts violated, but Topic 6 says simulation is sound → contradiction
- Topic 3 says engine patterns are wrong, but Topic 4 says docs are consistent → may still be consistently wrong

For each contradiction found: resolve it (one topic was wrong) or escalate it (genuine ambiguity). List all contradictions and their resolution in the review log.

**After all topics complete**, the reviewer must answer final questions and provide a rating:

1. **What is the single most dangerous Step 3 violation?** — the engine decision most likely to contradict or silently constrain a higher-ranked design decision.

2. **What would a developer get wrong despite reading all engine docs?** — the implicit assumption or undocumented convention most likely to cause implementation errors.

3. **Which engine doc is weakest?** — the doc that contributes least to implementation clarity or has the most unresolved content.

4. **Blocker classification** — for each issue found, classify its impact:
   - **Blocks implementation** — can't write code without this resolved
   - **Causes incorrect implementation** — code will compile but behavior will be wrong
   - **Increases maintenance cost** — works now but creates tech debt
   - **Does not block, increases risk** — development can proceed but this will cause pain later

5. **What is the most likely cross-doc inconsistency a developer will hit first?** — the real-world friction point, not the most abstract issue.

6. **Implementation consistency test** — would two developers, reading these docs independently, produce the same implementation? If not, identify the top divergence points.

7. **First failure scenario** — describe the first realistic implementation failure these docs would allow: what a developer builds, what goes wrong, and why the docs permitted it.

8. **Engine Implementation Strength Rating (1-5):**
   - 1 = fundamentally broken (major Step 3 contradictions, critical docs empty)
   - 2 = major gaps (key engine decisions missing, significant authority violations)
   - 3 = workable but risky (some Step 3 drift, several TODO areas, convention inconsistencies)
   - 4 = solid engine docs (correct but requires careful reading to implement without error)
   - 5 = strong engine docs (obvious and unambiguous — developer could implement correctly on the first attempt)

9. **Confidence:** High / Medium / Low — reason must reference: (a) doc completeness (how many sections are authored vs TODO), (b) Step 3 clarity (are upstream decisions locked or TBD), (c) contradiction density (how many cross-doc mismatches remain), (d) constrained area ratio (what percentage of critical sections are honestly waiting on Step 3)

## Reviewer Bias Pack

Include these detection patterns in the reviewer's system prompt. They represent the most common failure modes in engine doc sets.

1. **Implementation masquerading as design** — engine doc makes decisions that belong in Step 3. Looks like an engine convention but actually constrains architecture, authority, or contracts. Test: could you remove this decision and still implement correctly using Step 3 docs alone? If removing it would leave a gap, the decision should be in Step 3, not the engine doc.

2. **Engine cargo cult** — engine doc recommends patterns because "that's how Godot/Unity/Unreal does it" without checking whether the pattern fits the game's needs. A colony sim may need different patterns than the engine's default tutorials suggest.

3. **Phantom completeness** — engine doc has content in every section but the content is generic engine documentation, not project-specific decisions. Test: could you apply this doc to any Godot project, or is it specific to this game? If generic, it's not doing its job.

4. **Convention without enforcement** — engine doc establishes naming/pattern/structure conventions but provides no mechanism for enforcement. Rules that can't be checked in code review or automated testing are aspirational, not real.

5. **Optimistic implementation** — engine doc describes happy-path implementation without addressing what happens on failure, interruption, or edge cases. "Serialize all components" sounds simple until you hit circular references, in-flight tasks, or stale handles.

6. **Step 3 echo without engine value** — engine doc restates Step 3 decisions at the architecture level without adding engine-specific implementation guidance. The developer already has Step 3 docs; the engine doc should tell them what to type, not what to think.

7. **Silent constrained section** — engine doc pre-fills a section that depends on an unresolved Step 3 decision. Should be a Constrained TODO but was guessed. More dangerous than a missing section because it looks authoritative.

8. **Cross-engine contradiction** — two engine docs describe the same pattern differently. One says signals are wired in `_ready()`, the other says via autoload. Both can't be right. The developer who reads them in different order will build differently.

9. **Temporary scaffolding masquerading as final design** — engine doc pre-fills a section with an acknowledged workaround that "will be cleaned up later." In reality, workarounds become permanent. If it's temporary, it should be a Constrained TODO, not a guessed implementation. Test: does this doc implement the final architecture defined in Step 3, or does it describe a shortcut that contradicts Step 3 with the assumption someone will fix it?

10. **Architecture-implementation drift** — engine doc starts from Step 3 decisions but polishes and evolves them into something subtly different. The tick model is "based on" architecture.md but adds qualifications that change the semantics. The identity model "follows" the handle convention but adds exceptions that undermine it. The engine doc looks aligned but functionally diverges.

11. **Game-engine mismatch** — engine doc recommends patterns that work well in generic Godot/Unity/Unreal tutorials but fight the specific needs of a colony sim. Pure ECS for entities that need complex cross-component behavior. Loose event coupling for systems that need deterministic sequencing. Async patterns for operations that must be synchronous within a tick. The pattern is technically correct for the engine but wrong for the game.

12. **Fake completeness is worse than missing content** — a section that guesses implementation for an unresolved Step 3 decision is more severe than an empty or Constrained TODO section. The guessed section looks authoritative, will be implemented as-is, and may silently contradict the eventual Step 3 decision. An honest Constrained TODO at least signals "don't build this yet."

13. **Over-centralization bias** — engine doc introduces a "manager," "service," "controller," or "bus" that simplifies implementation but violates authority boundaries or creates hidden coupling. A SignalBus that routes everything looks clean but makes every system implicitly depend on it. A TaskManager that owns task lifecycle sounds helpful but may shadow authority.md's ownership assignments. Centralization that reduces boilerplate while increasing coupling is a net negative for a sim with 15+ systems.

14. **Over-abstraction bias** — engine doc introduces layers, wrappers, or abstractions that increase indirection, hide data flow, and make debugging harder. Common in "clean architecture" overuse. A colony sim needs transparent data flow for debugging emergent behavior — every layer of indirection makes "why did this colonist starve?" harder to answer. If an abstraction doesn't enable a concrete gameplay requirement, it's overhead.

## Per-Doc Mandatory Interrogation

For every engine doc in scope, the reviewer must run the doc's specialized failure-mode check **in addition to** the topic questions. This is not optional — it is mandatory and high-priority. If iteration budget is constrained, run per-doc interrogation even if some topics are skipped. Topics find structured correctness issues; per-doc interrogation finds real implementation failures.

Each doc section ends with a **First Failure Scenario** (required) and a **Top Risk** (required).

**Doc priority order** (when budget is tight, interrogate in this order):
1. simulation-runtime — tick correctness affects every system
2. save-load-architecture — persistence failures corrupt game state
3. ai-task-execution — task lifecycle is the most interruption-heavy code path
4. scene-architecture — boot races and lifecycle errors are invisible until they crash
5. coding-best-practices — convention drift compounds across all implementation
6. debugging-and-observability — without tracing, all other failures are opaque
7. ui-best-practices — UI is the player's window into simulation state
8. input-system — input routing errors block all player interaction
9. performance-budget — budget math determines whether the game runs
10. data-and-content-pipeline — content errors surface at runtime
11. build-and-test-workflow — build failures block all validation
12. asset-import-pipeline — import errors are caught late
13. localization — translation issues are cosmetic until they break layout
14. post-processing — visual effects rarely cause correctness failures
15. implementation-patterns — patterns grow from implementation, not ahead of it

### simulation-runtime

**Unique responsibility:** How the simulation tick actually executes — ordering, timing, queuing, draining, cleanup.

**Attack surface:**
- **Tick semantics** — is the tick model precisely defined? Fixed-step vs variable-step, delta accumulation, tick rate — all unambiguous?
- **Order guarantees** — could a developer predict exactly when each system runs, what state it sees, and what it can assume about prior systems' output?
- **Queue draining** — when queued work (deferred signals, intent responses, state transitions) drains, what order? What happens to work queued during draining?
- **Interruption cascades** — when one system's tick causes a state change that invalidates another system's in-progress work, how does the tick handle it? Is this explicit or assumed?
- **Determinism** — given the same initial state, does the tick model produce the same result every time? If not, where does non-determinism enter?
- **Stale work cleanup** — at end-of-tick, what happens to expired reservations, invalidated intents, destroyed entity references?
- **Same-tick vs next-tick** — for each cross-system interaction, is it crystal clear whether the consumer sees this tick's value or last tick's?

**Questions the reviewer must answer:**
1. Could a developer add a new system to the tick without reading any other engine doc?
2. If two systems both write and read shared state, does the tick model prevent stale reads?
3. What happens to in-flight work when the entity it targets is destroyed mid-tick?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### scene-architecture

**Unique responsibility:** How the engine's scene tree is structured, nodes are owned, and lifecycle events fire.

**Attack surface:**
- **Boot sequencing** — is cold-boot init order explicit? Are there startup races where one node's `_ready()` depends on another that hasn't initialized?
- **Cold boot vs load boot** — are they the same path or different? If different, both documented? If same, is that actually safe for load-from-save?
- **Node ownership/lifecycle** — who creates, who reparents, who frees each node type? Are there nodes with ambiguous ownership?
- **Signal wiring location** — where are signals connected? In `_ready()`? Via autoload? Via scene tree? Is this consistent with coding-best-practices?
- **Race-condition risk** — can signals fire before all nodes exist? Can a node receive a callback before its dependencies are ready?
- **Autoload vs instanced boundary** — which things are autoloads and why? Is the autoload list minimal? Could any autoload be an instanced node instead?

**Questions the reviewer must answer:**
1. If you added a new system node, where does it go in the tree, and what lifecycle guarantees does it get?
2. Can a signal fire before its consumer exists during boot?
3. Does load-from-save use the same init path or a different one?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### coding-best-practices

**Unique responsibility:** Naming conventions, code patterns, error handling, and cross-language boundaries.

**Attack surface:**
- **Naming conventions** — are naming rules concrete enough that two developers would name the same thing identically?
- **Handle/reference safety** — do the handle patterns match architecture.md's identity model? Is validation enforced or suggested?
- **Cross-language boundary** — if using multiple languages (C++/GDScript), is the boundary explicit? What goes where and why?
- **Signal conventions** — naming, payload rules, wiring patterns — all consistent with signal-registry.md conventions?
- **Error handling enforceability** — could a code reviewer accept or reject a PR using these rules? Or are they aspirational?
- **Anti-pattern prevention** — are the forbidden patterns from architecture.md translated into concrete "don't do this in code" rules?

**Questions the reviewer must answer:**
1. Would two developers writing the same system produce code that looks structurally similar?
2. Are the error handling rules testable in code review?
3. Does the cross-language boundary actually match what the project builds?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### save-load-architecture

**Unique responsibility:** How game state is serialized, restored, and migrated across versions.

**Attack surface:**
- **Persistence ownership fidelity** — does the serialization boundary match authority.md's Persistence Owner column exactly? No "convenient" reassignments?
- **Handle rebinding correctness** — after load, are all entity references revalidated? What happens to references pointing at destroyed or reused slots?
- **In-flight simulation restoration** — are tasks, reservations, queued intents, and pending state transitions preserved or cleanly abandoned on load? Which is it, and is it explicit?
- **Migration/versioning** — what happens when the save format changes? Is there a migration path, or do old saves break?
- **Partial world state safety** — what if a save is corrupted or incomplete? Does the system detect and handle it, or silently load garbage?

**Questions the reviewer must answer:**
1. After save/load, does the simulation reach the same state it would have without the save?
2. What happens to a colonist mid-task when the game is saved and reloaded?
3. Can a save from version N be loaded in version N+1?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### ai-task-execution

**Unique responsibility:** How AI actors discover, claim, execute, and recover from tasks.

**Attack surface:**
- **Interruption-first logic** — is interruption the primary design path, not an error path? Tasks are interrupted more than they complete in colony sims.
- **Reservation lifecycle** — who creates reservations, who validates them, who cleans them up? What invalidates a reservation (target destroyed, actor reassigned, timeout)?
- **Stale target cleanup** — when the target of an in-progress task is destroyed, consumed, or moved, what happens to the actor? Every code path must handle this.
- **Legal transition fidelity** — do task state transitions match state-transitions.md exactly? No extra states, no skipped states?
- **Rollback/recovery behavior** — when a task fails mid-execution, what state does the actor return to? Is it always legal per state-transitions.md?
- **Cross-system write discipline** — does task execution ever write to state owned by other systems (mood, needs, position)? That's an authority violation.

**Questions the reviewer must answer:**
1. Trace a task from discovery to interruption to recovery — is every step handled?
2. What happens if the reserved resource is consumed by another actor before this one arrives?
3. Can the task system put an actor in a state that state-transitions.md says is illegal?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### ui-best-practices

**Unique responsibility:** How the engine's UI framework is used to build panels, handle dynamic content, and scale across resolutions.

**Attack surface:**
- **Panel architecture** — how are panels created, managed, stacked, and destroyed? Does this align with ui-kit.md's component model?
- **Dynamic list handling** — colony sims have long, changing lists (colonists, tasks, inventory). Does the engine approach handle efficient updates, scrolling, and selection?
- **High-density info support** — can the UI approach display the information density the game requires? 20+ stats, multiple overlapping panels, live-updating values?
- **Scaling/localization resilience** — do UI layouts survive resolution changes, text expansion from translation, and different font metrics?
- **Engine-native UI usage** — does the doc use the engine's actual UI system correctly, or fight it with custom workarounds?
- **Update strategy for live sim state** — how does the UI reflect constantly-changing simulation data without polling every frame or missing updates?

**Questions the reviewer must answer:**
1. Can the UI approach handle the densest panel in the game without performance or layout issues?
2. What happens to a panel when the entity it displays is destroyed?
3. Does translated text break any layouts?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### input-system

**Unique responsibility:** How player input is captured, mapped to actions, and routed to the correct handler.

**Attack surface:**
- **Action map structure** — does the action map use the engine's input framework correctly? Are action names consistent with interaction-model.md?
- **Mouse/keyboard/gamepad parity** — can the same actions be performed on all supported devices? Are there device-specific gaps?
- **Placement/selection/context-menu coverage** — does the input system handle all interaction patterns from interaction-model.md?
- **Rebinding feasibility** — is the rebinding architecture engine-native and actually implementable?
- **Event propagation correctness** — does input correctly stop propagating when consumed by UI? Can camera controls fire while a modal is open?
- **Camera/input conflict handling** — when camera movement, entity selection, and UI interaction overlap, who wins?

**Questions the reviewer must answer:**
1. Can a player complete every interaction pattern from interaction-model.md using only keyboard+mouse? Only gamepad?
2. What happens when the player clicks a UI element that overlaps a selectable game entity?
3. Is rebinding persistent across sessions?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### performance-budget

**Unique responsibility:** Frame budget allocation, profiling strategy, and growth margin.

**Attack surface:**
- **Budget math sanity** — does total system time + rendering + GC/allocation + input + audio < 1/target_fps? Actually add it up.
- **Profiling realism** — are profiling tools correct for the engine version? Are the profiling instructions actionable?
- **Growth margin** — what happens when 5 more systems are added? Does the budget accommodate growth or is it already maxed?
- **Worst-case colony load** — what's the target colony size? Does the budget account for worst-case (max colonists, max structures, max active tasks)?
- **GC/allocation risks** — does the engine approach create per-frame allocations in hot paths? Are GC pauses accounted for?
- **Frame-time tradeoff discipline** — when the budget is exceeded, what gets cut first? Is there a priority ordering?

**Questions the reviewer must answer:**
1. Does the budget math actually add up for the target frame rate?
2. What's the first thing that breaks when the colony reaches maximum size?
3. Is there headroom for future systems, or is the budget already tight?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### debugging-and-observability

**Unique responsibility:** How developers trace causality, inspect state, and diagnose emergent behavior across 15+ systems.

**Attack surface:**
- **Causal tracing** — can a developer answer "why did this colonist starve?" by tracing events across systems? Or is causality opaque?
- **State inspection** — can live simulation state be inspected without pausing? Are there in-game overlays or debug panels?
- **Sim replay/log usefulness** — is event logging structured enough to reconstruct what happened? Or is it noise?
- **Multi-system debugging** — when a bug involves 3+ systems, can the developer correlate events across system boundaries?
- **Diagnostic noise vs signal** — are [DIAG] warnings specific enough to be actionable? Or do they fire so often they're ignored?
- **"Why did this colonist do this?" traceability** — the single most important debugging question in a colony sim. Can the tools answer it?

**Questions the reviewer must answer:**
1. A colonist is standing idle while hungry with food available. How do you diagnose why?
2. Can you trace a single gameplay event through all systems it touches?
3. Are diagnostic warnings actionable or just noise?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### localization

**Unique responsibility:** How translatable strings are managed, formatted, and maintained.

**Attack surface:**
- **Key namespace scalability** — as the game grows to thousands of strings, does the key naming convention remain navigable?
- **Dynamic string rules** — how are strings with variables handled? Pluralization? Gender? Number formatting? Are these rules engine-native?
- **Layout breakage handling** — German text is 30% longer than English. Does the UI survive? Are overflow rules defined?
- **Pluralization/formatting support** — does the localization approach handle plural forms, date formats, and number formats for target languages?
- **Tooltip/status text discipline** — are generated strings (tooltips with stats, status messages with entity names) translatable? Or are they concatenated in code?

**Questions the reviewer must answer:**
1. Can a translator work from the CSV/files alone without reading code?
2. What happens to a tooltip when the translated text is twice as long?
3. Are dynamically generated strings (e.g., "Colonist is Hungry (3/10)") translatable?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### asset-import-pipeline

**Unique responsibility:** How art, audio, and data assets flow from source files into the engine.

**Attack surface:**
- **Source/runtime boundary** — is it clear which files are source (edited by humans) and which are runtime (generated by the engine)?
- **Preset correctness** — do import presets match the engine's actual import system? Are they tested?
- **Repeatability** — does reimporting produce identical results? Are there import settings that drift?
- **Content pipeline coupling** — does asset import feed correctly into data-and-content-pipeline? Are IDs stable?
- **Import drift prevention** — can an artist accidentally change import settings and break the game?

**Questions the reviewer must answer:**
1. Can an artist add a new sprite and have it appear in-game without developer intervention?
2. If an import preset changes, what breaks?
3. Are data table imports validated before runtime?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### build-and-test-workflow

**Unique responsibility:** How the project builds, tests, and validates correctness.

**Attack surface:**
- **Actual engine build correctness** — are build configurations correct for the engine and platform? Debug/release/export builds all work?
- **Headless test realism** — can tests run headless for CI? Do headless runs produce reliable results?
- **CI practicality** — is the CI configuration complete enough to actually set up? Are engine downloads, dependencies, and environment variables documented?
- **Environment setup reproducibility** — can a new developer build and test the project from these docs alone?
- **Smoke-test coverage** — does the test suite cover enough to catch regressions? What's not tested?

**Questions the reviewer must answer:**
1. Can a new developer build the project from scratch using only this doc?
2. Do headless tests reliably catch the same bugs as interactive testing?
3. What's the most important thing that's NOT tested?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### implementation-patterns

**Unique responsibility:** Recording recurring code patterns that emerge during implementation.

**Attack surface:**
- **Template usefulness** — is the template structure usable for recording real patterns as they're discovered?
- **Duplication control** — are recorded patterns cross-referenced with coding-best-practices to avoid duplication?
- **Pattern admission standards** — what qualifies a pattern for inclusion? Is there a threshold (used 3+ times)?
- **Relationship to coding-best-practices** — is the boundary clear? (coding-best-practices = conventions; implementation-patterns = recurring solutions)
- **Anti-pattern prevention** — are anti-patterns recorded alongside patterns?

**Questions the reviewer must answer:**
1. Is this doc actually being used, or is it empty?
2. Do any recorded patterns contradict coding-best-practices?
3. Is the boundary between conventions (coding) and patterns (here) clear?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### post-processing

**Unique responsibility:** Visual effects, shaders, and rendering post-processing.

**Attack surface:**
- **Readability preservation** — colony sims need clear visual information. Do post-processing effects preserve entity readability, status visibility, and UI clarity?
- **Performance cost** — are post-processing effects within the frame budget? Are costs measured?
- **Style-guide fidelity** — do effects match the style-guide's rendering approach and tone registers?
- **Crisis-state usability** — during crisis/alert states, do visual effects help or hinder the player's ability to see what's happening?
- **Information clarity under effects** — can the player still read health bars, status icons, and text overlays with all effects active?

**Questions the reviewer must answer:**
1. Can the player read a health bar with all post-processing effects active?
2. Do visual effects for crisis states help or hurt decision-making?
3. What's the total frame-time cost of all post-processing?


**First Failure Scenario (required):** Describe the most likely real implementation failure this doc would allow — what gets built, what goes wrong, and why the doc permitted it.

**Top Risk (required):** The single most dangerous issue in this doc and why.
---

### data-and-content-pipeline

**Unique responsibility:** How game content (items, structures, recipes, traits) flows from authored files to runtime systems.

**Attack surface:**
- **Content/runtime separation** — is it clear what's authored content vs generated runtime data? Can content be modified without touching code?
- **ID stability** — are content IDs stable across saves, loads, and version updates? Can a content ID be reused or change meaning?
- **Validation depth** — are content definitions validated before runtime? Are missing references, invalid types, and broken chains caught early?
- **Tooling scalability** — as content grows to hundreds of items/structures/recipes, does the pipeline remain manageable?
- **Error surfacing before runtime** — does the pipeline fail loudly at import/load time, or silently at runtime?

**Questions the reviewer must answer:**
1. Can a content designer add a new item type without writing code?
2. What happens if a content definition references an ID that doesn't exist?
3. Are content IDs safe across save/load boundaries?

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--target` | No | all | Target a single doc by stem (e.g., `--target simulation-runtime`). When set, topics are scoped to the targeted doc's concerns — but cross-engine topics (4, 5, 6) still read all docs. |
| `--topics` | No | all | Comma-separated topic numbers to review (e.g., `"1,4,6"`). Used by revise-foundation when only certain areas need adversarial review. |
| `--focus` | No | -- | Narrow the review within each topic to a specific concern. |
| `--iterations` | No | 10 | Maximum outer loop iterations. Stops early on convergence. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic. |
| `--signals` | No | -- | Alignment signals from fix-engine to focus the review on known issues. Format: comma-separated signal descriptions. |

### --target to --topics mapping

When `--target` is set without explicit `--topics`, the skill automatically selects the relevant topics:

| Target | Auto-selected Topics |
|--------|---------------------|
| `coding-best-practices` | 1, 3, 4, 5 |
| `ui-best-practices` | 3, 4, 5 |
| `input-system` | 3, 4, 5 |
| `scene-architecture` | 1, 3, 4, 5 |
| `performance-budget` | 3, 5, 6 |
| `simulation-runtime` | 1, 2, 4, 5, 6 |
| `save-load-architecture` | 1, 2, 4, 5, 6 |
| `ai-task-execution` | 1, 2, 4, 5, 6 |
| `data-and-content-pipeline` | 2, 4, 5 |
| `localization` | 3, 4, 5 |
| `post-processing` | 3, 5 |
| `implementation-patterns` | 4, 5 |
| `asset-import-pipeline` | 3, 4, 5 |
| `debugging-and-observability` | 4, 5, 6 |
| `build-and-test-workflow` | 3, 4, 5 |

Topics 4 (Cross-Engine Consistency) and 5 (Implementation Sufficiency) are always included because they evaluate doc interactions and completeness.

Simulation-critical docs (simulation-runtime, save-load, ai-task-execution) always include Topics 1, 2, and 6.

Explicit `--topics` overrides this mapping.

## Preflight

Before running external review:

1. **Check engine docs exist.** Glob `scaffold/engine/*` to find engine docs. If fewer than 5 engine docs exist, stop: "Engine docs not ready. Run `/scaffold-bulk-seed-engine` first."
2. **Check fix-engine has run and docs are structurally clean.** All engine docs must satisfy:
   - No missing required sections (including Rules and Project Overrides)
   - No template placeholders (`[Engine]`, `ExampleSystem`, `TODO_SIGNAL_NAME`, etc.)
   - No template-default sections in critical docs (`simulation-runtime`, `save-load-architecture`, `ai-task-execution`, `scene-architecture`, `coding-best-practices`) — these must have authored content beyond scaffold filler
   - No duplicate section scaffolding blocks
   - All docs registered in `_index.md`
   - If any of these fail, stop: "Run `/scaffold-fix-engine` first to normalize structure."
3. **Check Step 3 docs exist.** The reviewer needs architecture.md, authority.md, interfaces.md, and signal-registry.md as context. If any are missing, stop: "Step 3 docs not ready."
4. **Determine engine and stack.** Read existing engine docs to identify the engine prefix and implementation stack. Pass this to the reviewer as context.

## Context Files

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| All engine docs (or targeted doc) | Primary targets |
| `design/architecture.md` | Architecture decisions that engine docs must implement |
| `design/authority.md` | Ownership rules that engine docs must respect |
| `design/interfaces.md` | Contracts that engine docs must implement |
| `design/state-transitions.md` | State machines that engine docs must implement |
| `reference/entity-components.md` | Entity data shapes the engine must handle |
| `reference/signal-registry.md` | Signal contracts the engine must implement |
| `design/design-doc.md` | Vision and target platforms |
| `design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| `design/style-guide.md` | Rendering approach (for UI, post-processing docs) |
| `scaffold/engine/_index.md` | Engine doc registration |
| `decisions/known-issues/_index.md` | Known gaps and constraints |
| ADRs with status `Accepted` | Decision compliance |
| Alignment signals from fix-engine (if `--signals` provided) | Focus areas |

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
│   └── Apply changes: accepted issues applied to engine docs
│
├── Per Doc in scope (mandatory interrogation):
│   └── Reviewer answers doc-specific failure-mode questions
│   └── Claude evaluates findings against existing topic results
│   └── Deduplicate: merge with topic findings by root cause
│
└── Cross-topic consistency check → resolve contradictions
```

Each topic gets its own review → respond → consensus cycle via the Python `doc-review.py` script. After topics complete, the per-doc mandatory interrogation runs for each doc in scope. Findings are deduplicated against topic results. After all topics and per-doc checks in one outer iteration, re-read updated docs and start the next outer iteration if issues remain.

### Multi-Doc Parallelization

When reviewing all engine docs (no `--target`), spawn parallel agents — one agent per doc. Each agent runs a **complete, self-contained review** of ONE engine doc — all per-doc topics, all exchanges, all iterations up to `--iterations` max, all adjudication, all edits. An agent is the same as running `iterate-engine --target <doc>` on that doc alone.

1. **Build work list.** Identify all engine docs in scope. Log: "Reviewing N engine docs: coding-best-practices, scene-architecture, ..."
2. **Spawn parallel agents.** One agent per doc, all spawned in parallel (use multiple Agent tool calls in a single message). Each agent receives the doc file, context files (Step 3 docs, design doc, glossary, other engine docs as read-only context, ADRs, known issues, design signals if provided), review config, and full topic/adjudication instructions.
3. **Collect results.** As agents complete, log progress: "coding-best-practices.md — Issues: Y accepted, Z rejected (N of M complete)"
4. **Cross-engine consistency check.** After ALL per-doc agents complete, run the cross-engine consistency topic across the full doc set. This evaluates naming conventions, pattern consistency, and cross-doc alignment.
5. **Agent failure handling.** Failed agents retry once. If retry fails, report as "review failed" with the error. The overall review continues.

When `--target` is specified, skip parallelization and review that single doc directly.

**Stop conditions** (any one stops iteration):
- **Clean** — a complete topic pass produces no new issues.
- **Converged** — two consecutive passes produce the same issue set with no new findings.
- **Human-only** — only issues requiring user decisions remain; further iteration won't resolve them.
- **Limit** — `--iterations` maximum reached.
- **Quality degradation** — later iterations produce fewer issues but with weaker reasoning, vaguer evidence, or recycled findings. Treat as convergence and stop early rather than continuing with diminishing returns.

**Verification pass rule:** A pass that found issues and applied fixes is NOT clean — it is a “fixed” pass. After a fixed pass, you MUST run at least one more full pass on the updated document to verify no new issues were introduced by the fixes and no previously-hidden issues are now exposed. Only a pass that finds ZERO new issues counts as **Clean**. Stopping after fixing issues without a verification pass is a skill failure.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording. Different framings of the same underlying mismatch count as the same issue. Examples:
- "tick timing mismatch," "simulation order inconsistency," and "delta vs fixed timestep conflict" → same issue if they stem from the same Step 3 / engine-doc gap.
- "authority violation in TaskSystem mood write" and "ownership boundary crossed for mood" → same issue.

**Lock enforcement:**
- The reviewer must NOT reintroduce a resolved issue in a different form.
- The reviewer must NOT raise stricter variants of a resolved issue unless: (a) new evidence exists that wasn't available when the issue was resolved, OR (b) the fix itself introduced a new problem.
- If a previously resolved issue reappears: classify it as a **review inconsistency**, not a new issue. Prefer rejecting the reappearance unless the reviewer provides materially different evidence.

**Cross-topic lock:** If Topic 1 resolves an issue, Topic 4 may not re-raise it under a different name. The cross-topic consistency check (end of review) catches this retroactively, but the lock prevents wasted exchanges proactively.

**Tracking:** Maintain a running resolved-issues list in the review log during execution. Before engaging with any new reviewer claim, check it against the resolved list by root cause. If it matches, reject with "previously resolved — see [iteration N, topic M]."

**Edit scope:**
- When `--target` is set, only edit the targeted engine doc. Flag cross-doc issues for fix-engine.
- When `--target` is not set, edit any engine doc.
- **Never edit Step 3 docs** (architecture.md, authority.md, interfaces.md, state-transitions.md, entity-components.md, resource-definitions.md, signal-registry.md, balance-params.md, enums-and-statuses.md).
- **Never edit system designs, design-doc, or planning docs.**
- If an engine doc contradicts Step 3 and the Step 3 doc appears correct, fix the engine doc. If the engine doc appears correct and Step 3 appears wrong, flag for revise-references — do not edit Step 3.

### Issue Adjudication

Every issue raised by the reviewer must be classified into exactly one outcome:

| Outcome | Action |
|---------|--------|
| **Accept → edit engine doc** | Apply change immediately. The issue is valid and the fix is within engine-doc scope. |
| **Reject reviewer claim** | Record reasoning in review log. The reviewer is wrong or the issue is out of scope. |
| **Escalate to user** | Requires design judgment, unclear authority, or the reviewer and Claude remain split after max-exchanges. |
| **Flag for revise-references** | Step 3 doc is likely incomplete or incorrect. The engine doc may be right; Step 3 needs updating. |
| **Defer (valid Constrained TODO)** | The section is correctly blocked by an unresolved Step 3 decision. Not a gap — an honest wait. |
| **Flag ambiguous upstream** | Step 3 permits multiple valid interpretations and the engine doc chose one. Not incorrect — underspecified upstream. Flag for revise-references to lock the interpretation; mark engine doc section with `<!-- Ambiguous upstream: [brief description of the two+ valid readings]. Interpretation chosen: [what the engine doc does]. Pending: revise-references to lock. -->`. Do NOT treat the engine doc as wrong or force a single interpretation at engine level. |

**Adjudication rules:**
- Prefer fixing engine docs over escalating — most issues are engine-level clarity.
- Never "half-accept" — choose exactly one outcome per issue.
- If the issue depends on a missing Step 3 decision → flag for revise-references, not engine fix.
- If the issue is engine-specific clarity or convention → accept and fix.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.
- If multiple valid interpretations of a Step 3 decision exist and the engine doc chose a reasonable one → flag ambiguous upstream, not reject or accept. Do not treat a valid interpretation as an unauthorized decision. Do not force the engine doc to pick a different valid interpretation.

### Scope Collapse Guard

Before accepting any change to an engine doc, enforce these three tests to prevent engine-layer expansion into design-layer responsibility:

**1. Ownership Test:**
Does this change introduce or tighten a decision that Step 3 did not explicitly define?
- If YES → reject, or flag for revise-references.
- Engine docs may: implement decisions, clarify execution, define engine-specific mechanics.
- Engine docs must NOT: introduce new constraints on architecture/authority/contracts, narrow valid interpretations left open by Step 3, convert flexible design into fixed implementation rules.

**2. Flexibility Preservation Test:**
If Step 3 allows multiple valid implementations, does the engine doc preserve that flexibility?
- If the engine doc collapses multiple valid approaches into a single enforced approach → it must be explicitly marked as either:
  - **Engine convention** (not design truth — other approaches remain valid if Step 3 changes), OR
  - **Ambiguous upstream** (pending Step 3 clarification via revise-references).
- Unmarked collapse = scope creep. Reject or require marking.

**3. "Would This Survive Step 3 Rewrite?" Test:**
If Step 3 changed tomorrow, would this engine decision still be valid?
- If NO → this is **design leakage** — the engine doc is encoding a design assumption, not an engine convention. Reject or escalate.
- If YES → safe engine convention. Accept.

These tests apply to both reviewer-proposed changes AND existing engine doc content flagged during review. An existing section that fails the ownership test is a finding, not a pre-existing right.

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-engine-[target-or-all]-<YYYY-MM-DD-HHMMSS>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

```
## Engine Review Complete [target / all]

### Most Dangerous Step 3 Violation
[The engine decision most likely to contradict or silently constrain a higher-ranked design decision.]

### What Would a Developer Get Wrong
[The implicit assumption most likely to cause implementation errors.]

### Weakest Engine Doc
[The doc that contributes least to implementation clarity.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Architecture Implementation Fidelity | N | N | N |
| 2. Authority & Contract Compliance | N | N | N |
| 3. Engine Convention Quality | N | N | N |
| 4. Cross-Engine Consistency | N | N | N |
| 5. Implementation Sufficiency | N | N | N |
| 6. Simulation-Layer Fitness | N | N | N |

### Per-Doc Issues
| Document | Issues Found | Accepted Changes | Key Finding |
|----------|-------------|-----------------|-------------|
| coding-best-practices | N | N | ... |
| ui-best-practices | N | N | ... |
| input-system | N | N | ... |
| scene-architecture | N | N | ... |
| performance-budget | N | N | ... |
| simulation-runtime | N | N | ... |
| save-load-architecture | N | N | ... |
| ai-task-execution | N | N | ... |
| data-and-content-pipeline | N | N | ... |
| localization | N | N | ... |
| post-processing | N | N | ... |
| implementation-patterns | N | N | ... |
| asset-import-pipeline | N | N | ... |
| debugging-and-observability | N | N | ... |
| build-and-test-workflow | N | N | ... |

**Engine Implementation Strength Rating:** N/5 — [one-line reason]
**Confidence:** High / Medium / Low — [reason]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Cross-topic contradictions:** N found, N resolved
**Review log:** scaffold/decisions/review/ITERATE-engine-[target]-YYYY-MM-DD-HHMMSS.md

### Recommended Next Action
One of:
- **`/scaffold-fix-engine`** — structural issues remain after review edits
- **`/scaffold-iterate-engine`** — further adversarial review needed (issues not yet converged)
- **`/scaffold-revise-references`** — Step 3 gaps or contradictions detected that engine docs cannot resolve
- **User decision required** — blocked on design judgment (escalated issues listed above)
- **Ready to proceed** — engine layer is stable, no blocking issues remain
```

## Rules

- **Project documents and authority order win.** Claude adjudicates conflicts using document authority. Higher-ranked docs are always right when they disagree with lower-ranked docs.
- **Engine docs describe HOW, not WHAT.** If the reviewer suggests the engine doc should make design decisions, reject. Step 3 decides what; engine docs decide how to build it in the chosen engine.
- **Edit only engine docs.** Never edit Step 3 docs, system designs, design-doc, planning docs, or ADRs during review.
- **Edits may clarify or tighten engine conventions but must not change Step 3 decisions.** Rewording for implementation clarity is fine; changing tick model, ownership, or contract semantics requires an ADR.
- **Never resolve Step 3 contradictions by changing Step 3.** If Step 3 appears wrong, flag for revise-references. Fix the engine doc to match Step 3.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Pushback is expected and healthy.** The reviewer is adversarial — disagreement is normal.
- **Material issue definition.** A material issue is one that: (a) blocks implementation entirely, (b) causes incorrect behavior despite compiling, (c) contradicts or silently constrains Rank 1-8 docs, (d) creates cross-doc inconsistency affecting multiple systems, or (e) converts an unresolved Step 3 dependency into fake certainty. Only material issues trigger escalation.
- **Scope control.** For each topic, the reviewer must identify the top 3-7 material issues only. Ignore minor or redundant issues. Prioritize: Step 3 violations, cross-doc contradictions, implementation blockers. If more than 7 issues exist, cluster by root cause and report clusters, not individual instances. This prevents review noise from drowning out real problems.
- **Evidence requirement.** Every issue must include: (a) source location (engine doc + section), (b) reference location (Step 3 doc or conflicting engine doc), and (c) concrete mismatch description. No vague findings ("this seems inconsistent") — cite the specific text that conflicts.
- **Verification before finalizing.** Before accepting any issue as real, re-read both cited sources and confirm the mismatch actually exists — not inferred, not assumed. If uncertainty remains after verification, downgrade to "possible inconsistency" or escalate rather than asserting a contradiction that may not exist.
- **Causal impact requirement.** For every material issue, explain the downstream impact chain: what breaks → when it surfaces → why it matters for gameplay or implementation. "This is wrong" is insufficient. "This timing mismatch will cause task interruptions to fire one tick late, which means reservations won't release until the next cycle, which means colonists will idle waiting for resources that are technically available" is useful.
- **Constrained section handling.** Constrained TODOs are neutral, not negative. Only penalize if the constraint is stale (blocking decision resolved) or another doc guessed where this one correctly waited. A high-quality doc may have many constrained sections if Step 3 is incomplete — that honesty should improve the rating, not lower it.
- **Reappearing material issues escalate to the user.** Escalate when the same material issue persists for 2 outer iterations, or when the reviewer and Claude remain split after max-exchanges on a topic. **Escalate immediately** (skip the 2-iteration wait) if the issue depends on a missing or contradictory Step 3 decision, or if resolution requires changing Rank 1-8 docs.
- **Issue deduplication.** Before reporting, merge issues that share the same root cause across topics. Keep one canonical issue with cross-topic tags (e.g., "Topics 1, 5: tick model mismatch"). This prevents noise from the same root problem appearing 3 times.
- **Engine best practices are subordinate to project architecture.** Prefer patterns that correctly implement Step 1-3 decisions, even if they are less idiomatic than default engine tutorials. Do not regress architecture compliance for engine purity.
- **No over-specification.** Do not introduce stricter constraints than Step 3 defines unless clearly marked as engine conventions. If Step 3 is flexible on a point, engine docs must preserve that flexibility — don't prematurely lock decisions that architecture.md intentionally left open.
- **When --target is set, respect edit scope.** Cross-doc issues found during targeted review are flagged for fix-engine, not fixed directly.
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Per-doc interrogation is highest priority.** If iteration budget is constrained, run per-doc mandatory interrogation even if some topics are skipped. Topics find structured correctness; per-doc interrogation finds real implementation failures.
- **Topics 4 and 5 are highest among topics.** If time or iteration budget is limited within the topic pass, prioritize Topics 4 (Cross-Engine Consistency) and 5 (Implementation Sufficiency) over per-doc topics.
- **Constrained TODOs are correct, not gaps.** An engine doc that honestly marks a section as Constrained TODO because Step 3 hasn't decided yet is better than one that guesses. Do not penalize constrained sections; penalize sections that guess when they should be constrained. A high-quality doc may have many constrained sections if Step 3 is incomplete — that honesty should improve the rating, not lower it.
- **Design for the final product, implement incrementally.** Engine docs must implement the final architecture defined in Step 3. An engine doc that implements half the ownership model correctly is incremental. An engine doc that implements the wrong ownership model because "the real one isn't built yet" is temporary design. Never accept temporary designs that require rework — use Constrained TODO instead.
- **Practicality check before finalizing changes.** Before accepting any reviewer-proposed change, ask: (a) would this change make the doc harder to use in real development? (b) does this improve clarity for a developer, or does it just enforce internal consistency for the review system's benefit? Reject changes that increase rigidity without improving implementability, optimize for review criteria over developer usability, or reduce readability to satisfy a formal check. Over iterations, the review system can overfit — producing docs that are hyper-consistent but less practical, readable, or flexible. The goal is docs a developer can build from, not docs that score perfectly on an internal consistency audit.
- **Ambiguous upstream interpretations are not errors.** When Step 3 is genuinely ambiguous (permits multiple valid readings) and the engine doc picks a reasonable interpretation, do not treat the engine doc as incorrect. Flag for revise-references to lock the interpretation upstream. Mark the engine doc section with an ambiguity comment. This prevents false positives, over-correction, and premature locking of design decisions at the engine layer.
- **Scope collapse guard.** Before accepting any change, apply three tests: (1) Ownership — does this introduce or tighten a decision Step 3 didn't define? If yes, reject or flag for revise-references. (2) Flexibility preservation — if Step 3 allows multiple valid implementations, does the engine doc preserve that flexibility or collapse it into one enforced approach? Unmarked collapse is scope creep. (3) "Would this survive Step 3 rewrite?" — if Step 3 changed tomorrow, would this engine decision still be valid? If no, it's design leakage, not an engine convention. Engine docs implement; they do not constrain design.
- **Resolved issues are locked across iterations.** Once an issue is accepted+fixed or rejected with reasoning, it is closed. The reviewer may not reintroduce it under different wording. Issues are identified by root cause, not phrasing — "tick timing mismatch" and "simulation order inconsistency" are the same issue if they share the same root. Only new evidence or a regression introduced by the fix can reopen a locked issue. This prevents evaluation drift, wasted cycles, and moving-target feedback across iterations.

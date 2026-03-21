---
name: scaffold-iterate-input
description: Adversarial per-topic review of Step 6 input docs using an external LLM. Reviews action-map, input-philosophy, default-bindings-kbm, default-bindings-gamepad, and ui-navigation across 6 topics (action coverage & traceability, philosophy & accessibility coherence, binding fitness & device parity, navigation model completeness, cross-doc consistency, interaction readiness). Consumes design signals from fix-input. Supports --target for single-doc focus and --topics for scoped review.
argument-hint: [--target doc.md] [--topics "1,3,6"] [--focus "concern"] [--iterations N] [--signals "..."]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Adversarial Input Review

Run an adversarial per-topic review of Step 6 input docs using an external LLM reviewer: **$ARGUMENTS**

This skill reviews the 5 Step 6 docs across 6 sequential topics, each with its own back-and-forth conversation. It uses the same Python infrastructure as iterate-design/iterate-systems/iterate-references/iterate-style but with input-doc-specific topics.

This is the **design reviewer** for Step 6 — not the formatter. It runs after `fix-input` has normalized the docs and detected design signals. It evaluates whether the input model is *sound* — whether actions are traceable, bindings are usable, navigation is complete, philosophy is enforceable, and the docs are consistent with upstream canon and with each other.

The real question this review answers: **do these 5 docs, taken together, give a developer everything they need to wire input correctly — without guessing, contradicting the interaction model, or leaving critical input decisions implicit?**

## Topics

| # | Topic | What It Evaluates | Primary Docs |
|---|-------|-------------------|-------------|
| 1 | Action Coverage & Traceability | Are all player verbs covered? Is every action traceable? No bloat? | action-map |
| 2 | Philosophy & Accessibility Coherence | Do principles hold together? Are accessibility promises real? | input-philosophy |
| 3 | Binding Fitness & Device Parity | Are bindings usable? Collision-free? Device-agnostic where required? | default-bindings-kbm, default-bindings-gamepad |
| 4 | Navigation Model Completeness | Does navigation work for all devices, all screens, all modes? | ui-navigation |
| 5 | Cross-Doc Consistency | Do all 5 input docs agree with each other and upstream canon? | All 5 docs |
| 6 | Interaction Readiness | Could a developer wire input from these docs alone? | All 5 docs |

### Topic 1 — Action Coverage & Traceability

Are all player verbs covered? Is every action traceable to design canon? Is there bloat?

**action-map focus:**
- **Player verb coverage** — does every player verb from the design doc's Player Verbs section and every player action from the interaction model have a corresponding action ID? Flag missing verbs — these are input gaps that will block spec implementation.
- **Traceability completeness** — does every action have a Source column entry tracing it to a specific design artifact (`design-doc: section`, `interaction-model: section`, etc.)? Are the source references accurate — does the cited section actually describe the behavior this action enables?
- **Traceability accuracy** — for each Source reference, verify the cited document and section actually contain the claimed behavior. A source reference pointing to a section that doesn't mention the action's behavior is a phantom trace.
- **Action bloat detection** — are there action IDs that don't trace to any player verb, UI need, camera need, or debug need? Actions without traceable sources are speculative bloat. This is the enforcement side of bulk-seed-input's "every action must trace to design canon" rule.
- **Namespace accuracy** — are actions in the correct namespace? A camera control in `player_`, a gameplay action in `ui_`, or a release-shipped action in `debug_` are all misclassified.
- **Action granularity** — are actions at the right level of abstraction? Too fine: `player_move_left`, `player_move_right`, `player_move_up`, `player_move_down` when `player_move` with a direction vector suffices. Too coarse: `player_interact` covering select, command, inspect, and cancel.
- **Deprecation discipline** — are deprecated actions clearly marked? Do any binding docs still reference deprecated action IDs?
- **ID stability** — are there signs that action IDs have been renamed (old references in other docs)? IDs should be permanent per the action-map rules.
- **Completeness vs phase scope** — are all actions needed for the current phase present? Are there actions for future phases that shouldn't exist yet?

**Exemplar findings:**
- "Design doc Player Verbs lists 'assign colonist to zone' but no action ID maps to zone assignment. A spec implementing zone assignment would have no input to bind."
- "Action `player_whistle` has Source: 'design-doc: Player Verbs' but the Player Verbs section contains no mention of whistling. Phantom trace."
- "15 debug actions defined but the design doc describes no debug features. These may be valid developer tools or may be speculative bloat — challenge the scope."
- "`player_select` and `player_inspect` are separate actions but the interaction model describes a single click that contextually selects or inspects. The action split doesn't match the interaction."

Core question: *if you traced every action ID back to its source, would every link be real — and would every player verb have an action?*

### Topic 2 — Philosophy & Accessibility Coherence

Do the input principles hold together? Are accessibility promises real?

**input-philosophy focus:**
- **Principle enforceability** — could each principle be tested during implementation? "Inputs should feel responsive" is not testable. "Input-to-action latency ≤ 33ms" is testable. Flag aspirational principles that can't be mechanically verified.
- **Principle-to-binding consistency** — do the binding docs actually honor the philosophy's stated principles? If philosophy says "no simultaneous key presses," but KBM bindings include Ctrl+Shift+Click combos, the philosophy is violated.
- **Accessibility promise realism** — are accessibility commitments actually reflected in the bindings and navigation docs? "All actions support remapping" — but are there actions bound to hardcoded keys? "Toggle alternative for every hold action" — are toggle variants actually defined?
- **Responsiveness target precision** — are responsiveness targets concrete numbers or vague aspirations? Are they realistic for the engine and platform?
- **Philosophy-to-interaction alignment** — do philosophy principles match the interaction model's design? If the interaction model uses drag behaviors extensively but philosophy says "minimize hold actions for accessibility," that's a tension the doc should acknowledge and resolve.
- **Constraint completeness** — are there implied constraints from the design doc or interaction model that philosophy doesn't acknowledge? If the design doc says "gamepad-first design" but philosophy doesn't mention gamepad priority, that's a gap.
- **Engine feasibility** — if the engine input doc exists, do philosophy promises conflict with stated engine limitations? Philosophy saying "simultaneous mouse+gamepad support" when the engine doc says "one active device at a time" is a feasibility gap.

**Exemplar findings:**
- "Philosophy says 'all actions remappable' but action-map has 3 hardcoded system actions (pause, screenshot, quit) with no remapping note."
- "Responsiveness target says '≤ 2 frames' but doesn't specify frame rate. At 30fps that's 66ms. At 60fps that's 33ms. Which does the project target?"
- "Philosophy says 'no chord requirements' but KBM bindings use Ctrl+Click for multi-select. That's a chord."
- "Accessibility section promises 'one-handed play support' but doesn't define which hand, which keys, or which actions are covered."

Core question: *if you tested every philosophy principle against the actual bindings and interaction model, would any principles fail?*

### Topic 3 — Binding Fitness & Device Parity

Are bindings usable, collision-free, and device-agnostic where required?

**default-bindings-kbm and default-bindings-gamepad focus:**
- **Same-context collision analysis** — go beyond fix-input's mechanical collision check. For each binding collision flagged or accepted, evaluate whether the overlap is actually safe during real gameplay. Two actions sharing a key in "different contexts" may both be relevant during the same gameplay moment (e.g., camera pan and entity selection during build mode).
- **Ergonomic assessment** — are core gameplay actions accessible without awkward hand positions? Are frequently used actions on easy-to-reach keys/buttons? Are emergency actions (cancel, pause) accessible instantly?
- **Device parity** — for actions the philosophy says must work on both devices, do both binding docs cover them? Are there gameplay actions with KBM bindings but no gamepad binding (or vice versa) without explicit exclusion documentation?
- **Modifier discipline** — do core gameplay actions (`player_` namespace) avoid modifiers? Are modifiers reserved for power-user or context-specific actions? Is the modifier policy consistent or arbitrary?
- **Gamepad button exhaustion** — gamepads have ~14 buttons plus sticks/triggers. With context switching, how many actions are available per context? Is there enough button space for the game's action set, or is the scheme silently overloaded?
- **Genre-appropriate defaults** — are the default bindings sensible for the game's genre? A colony sim should have different default bindings than an FPS. Are there bindings copied from genre conventions that don't fit?
- **Discoverability** — for bindings that aren't genre-standard, can the player discover them? Are there important but non-obvious bindings that need in-game hints?
- **Exclusion documentation** — for actions explicitly excluded from one device (e.g., debug actions not on gamepad), is the exclusion documented in the bindings doc or philosophy?

**Exemplar findings:**
- "Core gameplay action `player_assign` requires Ctrl+Click on KBM. That's a modifier on a primary action — philosophy says 'minimize modifiers for core actions.'"
- "`camera_zoom` is bound to mouse wheel on KBM but has no gamepad binding. Philosophy says 'device-agnostic gameplay' but camera control is gameplay-critical."
- "Gamepad has 12 player_ actions mapped but only 8 available buttons in gameplay context. 4 actions require shoulder+face button combos not documented anywhere."
- "ESC is bound to both `ui_cancel` and `player_deselect`. During build mode with a panel open, which fires? The context model doesn't distinguish these."

Core question: *could a player pick up a controller (or sit down at a keyboard) and play effectively using only the default bindings — without fighting the controls?*

### Topic 4 — Navigation Model Completeness

Does UI navigation work for all devices, all screens, and all modes?

**ui-navigation focus:**
- **Navigation model fitness** — does the chosen navigation model (spatial, tab-order, or hybrid) actually fit the game's UI? A colony sim with many dense panels may need spatial navigation for gamepad but tab-order makes more sense for simple menus. Is the model appropriate for every screen type?
- **Focus flow completeness** — for each major screen, is the initial focus element defined? Can the player reach every interactive element using only keyboard or only gamepad? Are there dead-end focus traps where the player can't navigate away?
- **Navigation action coverage** — are all `ui_` navigation actions from the action-map actually used in ui-navigation? Are there navigation needs described in ui-navigation that have no corresponding action ID?
- **Mode transition navigation** — when switching between game modes (gameplay → build mode → menu), what happens to focus? Does focus persist, reset, or follow a defined rule? Are there mode transitions where focus state becomes undefined?
- **Mouse behavior completeness** — are hover states, click behavior, right-click context, scroll behavior, and cursor visibility rules all defined? Are there UI elements that work with keyboard/gamepad but not mouse (or vice versa)?
- **UI-kit component alignment** — do navigation references match components defined in ui-kit? Are there navigation assumptions about components that don't exist?
- **Accessibility navigation** — can a player navigate all UI using only keyboard? Only gamepad? Are there UI elements that require mouse hover to discover?
- **Screen-specific vs global rules** — is it clear which navigation rules are global (apply everywhere) vs screen-specific? Are there screens that need exceptions to the global model?
- **Panel stacking navigation** — when multiple panels are open (overlay on overlay), is focus management defined? Can the player navigate between stacked panels? Does ESC/back always close the topmost?

**Exemplar findings:**
- "Navigation model says 'spatial' but the colonist stats panel is a vertical list where spatial navigation would be confusing — tab-order makes more sense there."
- "No initial focus defined for the build menu. Gamepad player opens build menu and focus is... nowhere? Or on the first item? Undefined."
- "Focus trap in the research panel: once focused on the research tree graph, no navigation action moves focus back to the panel's close button."
- "ui-navigation assumes a 'tooltip panel' that doesn't exist in ui-kit."
- "When build mode overlay opens over the main HUD, focus moves to the build palette. But pressing ESC closes the build overlay AND deselects the selected entity. Is that correct?"

Core question: *could a gamepad-only player navigate every screen, reach every interactive element, and return to gameplay — without getting stuck or confused?*

### Per-Doc Failure Probe (mandatory after each topic)

After each topic's review cycle completes, the reviewer must answer these 6 questions for the doc(s) that topic covers:

| # | Question |
|---|----------|
| 1 | **What breaks if this doc is wrong?** Be concrete: unmapped player verbs, unreachable UI, collision during gameplay, accessibility promise violated. |
| 2 | **What will developers guess here — and guess differently?** 1–3 decisions not explicitly defined that produce inconsistent implementations. |
| 3 | **Where will two developers diverge?** Same doc, different implementation — the exact ambiguity. |
| 4 | **What is most likely to drift over time?** Where future changes will silently break consistency. |
| 5 | **What is the hardest edge case this doc must define — but currently doesn't?** |
| 6 | **What does this doc assume another doc defines — but that doc does not actually define?** |

**Change impact check (mandatory for every accepted issue):** For each doc change, identify: (1) which other input docs must also change, (2) which upstream docs are affected (interaction-model, ui-kit), (3) which downstream artifacts are affected (engine input doc, specs, tasks).

### Topic 5 — Cross-Doc Consistency

Do all 5 input docs agree with each other and with upstream canon?

**Doc-pair checks:**
- **Action-map ↔ KBM bindings** — every action has a binding or an explicit exclusion. No orphan bindings referencing non-existent actions.
- **Action-map ↔ Gamepad bindings** — same coverage check. Explicit exclusions documented.
- **Action-map ↔ UI navigation** — all `ui_` navigation actions used in ui-navigation exist in action-map. All `ui_` actions defined in action-map are used or explicitly excluded.
- **Action-map ↔ Interaction model** — action IDs cover all interaction model player actions. No action IDs without an interaction model source (possible bloat).
- **Action-map ↔ Design doc** — action IDs cover all player verbs. No player verbs without an action ID.
- **Philosophy ↔ Bindings** — philosophy constraints (no chords, one-handed play, modifier limits) are not violated by actual bindings.
- **Philosophy ↔ Navigation** — philosophy accessibility requirements are reflected in navigation model (keyboard-only, gamepad-only traversal).
- **Philosophy ↔ Interaction model** — principles are consistent with interaction model behavior.
- **Navigation ↔ UI-kit** — navigation references components that exist in ui-kit (if ui-kit exists).
- **KBM ↔ Gamepad** — actions covered by one device but not the other are explicitly documented as exclusions.
- **All ↔ Glossary** — canonical terminology used consistently.
- **Canonical drift detection** — is any input doc more detailed or current-looking than the interaction model that should govern it? Are developers likely to treat the action-map as the source of truth for what actions exist, bypassing the interaction model?
- **Abstraction-level consistency** — are all 5 docs at the same abstraction level? Or has action-map drifted into implementation while philosophy remains aspirational?

**Exemplar findings:**
- "Action `player_zone_paint` has a KBM binding (Click+Drag) but no gamepad binding. Philosophy says 'device-agnostic' but no exclusion is documented."
- "UI navigation references `ui_tab_next` but action-map only defines `ui_navigate_right`. Are these the same action with different names?"
- "Input philosophy says 'no chord requirements' but KBM bindings include 4 Shift+key combos. The philosophy is violated."
- "Action-map has 45 actions but the interaction model describes 28 player interactions. 17 actions have no clear interaction model source."
- "Binding docs treat `debug_` actions as always-active. Philosophy doesn't specify whether debug bindings can conflict with gameplay bindings when both contexts are active."

Core question: *if you read all 5 input docs in sequence, would they tell one consistent story — or would you find contradictions?*

### Topic 6 — Interaction Readiness

Could a developer wire input from these docs alone?

This is the integration test. It evaluates whether the complete Step 6 doc set is sufficient for downstream work.

**Per-doc readiness:**
- **action-map** — could a developer set up all input actions using only this doc? Are IDs, namespaces, and descriptions sufficient for engine implementation?
- **input-philosophy** — could a developer make input design decisions (what to prioritize when tradeoffs arise) using only this doc?
- **KBM bindings** — could a developer wire all keyboard/mouse input using only this doc and action-map?
- **gamepad bindings** — could a developer wire all gamepad input using only this doc and action-map?
- **ui-navigation** — could a developer implement UI focus management using only this doc, action-map, and ui-kit?

**Integration checks:**
- **Spec derivation readiness** — could behavior specs be written referencing these input docs? Can a spec say "when the player performs `player_build`" and have that be unambiguously traceable through action-map → binding → interaction model?
- **Engine input doc readiness** — could the engine input doc be written from these docs? Does the developer know what actions to register, what bindings to set as defaults, what remapping to support, and what navigation model to implement?
- **Gap detection** — what's the biggest thing missing? Not "could be improved" but "a developer would get stuck here."
- **Ambiguity detection** — where could two developers legitimately wire input differently?
- **Multi-developer divergence test** — if two developers independently wired input from these docs, where would they diverge?

**End-to-end interaction test (mandatory):**

Walk one representative interaction through all 5 docs. Pick a scenario involving mode switching and error handling, not just happy path.

Example: *"Player selects colonist → switches to build mode → places structure → invalid location → error → corrects → success → exits build mode → colonist still selected"*

Trace through:
1. **action-map** — are all needed actions defined? (`player_select`, `player_build_mode`, `player_place`, `ui_cancel`, `player_deselect`)
2. **KBM bindings** — what keys does the player press for each step?
3. **gamepad bindings** — what buttons does the player press for each step?
4. **input-philosophy** — do the bindings honor responsiveness and accessibility principles?
5. **ui-navigation** — when build mode opens, where does focus go? Can the player navigate the build palette? Does ESC exit cleanly?

If any step is unclear, undefined, or contradictory → **fail**. Report which doc and which step broke.

**Device parity test (mandatory):**

Repeat the end-to-end test for both KBM and gamepad. If the experience differs significantly (one path is complete, the other has gaps), report the parity failure.

**Questions the reviewer must answer:**
1. What's the biggest gap a developer would hit when wiring input?
2. Where would two developers diverge?
3. Can the end-to-end interaction be completed on both devices?
4. Are input docs sufficient for spec derivation — can a spec reference actions unambiguously?

**After all topics complete**, the reviewer must answer final questions and provide a rating:

1. **What is the single most dangerous cross-doc inconsistency?** — the mismatch most likely to produce broken or confusing input.

2. **What could a developer get wrong despite reading all 5 docs?** — the implicit assumption most likely to produce incorrect input wiring.

3. **Which doc is weakest?** — the doc that contributes least to implementation clarity.

4. **Blocker classification** — for each issue found, classify its downstream impact:
   - **Blocks engine input doc** — can't write engine input implementation without this resolved
   - **Blocks specs** — can't derive behavior specs referencing input without this resolved
   - **Blocks tasks** — can't write input-related implementation tasks without this resolved
   - **Does not block, increases risk** — implementation can proceed but input bugs will surface later

5. **Input Model Strength Rating (1–5):**
   - 1 = fundamentally broken (major coverage gaps, action-map contradicts interaction model)
   - 2 = major gaps (missing device parity, philosophy violated by bindings, navigation incomplete)
   - 3 = workable but risky (some cross-doc drift, several coverage gaps, ambiguity in key areas)
   - 4 = solid input model (docs mostly consistent, minor gaps bounded, developer could wire input correctly)
   - 5 = strong input model (all docs consistent, full coverage, developer could implement input correctly on the first attempt)

## Reviewer Bias Pack

Include these detection patterns in the reviewer's system prompt.

1. **Phantom traceability** — action-map Source column entries that point to design doc sections that don't actually describe the claimed behavior. Looks traceable but the link is decorative.

2. **Philosophy-binding disconnect** — philosophy states beautiful principles (accessibility, device-agnostic, no chords) but the actual bindings violate them. The philosophy is aspirational, not enforced.

3. **Coverage completeness illusion** — every player verb has an action ID, but some actions are at the wrong granularity (too coarse: one action covers three distinct verbs; too fine: five actions for what should be one parameterized action).

4. **Gamepad afterthought** — KBM bindings are thoughtful and complete. Gamepad bindings are a mechanical copy with button exhaustion, missing actions, or no consideration of the physical control layout. The gamepad experience is an afterthought despite philosophy claiming device parity.

5. **Navigation blind spot** — navigation model works for the main gameplay screen but hasn't considered settings menus, modal dialogs, build palettes, or panels that overlay each other. The model is tested against the easy case, not the hard case.

6. **Accessibility lip service** — accessibility sections exist with good-sounding principles but no concrete verification. "We support remapping" with no documentation of which actions are actually remappable. "Toggle alternatives exist" with no toggle variants defined anywhere.

7. **Context-model invisibility** — actions live in namespaces that imply contexts (`player_`, `ui_`, `camera_`, `debug_`) but the actual context switching rules are undocumented. When is `player_` active? When does `ui_` take priority? The engine input doc should define this, but if it doesn't exist yet, the input docs should at least acknowledge the dependency.

8. **Mode transition amnesia** — individual modes (gameplay, build, inspect, menu) work fine, but transitions between modes have undefined input behavior. What happens to selection when entering build mode? What happens to camera when opening a modal? Transitions are the seams where input breaks.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--target` | No | all | Target a single doc by filename (e.g., `--target action-map.md`). When set, runs the targeted doc's topic plus Topics 5 and 6. |
| `--topics` | No | all | Comma-separated topic numbers to review (e.g., `"1,3,6"`). |
| `--focus` | No | — | Narrow the review within each topic to a specific concern. |
| `--iterations` | No | 10 | Maximum outer loop iterations. Stops early on convergence. |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic. |
| `--signals` | No | — | Design signals from fix-input to focus the review. Format: comma-separated signal descriptions. |

### --target to --topics mapping

When `--target` is set without explicit `--topics`:

| Target | Auto-selected Topics |
|--------|---------------------|
| `action-map.md` | 1, 5, 6 |
| `input-philosophy.md` | 2, 5, 6 |
| `default-bindings-kbm.md` | 3, 5, 6 |
| `default-bindings-gamepad.md` | 3, 5, 6 |
| `ui-navigation.md` | 4, 5, 6 |

Topics 5 (Cross-Doc Consistency) and 6 (Interaction Readiness) are always included. Explicit `--topics` overrides this mapping.

## Preflight

Before running external review:

1. **Check docs exist.** Verify at least action-map.md, input-philosophy.md, and one binding doc exist and are not at template defaults. If fewer than 3 input docs exist, stop: "Input docs not ready. Run `/scaffold-bulk-seed-input` first."
2. **Check fix-input has run.** Look for the most recent `FIX-input-*` log in `scaffold/decisions/review/`. If no log exists, or the most recent log reports FAIL-level structural issues, stop: "Run `/scaffold-fix-input` first to normalize structure." If no log exists but docs appear structurally clean, proceed with a warning.
3. **Check interaction model exists.** The reviewer needs the Rank 2 interaction model as primary upstream authority. If `design/interaction-model.md` does not exist or is at template defaults, stop: "Interaction model not ready. Run `/scaffold-bulk-seed-style` first."
4. **Check design doc exists.** The reviewer needs Player Verbs and Core Loop as context.

## Context Files

Read and pass as `--context-files` to the Python script:

| Context File | Why |
|-------------|-----|
| All 5 input docs in `scaffold/inputs/` | Primary targets |
| `scaffold/design/interaction-model.md` | Rank 2 authority: what the player does |
| `scaffold/design/design-doc.md` | Player Verbs, Core Loop, Input Feel, Accessibility |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking |
| `scaffold/design/ui-kit.md` | Component references for navigation (if exists) |
| `scaffold/design/feedback-system.md` | Input→response loop closure (if exists) |
| Engine input doc (glob `scaffold/engine/*-input-system.md`) | Implementation constraints (if exists) |
| `scaffold/decisions/known-issues/_index.md` | Known gaps (if exists) |
| Accepted ADRs referencing input | Decision compliance |
| Design signals from fix-input (if `--signals` provided) | Focus areas |

Only include context files that exist — skip missing ones silently.

## Execution

### Loop Structure

```
Outer Loop (iterations — fresh review of updated docs)
│
├── Topic 6 (runs first when budget is tight):
│   ├── End-to-end interaction test
│   ├── Device parity test
│   └── If mandatory gate fails → stop per-doc topics, apply fixes,
│       restart from Topic 6 in next iteration
│
├── Per-Doc Topics (1–4, if Topic 6 passed):
│   └── Per Topic:
│       └── Inner Loop (exchanges — back-and-forth conversation)
│           ├── Reviewer raises issues (structured JSON via doc-review.py)
│           ├── Claude evaluates each: AGREE / PUSHBACK / PARTIAL
│           ├── Reviewer counter-responds
│           └── ... until consensus or max-exchanges
│       └── Failure probe (6 questions) + change impact check
│       └── Consensus → apply accepted changes
│
├── Topic 5 (cross-doc consistency after per-doc fixes):
│   └── Same inner loop
│
└── Re-read updated docs → next outer iteration if issues remain
```

Each topic gets its own review → respond → consensus cycle via the Python `doc-review.py` script. Topic 6 runs first and can short-circuit: if a mandatory gate fails (end-to-end interaction test or device parity test), stop remaining per-doc topics, apply accepted fixes, and restart from Topic 6 in the next iteration.

### Multi-Doc Parallelization

When reviewing all 5 input docs (no `--target`), spawn parallel agents for the per-doc topics (1-4) — one agent per doc. Each agent runs a **complete, self-contained review** of ONE input doc — its per-doc topics, all exchanges, all iterations up to `--iterations` max, all adjudication, all edits. An agent is the same as running `iterate-input --target <doc>` on that doc alone.

1. **Run Topic 6 first** (cross-doc integration gate). If mandatory gates fail, apply fixes before spawning per-doc agents.
2. **Build work list.** Identify all 5 input docs. Log: "Reviewing 5 input docs: action-map, input-philosophy, default-bindings-kbm, default-bindings-gamepad, ui-navigation"
3. **Spawn parallel agents.** One agent per doc, all spawned in parallel (use multiple Agent tool calls in a single message). Each agent receives the doc file, context files (design doc, interaction model, other input docs as read-only context, glossary, ADRs, design signals if provided), review config, and full topic/adjudication instructions.
4. **Collect results.** As agents complete, log progress: "action-map.md — Issues: Y accepted, Z rejected (N of M complete)"
5. **Run Topic 5** (cross-doc consistency) after ALL per-doc agents complete.
6. **Agent failure handling.** Failed agents retry once. If retry fails, report as "review failed" with the error.

When `--target` is specified, skip parallelization and review that single doc directly.

**Stop conditions** (any one stops iteration):
- **Clean** — a complete topic pass produces no new issues.
- **Converged** — two consecutive passes produce the same issue set with no new findings.
- **Human-only** — only issues requiring user decisions remain.
- **Limit** — `--iterations` maximum reached.

**Verification pass rule:** A pass that found issues and applied fixes is NOT clean — it is a “fixed” pass. After a fixed pass, you MUST run at least one more full pass on the updated document to verify no new issues were introduced by the fixes and no previously-hidden issues are now exposed. Only a pass that finds ZERO new issues counts as **Clean**. Stopping after fixing issues without a verification pass is a skill failure.

**Budget priority:** When `--topics` is omitted and `--iterations` is low (≤ 3), run Topic 6 first. Topic 6 is the highest-value topic — it catches integration failures that per-doc reviews miss.

### Review Consistency Lock

Across iterations and topics, resolved issues are locked. Once an issue is **accepted and fixed** or **explicitly rejected with reasoning**, it must not be re-litigated.

**Issue identity rule:** Issues are tracked by root cause, not wording.

**Lock enforcement:**
- The reviewer must NOT reintroduce a resolved issue in a different form.
- The reviewer must NOT raise stricter variants unless: (a) new evidence exists, OR (b) the fix itself introduced a new problem.
- If a previously resolved issue reappears: classify as **review inconsistency**, not a new issue.

**Cross-topic lock:** If Topic 1 resolves a traceability issue, later topics may not re-raise it as a coverage gap.

**Tracking:** Maintain a running resolved-issues list in the review log. Check every new claim against it by root cause.

**Edit scope:**
- When `--target` is set, only edit the targeted doc. Flag cross-doc issues for fix-input.
- When `--target` is not set, edit any of the 5 input docs.
- Never edit interaction-model, design-doc, ui-kit, feedback-system, engine docs, or planning docs.

### Issue Adjudication

Every issue raised by the reviewer must be classified into exactly one outcome:

| Outcome | Action |
|---------|--------|
| **Accept → edit input doc** | Apply change immediately. The issue is valid and within Step 6 scope. |
| **Reject reviewer claim** | Record reasoning in review log. |
| **Escalate to user** | Requires design judgment, or unresolved after adjudication across 2 outer iterations. |
| **Flag for revise-style** | Interaction-model (Rank 2) is likely incomplete or incorrect. The input doc may be right; upstream needs updating. |
| **Defer (valid TBD)** | Correctly blocked by an unresolved upstream decision. |
| **Flag ambiguous upstream** | Interaction-model permits multiple valid input interpretations. Flag for user decision. |

**Adjudication rules:**
- Prefer fixing input docs over escalating — most issues are input-level clarity.
- Never "half-accept" — choose exactly one outcome per issue.
- If the issue depends on a missing interaction-model decision → flag for revise-style.
- If the reviewer and Claude disagree after max-exchanges → escalate to user.

### Scope Collapse Guard

Before accepting any change:

**1. Upward Leakage Test:**
Does this change introduce decisions belonging in the interaction model or design doc?
- Input docs may: define action IDs, bindings, navigation rules, input principles.
- Input docs must NOT: change what interactions exist, alter what the player can do, or redefine system behavior.

**2. Downward Leakage Test:**
Does this change introduce engine-specific implementation detail?
- Input docs must NOT: specify engine input APIs, node types, signal wiring, or input routing implementation.
- Test: could this input definition be implemented in any engine? If engine-specific → wrong layer.

**3. Lateral Leakage Test:**
Does this change belong in a different input doc?
- Action-map must not define bindings (→ binding docs).
- Binding docs must not define actions (→ action-map).
- Philosophy must not define specific bindings (→ binding docs).
- Navigation must not define interaction behavior (→ interaction-model).

### Review Log

Create review log in `scaffold/decisions/review/`:
- Name: `ITERATE-input-[target-or-all]-<YYYY-MM-DD-HHMMSS>.md`
- Use the template at `scaffold/templates/review-template.md`.
- Update `scaffold/decisions/review/_index.md` with a new row.

## Report

```
## Input Review Complete [target / all]

### Most Dangerous Cross-Doc Inconsistency
[The mismatch most likely to produce broken or confusing input.]

### What Could a Developer Get Wrong
[The implicit assumption most likely to produce incorrect input wiring.]

### Weakest Doc
[The doc that contributes least to input implementation clarity.]

### Topic Summary

| Topic | Issues | Accepted | Rejected |
|-------|--------|----------|----------|
| 1. Action Coverage & Traceability | N | N | N |
| 2. Philosophy & Accessibility Coherence | N | N | N |
| 3. Binding Fitness & Device Parity | N | N | N |
| 4. Navigation Model Completeness | N | N | N |
| 5. Cross-Doc Consistency | N | N | N |
| 6. Interaction Readiness | N | N | N |

### Per-Doc Issues
| Document | Issues Found | Accepted Changes | Key Finding |
|----------|-------------|-----------------|-------------|
| action-map.md | N | N | ... |
| input-philosophy.md | N | N | ... |
| default-bindings-kbm.md | N | N | ... |
| default-bindings-gamepad.md | N | N | ... |
| ui-navigation.md | N | N | ... |

**Input Model Strength Rating:** N/5 — [one-line reason]
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N
**Review log:** scaffold/decisions/review/ITERATE-input-[target]-YYYY-MM-DD-HHMMSS.md

### Recommended Next Action
One of:
- **`/scaffold-fix-input`** — structural issues remain after review edits
- **`/scaffold-iterate-input`** — further adversarial review needed (not converged)
- **`/scaffold-revise-style`** — interaction-model gaps detected that input docs cannot resolve
- **User decision required** — blocked on input design judgment
- **Ready to proceed** — input layer is stable, no blocking issues
```

## Rules

- **Interaction-model and design-doc are the primary authority.** Input docs (Rank 3) must conform to interaction-model (Rank 2) and design-doc (Rank 1). On mismatch, the higher-ranked doc is canonical.
- **Input docs describe WHAT TO BIND, not HOW TO IMPLEMENT.** Reject engine-specific input APIs, signal wiring, or routing implementation. Those belong in the engine input doc.
- **Edit only input docs.** Never edit interaction-model, design-doc, ui-kit, feedback-system, engine docs, or planning docs during review.
- **Never blindly accept.** Every issue gets evaluated against project context and upstream canon.
- **Pushback is expected and healthy.** The reviewer is adversarial — disagreement is normal.
- **Escalate only after real adjudication failure.** Same material issue must persist for 2 outer iterations. Escalate immediately if the issue depends on a missing interaction-model decision.
- **When --target is set, respect edit scope.** Cross-doc issues are flagged for fix-input, not fixed directly.
- **Sleep between API calls.** Add `sleep 10` between topic transitions.
- **Clean up temporary files** after use.
- **If the Python script fails, report the error and stop.**
- **Topic 6 is highest-value.** When budget is tight, run Topic 6 first. It catches integration failures per-doc reviews miss.
- **Ambiguous upstream is not an input defect.** When the interaction model permits multiple valid input interpretations and the input doc chose a reasonable one, flag for user decision — don't treat the input doc as wrong.
- **Practicality check before finalizing changes.** Would this change make the doc harder to use? Does it improve clarity for developers or just enforce consistency for the review system? Reject changes that increase rigidity without improving implementability.
- **Scope collapse guard.** Before accepting: (1) Upward — does this change player interactions or system behavior? (2) Downward — does this introduce engine-specific implementation? (3) Lateral — does this belong in a different input doc?
- **Resolved issues are locked across iterations.** Once accepted+fixed or rejected with reasoning, closed. Only new evidence or regression can reopen. Identified by root cause, not phrasing.

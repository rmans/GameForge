# TASK-### — [Task Name]

> **Authority:** Rank 8
> **Layer:** Execution
> **Implements:** SPEC-### (link to parent spec)
> **Phase:** PHASE-### (link to parent phase)
> **Depends on:** — (TASK-### IDs this task requires to be complete first, or "—")
> **Task Type:** foundation / behavior / integration / UI / verification / wiring / art / audio
> **Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Status:** Draft
> **Changelog:**

## Goal

### Objective

<!-- One sentence: what this task produces. -->

### Deliverable

<!-- What should concretely exist when this task is done. More specific than Objective. -->

### Out of Scope

<!-- What this task intentionally does not implement. Prevents task bloat. -->

## Asset Delivery

<!-- ONLY for Task Type: art or audio. Delete this section for code tasks.
     Lists every asset this task must produce, with file paths, specs, and generation prompts.
     The human creates these assets externally and places them at the listed paths.
     Once all assets are delivered, a wiring task connects them to the codebase. -->

<!--
| Asset | Type | File Path | Dimensions / Duration | Prompt |
|-------|------|-----------|----------------------|--------|

Type: Sprite, Mesh, Icon, UI Element, Concept Art, Texture, Tileset, SFX, Music, Ambience, Voice
Dimensions: e.g., 64x64, 1024x1024, 1792x1024 (art) or duration in seconds (audio)
Prompt: Ready-to-use generation prompt incorporating style guide, color system, and design context.

### Style Context

Source docs read to build these prompts:
- `design/style-guide.md` — [relevant sections]
- `design/color-system.md` — [relevant tokens/palette]
- `design/audio-direction.md` — [relevant direction] (audio tasks only)

### Delivery Checklist

- [ ] All assets created and placed at listed file paths
- [ ] Assets match style guide direction
- [ ] Assets match specified dimensions/duration
- [ ] Asset naming follows kebab-case convention
-->

## Implementation

<!-- ONLY for code tasks (foundation/behavior/integration/UI/verification/wiring).
     Delete the Asset Delivery section above for code tasks. -->

### Steps

<!-- Ordered list of implementation steps. Each step should be concrete and verifiable. -->

1. Step one
2. Step two
3. Step three

### Files Created

<!-- New files this task introduces. -->

### Files Modified

<!-- Existing files this task changes. -->

### Data Tables

<!-- If this task adds or modifies game balance values or content definitions:

#### Balance Parameters (ADR-027)
If this task introduces or changes tunable numeric values (damage rates, thresholds,
durations, multipliers, percentages), they must live in the owning system's balance CSV
in `game/data/balance/`. Do NOT hardcode balance values as `static const` in C++.

1. **Add/update entries** in the appropriate `game/data/balance/<system>_balance.csv`.
2. **Load in _ready()** using the established CSV loading pattern.
3. **Provide fallback defaults** in code for graceful degradation if CSV is missing.

#### Content Definitions (ADR-019, ADR-020, ADR-022)
If this task introduces new content types (wound types, infection types, recipes,
constructions, structure definitions), they must live in CSV files in `game/data/content/`.

1. **Add/update entries** in the appropriate content CSV.
2. **Use string IDs** (not enum integers) for serialization compatibility.

#### Display Configuration (ADR-021)
If this task adds or changes how task types or entities appear in the UI,
update `game/data/display/task_display.csv`.

Skip this section for tasks that don't introduce or modify game data values. -->

### Diagnostics

<!-- If this task adds or modifies system logic that manages colonist state, task lifecycle, or cross-system data:

1. **Add [DIAG] warnings** at key decision points where unexpected values indicate a bug.
   Use `push_warning("[DIAG] SystemName::method() — description")` so they're easy to grep.
   These should only fire when something is wrong — NOT high-volume trace prints.

2. **Add invariants to _validate_state()** in SimulationOrchestrator if the task introduces
   new state relationships (e.g., a new lifecycle state, a new assignment field, a new
   cross-reference between systems).

3. **Verify with diagnostics enabled**: Set `diagnostics_enabled = true` on SimulationOrchestrator
   and run the simulation. Confirm zero `[DIAG]` warnings and zero invariant violations.

Skip this section for tasks that don't touch simulation state (e.g., UI-only, audio, scaffold docs). -->

### Localization

<!-- If this task adds or modifies player-visible UI text:

1. **Add keys to `game/translations/strings.csv`** before writing code.
   Use SCREAMING_SNAKE_CASE: `DOMAIN_CONTEXT_ITEM` (e.g., `UI_BUILD_WALL`).
   Fill the `en` column with the English string.

2. **Use `tr("KEY")` in all GDScript** for player-visible text.
   Dynamic strings: `tr("KEY").format([value])` with `{0}` placeholders.
   Arrays of translatable strings: initialize in `_ready()`, not at class level.

3. **Exempt from localization:** `print()` debug output, `push_error()`,
   `push_warning()`, signal names, node paths, enum values, UI symbols ("X", "!").

See `scaffold/engine/godot4-localization.md` for full conventions.

Skip this section for tasks with no player-visible text (e.g., C++ simulation, backend logic). -->

## Testing

### Regression Tests

<!-- Add test coverage to game/scripts/test/test_full_regression.gd for all public methods
and signals introduced or modified by this task. Structure tests across ALL 6 layers below.
Not every layer applies to every task — skip layers that genuinely don't apply and note why.
Update test_full_regression.tscn if a new system node type was added.
Run the full suite to confirm 0 failures, 0 errors, 0 warnings, no regressions.

#### Layer 1 — Core Functionality
The happy path. Prove that the basic data and rules are wired correctly.
  - Test each new public API method with normal, expected inputs.
  - Verify return values match expected behavior.
  - Assert signal payloads are correct when signals fire.
  - Add a new section function (_section_XX) for the system's primary tests.

#### Layer 2 — Edge Cases
Boundaries, invalid states, and rare conditions that colony sims constantly create.
  - Boundary values (zero, max, negative, off-by-one).
  - Invalid IDs (non-existent colonist, non-existent structure, non-existent room).
  - Operations on wrong state (e.g., opening an already-open door, healing a dead colonist).
  - Concurrent access patterns (two tasks targeting the same item, two colonists claiming same task).
  - NOTE: Avoid calling APIs that trigger push_error/push_warning. Instead, verify state
    before or after the operation to confirm the system handled it correctly.

#### Layer 3 — Invariants / Authority Rules
Rules that must NEVER be violated. These are architecture tests that protect the design.
  - Data range invariants (HP never > hp_max, hunger always in [0,1], etc.).
  - Ownership invariants (single writer per variable — confirm no system writes another's data).
  - Structural invariants (every tile has exactly one type, every colonist has exactly one lifecycle state).
  - Relationship invariants (task assigned_worker matches agent_state assignment, grid balance = gen - load).
  - Post-operation invariants (after any operation, verify the system's internal consistency holds).

#### Layer 4 — State Transitions
If the system has changing states, test all valid transitions AND confirm invalid ones are rejected.
  - Test each valid transition individually (e.g., QUEUED → CLAIMED, CLAIMED → IN_PROGRESS).
  - Test the full lifecycle end-to-end (e.g., BLUEPRINT → UNDER_CONSTRUCTION → OPERATIONAL → destroyed).
  - Confirm invalid transitions don't corrupt state (e.g., DEAD → WORKING should not happen).
  - Verify that state changes emit the correct signals with correct payloads.

#### Layer 5 — Integration Points
Most bugs in colony sims happen BETWEEN systems, not inside them.
  - Test what this system READS from other systems (e.g., PowerSystem reads StructureSystem integrity).
  - Test what this system OUTPUTS that other systems consume (e.g., HealthSystem emits damage_applied → InjurySystem).
  - Verify cross-system data stays consistent after operations (e.g., structure destroyed → room dissolves → environment loses data).
  - Add cross-reference tests (_section_XXX) for each system pair that interacts.

#### Layer 6 — Stress / Scale / Repetition
A system that works once may fail after 500 iterations. Catches accumulating state corruption.
  - Repeat core operations N times (10-50) and verify state stays consistent.
  - Create many entities (structures, tasks, items) rapidly, then verify counts and references.
  - Destroy many entities rapidly and verify no stale references remain.
  - Tick systems many times and verify values stay clamped / don't drift.
  - Operations that modify shared state (room detection after repeated wall changes, grid recalc after generator churn).
-->

### GUT Unit Tests

<!-- If this task involves GDScript (UI panels, orchestration, helpers):

Write GUT (Godot Unit Testing) tests for the GDScript code introduced or modified.
Place test files in `game/tests/` following GUT conventions:
  - Test file: `test_<script_name>.gd`
  - Test class: `extends GutTest`
  - Test functions: `func test_<behavior>():`

Focus on:
  - Public functions and their return values
  - State changes after method calls
  - Edge cases (empty input, boundary values, invalid state)
  - Signal emissions from GDScript code

GUT tests complement the C++ regression tests above. Regression tests cover C++ system
APIs and cross-system integration. GUT tests cover GDScript-layer logic and UI behavior.

Skip this section for tasks that are purely C++ with no GDScript changes. -->

### GDScript Lint

<!-- If this task creates or modifies GDScript files:

Run `gdlint` on each changed `.gd` file from the `game/` directory.
All files must pass with "Success: no problems found".

The project's `gdlintrc` config is tuned for our codebase:
  - 150 char line length (draw calls are long)
  - SCREAMING_SNAKE_CASE allowed for class-scope vars
  - class-definitions-order disabled (we group by logical section)
  - addons directory excluded

Skip this section for tasks with no GDScript changes. -->

### Manual Playtest Checklist

<!-- Click-by-click steps for the project owner to verify things the automated regression tests cannot catch. This includes visual behavior, UI feedback, real-time gameplay feel, tick ordering in the live orchestrator, and emergent interactions between systems.

Each checklist item should follow this format:
  1. **Setup**: What scene to open, what to do before the test (e.g., "Run the game scene, unpause, wait 10 seconds")
  2. **Action**: Exactly what to click, press, or observe
  3. **Expected result**: What you should see, hear, or notice
  4. **Pass/Fail**: [ ] checkbox

Focus on things automated tests CANNOT verify:
  - Visual/UI: sprites, animations, labels, HUD updates, color changes
  - Audio: sound effects, music triggers
  - Input: mouse clicks, keyboard shortcuts, drag-and-drop
  - Game feel: timing, responsiveness, frame rate during load
  - Emergent behavior: multi-system interactions during live gameplay
  - Tick ordering: systems updating in the correct order via the real orchestrator

Skip this section for tasks that are purely internal (no player-visible behavior). -->

## Verification

### Summary

<!-- How to confirm this task is done correctly. Summary of both automated and manual checks.
Always include: "Build with scons — zero errors. Run with diagnostics_enabled = true — zero [DIAG] output." -->

### Verification Mapping

<!-- Maps parent spec acceptance criteria to verification steps. Makes spec coverage auditable. -->
<!--
- AC-1 → Verification step N
- AC-2 → Verification step M
-->

## Risk & Notes

### Risks

<!-- Task-local execution risks. Where the implementer is most likely to break things. -->

### Notes

<!-- Implementation notes, gotchas, references to engine docs. -->

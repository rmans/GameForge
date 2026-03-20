# Workflow — Step-by-Step

> **What this is:** A numbered recipe. Start at Step 1, follow in order. Each step is one skill command and one sentence of context.

## Two-Loop Model

This workflow has two loops. The **outer loop** ensures architectural stability. The **inner loop** produces documents and code.

```
OUTER LOOP (architecture stability)
│
├─ Pre-Gate Context (Steps 1–6)
│   Design → Systems → References → Engine → Visual/UX → Inputs
│
├─ Foundation Architecture (Step 7)
│   Revise (no-op initial / dispatch on recheck) → fix (cross-doc integration) → validate (gate) → fix cross-cutting
│
├─ INNER LOOP (planning + implementation)
│   │
│   ├─ Planning: Roadmap (Step 8: create→fix→iterate→validate)
│   │            → Phases (Step 9: seed→fix→iterate→validate→approve)
│   │                         → Slices (seed→fix→iterate→validate→approve)
│   │                         → Specs (seed→fix→iterate→triage→validate→approve)
│   │                         → Tasks (seed→fix→iterate→triage→validate→reorder→approve)
│   ├─ Building: Implement → Test → Review → Complete
│   └─ Feedback: ADRs, known issues, triage logs
│
├─ Feedback Absorption (Step 14, outer loop)
│   Revise roadmap → revise phases → review ADRs, triage logs, playtest patterns
│
└─ Foundation Recheck (Step 14, outer loop)
    Did implementation shift any foundation assumptions?
    ├─ No drift → proceed to next inner loop cycle
    └─ Drift detected → update architecture docs, file ADRs, then proceed
```

**The outer loop is a stability check, not a guaranteed rewrite.** Most cycles pass through quickly. It only triggers real work when implementation reveals a foundational contradiction — a new ADR changes ownership rules, a triage decision implies upstream architecture work.

**Steps 1–7 establish the initial foundation.** Steps 8–14 then operate inside the repeating two-loop cycle, with Step 7 re-entered in recheck mode whenever implementation feedback suggests foundation drift.

## Range Parallelization

When a skill processes a range (e.g., `SPEC-001-SPEC-010`, `TASK-001-TASK-020`), items can run in parallel if their dependencies are met. Items with unmet dependencies wait.

```
1. Build dependency graph for all items in the range
   - Tasks: read Depends on: TASK-### header
   - Slices: read Depends on: SLICE-### header
   - Phases: read entry criteria for phase ID references
   - Specs: independent within a slice (no spec-to-spec dependencies)

2. Identify the ready set — items whose dependencies are ALL complete
   (either already Complete/done, or not in the current range)

3. Process the ready set in parallel
   - For fix/iterate skills: respect rate limits (sleep 10 between API calls)
   - For implement-task: fully parallel for independent tasks

4. As items complete, re-evaluate the dependency graph
   - Newly unblocked items join the next parallel batch
   - Items still waiting continue to hold

5. Repeat until all items are processed or a failure stops the run
```

**Dependency sources by document type:**

| Document | Dependency Field | Parallel When |
|----------|-----------------|---------------|
| Phase | Entry Criteria (phase ID refs) | All referenced phases are Complete |
| Slice | `> **Depends on:** SLICE-###` | All declared dependencies are Complete |
| Spec | None (independent within slice) | Always parallel within a slice |
| Task | `> **Depends on:** TASK-###` | All declared dependencies are Complete |

**Failure handling:** If an item fails during parallel processing, items that depend on it are skipped (they can't proceed). Independent items continue.

**Rate limiting:** For skills that call external APIs (iterate-* skills using doc-review.py), add `sleep 10` between parallel batches to respect rate limits. Do not fire all API calls simultaneously.

**Sequential fallback:** If no dependency information exists (field is absent or all items say "—"), process sequentially in range order. Don't assume independence when dependency data is missing.

## Human Decision Presentation

When a skill requires human input (triage, seed confirmation, revision proposals, approval overrides), follow these principles consistently:

1. **Group issues by category** — don't mix splits with merges with scope changes. Each category gets its own section header.
2. **Number each issue** — every decision point gets a unique number for reference.
3. **Present concrete options per issue** — each issue has lettered choices (a/b/c), not open-ended questions. The user picks an option, not writes an essay.
4. **Wait for decisions before proceeding** — never auto-decide. Never infer intent from silence.
5. **Classify decisions before applying** — local decisions (change only this document) apply immediately. Architecture-impacting decisions (change ownership, authority, interfaces, persistence, state machines, contracts) get an upstream action or ADR stub in addition to the local change.
6. **Show what will change** — for each option, state the concrete edit that will happen. "Narrow scope to X" not just "narrow scope."
7. **Record decisions persistently** — triage decisions go in triage logs. Revision decisions go in revision logs. Seed decisions are implicit in the confirmed candidate set.

This pattern applies to:
- `/scaffold-triage-tasks` and `/scaffold-triage-specs` (the original triage skills)
- `/scaffold-bulk-seed-slices` and `/scaffold-bulk-seed-phases` (candidate confirmation)
- `/scaffold-revise-slices` and `/scaffold-revise-phases` (revision proposals)
- Any skill with a "user must confirm" or "override" path

---

## Pre-Gate Document Production (Steps 1–6)

Steps 1–6 produce the canonical design, system, reference, input, and engine context required for the **Foundation Architecture** step (Step 7). These steps define the game and surface architectural pressure points, but they do not assume that all cross-cutting implementation decisions are already locked. The goal is to enter the Foundation Architecture Gate with enough information to make stable decisions about identity, storage, content definitions, save/load, spatial model, and API boundaries — before the planning graph scales into phases, slices, specs, and tasks.

Each step feeds the gate:

| Step | What it produces | What it surfaces for the gate |
|------|-----------------|-------------------------------|
| 1 | Design truth (vision, loops, mechanics) | Core simulation pressures, player verbs, content categories |
| 2 | System candidates and boundaries | Ownership conflicts, dependency patterns, persistence implications |
| 3 | Reference drafts + architecture (authority, interfaces, states, signals) | Identity model assumptions, storage patterns, cross-system contract gaps |
| 4 | Engine constraints (coding, UI, input, scene, performance, simulation runtime, save/load, AI/task execution, data pipeline, localization, post-processing, implementation patterns) | Engine-level viability risks, rendering approach, save architecture, data storage patterns, simulation loop implementation, task/reservation execution, content pipeline |
| 5 | Visual/UX truth (style, colors, UI kit, interaction model, audio direction) | UI architecture needs, presentation rules, interaction constraints |
| 6 | Input model (actions, bindings, navigation) | Input architecture constraints |

---

## Step 1 — Design Definition

> **Output:** `design/design-doc.md` with all sections filled and reviewed. **Proceed when:** iterate passes with no critical issues. **Surfaces for Step 7:** core simulation pressures, player verbs, content categories.

### 1a — Initialize

```
/scaffold-init-design [--mode seed|fill-gaps|reconcile|refresh]
```

Ingests existing project material, classifies each design doc section (Complete/Partial/Conflicted/Missing), pre-fills what can be inferred from other docs, and only interviews for genuine gaps. Supports 4 modes: `seed` (first time), `fill-gaps` (incomplete sections), `reconcile` (contradiction resolution), `refresh` (rethink specific sections). This is the highest-authority document — everything else flows from it.

### 1b — Fix (mechanical cleanup)

```
/scaffold-fix-design
```

Auto-fixes template text, incomplete governance formats (invariants, pressure tests), terminology drift, system index mismatches, and missing section stubs. Surfaces strategic issues (contradictions, invariant violations from downstream, unescalated mechanics, layer violations, philosophy drift) for human decision.

> `/scaffold-review-design` provides a read-only audit at any time.

### 1c — Iterate (adversarial review)

```
/scaffold-iterate-design
```

Adversarial per-topic review by an external LLM across 5 topics: vision coherence, player experience model, world & presentation integrity, governance mechanism quality, scope & content realism. Catches structural design weaknesses self-review misses. A passing review sets the document's status to `Approved`.

> The generic `/scaffold-iterate design/design-doc.md` also works but lacks the design-specific topic structure, governance checks, and final questions (biggest contradiction, accidental player experience, weakest governance mechanism).

### 1d — Validate (structural gate)

```
/scaffold-validate --scope design
```

Deterministic structural gate: 13 checks covering existence, section structure (10 core-required sections are FAIL if missing), weighted health (Complete=1.0, Partial=0.5, Empty=0), governance format validation (invariants, anchors, pressure tests, gravity, boundaries), system index sync, glossary compliance, ADR consistency, provisional markers, and review freshness.

### 1e — Revise (post-implementation feedback loop)

```
/scaffold-revise-design [--source P#-###|SLICE-###|foundation-recheck]
```

Called from the outer loop (Step 14) or when `/scaffold-revise-foundation --mode recheck` detects Step 1 drift. Reads ADRs, known issues, playtest patterns, and downstream friction. Classifies drift as design-led (intentional) vs implementation-led (unapproved divergence). Auto-updates safe mechanical changes; dispatches to `init-design --mode reconcile/refresh` for design decisions; escalates governance impacts to the user. After revise-design runs, re-run the stabilization loop: **revise-design → fix-design (1b) → iterate-design (1c) → validate --scope design (1d)**.

---

## Step 2 — System Definition

> **Output:** `design/glossary.md` seeded with key terms; all `design/systems/SYS-###-*.md` files filled with purpose, ownership, dependencies, interfaces, state transitions, observability, and performance characteristics. **Proceed when:** fix + iterate + validate --scope systems passes. **Surfaces for Step 7:** ownership conflicts, dependency patterns, persistence implications.

### 2a — Create

```
/scaffold-bulk-seed-systems
```

Proposes systems from simulation responsibilities and owned player-facing concerns — not raw verbs. Reads Design Invariants, Player Control Model, Major System Domains, and Simulation Depth Target to shape proposals. Audits for overlap, missing coverage, invariant conflicts, and system category coverage before creation. Seeds glossary terms and creates system stubs with pre-filled purpose, simulation responsibility, design constraints, owned state, and dependencies.

To add a single system after initial seeding (e.g., when `revise-systems` detects emergent subsystem pressure, `validate` finds a design-to-systems gap, or a split is needed), use:

```
/scaffold-new-system [name] [--split-from SYS-###] [--trigger ADR-###|KI:keyword]
```

Performs the same overlap/authority/invariant audit as bulk-seed but for one system. When `--split-from` is provided, also updates the parent system's Non-Responsibilities and dependency tables.

### 2b — Fix (mechanical cleanup)

```
/scaffold-fix-systems SYS-###-SYS-###
```

Mechanical cleanup pass — normalizes structure, repairs terminology drift, fixes registration gaps, detects dependency asymmetry. Detects design signals (invariant violations, ownership conflicts, layer breaches) and reports them for adversarial review. All individual fix loops run in parallel; a cross-system pass runs after to catch inter-system issues.

### 2c — Iterate (adversarial review)

```
/scaffold-iterate-systems SYS-###-SYS-###
```

Adversarial per-topic review via external LLM. Consumes design signals from fix-systems. Reviews system designs for ownership correctness, design governance compliance, cross-system coherence, and behavioral completeness. A passing review sets the document's status to `Approved`.

### 2d — Validate (structural gate)

```
/scaffold-validate --scope systems
```

Deterministic structural gate: 16 checks covering index registration, design-doc sync, status sync, section structure, core-section defaults, weighted health, owned state format, glossary compliance, dependency symmetry, owned state overlap, dependency cycles, orphan detection, dependency table format, template drift, seeded markers, and review freshness. Supports `--range SYS-###-SYS-###` for targeted validation.

### 2e — Revise (post-implementation feedback loop)

```
/scaffold-revise-systems [--source P#-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword]
```

Called from the outer loop (Step 14) or when `/scaffold-revise-foundation --mode recheck` detects Step 2 drift. Reads ADRs, known issues, spec/task friction, and code review findings. Classifies drift as design-led vs implementation-led. Auto-updates safe changes (dependency entries, edge cases, stale references); escalates ownership shifts, authority violations, and behavior gaps. After revise-systems runs, re-run the stabilization loop: **revise-systems → fix-systems (2b) → iterate-systems (2c) → validate --scope systems (2d)**.

---

## Step 3 — Reference Model

> **Output:** `design/architecture.md`, `design/authority.md`, `design/interfaces.md`, `design/state-transitions.md`, `reference/entity-components.md`, `reference/resource-definitions.md`, `reference/signal-registry.md`, `reference/balance-params.md`, `reference/enums-and-statuses.md` — all populated and reviewed. **Proceed when:** fix + validate --scope refs passes. **Surfaces for Step 7:** identity model assumptions, storage patterns, cross-system contract gaps, foundation area definitions, shared status vocabulary.

### 3a — Create

```
/scaffold-bulk-seed-references
```

Reads all system designs and bulk-populates: architecture (foundation area definitions derived from system patterns), authority table, interface contracts, state transitions, entity components (including identity semantics — handle format, invalidation, persistence mapping), resource definitions, signal registry (with event-level taxonomy: gameplay/domain/engine), balance parameters, and shared enums/statuses. These docs surface the cross-cutting architecture assumptions that must be locked in Step 7.

### 3b — Fix (mechanical cleanup)

```
/scaffold-fix-references
```

Mechanical cleanup pass for all 9 Step 3 docs. Per-doc checks (section structure, table columns, terminology, registration) followed by cross-doc consistency pass (authority→entity-components, interfaces→signals, state-transitions→enums, architecture→scene tree). Auto-fixes alignment issues and detects design signals for adversarial review. Supports `--target doc.md` for single-doc focus (used by revise-foundation when only one doc was revised).

### 3c — Iterate (adversarial review)

```
/scaffold-iterate-references
```

Adversarial per-topic review via external LLM across 6 topics (architectural coherence, ownership & authority model, contract & interface quality, data model fitness, cross-doc consistency, simulation readiness). Consumes design signals from fix-references. Supports `--target doc.md` for single-doc focus and `--topics` for scoped review. A passing review sets the documents' status to `Approved`.

### 3d — Validate

```
/scaffold-validate --scope refs
```

Deterministic checks in two layers: (1) Python script — system IDs, authority entities, signal systems, interface systems, state authorities, glossary NOT-terms, bidirectional registration. (2) Expanded reference checks — doc existence, section structure for all 9 Step 3 docs, column completeness, enumerated value validity, cross-doc consistency (authority↔entity, interface↔signal, state↔enum, architecture↔scene tree), duplicate detection, production chain completeness.

### 3e — Revise (post-implementation feedback loop)

```
/scaffold-revise-references [--source P#-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword] [--target doc.md]
```

Called from the outer loop (Step 14) or when `/scaffold-revise-foundation --mode recheck` detects Step 3 drift. Reads ADRs, known issues, system doc changes, spec/task friction, and code review findings. Classifies drift as design-led vs implementation-led. Auto-updates safe changes (missing registrations, stale references, column updates); escalates authority changes, architecture changes, contract changes, and state machine changes. Respects canonical direction (authority→entity-components, interfaces→signal-registry, state-transitions→enums). After revise-references runs, re-run the stabilization loop: **revise-references → fix-references (3b) → iterate-references (3c) → validate --scope refs (3d)**.

---

## Step 4 — Engine Constraints

> **Output:** `engine/[prefix]-coding-best-practices.md`, `engine/[prefix]-ui-best-practices.md`, `engine/[prefix]-input-system.md`, `engine/[prefix]-scene-architecture.md`, `engine/[prefix]-performance-budget.md`, `engine/[prefix]-simulation-runtime.md`, `engine/[prefix]-save-load-architecture.md`, `engine/[prefix]-ai-task-execution.md`, `engine/[prefix]-data-and-content-pipeline.md`, `engine/[prefix]-localization.md`, `engine/[prefix]-post-processing.md`, `engine/implementation-patterns.md`, `engine/[prefix]-asset-import-pipeline.md`, `engine/[prefix]-debugging-and-observability.md`, `engine/[prefix]-build-and-test-workflow.md` — all populated and reviewed. **Proceed when:** iterate pass converged, validate gate passes (`/scaffold-validate --scope engine`). **Surfaces for Step 7:** engine-level viability risks for identity, storage, save/load, scene architecture, UI rendering approach, data storage patterns, simulation runtime, task/reservation execution, content pipeline, performance, observability, testing.

Step 4 runs after systems and references are defined, so engine decisions have full context: what systems exist, what data they own, what signals they use, and what cross-system contracts apply. Engine docs lock the technical foundations (rendering approach, save architecture, data table patterns, UI implementation strategy) that Visual/UX and Input docs build on top of.

### 4a — Create

```
/scaffold-bulk-seed-engine
```

Asks which engine and implementation stack, then seeds all 14 engine docs from templates in one pass — no per-doc confirmation. Reads Step 1-3 outputs to align with architecture decisions. Confidence-tiered pre-fill: Strong (engine conventions known + Step 3 locked), Constrained TODO (Step 3 is TBD), Open TODO (no basis). Reports architecture alignment and constrained TODOs.

### 4b — Fix (mechanical cleanup)

```
/scaffold-fix-engine [--target doc-stem]
```

Mechanical cleanup pass for all 15 engine docs. Per-doc checks (section structure, terminology, registration, constrained TODO currency) plus alignment signal detection (architecture contradictions, authority assumptions, interface timing mismatches, layer breaches). Cross-doc pass checks convention consistency, architecture alignment coverage, and maturity imbalance. Supports `--target` for single-doc focus.

### 4c — Iterate (adversarial review)

```
/scaffold-iterate-engine [--target doc-stem] [--topics "1,2,5"] [--iterations N]
```

Adversarial per-topic review of all 15 engine docs via external LLM across 6 topics (architecture implementation fidelity, authority & contract compliance, engine convention quality, cross-engine consistency, implementation sufficiency, simulation-layer fitness). Consumes alignment signals from fix-engine. Reviews whether engine docs correctly implement Steps 1-3 decisions using sound engine patterns. Supports `--target` for single-doc focus and `--topics` for scoped review. A passing review sets the document's status to `Approved`.

Includes safeguards: scope collapse guard (engine docs implement, not define), ambiguous upstream handling (flags for revise-references instead of forcing interpretations), review consistency lock (resolved issues stay resolved across iterations), and practicality check (rejects changes that optimize for review criteria over developer usability).

### 4d — Validate (structural gate)

```
/scaffold-validate --scope engine
```

Deterministic validation of engine doc structural integrity: index registration, header metadata (Layer, Rank 9, Conforms-to resolution), required sections, content health, Step 3 alignment, cross-engine consistency, layer boundary compliance, template drift, and review freshness. Heuristic checks (authority compliance, design content detection, naming consistency) are labeled `[ADVISORY]` to separate them from deterministic failures.

### 4e — Revise (post-implementation feedback loop)

```
/scaffold-revise-engine [--source P#-###|SLICE-###|foundation-recheck] [--signals ADR-###,REFS:doc-stem] [--target doc-stem]
```

Called from the outer loop (Step 14) or when `/scaffold-revise-foundation --mode recheck` detects Step 4 drift. Reads ADRs, known issues, spec/task friction, code review findings, and Step 3 doc changes to identify when engine docs no longer match what was actually built or what Steps 1-3 now define. Signal-driven with explicit resolution table. Classifies drift as design-led (Step 3 changed, engine follows) vs implementation-led (code diverged without authority). Auto-updates safe changes (stale references, Step 3 alignment, constrained TODO resolution, new implementation patterns). Escalates convention changes, performance budget revisions, and architecture implementation changes with CRITICAL/HIGH/MEDIUM priority weighting. Includes early exit when no engine-impacting signals remain, repeated divergence escalation (forced decision at 2+ runs), duplicate pattern guard for implementation-patterns.md, partial Step 3 instability suppression, and post-edit reference integrity check. After revise-engine runs, re-run the stabilization loop: **fix-engine (4b) → iterate-engine (4c) → validate --scope engine (4d)**.

---

## Step 5 — Visual & UX Definition

> **Output:** `design/style-guide.md`, `design/color-system.md`, `design/ui-kit.md`, `design/interaction-model.md`, `design/feedback-system.md`, `design/audio-direction.md` all filled and reviewed. **Proceed when:** bulk review passes. **Surfaces for Step 7:** presentation rules, interaction patterns, feedback coordination (timing, priority, cross-modal), audio integration requirements.

Step 5 runs after engine constraints are locked, so visual/UX decisions have full context: what systems exist, how entities are identified, what the player interacts with, what architecture constraints apply, and critically — how the engine renders UI (`_draw()` vs Control nodes), what scene patterns exist, and what performance constraints apply. The ui-kit and interaction-model can make concrete implementation-aware decisions instead of abstract ones.

### 5a — Create

```
/scaffold-bulk-seed-style
```

Reads the design doc and system designs (primary), architecture/reference/engine docs (secondary constraints), and theory docs (advisory) to seed all 6 docs. Auto-writes high-confidence sections directly, tags medium-confidence sections with rationale in the changelog, and leaves low-confidence sections as TODOs. Only pauses for user confirmation on ambiguous style direction, competing visual interpretations, major UX model choices, or decisions that would materially change downstream docs. Phases are processed in order (style-guide → color-system → ui-kit → interaction-model → feedback-system → audio-direction) but ui-kit and interaction-model may reveal back-propagation needs — these are noted in the report, not silently fixed. Skips already-authored docs.

After seeding, review the report for medium-confidence assumptions and low-confidence TODOs. For any sections the bulk seed couldn't derive, fill them interactively.

**`interaction-model.md` covers:**
- **Selection model** — single select, multi-select, drag-select, what's selectable, selection persistence across layers, deselection rules
- **Command model** — direct commands, queued commands, priority commands, modal commands, command cancellation
- **Secondary actions** — right-click context, modifier-key actions, double-click behaviors
- **Drag behaviors** — drag-to-select, drag-to-place, drag-to-assign, drag thresholds
- **Interaction patterns** — select entity, issue command, inspect information, cancel action, navigate layers
- **UI feedback rules** — hover feedback, selection highlight, invalid action feedback, warning states, confirmation prompts, success/failure indicators
- **Layer navigation** — how the player moves between game layers (build mode, zone mode, colonist view, etc.), what persists across layer switches

**`feedback-system.md` covers:**
- **Feedback types** — action confirmation, action failure, state change notification, warning/escalation, critical alert, selection/hover, sustained state
- **Timing rules** — instant vs delayed, sustained vs transient, queued vs immediate
- **Priority & stacking** — priority hierarchy (critical > warning > confirmation > notification > selection), visual stacking, audio stacking, modal interaction
- **Cross-modal coordination** — how visual + audio + UI fire together for each event, channel responsibilities, redundancy principle (two-channel minimum for gameplay-critical info)
- **Event-response table** — practical reference mapping every major game event to its coordinated response across all channels

**`audio-direction.md` covers:**
- **Audio philosophy** — what role sound plays in the experience (simulation awareness vs spectacle, ambient vs reactive)
- **Sound categories** — feedback sounds, ambient world sound, system alerts, music, UI sounds
- **Music direction** — when music plays, what it communicates, pacing relationship to gameplay
- **Silence & space** — when the game should be quiet, how audio density relates to game state
- **Feedback hierarchy** — priority ordering of audio signals (critical alerts > interaction feedback > ambient)
- **Asset style rules** — 2D/3D audio, realistic vs stylized, frequency ranges, loudness conventions

**`style-guide.md` covers:**
- **Art direction** — aesthetic pillars, visual references, overall style (pixel art, hand-painted, low-poly, etc.)
- **Visual tone** — tone registers (baseline, tension, crisis) and how mood shifts visually with game state
- **Rendering approach** — 2D / 3D / hybrid, camera perspective, resolution and scale
- **Character & entity style** — entity visual hierarchy, how types are distinguished at a glance
- **Environment style** — terrain, structures, how player-built is distinct from natural
- **Animation style** — motion language, transition timing, feedback animations
- **Iconography style** — icon design rules, readability requirements, state representation

**`color-system.md` covers:**
- **Palette** — base palette (default look), signal palette (system state colors), identity palette (factions, zones, categories)
- **Color tokens** — semantic tokens that decouple meaning from hex values (state tokens, UI tokens)
- **Usage rules** — how many accent colors on screen, signal color reservation, contrast requirements
- **UI vs world colors** — relationship between UI overlay palette and game world colors
- **Accessibility** — WCAG contrast targets, color-blind safe palette, redundant encoding rules
- **Theme variants** — faction palettes, biome shifts, escalation-driven palette changes

**`ui-kit.md` covers:**
- **Component definitions** — panels, buttons, tooltips, progress bars, alerts, confirmation dialogs
- **Component states** — default, hover, pressed, focused, disabled, error, selected (mapped to color tokens)
- **Typography** — type scale, font choices, weight usage, data density rules
- **Iconography** — icon categories, size constraints, color usage, state variants
- **Spacing & layout conventions** — spacing scale, safe zones (component-level, not screen maps)
- **Animation & transitions** — panel open/close, hover/press timing, easing curves
- **Sound feedback** — per-component sounds only (click, hover, toggle); cross-modal coordination is in feedback-system

### 5b — Fix (mechanical cleanup)

```
/scaffold-fix-style
```

Mechanical cleanup pass for all 6 Step 5 docs. Auto-fixes template text, terminology drift, cross-doc inconsistencies, token normalization, and boundary violations. Detects design signals (tone mismatches, component gaps, scope creep, priority conflicts) for adversarial review. Supports `--target` for single-doc focus. Authority flows downstream within Step 5: style-guide → color-system → ui-kit; interaction-model ↔ feedback-system (peers); audio-direction derives priority from feedback-system.

### 5c — Iterate (adversarial review)

```
/scaffold-iterate-style
```

Adversarial review of all 6 Step 5 docs using an external LLM. Each doc gets its own specialized review lens targeting its unique failure modes: (1) visual identity & readability, (2) color semantics & accessibility, (3) UI component model, (4) input clarity & command structure, (5) response coverage & priority logic, (6) audio tone & boundary discipline. Then Topic 7 checks the cross-doc seams — whether the 6 docs work together as one system. Topic 7 runs first when budget is tight. Supports `--target` for single-doc focus and `--topics` for scoped review. A passing review sets the document's status to `Approved`.

### 5d — Validate (gate check)

```
/scaffold-validate --scope style
```

Validates Step 5 doc structural integrity, content health, cross-doc consistency, authority flow, boundary compliance, token resolution, and accessibility coherence. Checks that color tokens resolve, no raw hex values leak into downstream docs, interaction actions have feedback coverage, feedback priorities align with audio priorities, and accessibility promises are enforced (no color-only states, no hover-only cues, multi-channel critical events).

> **Art & Audio:** With style docs in place, you can now generate visual and audio assets at any point. See the Quick Reference table for all art and audio skills.

### 5e — Revise (post-implementation feedback loop)

```
/scaffold-revise-style [--source P#-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword,PLAYTEST:keyword] [--target doc.md]
```

Detect Step 5 doc drift from implementation feedback. Reads ADRs, known issues, playtest feedback patterns, design doc changes, system doc changes, Step 3 doc changes, spec/task friction, and code review findings. Classifies each signal as design-led (upstream authority changed), playtest-led (player feedback pattern), or implementation-led (code diverged without approval). Auto-updates safe changes: missing tokens, stale references, new feedback entries (conservative defaults — never auto-adds Critical events), cross-doc alignment. Escalates aesthetic direction changes, interaction model changes, priority hierarchy changes, accessibility changes (always escalates even with ADR), component removals, and token system restructures. Follows Step 5 authority flow: style-guide → color-system → ui-kit; feedback-system → audio-direction. Supports `--target` for single-doc focus and `--signals` for targeted dispatch from revise-foundation.

---

## Step 6 — Input Model

> **Output:** `inputs/action-map.md`, `inputs/input-philosophy.md`, `inputs/default-bindings-kbm.md`, `inputs/default-bindings-gamepad.md`, `inputs/ui-navigation.md` — all populated and reviewed. **Proceed when:** fix + iterate + validate --scope input passes. **Surfaces for Step 7:** input architecture constraints, action model assumptions, device support commitments.

### 6a — Create

```
/scaffold-bulk-seed-input
```

Reads the design doc, interaction model, and engine input docs to pre-fill action-map, input-philosophy, keyboard/mouse bindings, gamepad bindings, and UI navigation.

### 6b — Fix (mechanical cleanup)

```
/scaffold-fix-input [--target doc.md] [--iterate N]
```

Mechanical cleanup pass for input docs. Auto-fixes action ID naming conventions, binding collisions, orphan bindings, template text, terminology drift, and cross-doc inconsistencies (action-map ↔ bindings ↔ navigation ↔ interaction-model ↔ design doc). Detects design signals (missing player verbs, namespace confusion, action bloat, philosophy-interaction mismatches, accessibility gaps, button exhaustion) for adversarial review. Supports `--target` for single-doc focus. Context-aware collision detection — namespace-separated and mode-separated overlaps are not flagged.

### 6c — Iterate (adversarial review)

```
/scaffold-iterate-input [--target doc.md] [--topics "1,3,6"] [--focus "concern"] [--iterations N]
```

Adversarial per-topic review via external LLM. Consumes design signals from fix-input. Reviews across 6 topics: action coverage & traceability, philosophy & accessibility coherence, binding fitness & device parity, navigation model completeness, cross-doc consistency, and interaction readiness. Mandatory end-to-end interaction test and device parity test gate further per-doc reviews. A passing review sets the document's status to `Approved`.

### 6d — Validate (structural gate)

```
/scaffold-validate --scope input
```

Deterministic structural gate: action ID conventions, traceability (Source column), binding coverage and collision detection, navigation completeness, upstream alignment (interaction-model and design-doc coverage), philosophy-binding compliance, device parity, and review freshness.

### 6e — Revise (post-implementation feedback loop)

```
/scaffold-revise-input [--source P#-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword,STYLE:doc-changed]
```

Called from the outer loop (Step 14) or when `/scaffold-revise-foundation --mode recheck` detects Step 6 drift. Reads ADRs, known issues, spec/task friction, code review findings, interaction model changes, and ui-kit changes. Classifies drift as design-led vs implementation-led. Auto-updates safe changes (stale references, missing actions from upstream, orphan bindings, terminology drift); escalates philosophy violations, navigation model changes, device parity gaps, and accessibility changes. After revise-input runs, re-run the stabilization loop: **revise-input → fix-input (6b) → iterate-input (6c) → validate --scope input (6d)**.

---

## Step 7 — Foundation Architecture

> **Output:** All 6 foundation areas Locked or Partial (bounded, tracked). Architecture docs consistent across domains. **Proceed when:** gate passes (PASS or CONDITIONAL). **Surfaces for planning:** stable cross-cutting rules that downstream phases, slices, specs, and tasks can rely on.

Steps 1–6 stabilized individual document domains. Step 7 is the **architecture orchestrator** — it performs cross-document integration, detects contradictions across all foundation docs, and ensures rewrite-multiplier decisions are explicitly resolved before the planning graph scales.

The pipeline is **revise → fix → validate**. On initial pass, revise is a readiness check (nothing to revise yet). On recheck, revise reads implementation feedback and dispatches revision loops to affected Step 1–6 docs. Fix performs cross-document integration and surfaces Lock/Partial/Defer decisions for human resolution. Validate is the deterministic gate.

Step 7 does not re-run adversarial review on foundational docs — adversarial review happens within Steps 1–6 on each individual doc. Step 7 only handles cross-document integration, contradiction repair, and foundation-level validation. Foundational docs are living documents (like the roadmap) that are semi-locked, not formally approved artifacts.

The purpose is not to finalize every low-level implementation detail — it's to lock the rewrite-multiplier decisions that would otherwise cause broad downstream churn. Final direction for unresolved foundation questions comes from explicit user decisions or accepted ADRs.

**Foundation areas:**

1. **Runtime identity / handle model** — how entities are identified, what happens on destroy/reuse, handle validation rules
2. **Content-definition model** — what stays enum/hardcoded vs registry-backed external content, ID/namespacing policy, mod-extensibility assumptions
3. **Runtime entity / storage model** — how entities are stored (ECS, slot arrays, object pools), iteration/reuse rules, stale-reference semantics
4. **Save/load architecture** — schema philosophy, validation pipeline, versioning/migration policy, external-ID vs runtime-ID mapping
5. **Map / spatial model** — fixed vs variable dimensions, tile indexing convention, dense vs sparse spatial storage, multi-layer rules
6. **Core API boundary rules** — who owns what, who queries what, who emits what, what no system may mutate directly, tick-ordering dependencies

### 7a — Revise

```
/scaffold-revise-foundation [--mode initial|recheck]
```

**Initial mode** (first pass): Verifies Steps 1–6 each completed their Create → Review → Iterate pipeline. Reports readiness per doc layer. No revisions needed — nothing has been implemented yet. Proceeds to 7b.

**Recheck mode** (outer loop, after phase completion): Reads implementation feedback (ADRs, KIs, triage logs, playtest patterns, revision logs, code review findings). Identifies which foundation areas drifted and which Step 1–6 docs need updating. Dispatches revision loops (revise → fix → iterate → validate) to affected docs only. After dispatched revisions complete, proceeds to 7b for foundation validation gate.

### 7b — Validate (gate)

```
/scaffold-validate --scope foundation
```

Deterministic checks: foundation area coverage, area status (Locked/Partial/Deferred), authority-architecture consistency, interface completeness, signal consistency, entity consistency, iterate freshness.

If cross-cutting findings are surfaced, run `/scaffold-fix-cross-cutting` to resolve them interactively.

**Gate assessment:**
- **PASS** — all areas are Locked, or Partial with tracked bounded gaps. Safe to proceed into planning.
- **CONDITIONAL** — one or more Partial areas have untracked or weakly bounded gaps. Update `known-issues.md` or docs before proceeding.
- **FAIL** — one or more areas remain Undefined. Do not scale into phases, slices, specs, or tasks until resolved.

### 7c — Fix Cross-Cutting Issues

```
/scaffold-fix-cross-cutting [--category decision-closure|workflow|staleness] [--id XC-###]
```

Reads `scaffold/decisions/cross-cutting-findings.md` (populated by `/scaffold-validate --scope all` Section 2l checks) and dispatches resolution actions per finding category:

- **Decision closure** — resolves untracked TODOs/TBDs in Approved docs. Auto-fills when the answer exists in upstream docs; presents options for genuine open questions (resolve, defer with tracking, or downgrade doc status).
- **Workflow integrity** — dispatches missing pipeline steps (iterate runs, reorder passes, roadmap revisions). Cannot auto-fix — tells you what command to run.
- **Upstream staleness** — classifies upstream changes as no-impact (auto-resolve), minor-impact (auto-edit), or major-impact (dispatch restabilization or file ADR).

Each finding gets exactly one outcome: Resolved, Acknowledged (with reason), or Deferred (with KI/ADR reference). Updated in the findings doc immediately.

Run after `7b — Validate` when cross-cutting findings are reported. Also run during the outer loop (Step 14) after phase completion when validate surfaces new staleness or workflow drift.

---

## Planning

### Step 8 — Roadmap

The roadmap follows the same stabilization pattern as phases. **Loop 1** runs once when the roadmap is first created. **Loop 2** runs after each phase completes (as part of the outer loop). Since the roadmap is a singleton document (not a numbered set), there's no bulk-seed or approve gate — validation and iterate serve as the quality gate before phase seeding.

#### 8a — Create the roadmap

```
/scaffold-new-roadmap
```

Proposes a phase skeleton from design context, maps systems to phases, validates ordering and coverage, then writes `phases/roadmap.md` with 20 sections: vision checkpoint, design pillars, ship definition, capability ladder, phase overview, phase boundaries, system coverage map, phase ordering rationale, and more. Includes demo scenarios, success metrics, and sliceability checks per phase.

#### 8b — Fix mechanical issues

```
/scaffold-fix-roadmap
```

Auto-fixes template text, vague phase goals, vision checkpoint drift, stale ADR log entries, terminology drift, and registration mismatches. Surfaces strategic issues (coverage gaps, over-scoping, ordering conflicts) for human decision.

#### 8c — Adversarial review

```
/scaffold-iterate-roadmap
```

Runs adversarial per-topic review via external LLM across 5 topics (vision coverage & scope alignment, phase sequencing & dependency logic, milestone quality & capability progression, risk distribution & ADR currency, player experience evolution). Produces a Roadmap Strength Rating (1–5).

> `/scaffold-review-roadmap` provides a read-only audit at any time.

#### 8d — Validate

```
/scaffold-validate --scope roadmap
```

Checks roadmap structural integrity: 13 deterministic checks including required sections (13 sections), vision sync, design pillars presence, ship definition, capability ladder sync, phase sync, order integrity, phase boundaries, system coverage map, ADR currency, completed phases, and current phase pointer.

#### Revision loop — After each phase completes

The roadmap goes through the same stabilization loop as the initial pass:

**8e — Revise the roadmap**

```
/scaffold-revise-roadmap P#-### (the just-completed phase)
```

Formalizes the Phase Transition Protocol. Moves the completed phase to Completed Phases with delivery notes, completion date, and implementation friction rating (LOW/MEDIUM/HIGH per rubric). Logs ADR feedback (with dedupe), updates Current Phase to earliest Approved phase (from actual file status), adds Revision History entry, and surfaces roadmap-level observations. Includes Roadmap Confidence signal (Stable/Decreased/Improved). Recommended before `/scaffold-revise-phases` but resilient to either order.

**8f — Fix the revised roadmap**

```
/scaffold-fix-roadmap
```

Auto-fixes any mechanical issues introduced by the revision — stale ADR log entries, capability ladder drift, system coverage gaps, vision checkpoint drift.

**8g — Iterate the revised roadmap**

```
/scaffold-iterate-roadmap
```

Adversarial review on the revised roadmap. Particularly important after phases that produced HIGH friction or Decreased confidence — the roadmap structure may need strategic adjustment.

**8h — Validate the revised roadmap**

```
/scaffold-validate --scope roadmap
```

Structural integrity check after revision. Ensures all 13 checks pass before proceeding to phase revision.

> **Key principle:** The roadmap is a living document. It's revised after every phase completion — not just once at project start. The full loop (revise → fix → iterate → validate) ensures the roadmap stays structurally sound as it evolves. `revise-roadmap` handles the macro view (roadmap document updates), while `revise-phases` (Step 9f) handles the micro view (remaining phase file adjustments).

### Step 9 — Define and manage phases

Phases follow the same pipeline pattern as slices. **Loop 1** runs once when the roadmap is first populated. **Loop 2** runs after each phase completes (as part of the outer loop).

#### Loop 1 — Fresh roadmap (no phases implemented yet)

#### 9a — Seed phases

```
/scaffold-bulk-seed-phases
```

Generates phase scope gate stubs from the roadmap, design doc, system designs, and ADR/KI history. Roadmap goals drive phase selection. Uses temporary labels during confirmation; assigns permanent IDs only after the user confirms. Additive-aware — won't re-generate existing phases.

> To create a single phase interactively: `/scaffold-new-phase [phase-name]`

#### 9b — Fix mechanical issues in phases

```
/scaffold-fix-phase P#-###-P#-###
```

Auto-fixes mechanical issues (template text, vague criteria, broken system references, terminology drift). Surfaces strategic issues (scope too broad, entry/exit chain breaks, ADR contradictions) for human decision.

#### 9c — Iterate phases

```
/scaffold-iterate-phase P#-###-P#-###
```

Runs adversarial per-topic review via external LLM across 4 topics (scope quality & milestone clarity, entry/exit chain & sequencing, system coverage & authority, risk awareness & decision currency).

#### 9d — Validate

```
/scaffold-validate --scope phases
```

Checks phase structural integrity: index sync, roadmap sync, order integrity, status-filename sync, required section structure, entry chain resolution, single-active-phase, system resolution, slice resolution, review freshness (10 checks).

#### 9e — Approve first phase

```
/scaffold-approve-phases P#-###
```

Lifecycle gate that approves exactly one phase — the next in roadmap order. Enforces 9 preconditions: validation passes, no other active phase, correct roadmap order, all entry criteria satisfied, review freshness, no unresolved iterate escalations, no pending ADRs/KIs, content readiness, and slice seeding readiness. The gate never rewrites content — it only reads and judges. Later phases stay Draft.


#### Loop 2 — After each phase completes (repeats for remaining phases)

#### 9f — Revise remaining phases

```
/scaffold-revise-phases P#-### (the just-completed phase)
```

Reads ADRs, known issues, playtest patterns, triage logs, foundation recheck results (advisory), slice review logs, and implementation friction signals from the completed phase. Four-tier classification: safe refinement (direct-apply, no pause), scope widening (confirmation required), milestone weakening (confirmation required), scope invalidation (ADR required). Safe refinements must preserve or strengthen milestone meaning. Direct-apply changes proceed without user pause; only confirmation and ADR items stop for decisions. Volume guardrail: >5 direct-apply changes to a single phase triggers acknowledgement. Approved phases stay Approved — no status regression.

#### 9g — Fix the next phase

```
/scaffold-fix-phase P#-###
```

Auto-fixes mechanical issues in the revised phase before adversarial review.

#### 9h — Iterate the next phase

```
/scaffold-iterate-phase P#-###
```

Adversarial per-topic review on the revised phase.

#### 9i — Validate

```
/scaffold-validate --scope phases
```

Structural integrity check after revision.

#### 9j — Approve next phase

```
/scaffold-approve-phases P#-###
```

Approves the next phase in roadmap order. Repeat Loop 2 (9f–9j) for each remaining phase.

> **Key principle:** Only approve one phase at a time. Each implementation cycle produces feedback that may change remaining phases. The phase stays Approved during implementation — scope refinement happens directly without status regression.

> **Bulk review:** Run `/scaffold-bulk-review-phases` to audit all phases for roadmap alignment, entry/exit chains, scope coverage, and ADR absorption.

### Step 10 — Define and manage slices

Slices have two loops depending on where you are in the phase. **Loop 1** runs once when the phase starts. **Loop 2** runs after each slice completes.

#### Loop 1 — Fresh phase (no slices implemented yet)

#### 10a — Seed slices

```
/scaffold-bulk-seed-slices
```

Generates slice stubs for the phase from phase goals, system designs, and interface contracts. Phase goals drive slice selection. Lifecycle-aware — behaves differently for fresh phases vs phases with existing slices. Filters weak candidates (progress theater, fake verticality, duplicate proof) before presentation. Uses temporary labels during confirmation; assigns permanent IDs only after the user confirms the full candidate set, order, and dependencies. Defines implementation order and `Depends on` declarations — only the first slice will be approved initially.

> To create a single slice interactively: `/scaffold-new-slice [slice-name]`

#### 10b — Fix mechanical issues in the first slice

```
/scaffold-fix-slice SLICE-###
```

Reviews the first slice, auto-fixes mechanical issues (template text, vague done criteria, broken references, stale dependencies, terminology drift), and surfaces strategic issues (goal quality, boundary design, proof value) for human decision.

#### 10c — Iterate the first slice

```
/scaffold-iterate-slice SLICE-###
```

Runs adversarial per-topic review via external LLM across 5 topics (proof quality, boundary design, integration completeness, demo sufficiency, sequencing & transition). Catches blind spots review-slice misses: whether the slice is buying real certainty, whether boundaries are optimal, whether the demo is convincing proof.

> `/scaffold-iterate` also works on slices (general-purpose monolithic review), but `/scaffold-iterate-slice` provides deeper per-topic analysis — recommended for the slice loop.

#### 10d — Validate

```
/scaffold-validate --scope slices
```

Checks slice structural integrity: index sync, phase resolution, status-filename sync, interface references, dependency resolution, dependency order, single-active-slice discipline, and review freshness.

#### 10e — Approve first slice

```
/scaffold-approve-slices SLICE-###
```

Lifecycle gate that approves exactly one slice — the first in implementation order. Enforces 8 preconditions: validation passes, no other active slice, correct implementation order, all declared dependencies Complete, review and iterate logs fresh, no pending upstream actions, phase-scope alignment, and no spec pipeline drift. Later slices stay Draft because implementation feedback may change them.


#### Loop 2 — After each slice completes (repeats for remaining slices)

#### 10f — Revise remaining slices

```
/scaffold-revise-slices SLICE-### (the just-completed slice)
```

Reads ADRs, known issues, triage decision logs, and from the completed slice's implementation. Proposes scope, goal, dependency, and integration changes to remaining Draft slices. Applies confirmed changes. After edits, reconciles `_index.md` order against the dependency graph — if a split or new dependency creates an impossible implementation sequence, proposes a topological reorder.

#### 10g — Fix the next slice

```
/scaffold-fix-slice SLICE-###
```

Auto-fixes mechanical issues in the revised slice before adversarial review.

#### 10h — Iterate the next slice

```
/scaffold-iterate-slice SLICE-###
```

Adversarial per-topic review on the revised slice.

#### 10i — Validate

```
/scaffold-validate --scope slices
```

Structural integrity check after revision — includes dependency resolution, dependency order, single-active-slice, and review freshness.

#### 10j — Approve next slice

```
/scaffold-approve-slices SLICE-###
```

Approves the next slice in implementation order. Repeat Loop 2 (10f–10j) for each remaining slice in the phase.

> **Key principle:** Only approve one slice at a time. Each implementation cycle produces feedback that may change remaining slices. Approving all slices upfront locks in assumptions that haven't been validated.

### Step 11 — Write and stabilize specs

This step uses a multi-pass planning loop to produce behavior-ready specs. The loop mirrors Step 12's task stabilization pattern: mechanical cleanup, adversarial review, human decisions, then approval.

#### 11a — Seed specs

```
/scaffold-bulk-seed-specs
```

Generates spec stubs for all slices from system designs and state transitions. Each spec describes BEHAVIOR, not implementation — no engine constructs.

> To create a single spec interactively: `/scaffold-new-spec [spec-name]`

#### 11b — Fix mechanical issues

```
/scaffold-fix-spec SPEC-###-SPEC-###
```

Reviews all specs, auto-fixes mechanical issues (vague ACs, missing sections, implementation leaks, terminology drift, registration gaps), and surfaces strategic issues for human decision (system scope mismatches, authority violations, state machine conflicts, spec overlaps).

#### 11c — Adversarial review

```
/scaffold-iterate-spec SPEC-###-SPEC-###
```

Runs adversarial per-topic review via external LLM across 6 topics (behavioral correctness, system & authority alignment, slice coverage, cross-system contracts, acceptance criteria quality, edge cases & known issues). Catches blind spots: determinism gaps, actor ambiguity, trigger/sequence issues, authority violations, missing failure paths, unabsorbed ADRs.

> `/scaffold-iterate` also works on specs (general-purpose monolithic review), but `/scaffold-iterate-spec` provides deeper per-topic analysis with back-and-forth discussion — recommended for the stabilization loop.

#### 11d — Triage human-required issues

```
/scaffold-triage-specs SLICE-###
```

Collects all unresolved human-required issues from fix-spec and iterate runs: coverage gaps, spec overlaps, system scope mismatches, authority violations, state machine conflicts. Presents them as a decision checklist: splits, merges, scope changes, new specs, reassignments, deferrals. Applies the user's decisions.

Writes a persistent decision log to `decisions/triage-logs/TRIAGE-SPECS-SLICE-###.md` with Decisions and Upstream Actions sections.

#### 11e — Repeat until stable

Repeat steps 11b–11d until the spec set is stable. **The spec set is stable when all four conditions are met:**

1. **No unresolved human-required issues remain** — the last triage pass produced zero issues, or all issues were resolved/deferred with recorded decisions.
2. **No new specs were created in the last triage pass** — if triage created new specs, they need their own fix-spec and iterate passes.
3. **No merges or splits remain pending** — all triage decisions have been applied.
4. **Two consecutive iterate passes produce no new meaningful issues** — the review loop has converged.

Deferred issues with recorded decisions do **not** block stabilization. Only issues without a decision count as unresolved.

#### 11f — Validate

```
/scaffold-validate --scope specs
```

Runs spec-pipeline validation to catch synchronization drift before approving: spec index integrity, spec-slice membership, system reference resolution, spec status sync, and spec triage log targets. Fix any reported issues.

> **Full validation:** Run `/scaffold-validate` (no scope) to also include reference checks and task-layer checks.

#### 11g — Approve specs

```
/scaffold-approve-specs SLICE-###
```

Marks all Draft specs as Approved. Renames files (`_draft` → `_approved`), updates `specs/_index.md`, and syncs the slice's Specs table. Blocked/deferred specs stay Draft.

This is the gate between spec planning and task seeding — specs must be Approved before tasks are generated from them.

> **Read-only audit:** Run `/scaffold-review-spec SPEC-###` for a single-spec multi-pass audit at any point.
> **Cross-spec audit:** Run `/scaffold-bulk-review-specs` to audit all specs for slice coverage, system coverage, and state machine alignment.

### Step 12 — Write and stabilize tasks

This step uses a multi-pass planning loop to produce implementation-ready tasks. The loop separates mechanical cleanup, adversarial review, and human decisions into distinct passes.

#### 12a — Seed tasks

```
/scaffold-bulk-seed-tasks SLICE-###
```

Creates initial task stubs from the slice's specs, engine docs, and architecture context. Tasks describe HOW to implement spec behavior in the target engine.

> To create a single task interactively: `/scaffold-new-task [task-name]`

#### 12b — Fix mechanical issues

```
/scaffold-fix-task TASK-###-TASK-###
```

Reviews all tasks, auto-fixes mechanical issues (vague objectives, weak verification, missing files, terminology drift, bad step order, missing integration touchpoints), and surfaces strategic issues for human decision.

#### 12c — Adversarial review

```
/scaffold-iterate-task TASK-###-TASK-###
```

Runs adversarial per-topic review via external LLM across 5 topics (spec coverage, architecture compliance, integration correctness, step executability, edge cases & safety). Catches blind spots: hidden assumptions, coverage gaps, architecture interpretation issues, dependency problems, overlooked edge cases.

> `/scaffold-iterate` also works for tasks (it delegates to `/scaffold-iterate-task` internally), but calling the task-specific skill directly is clearer.

#### 12d — Triage human-required issues

```
/scaffold-triage-tasks SLICE-###
```

Collects all unresolved human-required issues from fix-task and iterate runs, plus cross-cutting checks: integration gaps, execution path validation, data ownership violations, state transition coverage, persistence gaps, weak verification, and file overlap conflicts. Presents them as a decision checklist: splits, merges, scope changes, new tasks, spec conflicts, blockers, deferrals, ownership. Applies the user's decisions to task files.

Writes a persistent decision log to `decisions/triage-logs/TRIAGE-SLICE-###.md` with two sections: **Decisions** (task-level changes applied) and **Upstream Actions Required** (non-task doc changes that triage identified but did NOT apply — these must be handled via `/scaffold-update-doc` or ADRs). The triage decision log becomes the authoritative record of planning decisions and upstream changes required before implementation. Both `/scaffold-reorder-tasks` and `/scaffold-approve-tasks` read this log downstream.

#### 12e — Repeat until stable

Repeat steps 12b–12d until the task graph is stable. **The task graph is stable when all four conditions are met:**

1. **No unresolved human-required issues remain** — the last triage pass produced zero issues, or all issues were resolved/deferred with recorded decisions.
2. **No new tasks were created in the last triage pass** — if triage created new tasks, they need their own fix-task and iterate passes before the graph can stabilize.
3. **No merges or splits remain pending** — all triage merge/split decisions have been applied.
4. **Two consecutive iterate-task passes produce no new meaningful issues** — the review loop has converged. Minor wording suggestions don't count; only spec coverage gaps, architecture issues, or dependency problems count as meaningful.

Deferred issues with recorded decisions (noted in task files and tracked in design-debt or blocker logs) do **not** block stabilization. Only issues without a decision count as unresolved.

Do not proceed to validate/reorder until all four conditions hold. Stopping early risks approving an unstable task graph.

#### 12f — Validate the planning graph

```
/scaffold-validate --scope tasks
```

Runs planning-pipeline validation before committing to a final task order. Catches synchronization drift triage may miss: slice-task membership, task index integrity, status-filename sync, slice table status drift, triage log targets, reference file resolution, and slice order integrity. Fix any reported issues before proceeding to reorder.

> **Full validation:** Run `/scaffold-validate` (no scope) to also include reference checks — system IDs, authority, signals, interfaces, glossary. Recommended after major triage churn or when reference docs may have drifted.

#### 12g — Reorder tasks

```
/scaffold-reorder-tasks SLICE-###
```

Discovers the actual task set from task files (not the existing slice table), builds a dependency graph, detects circular dependencies, missing prerequisites, and ambiguous file overlaps, and proposes an optimal implementation order. Regenerates the slice's Tasks table from scratch and syncs `tasks/_index.md`. Also checks the triage decision log for any pending upstream actions and surfaces them in the report.

Run this only after the task graph has stabilized and validation is clean — reordering before stabilization is wasted effort.

#### 12h — Approve tasks

```
/scaffold-approve-tasks SLICE-###
```

Marks all Draft tasks as Approved after reorder confirms the task graph is clean. Renames files (`_draft` → `_approved`), updates `tasks/_index.md`, and syncs the slice's Tasks table status column. Blocked/deferred tasks stay Draft.

This is the final gate before implementation — tasks must have passed through fix-task, iterate, triage, and reorder to reach this point.

> **Read-only audit:** Run `/scaffold-review-task [TASK-###]` for a single-task read-only review at any point.
> **Cross-task audit:** Run `/scaffold-bulk-review-tasks` to audit all tasks for spec coverage, engine consistency, and file conflicts.

---

## Building

### Step 13 — Implement tasks

```
/scaffold-implement-task TASK-### [--CRI N]
```

Runs the full implementation pipeline for a single task or a range (`TASK-###-TASK-###`):

1. **Read** — task, spec, system design, architecture, engine docs, ADRs, existing code
2. **Plan** — output a brief implementation plan for review
3. **Implement** — write the code following the task's Steps section
4. **Add tests** — regression tests via `/scaffold-add-regression-tests`
5. **Build and test** — verification gate via `/scaffold-build-and-test`
6. **Code review** — adversarial review via `/scaffold-code-review` (file-scope per changed file, optional system-scope coherence pass). `--CRI N` sets max review iterations (default: 10, stops early when stable).
7. **Rebuild and retest** — if code review applied changes, re-verify
8. **Sync docs** — update reference and architecture docs via `/scaffold-sync-reference-docs`
9. **Complete** — mark task done and ripple upward via `/scaffold-complete`

The pipeline stops on failure — build errors, test failures, or unresolvable review issues must be fixed before proceeding. For ranges, later tasks are skipped if an earlier task fails (they may depend on it).

> **ADRs during implementation:** When a conflict or ambiguity arises during implementation, create `decisions/ADR-###.md` using `templates/decision-template.md`. ADRs are permanent records that feed back into upcoming phases, specs, and tasks. This happens naturally during implementation — it's not a separate step.

> **Asset review:** If art or audio assets have been generated, run `/scaffold-review-art` and
> `/scaffold-review-audio` to audit visual consistency, prompt quality, and coverage gaps.

### Step 14 — Repeat (the two-loop cycle)

**Inner loop — within a phase:**

1. Implement tasks (Step 13) until the current slice is complete.
2. Run `/scaffold-revise-slices` (Step 10f) to update remaining Draft slices from implementation feedback.
3. Fix, iterate, validate, and approve the next slice (Steps 10g–10j).
4. Seed specs and tasks for the newly approved slice (Steps 11–12).
5. Return to step 1. Repeat for each slice in the phase.

**Outer loop — between phases (Phase Transition Protocol):**

After all slices in a phase are complete:

6. **Run the foundation architecture pipeline (Step 7a–7b in recheck mode):** `/scaffold-revise-foundation --mode recheck` detects drift and dispatches doc revisions — including `/scaffold-revise-design` (Step 1 drift), `/scaffold-revise-systems` (Step 2 drift), `/scaffold-revise-references` (Step 3 drift), `/scaffold-revise-engine` (Step 4 drift), `/scaffold-revise-style` (Step 5 drift), and `/scaffold-revise-input` (Step 6 drift). Then `validate --scope foundation` gates, and `fix-cross-cutting` resolves any cross-cutting findings. If revise-design was dispatched, re-run the Step 1 stabilization loop. If revise-engine was dispatched, re-run: fix-engine → iterate-engine → validate --scope engine. If revise-style was dispatched, re-run: fix-style → iterate-style → validate --scope style. If revise-input was dispatched, re-run: fix-input → iterate-input → validate --scope input. If no drift, proceeds directly.
7. **Revise the roadmap (Steps 8e–8h):** revise-roadmap → fix-roadmap → iterate-roadmap → validate --scope roadmap. Full stabilization loop on the revised roadmap before phase revision, so remaining phases are adjusted against the latest roadmap state rather than a stale macro plan.
8. **Revise remaining phases:** `/scaffold-revise-phases P#-###` (Step 9f) — reads ADRs, KIs, playtest patterns, triage logs, foundation recheck results, slice review logs, implementation friction signals. Four-tier classification with direct-apply path. Approved phases stay Approved.
9. Fix, iterate, validate, and approve the next phase (Steps 9g–9j).
10. Seed slices for the newly approved phase (Step 10) and return to the inner loop.

The outer loop is a stability check. Most cycles pass through quickly — it only triggers real work when implementation reveals a foundational contradiction.


---

## Skill Reference

### Step 1 — Design

| Skill | What | Why | How |
|-------|------|-----|-----|
| `init-design` | Create/update design doc | Highest-authority document — everything flows from it | Ingests canon, classifies sections, pre-fills from existing docs, interviews for gaps. 4 modes: seed, fill-gaps, reconcile, refresh |
| `fix-design` | Mechanical cleanup | Normalize structure before adversarial review | Auto-fixes template text, governance formats, terminology. Surfaces contradictions/drift for human decision |
| `iterate-design` | Adversarial review | Catch coherence issues self-review misses | 6 topics — 5 structural (vision, experience, world, governance, scope) + 1 design interrogation (stress test). Design Identity Check + Design Choice Examination. External LLM reviewer |
| `validate --scope design` | Structural gate | Confirm doc is ready to govern downstream work | 13 deterministic checks: structure, health, governance format, glossary, ADR consistency |
| `revise-design` | Post-implementation drift | Keep design doc matching accepted project reality | Reads ADRs/KIs/playtest/friction. Classifies design-led vs implementation-led. Auto-updates safe changes, escalates governance |

### Step 2 — Systems

| Skill | What | Why | How |
|-------|------|-----|-----|
| `bulk-seed-systems` | Propose and create system stubs | Define simulation layer from design intent | Proposes systems by ownership (not verbs). 9 category coverage audit, overlap/gap/invariant checks. Batch confirmation |
| `new-system` | Create a single system | Add a system after initial seeding | Overlap/authority/invariant audit for one system. Supports `--split-from` (split context) and `--trigger` (ADR/KI context). Pre-fills from parent or trigger |
| `fix-systems` | Mechanical cleanup | Normalize before adversarial review | Formatter + linter. Auto-fixes structure/terminology/registration. Detects design signals for iterate-systems. All loops parallel |
| `iterate-systems` | Adversarial review | Challenge system design quality | 5 topics (ownership, behavior, governance, cross-system, fitness) + System Identity Check + Reviewer Bias Pack. External LLM |
| `validate --scope systems` | Structural gate | Confirm systems are structurally ready | 16 deterministic checks: index sync, structure, health, owned-state overlap, dependency cycles, template drift |
| `revise-systems` | Post-implementation drift | Keep system docs matching accepted reality | 9 architectural drift detections. Classifies design-led vs implementation-led. Suppresses patching when identity unstable |

### Step 3 — References + Architecture

| Skill | What | Why | How |
|-------|------|-----|-----|
| `bulk-seed-references` | Create all Step 3 docs (9 docs) | Surface cross-cutting assumptions for Step 7 | 10-phase pipeline: architecture (scene tree, dependencies, tick order, update semantics, identity model, data flow rules, forbidden patterns, code patterns) → authority → interfaces → state transitions → entity components (with identity semantics) → resources → signals (with event taxonomy + Level column) → balance params → enums/statuses → report. Creates from templates if docs don't exist. Flags identity model decisions for Step 7 |
| `fix-references` | Mechanical cleanup (Step 3) | Normalize before adversarial review | Per-doc checks (section structure, columns, terminology) + cross-doc consistency (authority↔entities, interfaces↔signals, states↔enums). Supports `--target doc.md` for single-doc focus |
| `iterate-references` | Adversarial review (Step 3) | Challenge reference doc quality | 6 topics (architecture coherence, ownership model, contract quality, data model fitness, cross-doc consistency, simulation readiness) + Reviewer Bias Pack (8 patterns). Supports `--target` and `--topics` |
| `revise-references` | Post-implementation drift | Keep reference docs matching accepted reality | Reads ADRs/KIs/system doc changes/spec friction/code review. Classifies design-led vs implementation-led. Auto-updates safe changes, escalates authority/architecture/contract/state changes. Supports `--target` and `--signals` |
| `validate --scope refs` | Structural gate | Cross-reference + Step 3 doc integrity | Python script (9 checks: system IDs, authority, signals, interfaces, states, glossary, bidirectional) + expanded checks (doc existence, section structure, column completeness, value validity, cross-doc consistency, duplicates, production chains) |

### Step 4 — Engine

| Skill | What | Why | How |
|-------|------|-----|-----|
| `bulk-seed-engine` | Create engine docs (15 total) | Lock technical foundations before visual/UX | One-pass seed of 15 docs from templates. Auto-detects engine + implementation stack. Confidence-tiered: Strong/Constrained TODO/Open TODO based on Step 3 maturity. No per-doc confirmation. Create-missing-only by default. |
| `fix-engine` | Mechanical cleanup (Step 4) | Normalize before adversarial review | Per-doc checks (section structure, terminology, constrained TODO currency) + alignment signals (architecture contradictions, authority assumptions, timing mismatches, layer breaches). Cross-doc consistency pass. Supports `--target` |
| `iterate-engine` | Adversarial review (Step 4) | Catch Step 3 violations, convention gaps, cross-engine inconsistencies | 6 topics via external LLM. Scope collapse guard, ambiguous upstream handling, review consistency lock, practicality check. Supports `--target` and `--topics` |
| `validate --scope engine` | Structural gate (Step 4) | Deterministic engine doc validation | 28 checks: index, headers, structure, health, Step 3 alignment, cross-engine consistency, layer boundary, template drift, review freshness. Heuristic checks labeled [ADVISORY] |
| `revise-engine` | Post-implementation drift (Step 4) | Keep engine docs matching accepted reality | Signal-driven. Reads ADRs/KIs/Step 3 changes/code review/task friction. Auto-updates safe changes, escalates conventions with CRITICAL/HIGH/MEDIUM priority. Repeated divergence escalation, duplicate pattern guard, partial Step 3 suppression. Supports `--target` and `--signals` |

### Step 5 — Visual & UX

| Skill | What | Why | How |
|-------|------|-----|-----|
| `bulk-seed-style` | Create style/UX docs (6 total) | Define visual language, interaction, feedback, audio | Seeds 6 docs in order: style-guide → color-system → ui-kit → interaction-model → feedback-system → audio-direction. Auto-writes high-confidence, tags medium in changelog, leaves low as TODO. Design doc and system designs are primary sources; architecture/reference/engine are secondary constraints. Pauses only on ambiguous or high-impact decisions. Reports confidence, assumptions, and cross-doc tensions. |
| `revise-style` | Post-implementation drift (Step 5) | Keep style docs matching accepted reality | Signal-driven. Reads ADRs/KIs/playtest patterns/design doc changes/system changes/Step 3 changes/code review/task friction. Auto-updates safe changes (tokens, entries, alignment), escalates aesthetic/interaction/accessibility with CRITICAL/HIGH/MEDIUM priority. Playtest patterns rank above individual specs. Follows Step 5 authority flow. Supports `--target` and `--signals` |

### Step 6 — Input

| Skill | What | Why | How |
|-------|------|-----|-----|
| `bulk-seed-input` | Create input docs | Map interaction primitives to hardware | Seeds action-map, bindings, navigation, philosophy from design doc + interaction model + engine input docs |
| `fix-input` | Mechanical cleanup | Normalize before adversarial review | Auto-fixes ID conventions, binding collisions, orphan bindings, terminology. Detects missing verbs, namespace confusion, action bloat, philosophy-interaction mismatches. Supports `--target` |
| `iterate-input` | Adversarial review | Challenge input design quality | 6 topics (action traceability, philosophy coherence, binding fitness, navigation completeness, cross-doc, readiness) + mandatory end-to-end + device parity tests. External LLM. Supports `--target` and `--topics` |
| `validate --scope input` | Structural gate | Confirm input docs are structurally ready | Action ID conventions, traceability (Source column), binding coverage/collisions, navigation completeness, upstream alignment, philosophy compliance, device parity, review freshness |
| `revise-input` | Post-implementation drift | Keep input docs matching accepted reality | Reads ADRs/KIs/interaction-model changes/spec friction/code review. Design-led vs implementation-led classification. Auto-updates safe changes, escalates philosophy/navigation/parity/accessibility |

### Step 7 — Foundation Architecture

| Skill | What | Why | How |
|-------|------|-----|-----|
| `revise-foundation` | Orchestrate foundation revisions | Dispatch to affected Step 1-6 skills | Initial: readiness check. Recheck: reads feedback, dispatches revision loops (revise-design, revise-systems, revise-references, revise-engine, revise-style) with --signals. Explicit skill-by-skill dispatch |
| `validate --scope foundation` | Foundation gate | Verify cross-doc consistency | 8 checks: docs exist, area coverage, area status, authority consistency, interface completeness, signals, entities, freshness |
| `fix-cross-cutting` | Resolve cross-cutting findings | Fix decision closure, workflow, staleness issues | Reads cross-cutting-findings.md. Auto-fixes safe items, dispatches missing pipeline steps, escalates judgment calls. Supports `--category` and `--id` |
| `validate --scope all` | Full validation including cross-cutting | Everything plus decision closure, workflow integrity, staleness | Runs all scope checks + Section 2l cross-cutting checks. Writes findings to cross-cutting-findings.md |

### Steps 8-9 — Roadmap + Phases

| Skill | What | Why | How |
|-------|------|-----|-----|
| `new-roadmap` | Create the roadmap | Define phases from start to ship | Proposes skeleton, maps systems, validates ordering, writes capability ladder |
| `fix-roadmap` | Mechanical cleanup | Normalize roadmap structure | Auto-fixes vague goals, vision drift, stale ADR log, terminology |
| `iterate-roadmap` | Adversarial review | Stress-test the roadmap | 5 topics (vision coverage, sequencing, milestones, risk, player experience). Roadmap Strength Rating |
| `revise-roadmap` | Post-phase update | Keep roadmap current | Moves phase to Completed, updates Current Phase, logs ADRs, surfaces roadmap-level changes |
| `bulk-seed-phases` | Create phase stubs | Define scope gates from roadmap | Seeds from roadmap goals + design doc + systems + ADRs |
| `new-phase` | Create one phase | Individual phase with ADR context | Reads ADRs from prior phases to inform scope |
| `fix-phase` | Mechanical cleanup | Normalize phases | Auto-fixes template text, vague criteria, broken references |
| `iterate-phase` | Adversarial review | Stress-test phases | 4 topics (scope, entry/exit, systems, risk). Phase Strength Rating |
| `approve-phases` | Lifecycle gate | Approve for slice seeding | 9 preconditions: validation, single-active, ordering, entry criteria, freshness |
| `revise-phases` | Post-implementation update | Adjust remaining phases | 4-tier classification, milestone weakening detection, friction signals |
| `validate --scope phases` | Phase gate | Phase structural integrity | 10 checks: index, roadmap sync, status, structure, entry chain, review freshness |
| `validate --scope roadmap` | Roadmap gate | Roadmap structural integrity | 13 checks: structure, vision sync, capability ladder, phase sync, system coverage |

### Steps 10-12 — Slices, Specs, Tasks

| Skill | What | Why | How |
|-------|------|-----|-----|
| `bulk-seed-slices` | Create slice stubs | Define vertical proof chunks | Lifecycle-aware seeding from phases + systems + interfaces |
| `new-slice` | Create one slice | Individual vertical slice | End-to-end playable chunk that proves something works |
| `fix-slice` | Mechanical cleanup | Normalize slices | Auto-fixes template text, vague criteria, broken refs, stale dependencies |
| `iterate-slice` | Adversarial review | Stress-test slices | 5 topics (proof, boundaries, integration, demo, sequencing) |
| `approve-slices` | Lifecycle gate | Approve for spec seeding | 8 preconditions: order, dependencies, freshness, single-active |
| `revise-slices` | Post-implementation update | Adjust remaining slices | Reads ADRs/KIs/triage/friction, reconciles dependency graph |
| `validate --scope slices` | Slice gate | Slice structural integrity | Index, phase resolution, status, dependencies, single-active, review freshness |
| `bulk-seed-specs` | Create spec stubs | Define atomic behaviors from slices | Slice-driven. Authority trace, behavior path completeness, ADR/KI impact. Overlap handling |
| `new-spec` | Create one spec | Individual behavior spec | Reads system designs and ADRs for testable behavior |
| `fix-spec` | Mechanical cleanup | Normalize specs | Auto-fixes vague ACs, missing sections, terminology, system misalignment |
| `iterate-spec` | Adversarial review | Stress-test specs | 6 topics (behavior, systems, slices, contracts, ACs, edge cases) |
| `triage-specs` | Human decisions | Resolve spec issues | Walks through merge/split/reassign/defer decisions. Writes decision log |
| `approve-specs` | Lifecycle gate | Approve for task seeding | Marks Draft specs as Approved after stabilization converges |
| `validate --scope specs` | Spec gate | Spec structural integrity | Index, slice membership, system resolution, status sync, triage targets |
| `bulk-seed-tasks` | Create task stubs | Define implementation steps | Seeds from specs + engine/architecture/reference context |
| `new-task` | Create one task | Individual implementation task | Reads engine docs and ADRs for concrete steps |
| `fix-task` | Mechanical cleanup | Normalize tasks | Auto-fixes vague objectives, missing files, terminology |
| `iterate-task` | Adversarial review | Stress-test tasks | 5 topics (spec coverage, architecture, integration, executability, edge cases) |
| `triage-tasks` | Human decisions | Resolve task issues | Creates new tasks, applies scope changes, records deferrals |
| `reorder-tasks` | Dependency ordering | Optimal implementation order | Builds dependency graph, regenerates slice table |
| `approve-tasks` | Lifecycle gate | Approve for implementation | Marks Draft tasks as Approved after reorder confirms clean graph |
| `validate --scope tasks` | Task gate | Task structural integrity | Index, slice membership, status sync, order integrity, reference resolution |

### Step 13 — Implementation

| Skill | What | Why | How |
|-------|------|-----|-----|
| `implement-task` | Build it | End-to-end task execution | Code → tests → build → code review → doc sync → mark complete |
| `add-regression-tests` | Test coverage | Ensure implementation correctness | Adds tests to regression harness from implementation files |
| `build-and-test` | Verification gate | Confirm build + tests pass | Build, lint, regression, GUT suite |
| `code-review` | Code quality | Adversarial review of code | 7 topics via external LLM. File-scope (pipeline) or system-scope (manual) |
| `sync-reference-docs` | Doc sync | Keep docs matching code | Updates reference/architecture docs from implemented code |
| `complete` | Lifecycle transition | Mark work done | Marks task/spec/slice/phase Complete. Ripples up through parents |

### Utility

| Skill | What | Why | How |
|-------|------|-----|-----|
| `update-doc` | General editor | Add/remove/modify any scaffold doc | Updates cross-references and indexes automatically |
| `sync-glossary` | Glossary maintenance | Keep glossary current with project vocabulary | Scans structured doc fields for unregistered domain terms. Use after any bulk-seed step or when validate flags glossary gaps |
| `validate --scope all` | Full validation | Everything at once | Runs all scope checks: design, systems, foundation, roadmap, phases, slices, specs, tasks, refs, engine + cross-cutting integrity (decision closure, workflow, staleness). Writes findings to cross-cutting-findings.md |
| `fix-cross-cutting` | Resolve cross-cutting findings | Fix decision closure, workflow, staleness | Reads cross-cutting-findings.md. Auto-fixes safe items, dispatches missing pipeline steps, escalates judgment calls |
| `playtest-log` | Capture feedback | Record playtester observations | Detects duplicates, promotes patterns at 3+ reports |
| `playtest-review` | Analyze feedback | Review playtest patterns | Severity x frequency grid, cross-reference checks, delight inventory |

### Art & Audio Generation

| Skill | What |
|-------|------|
| `art-concept`, `art-character`, `art-environment`, `art-icon`, `art-promo`, `art-sprite`, `art-ui-mockup` | Generate visual assets informed by style guide and color system |
| `audio-music`, `audio-sfx`, `audio-ambience`, `audio-voice` | Generate audio assets informed by style guide and design doc |

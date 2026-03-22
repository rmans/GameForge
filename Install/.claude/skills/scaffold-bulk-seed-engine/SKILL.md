---
name: scaffold-bulk-seed-engine
description: Determine engine and implementation stack, then seed all 15 engine docs from templates in one pass. Reads Step 1-3 outputs to align engine constraints with the simulation layer. Confidence-tiered pre-fill based on Step 3 maturity. No per-doc confirmation.
argument-hint: [--engine godot4|unity|unreal5|other] [--stack "..."] [--mode create-missing|overwrite-all|overwrite-specific] [--docs "doc1,doc2"]
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Seed Engine Documents

Determine the engine and implementation stack, then create all engine docs from templates in one pass: **$ARGUMENTS**

Step 4 runs after core Step 3 architecture and reference decisions are defined well enough to constrain engine implementation. Engine docs lock the implementation-side technical foundations that Visual/UX and Input design decisions must eventually map onto. This skill seeds everything at once — review and refinement happen in fix-engine and iterate-engine, not here.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--engine` | No | auto-detect | Engine: `godot4`, `unity`, `unreal5`, or user-provided prefix. If omitted, infer from existing engine docs or project files. |
| `--stack` | No | auto-detect | Implementation stack within the engine (e.g., `gdscript+cpp`, `csharp+dots`). If omitted, infer from existing code or ask. |
| `--platforms` | No | `default` | Non-default platform targets that affect engine docs now. |
| `--mode` | No | `create-missing` | `create-missing` (default — only seed docs that don't exist), `overwrite-all` (replace everything), `overwrite-specific` (replace only docs listed in `--docs`). |
| `--docs` | No | all | Comma-separated list of doc stems to create/overwrite. Only used with `--mode overwrite-specific`. Valid stems: `coding-best-practices`, `ui-best-practices`, `input-system`, `scene-architecture`, `performance-budget`, `simulation-runtime`, `save-load-architecture`, `ai-task-execution`, `data-and-content-pipeline`, `localization`, `post-processing`, `implementation-patterns`, `asset-import-pipeline`, `debugging-and-observability`, `build-and-test-workflow`. |

## Preconditions

1. **design-doc.md exists** — needed for vision, platforms, simulation depth context.
2. **architecture.md exists with authored content** — these specific sections must exist and contain authored content beyond template placeholders: Scene Tree Layout, Simulation Update Semantics, Data Flow Rules, and Entity Identity & References. If missing or if these sections are still placeholder, stop: "Architecture doc not ready. Complete Step 3 first." Note: "authored content" means the sections exist with real decisions — sub-decisions within those sections may still be TBD, which is handled by the maturity check (precondition 4), not this gate.
3. **Core reference docs exist with substantive content** — all 4 must exist with at least non-template structural content: `design/authority.md`, `design/interfaces.md`, `reference/entity-components.md`, and `reference/signal-registry.md`. If any are missing or entirely template-default, stop: "Reference docs not ready. Complete Step 3 first."
4. **Step 3 maturity check** — check these specific architecture hotspots. If any are marked TBD or still placeholder, seed the corresponding engine sections as Constrained TODOs rather than strong pre-fill:
   - Simulation Update Semantics (timing model)
   - Entity Identity / Handle Model
   - Save/Load Reconstruction Policy
   - Task Reservation Ownership
   - Signal Dispatch Timing
   - Boot/Init Order
   - Task Reservation Writer Ownership (if authority.md has unresolved task/reservation ownership, suppress strong pre-fill in ai-task-execution, save-load-architecture, and reservation-related sections of simulation-runtime)
   - Interface Timing / Realization Path (if interfaces.md has unresolved Timing or Realization Path for major simulation contracts, suppress strong pre-fill in simulation-runtime, ai-task-execution, and event-tracing sections of debugging-and-observability). Major simulation contracts include: task assignment/execution, reservation/claims/locks, state transitions affecting actor behavior, persistence/save-load interactions, and any contract referenced by architecture timing rules.

## Phase 1 — Determine Engine Stack

**Attempt auto-detection first.** Check these sources in order:
1. `--engine` and `--stack` arguments (if provided, use them directly)
2. Existing engine docs in `scaffold/engine/` (infer prefix and stack from filenames and content)
3. Project files (e.g., `project.godot`, `*.csproj`, `*.uproject`)
4. design-doc.md Target Platforms or engine references
5. CLAUDE.md or README.md engine mentions

**Only ask the user for values that cannot be inferred confidently.** If engine and stack are clear from project context, proceed without asking.

**Confidence thresholds for auto-detection:**
- `project.godot` present → engine is confidently Godot
- `.uproject` present → engine is confidently Unreal
- `.csproj` alone → NOT confident (could be Unity, general C#, or Godot C#) — ask
- Existing engine docs with consistent prefix + stack references → confident for both engine and stack
- README/CLAUDE.md mention only → confident if corroborated by project files, otherwise ask

If asking is needed, collect:
- **Engine:** Godot 4 / Unity / Unreal Engine 5 / other
- **Implementation stack:** e.g., GDScript + C++ GDExtension, C# MonoBehaviour, C++ + Blueprints
- **Platform targets** (if non-default)

The implementation stack materially changes: coding-best-practices, performance-budget, simulation-runtime, save-load-architecture, and ai-task-execution.

## Phase 2 — Check Existing Docs

1. Glob `scaffold/engine/*` to see what already exists.
2. Apply `--mode`:
   - **create-missing** (default): skip existing docs, create only what's missing.
   - **overwrite-specific**: overwrite only docs listed in `--docs`, create any other missing docs. If a listed doc does not exist, create it. If any `--docs` entry does not match a known engine doc filename stem, stop and report invalid doc names.
   - **overwrite-all**: replace everything.

## Phase 3 — Read Context

Read these docs to inform engine-specific pre-fill. Skip any that don't exist.

| Context Source | What it informs |
|---------------|-----------------|
| `design/design-doc.md` | Target platforms, input feel, camera, simulation depth |
| `design/architecture.md` | Scene tree, dependency graph, tick order, simulation update semantics, identity model, data flow rules, boot order, forbidden patterns |
| `design/authority.md` | Ownership model, persistence responsibilities |
| `design/interfaces.md` | Cross-system contracts, realization paths, timing |
| `design/state-transitions.md` | State machine timing |
| `reference/entity-components.md` | Entity data shapes, handle conventions, persistence model |
| `reference/signal-registry.md` | Signal dispatch timing, delivery expectations |
| `reference/enums-and-statuses.md` | Shared state vocabulary for coding conventions |
| `reference/resource-definitions.md` | Resource data shapes for content pipeline engine doc |
| `design/style-guide.md` | Visual style, rendering approach |
| `design/color-system.md` | Color semantics for UI and post-processing engine docs |
| `design/feedback-system.md` | Feedback coordination for UI and post-processing engine docs |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| `design/ui-kit.md` | UI patterns, panel architecture |
| `design/interaction-model.md` | Player interaction patterns for input-system engine doc |
| `design/systems/_index.md` + system files | System set, owned state, dependencies — especially TaskSystem, WorkAI |

## Phase 4 — Seed All Docs (one pass)

Create all docs from templates in a single pass. No stopping for confirmation. The fix-engine / iterate-engine pipeline handles review.

### Confidence tiers

| Tier | When | Action |
|------|------|--------|
| **Strong** | Engine conventions are well-known AND Step 3 docs support the decision | Pre-fill with concrete content |
| **Constrained TODO** | Step 3 decision exists but is marked TBD, or engine convention depends on unresolved architecture | Seed heading + `<!-- Constrained: depends on [architecture decision X] -->` + `*TODO: Resolve after Step 3 locks [X]*` |
| **Open TODO** | No Step 3 context and no strong engine convention | Seed heading + `*TODO: Define [topic]*` |

**Rule:** If a simulation rule, save/load behavior, reservation lifecycle, or timing guarantee is not established by Step 1-3, do not invent a concrete engine-level rule just to make the doc look complete. Use Constrained TODO. Fake certainty in engine docs is dangerous.

### 4a. Engine-general docs (5 from templates)

| Template | Output | Confidence |
|----------|--------|------------|
| `engine-coding-template.md` | `[prefix]-coding-best-practices.md` | Strong |
| `engine-ui-template.md` | `[prefix]-ui-best-practices.md` | Strong |
| `engine-input-template.md` | `[prefix]-input-system.md` | Strong |
| `engine-scene-architecture-template.md` | `[prefix]-scene-architecture.md` | Strong for structure, Constrained TODO for simulation-specific patterns |
| `engine-performance-template.md` | `[prefix]-performance-budget.md` | Strong for targets, Constrained TODO for per-system budgets |

### 4b. Simulation-specific docs (4 from templates)

These depend heavily on Step 3 maturity. Pre-fill aggressively only where Step 3 decisions are locked.

| Template | Output | Confidence |
|----------|--------|------------|
| `engine-simulation-runtime-template.md` | `[prefix]-simulation-runtime.md` | Strong if architecture.md Simulation Update Semantics is populated. Constrained TODO if timing is TBD. |
| `engine-save-load-template.md` | `[prefix]-save-load-architecture.md` | Strong if identity model and Persistence column populated. Constrained TODO otherwise. |
| `engine-ai-task-execution-template.md` | `[prefix]-ai-task-execution.md` | Strong if TaskSystem/WorkAI designs populated and authority covers task ownership. Constrained TODO otherwise. |
| `engine-data-content-pipeline-template.md` | `[prefix]-data-and-content-pipeline.md` | Strong if Content Identity Convention populated. Constrained TODO otherwise. |

### 4c. Cross-cutting docs (3 from templates)

| Template | Output | Confidence |
|----------|--------|------------|
| `engine-localization-template.md` | `[prefix]-localization.md` | Strong for engine patterns, Open TODO for project-specific conventions |
| `engine-post-processing-template.md` | `[prefix]-post-processing.md` | Open TODO unless style-guide has rendering direction |
| `engine-implementation-patterns-template.md` | `implementation-patterns.md` | Structure only — seed pattern template with 2-3 empty entry shells. Never pre-fill patterns. Empty shells do not count as "strongly pre-filled" in reporting. |

### 4d. Asset pipeline (1 from template)

| Template | Output | Confidence |
|----------|--------|------------|
| `engine-asset-import-pipeline-template.md` | `[prefix]-asset-import-pipeline.md` | Strong for engine import conventions, Open TODO for project-specific presets and data table formats |

### 4e. Debugging and testing docs (2 from templates)

| Template | Output | Confidence |
|----------|--------|------------|
| `engine-debugging-template.md` | `[prefix]-debugging-and-observability.md` | Strong for engine tools, Constrained TODO for sim-specific instrumentation |
| `engine-build-test-template.md` | `[prefix]-build-and-test-workflow.md` | Strong for engine build patterns, Open TODO for CI/headless/perf tests |

### Pre-fill sources per doc

| Doc | Primary pre-fill sources |
|-----|------------------------|
| coding-best-practices | Engine conventions + implementation stack |
| ui-best-practices | Engine UI framework + style-guide + ui-kit |
| input-system | Engine input framework + interaction-model (if exists) |
| scene-architecture | Engine scene patterns + architecture.md scene tree + systems/_index.md |
| performance-budget | Engine profiling tools + implementation stack |
| simulation-runtime | architecture.md tick order + simulation update semantics + system designs |
| save-load-architecture | architecture.md identity model + entity-components Persistence column |
| ai-task-execution | System designs for TaskSystem/WorkAI + authority.md task ownership |
| data-and-content-pipeline | architecture.md Content Identity Convention |
| localization | Engine localization framework |
| post-processing | Engine rendering pipeline + style-guide rendering approach |
| implementation-patterns | None — structure only |
| asset-import-pipeline | Engine import system + style-guide (visual conventions) + data-and-content-pipeline (data table format) |
| debugging-and-observability | Engine debug tools + architecture.md (what needs to be observable) + system designs |
| build-and-test-workflow | Engine build system + implementation stack |

For each doc:
1. Read the template from `scaffold/templates/`.
2. Replace `[Engine]` with the actual engine name.
3. Pre-fill sections at the appropriate confidence tier.
4. Write the file to `scaffold/engine/`.

## Phase 5 — Update Engine Index

Update `scaffold/engine/_index.md` to list all created docs with correct prefix and descriptions. If `_index.md` does not exist, create it following the scaffold engine index convention.

## Phase 6 — Report

```
## Engine Docs Seeded

### Configuration
| Field | Value |
|-------|-------|
| Engine | [selected engine] |
| Implementation stack | [stack choice] |
| Platform targets | [targets or "default"] |
| Prefix | [prefix] |
| Mode | [create-missing / overwrite-all / overwrite-specific] |
| Docs created | N |
| Docs skipped (existing) | N |
| Docs overwritten | N |
| Sections strongly pre-filled | N |
| Sections constrained TODO | N |
| Sections open TODO | N |

### Per-Doc Summary
| Doc | Status | Strong | Constrained | Open TODO |
|-----|--------|--------|-------------|-----------|
| coding-best-practices | Created / Skipped / Overwritten | N | N | N |
| ui-best-practices | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

### Architecture Alignment
| Architecture Decision | Engine Doc | Section | Confidence |
|----------------------|-----------|---------|------------|
| Identity model (handles) | simulation-runtime, save-load, coding | Handle implementation, rebind, SlotPool | Strong / Constrained TODO |
| Tick/update semantics | simulation-runtime | Tick orchestration, fixed/variable | Strong / Constrained TODO |
| Signal dispatch timing | simulation-runtime, coding | Dispatch implementation | Strong / Constrained TODO |
| Save/load serialization | save-load | All sections | Strong / Constrained TODO |
| Task/reservation lifecycle | ai-task-execution | All sections | Strong / Constrained TODO |
| Content/runtime boundary | data-content-pipeline | ID mapping, loading | Strong / Constrained TODO |
| UI rendering approach | ui-best-practices | Rendering rules | Strong / Constrained TODO |
| Scene composition | scene-architecture | Tree layout, lifecycle | Strong / Constrained TODO |
| Boot/init order | scene-architecture, simulation-runtime | Init sequence | Strong / Constrained TODO |

### Constrained TODOs (blocked on Step 3)
| Doc | Section | Waiting on |
|-----|---------|-----------|
| simulation-runtime | Fixed vs variable step | architecture.md Simulation Update Semantics is TBD |
| ... | ... | ... |

### Next Steps
- Fill in Open TODOs with project-specific decisions
- Resolve Constrained TODOs after Step 3 locks the blocking decisions
- Run `/scaffold-fix-engine` (when available) to normalize structure
- Run `/scaffold-iterate engine` (when available) for adversarial review
```

## Rules

- **Strong-confidence sections must contain substantive content, not template placeholders.** When the confidence tier is Strong, write real authored prose for every section in the engine template — do not leave as TODO, HTML comment prompts, or single generic sentences. Remove template HTML comments from Strong sections and replace with the authored content. Each engine template defines its own sections (Purpose, Conventions, Patterns, Rules, etc.) — every section that receives Strong-confidence content must have at least 2-3 sentences of specific, project-relevant prose. Constrained TODO and Open TODO sections retain their markers by design, but Strong sections must be fully authored. An engine doc where a Strong section is still at template defaults has failed the seed. When writing Strong sections, reference the actual engine, stack, and project conventions detected during auto-detection — do not write generic boilerplate that could apply to any project.
- **Seed everything in one pass.** No per-doc confirmation. The fix/iterate pipeline handles review.
- **Auto-detect before asking.** Infer engine, stack, and platform from project context. Only ask for values that cannot be confidently determined.
- **Default to create-missing.** Never overwrite existing docs unless explicitly requested via `--mode`.
- **Respect confidence tiers.** Strong pre-fill only when both engine conventions and Step 3 context support it. Constrained TODO when Step 3 is TBD. Open TODO when no basis exists.
- **Never invent unresolved simulation behavior.** If a simulation rule, save/load behavior, reservation lifecycle, or timing guarantee is not established by Step 1-3, use Constrained TODO. Fake certainty in engine docs is dangerous.
- **Implementation stack matters.** GDScript-only vs C++ GDExtension produces materially different docs. Get the stack right.
- **Be engine-specific.** Pre-filled content should use the engine's actual API names, patterns, and terminology.
- **Align with Step 3 docs.** Engine docs must not contradict architecture.md, authority.md, interfaces.md, or other reference docs.
- **If unsure about an engine's conventions**, leave the section as TODO rather than guessing wrong.
- **Asset/import conventions must not redefine visual style.** The asset-import-pipeline doc governs import, packaging, naming, presets, and runtime handling — not visual direction. Visual style rules belong in style-guide/color-system/ui-kit (Rank 2).
- **Post-processing seeds as Open TODO if style-guide rendering approach is unresolved.** Post-processing docs get fake-fast if the look target isn't locked.
- **implementation-patterns.md is structure-only.** Seed the pattern template with empty entry shells. Never pre-fill patterns — they grow from real implementation experience. Patterns must not contradict higher-ranked engine docs. If a pattern becomes broadly required, promote it into the relevant engine doc and leave a reference in implementation-patterns.
- **Update the engine index** to reflect the actual files created.
- **Created documents start with Status: Draft.**

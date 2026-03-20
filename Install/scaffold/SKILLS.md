# Skills Reference

> Man-page reference for all 77 scaffold slash commands. Each entry shows synopsis, description, arguments, examples, and related skills.
>
> **When to use each skill** — see [WORKFLOW.md](WORKFLOW.md) for the step-by-step pipeline order.

---

## Quick Reference

| Skill | Arguments | What it does |
|-------|-----------|-------------|
| **Init** | | |
| `/scaffold-init-design` | `[--mode seed\|fill-gaps\|reconcile\|refresh]` | Initialize or update design document |
| **Create** | | |
| `/scaffold-new-roadmap` | — | Create the project roadmap |
| `/scaffold-new-phase` | `[phase-name]` | Create a phase scope gate with auto P#-### ID |
| `/scaffold-new-slice` | `[slice-name]` | Create a vertical slice with auto SLICE-### ID |
| `/scaffold-new-system` | `[system-name] [--split-from SYS-###] [--trigger ADR-###\|KI:keyword]` | Create a single system design with overlap/authority audit |
| `/scaffold-new-spec` | `[spec-name]` | Create a behavior spec with auto SPEC-### ID |
| `/scaffold-new-task` | `[task-name]` | Create an implementation task with auto TASK-### ID |
| **Bulk Seed** | | |
| `/scaffold-bulk-seed-style` | — | Seed all 6 Step 5 visual/UX docs from upstream context |
| `/scaffold-bulk-seed-systems` | — | Seed glossary + system stubs from design doc |
| `/scaffold-bulk-seed-references` | — | Seed all 9 reference/architecture docs from systems |
| `/scaffold-bulk-seed-engine` | `[--engine godot4\|unity\|unreal5\|other]` | Select engine, then seed all engine docs |
| `/scaffold-bulk-seed-input` | — | Seed all 5 input docs from design doc |
| `/scaffold-bulk-seed-phases` | — | Seed phase stubs from roadmap |
| `/scaffold-bulk-seed-slices` | — | Seed slice stubs from phases + systems + interfaces |
| `/scaffold-bulk-seed-specs` | — | Seed spec stubs from slices + systems + states |
| `/scaffold-bulk-seed-tasks` | — | Seed task stubs from specs + engine docs + signals |
| **Fix** | | |
| `/scaffold-fix-design` | `[--iterate N]` | Mechanical cleanup for design doc |
| `/scaffold-fix-style` | `[--target doc.md] [--iterate N]` | Mechanical cleanup for all 6 Step 5 visual/UX docs |
| `/scaffold-iterate-style` | `[--target doc.md] [--topics "1,4,7"] [--focus "..."]` | Adversarial per-doc review of Step 5 visual/UX docs (7 topics) |
| `/scaffold-fix-systems` | `[--target SYS-###] [--iterate N]` | Mechanical cleanup for system designs |
| `/scaffold-fix-references` | `[--target doc.md] [--iterate N]` | Mechanical cleanup for Step 3 reference/architecture docs |
| `/scaffold-fix-engine` | `[--target doc.md] [--iterate N]` | Mechanical cleanup for engine docs |
| `/scaffold-fix-roadmap` | `[--iterate N]` | Mechanical cleanup for roadmap |
| `/scaffold-fix-phase` | `[--target P#-###] [--iterate N]` | Mechanical cleanup for phase docs |
| `/scaffold-fix-slice` | `[--target SLICE-###] [--iterate N]` | Mechanical cleanup for slice docs |
| `/scaffold-fix-spec` | `[--target SPEC-###] [--iterate N]` | Mechanical cleanup for spec docs |
| `/scaffold-fix-task` | `[--target TASK-###] [--iterate N]` | Mechanical cleanup for task docs |
| `/scaffold-fix-input` | `[--target doc.md] [--iterate N]` | Mechanical cleanup for Step 6 input docs |
| `/scaffold-fix-cross-cutting` | — | Resolve cross-document integrity findings |
| **Iterate** | | |
| `/scaffold-iterate-design` | `[--topic N] [--iterations N]` | Adversarial per-topic design doc review (5 structural + 1 design stress test) |
| `/scaffold-iterate-systems` | `[SYS-### or SYS-###-SYS-###]` | Adversarial per-topic system design review |
| `/scaffold-iterate-references` | `[--target doc.md] [--topic N]` | Adversarial per-topic Step 3 docs review |
| `/scaffold-iterate-engine` | `[--target doc.md] [--topic N]` | Adversarial per-topic engine doc review |
| `/scaffold-iterate-roadmap` | `[--topic N]` | Adversarial per-topic roadmap review |
| `/scaffold-iterate-phase` | `[P#-###] [--topic N]` | Adversarial per-topic phase review |
| `/scaffold-iterate-slice` | `[SLICE-###] [--topic N]` | Adversarial per-topic slice review |
| `/scaffold-iterate-spec` | `[SPEC-### or range] [--topic N]` | Adversarial per-topic spec review |
| `/scaffold-iterate-input` | `[--target doc.md] [--topics "1,3,6"] [--focus "..."]` | Adversarial per-topic input doc review (6 topics) |
| `/scaffold-iterate-task` | `[TASK-### or range] [--topic N]` | Adversarial per-topic task review |
| **Revise** | | |
| `/scaffold-revise-design` | `[--source P#-###\|SLICE-###\|foundation-recheck]` | Detect design drift from implementation feedback |
| `/scaffold-revise-systems` | `[--source SLICE-###]` | Detect system design drift from implementation feedback |
| `/scaffold-revise-references` | `[--source SLICE-###]` | Detect Step 3 doc drift from implementation feedback |
| `/scaffold-revise-engine` | `[--source SLICE-###]` | Detect engine doc drift from implementation feedback |
| `/scaffold-revise-style` | `[--source SLICE-###]` | Detect Step 5 visual/UX doc drift from implementation feedback |
| `/scaffold-revise-input` | `[--source SLICE-###] [--target doc.md]` | Detect Step 6 input doc drift from implementation feedback |
| `/scaffold-revise-foundation` | `[--mode initial\|recheck]` | Verify foundation stability, dispatch revision loops |
| `/scaffold-revise-roadmap` | — | Update roadmap after phase completion |
| `/scaffold-revise-phases` | `[--source P#-###]` | Update remaining phases from implementation feedback |
| `/scaffold-revise-slices` | `[--source SLICE-###]` | Update remaining slices from implementation feedback |
| **Approve** | | |
| `/scaffold-approve-phases` | — | Lifecycle gate: approve Draft phases for slice seeding |
| `/scaffold-approve-slices` | — | Lifecycle gate: approve Draft slices for spec seeding |
| `/scaffold-approve-specs` | — | Lifecycle gate: approve Draft specs in a slice |
| `/scaffold-approve-tasks` | — | Lifecycle gate: approve Draft tasks in a slice |
| **Triage** | | |
| `/scaffold-triage-specs` | `[SLICE-###]` | Resolve spec-level issues from iterate-spec |
| `/scaffold-triage-tasks` | `[SLICE-###]` | Resolve task-level issues from iterate-task |
| `/scaffold-reorder-tasks` | `[SLICE-###]` | Reorder tasks by dependency and implementation sequence |
| **Implement** | | |
| `/scaffold-implement-task` | `[TASK-### or range]` | Implement task(s) end-to-end: code, tests, review, sync |
| `/scaffold-build-and-test` | `[--files file...] [--skip-unit] [--skip-lint]` | Pure verification gate: build, lint, tests |
| `/scaffold-code-review` | `[file or system scope]` | Adversarial code review via external LLM (7 topics) |
| `/scaffold-add-regression-tests` | `[TASK-###]` | Add regression tests using 6-layer model |
| **Complete** | | |
| `/scaffold-complete` | `[document-path\|ID]` | Mark a planning doc as Complete; ripples up through parents |
| **Edit** | | |
| `/scaffold-update-doc` | `[doc-name\|path]` | Add, remove, or modify entries in any scaffold doc |
| `/scaffold-sync-glossary` | `[--scope all\|design\|systems\|references\|style\|input] [--dry-run]` | Scan docs for glossary-worthy terms with worthiness gate and ambiguity detection |
| `/scaffold-sync-reference-docs` | — | Sync reference docs after upstream changes |
| **Validate** | | |
| `/scaffold-validate` | `[--scope refs\|design\|systems\|foundation\|roadmap\|phases\|slices\|specs\|tasks\|engine\|style\|input\|all]` | Run cross-reference validation across scaffold docs |
| **Playtest** | | |
| `/scaffold-playtest-log` | `[session-type]` | Log playtester observations into the feedback tracker |
| `/scaffold-playtest-review` | — | Analyze playtest feedback patterns with priority grid |
| **Art** | | |
| `/scaffold-art-concept` | `[prompt or document-path]` | Generate concept art using DALL-E |
| `/scaffold-art-ui-mockup` | `[prompt or document-path]` | Generate UI mockup art using DALL-E |
| `/scaffold-art-character` | `[prompt or document-path]` | Generate character art using DALL-E |
| `/scaffold-art-environment` | `[prompt or document-path]` | Generate environment art using DALL-E |
| `/scaffold-art-sprite` | `[prompt or document-path]` | Generate sprite art using DALL-E |
| `/scaffold-art-icon` | `[prompt or document-path]` | Generate icon art using DALL-E |
| `/scaffold-art-promo` | `[prompt or document-path]` | Generate promotional art using DALL-E |
| **Audio** | | |
| `/scaffold-audio-music` | `[prompt or document-path]` | Generate music tracks using ElevenLabs |
| `/scaffold-audio-sfx` | `[prompt or document-path]` | Generate sound effects using ElevenLabs |
| `/scaffold-audio-ambience` | `[prompt or document-path]` | Generate ambient audio loops using ElevenLabs |
| `/scaffold-audio-voice` | `[prompt or document-path]` | Generate voice audio using OpenAI TTS |

---

## Create

Skills for initializing individual documents from templates. All create skills ask one section at a time, write answers immediately, and set Status to Draft.


### /scaffold-new-roadmap

Create the project roadmap.

**Synopsis**

    /scaffold-new-roadmap

**Description**

Creates the project roadmap by copying Core Fantasy from the design doc as the Vision Checkpoint, then walking through phase definition. Asks about goals, deliverables, and outcome orientation for each phase. Typical progression: Foundation → Systems → Content → Polish → Ship. Reports the completed roadmap overview.

**Examples**

    /scaffold-new-roadmap

**See Also**

`/scaffold-new-phase`

---

### /scaffold-new-phase

Create a phase scope gate with automatic ID assignment.

**Synopsis**

    /scaffold-new-phase [phase-name]

**Description**

Creates a phase scope gate at `phases/P#-###-<name>.md` with automatic sequential ID assignment. Reads the roadmap, design doc, all systems, and all ADRs for impact analysis before defining the phase. Walks through Goal, Entry Criteria (with specific IDs), In Scope, Out of Scope, Deliverables, Exit Criteria, and Dependencies. Registers in `phases/_index.md`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `phase-name` | No | Name for the phase. If omitted, asks interactively. |

**Examples**

    /scaffold-new-phase foundation
    /scaffold-new-phase content-pipeline
    /scaffold-new-phase

**See Also**

`/scaffold-new-slice`

---

### /scaffold-new-slice

Create a vertical slice with automatic ID assignment.

**Synopsis**

    /scaffold-new-slice [slice-name]

**Description**

Creates a vertical slice at `slices/SLICE-###-<name>.md` with automatic sequential ID assignment. Reads the slice template, slices index, phase files, systems, and interfaces. Asks which phase the slice belongs to (or infers from context). Walks through Goal, Specs Included (marked TBD), Integration Points (referencing `interfaces.md`), Done Criteria, and Demo Script. Registers in `slices/_index.md`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `slice-name` | No | Name for the slice. If omitted, asks interactively. |

**Examples**

    /scaffold-new-slice core-combat-loop
    /scaffold-new-slice inventory-ui
    /scaffold-new-slice

**See Also**

`/scaffold-bulk-seed-slices`, `/scaffold-new-spec`

---

### /scaffold-new-system

Create a single system design document with automatic ID assignment.

**Synopsis**

    /scaffold-new-system [system-name] [--split-from SYS-###] [--trigger ADR-###|KI:keyword]

**Description**

Creates a single system design at `design/systems/SYS-###-<name>_draft.md` with automatic sequential ID assignment. Reads the design doc (invariants, simulation depth, system domains), all existing systems, authority table, and ADRs. Audits for overlap, authority conflicts, invariant violations, simulation depth compliance, authority flow, and necessity (required vs premature vs redundant) before defining the system. Walks through all 18 template sections interactively (including observability and performance characteristics), pre-filling from context. Runs an identity check after definition (one-sentence, absorption, core-concept tests). Enforces authority registration as a gate when owned state is defined. Registers in both `design/systems/_index.md` and the design doc System Design Index. When `--split-from` is provided, also updates the parent system's Non-Responsibilities and dependency tables.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `system-name` | No | Name for the system. If omitted, asks interactively. |
| `--split-from` | No | SYS-### ID of a parent system being split. Pre-fills context from parent. |
| `--trigger` | No | ADR-### or KI:keyword that motivated the new system. Reads the trigger for context. |

**Examples**

    /scaffold-new-system mood-resolution
    /scaffold-new-system task-scheduling --split-from SYS-005
    /scaffold-new-system zone-management --trigger ADR-018
    /scaffold-new-system

**See Also**

`/scaffold-bulk-seed-systems`, `/scaffold-fix-systems`, `/scaffold-iterate-systems`

---

### /scaffold-new-spec

Create a behavior spec with automatic ID assignment.

**Synopsis**

    /scaffold-new-spec [spec-name]

**Description**

Creates a behavior spec at `specs/SPEC-###-<name>.md` with automatic sequential ID assignment. Reads the spec template, parent slice, parent system design, state transitions, and all ADRs for impact check. Pre-fills from system design where possible (Behavior from Player Actions, Edge Cases from system Edge Cases). Walks through Summary, Preconditions, Behavior, Postconditions, Edge Cases, and Acceptance Criteria. Registers in `specs/_index.md` and parent slice's table.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `spec-name` | No | Name for the spec. If omitted, asks interactively. |

**Examples**

    /scaffold-new-spec player-attack
    /scaffold-new-spec item-pickup
    /scaffold-new-spec

**See Also**

`/scaffold-bulk-seed-specs`, `/scaffold-new-task`

---

### /scaffold-new-task

Create an implementation task with automatic ID assignment.

**Synopsis**

    /scaffold-new-task [task-name]

**Description**

Creates an implementation task at `tasks/TASK-###-<name>.md` with automatic sequential ID assignment. Reads the task template, parent spec, parent system, engine docs, signal registry, entity components, and all ADRs for impact check. Pre-fills implementation steps from spec Behavior, translating to engine patterns. Walks through Objective, Steps, Files Affected, Verification, and Notes. Registers in `tasks/_index.md` and parent slice's Tasks table.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `task-name` | No | Name for the task. If omitted, asks interactively. |

**Examples**

    /scaffold-new-task implement-attack-resolution
    /scaffold-new-task wire-inventory-ui
    /scaffold-new-task

**See Also**

`/scaffold-bulk-seed-tasks`, `/scaffold-complete`

---

## Bulk Seed

Skills for bulk-populating multiple documents from source documents. All bulk seed skills present proposed content for user confirmation and set Status to Draft.

---

### /scaffold-bulk-seed-style

Seed all 6 Step 5 visual/UX docs from upstream context.

**Synopsis**

    /scaffold-bulk-seed-style

**Description**

Reads the design doc, system designs, and supporting docs to seed `style-guide.md`, `color-system.md`, `ui-kit.md`, `interaction-model.md`, `feedback-system.md`, and `audio-direction.md` in 6 phases. Auto-writes high-confidence sections directly, tags medium-confidence sections with rationale in the changelog, and leaves low-confidence sections as TODOs. Only pauses for user confirmation on ambiguous style direction, competing visual interpretations, major UX model choices, or decisions that would materially change downstream docs. Skips already-authored docs. Reports confidence breakdown, assumptions made, unresolved questions, and cross-doc tensions.

**Examples**

    /scaffold-bulk-seed-style

---

### /scaffold-fix-style

Mechanical cleanup for all 6 Step 5 visual/UX docs.

**Synopsis**

    /scaffold-fix-style [--target doc.md] [--iterate N]

**Description**

Formatter and linter for Step 5 docs: style-guide, color-system, ui-kit, interaction-model, feedback-system, and audio-direction. Auto-fixes structural issues (missing sections, template text, terminology drift, token normalization, hex formatting, duplicate entries). Detects design signals (tone mismatches, component gaps, priority conflicts, scope creep, boundary violations) for adversarial review. Enforces cross-doc consistency: style-guide → color-system → ui-kit, interaction-model ↔ feedback-system, audio-direction derives priority from feedback-system. Supports `--target` for single-doc focus (cross-doc checks still run, only target is edited). Iterates until clean, human-only, stable, or limit reached.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `--target` | No | Single doc to fix (e.g., `style-guide.md`, `ui-kit.md`). Omit to fix all 6. |
| `--iterate N` | No | Max passes (default: 10). |

**Examples**

    /scaffold-fix-style
    /scaffold-fix-style --target ui-kit.md
    /scaffold-fix-style --target feedback-system.md --iterate 5

**See Also**

`/scaffold-bulk-seed-style`, `/scaffold-iterate-style`

---

### /scaffold-iterate-style

Adversarial per-topic review of all 6 Step 5 visual/UX docs.

**Synopsis**

    /scaffold-iterate-style [--target doc.md] [--topics "1,2,5"] [--focus "concern"] [--iterations N]

**Description**

Each of the 6 Step 5 docs gets its own specialized review lens targeting its unique failure modes, then Topic 7 checks the seams with a mandatory end-to-end scenario test. Topics: (1) visual identity & readability, (2) color semantics & accessibility, (3) UI component model & composition discipline, (4) input clarity & command structure, (5) response coverage & priority logic, (6) audio tone & boundary discipline, (7) cross-doc integration. Each topic concludes with a per-doc failure probe (what breaks, what developers guess, where two devs diverge, what drifts, hardest missing edge case). Topic 7 runs first when budget is tight. Review consistency lock, scope collapse guard, end-to-end scenario trace through all 6 docs.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `--target` | No | Single doc to review (e.g., `ui-kit.md`). Omit to review all 6. |
| `--topics` | No | Comma-separated topic numbers (e.g., `"1,3,5"`). |
| `--focus` | No | Narrow review to a specific concern. |
| `--iterations N` | No | Max outer loop iterations (default: 10). |
| `--signals` | No | Design signals from fix-style. |

**Examples**

    /scaffold-iterate-style
    /scaffold-iterate-style --target feedback-system.md
    /scaffold-iterate-style --topics "5,7" --focus "priority hierarchy"
    /scaffold-iterate-style --signals "tone mismatch, component gap"

**See Also**

`/scaffold-fix-style`, `/scaffold-bulk-seed-style`

---

### /scaffold-bulk-seed-systems

Seed glossary and system stubs from the design doc.

**Synopsis**

    /scaffold-bulk-seed-systems

**Description**

Reads the completed design doc and bulk-seeds the glossary and system design stubs. Phase 1 extracts candidate glossary terms. Phase 2 identifies systems from Player Verbs, Core Loop, Meta Loop, and Failure States. Phase 3 bulk-creates system files with SYS-### IDs, pre-filling Purpose and Player Intent. Registers in both system index and design doc.

**Examples**

    /scaffold-bulk-seed-systems

**See Also**

`/scaffold-fix-systems`, `/scaffold-iterate-systems`

---

### /scaffold-bulk-seed-references

Seed all 7 reference docs from system designs.

**Synopsis**

    /scaffold-bulk-seed-references

**Description**

Reads all completed system designs and bulk-populates 7 companion docs in order: authority table, interface contracts, state transitions, entity components, resource definitions, signal registry, and balance parameters. Each phase presents proposed entries to user for confirmation. Reports what was added and flags any gaps (systems that didn't contribute, orphaned references).

**Examples**

    /scaffold-bulk-seed-references

**See Also**

`/scaffold-fix-references`, `/scaffold-iterate-references`

---

### /scaffold-bulk-seed-engine

Select engine, then seed all 5 engine docs.

**Synopsis**

    /scaffold-bulk-seed-engine

**Description**

Asks which engine the project uses (Godot 4, Unity, Unreal 5, or custom), then creates all 5 engine docs from templates with engine-specific pre-filled conventions. Reads design, style, and UI docs for context. Creates `[engine]-coding`, `-ui`, `-input`, `-scene-architecture`, and `-performance` docs. Updates the engine index.

**Examples**

    /scaffold-bulk-seed-engine

**See Also**

`/scaffold-fix-engine`, `/scaffold-iterate-engine`

---

### /scaffold-bulk-seed-input

Seed all 5 input docs from the design doc.

**Synopsis**

    /scaffold-bulk-seed-input

**Description**

Reads the completed design doc and bulk-seeds all 5 input documents in 5 sequential phases. Phase 1 extracts player verbs and proposes action-map entries with namespaces. Phase 2 derives input philosophy from the design doc's Input Feel and Accessibility sections. Phase 3 proposes default keyboard/mouse bindings from the action-map. Phase 4 proposes default gamepad bindings. Phase 5 proposes UI navigation model and focus flow from the action-map and UI kit. Presents each phase to user for confirmation; writes confirmed content only.

**Examples**

    /scaffold-bulk-seed-input

**See Also**

`/scaffold-fix-style`, `/scaffold-bulk-seed-input`

---

### /scaffold-bulk-seed-slices

Seed slice stubs from phases, systems, and interfaces.

**Synopsis**

    /scaffold-bulk-seed-slices

**Description**

Reads all phases, system designs, and interface contracts to bulk-create vertical slice stubs. Identifies slice candidates by grouping In Scope items into end-to-end experiences. Presents all candidates to user for confirmation. Creates SLICE-### files with pre-filled Goals, Integration Points from `interfaces.md`, and suggested specs. Registers in `slices/_index.md`.

**Examples**

    /scaffold-bulk-seed-slices

**See Also**

`/scaffold-new-slice`

---

### /scaffold-bulk-seed-specs

Seed spec stubs from slices, systems, and state transitions.

**Synopsis**

    /scaffold-bulk-seed-specs

**Description**

Reads all slices, system designs, and state transitions to bulk-create behavior spec stubs. Extracts spec candidates from slice Specs Included tables and system Player Actions. Checks ADRs for behavior changes. Presents all candidates to user for confirmation. Creates SPEC-### files with pre-filled Summary, Behavior, Edge Cases, and Acceptance Criteria. Registers in `specs/_index.md` and slice tables.

**Examples**

    /scaffold-bulk-seed-specs

**See Also**

`/scaffold-new-spec`

---

### /scaffold-bulk-seed-tasks

Seed task stubs from specs, engine docs, and signal registry.

**Synopsis**

    /scaffold-bulk-seed-tasks

**Description**

Reads all specs, engine docs, and signal registry to bulk-create implementation task stubs. Translates each spec to implementation tasks using engine patterns. Determines task ordering within slices (foundational files → core logic → wiring → UI/feedback). Checks ADRs for implementation approach changes. Presents all candidates to user for confirmation. Creates TASK-### files with pre-filled Objective, Steps, and Files Affected. Registers in `tasks/_index.md` and slice Tasks tables.

**Examples**

    /scaffold-bulk-seed-tasks

**See Also**

`/scaffold-new-task`


## Complete

Mark planning-layer documents as Complete with automatic upward rippling.

---

### /scaffold-complete

Mark a planning doc as Complete; ripple status upward through parents.

**Synopsis**

    /scaffold-complete [document-path|ID]

**Description**

Marks planning-layer documents (tasks, specs, slices, phases) as Complete with automatic upward rippling. Applies only to the planning layer — design, style, reference, engine, and theory docs use Approved status and are not eligible.

For tasks: direct Complete (leaf nodes, no children check). For specs, slices, and phases: verifies all children are Complete first (specs check tasks, slices check specs, phases check slices). Sets document status to Complete, then ripples upward — if the target's parent now has all children Complete, auto-marks the parent Complete and continues up the hierarchy. Stops rippling when a parent still has incomplete children. Idempotent: already-Complete docs report status and do nothing.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `document-path\|ID` | No | Document to complete (e.g., `TASK-001`, `SPEC-003`, or file path). If omitted, asks interactively. |

**Examples**

    /scaffold-complete TASK-001
    /scaffold-complete SPEC-003
    /scaffold-complete phases/P1-001-foundation.md
    /scaffold-complete

**See Also**

`/scaffold-iterate-task`, `/scaffold-complete`

---

## Edit

Targeted edits to any scaffold document with automatic cross-reference updates.

---

### /scaffold-update-doc

Add, remove, or modify entries in any scaffold document.

**Synopsis**

    /scaffold-update-doc [doc-name|path]

**Description**

Makes targeted edits to any scaffold document (add, remove, or modify entries or sections). Identifies the target by doc-name, SYS-### ID, or file path. Asks for the action (Add/Remove/Modify) if not specified. For table docs: validates format, maintains ordering (alphabetical for glossary, grouped for balance params). For section docs: replaces TODOs with content. For state machines: manages blocks. Handles complex edits (issue tracking, state machines).

Updates cross-references automatically: glossary term renames propagate, system add/remove/rename updates both indexes, signal/entity/resource changes check related docs. Confirms proposed edit before writing. Reports what changed and any cross-references flagged for manual attention. Never silently breaks references.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `doc-name\|path` | No | Target document (e.g., `glossary`, `SYS-001`, or file path). If omitted, asks interactively. |

**Examples**

    /scaffold-update-doc glossary
    /scaffold-update-doc SYS-001
    /scaffold-update-doc reference/signal-registry.md
    /scaffold-update-doc

---

### /scaffold-sync-glossary

Scan scaffold docs for domain terms missing from the glossary.

**Synopsis**

    /scaffold-sync-glossary [--scope all|design|systems|references|style|input] [--dry-run]

**Description**

Scans scaffold docs for domain terms that should be in the glossary but aren't. Extracts candidates from structured doc fields with source weighting (Strong vs Advisory). Normalizes variants (case, hyphens, plurals) and deduplicates. Applies a glossary worthiness gate (cross-layer usage, player-facing, authority-significant, disambiguating). Checks for ambiguity with existing terms (near-equivalents, prefix variants, cross-layer confusion). Assigns confidence tiers (High/Medium/Low). Presents candidates with per-term decisions: Canonical (new term), Alias (redirect to existing), NOT (discouraged synonym), or Reject. Also detects stale glossary terms no longer referenced in current docs. Blocks Draft-only provisional terms until upstream stabilizes.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `--scope` | No | Which doc layers to scan. Default: `all`. Options: `design`, `systems`, `references`, `style`, `input`. Comma-separated for multiple. |
| `--dry-run` | No | Report candidate terms without writing anything. |

**Examples**

    /scaffold-sync-glossary
    /scaffold-sync-glossary --scope references
    /scaffold-sync-glossary --scope style,input
    /scaffold-sync-glossary --dry-run

**See Also**

`/scaffold-bulk-seed-systems` (initial glossary seeding), `/scaffold-validate` (glossary coverage check), `/scaffold-update-doc glossary` (manual edits)

---

## Validate

Cross-reference validation across the entire scaffold.

---

### /scaffold-validate

Run cross-reference validation across all scaffold documents.

**Synopsis**

    /scaffold-validate

**Description**

Runs `validate-refs.py` to check referential integrity across all scaffold documents. Reports broken references, missing registrations, glossary NOT-column violations, and orphaned entries. Checks: system IDs registered in `systems/_index.md`, authority ↔ entity ownership, signal emitters/consumers, interface sources/targets, state machine authorities, glossary NOT-column usage, bidirectional system registration (index ↔ design doc), spec ↔ slice coverage, and task ↔ spec links.

Presents results as a summary table with PASS/FAIL per check and lists each failing issue with file, line, and message. Suggests specific fixes for each issue. Read-only — does not modify any files.

**Examples**

    /scaffold-validate

**See Also**

`/scaffold-update-doc`

---

## Playtest

Skills for capturing and analyzing playtester feedback. Observations are logged with `/scaffold-playtest-log` and analyzed with `/scaffold-playtest-review`.

---

### /scaffold-playtest-log

Log playtester observations into the feedback tracker.

**Synopsis**

    /scaffold-playtest-log [session-type]

**Description**

Captures playtester observations into `decisions/playtest-feedback.md`. Creates or identifies a playtest session, then walks through observations one at a time — Type, Observation, System/Spec, Severity, Frequency. Checks for duplicates before adding (aggregates frequency if the same issue is already logged). After all observations are entered, scans for entries with 3+ reports and prompts to promote them to Patterns per the Rule of Three. Reports entries logged, duplicates merged, and patterns promoted.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `session-type` | No | Session type hint (e.g., `in-person`, `remote`, `self-play`). If omitted, asks interactively. |

**Examples**

    /scaffold-playtest-log in-person
    /scaffold-playtest-log remote
    /scaffold-playtest-log

**See Also**

`/scaffold-playtest-review`, `/scaffold-update-doc`

---

### /scaffold-playtest-review

Analyze playtest feedback patterns with severity x frequency grid.

**Synopsis**

    /scaffold-playtest-review

**Description**

Read-only analysis of `decisions/playtest-feedback.md`. Groups feedback by system to identify hot spots, classifies entries into a severity x frequency priority grid (ACT NOW / WATCH CLOSELY / MONITOR / NOTE & MOVE ON), recommends actions for high-priority entries, cross-references with known issues, design debt, and ADRs for overlaps, checks for stale entries, and produces a delight inventory of positive observations to protect. Does not modify any files.

**Examples**

    /scaffold-playtest-review

**See Also**

`/scaffold-playtest-log`, `/scaffold-new-phase`

---

## Art

Skills for generating visual assets informed by the project's style guide and color system.

---

### /scaffold-art-concept

Generate concept art using DALL-E, informed by the project's style guide and color system.

**Synopsis**

    /scaffold-art-concept [prompt or document-path]

**Description**

Generates concept art using DALL-E, grounded in the project's visual identity. Reads `design/style-guide.md` and `design/color-system.md` to build a style context, then combines it with the user's prompt or a document's visual elements. Supports two modes: freeform (text prompt) and document-driven (reads a scaffold doc and extracts visual elements). Shows the composed prompt for user confirmation before calling the API. Saves images to `art/concept-art/` with kebab-case timestamped filenames and updates the art index.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-art-concept a misty pixel-art village at dawn
    /scaffold-art-concept scaffold/design/systems/SYS-001-combat.md
    /scaffold-art-concept

**See Also**

`/scaffold-art-ui-mockup`, `/scaffold-art-character`, `/scaffold-art-environment`, `/scaffold-art-sprite`, `/scaffold-art-icon`, `/scaffold-art-promo`

---

### /scaffold-art-ui-mockup

Generate UI mockup art using DALL-E, informed by the project's UI kit, style guide, and color system.

**Synopsis**

    /scaffold-art-ui-mockup [prompt or document-path]

**Description**

Generates UI mockup art using DALL-E, grounded in the project's visual identity. Reads `design/ui-kit.md`, `design/style-guide.md`, and `design/color-system.md` to build a style context focused on screen composition, HUD layout, menu flows, and readability. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts UI elements) modes. Shows the composed prompt for user confirmation before calling the API. Saves images to `art/ui-mockups/` with kebab-case timestamped filenames. Default size: 1792x1024.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-art-ui-mockup main HUD with health bar, minimap, and hotbar
    /scaffold-art-ui-mockup scaffold/design/ui-kit.md
    /scaffold-art-ui-mockup

**See Also**

`/scaffold-art-concept`, `/scaffold-art-icon`

---

### /scaffold-art-character

Generate character art using DALL-E, informed by the project's style guide and color system.

**Synopsis**

    /scaffold-art-character [prompt or document-path]

**Description**

Generates character art using DALL-E, grounded in the project's visual identity. Reads `design/style-guide.md` and `design/color-system.md` to build a style context, plus checks the design doc for character descriptions. Focuses on silhouette readability, proportions, color identity, expression, and costume design. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts character descriptions) modes. Shows the composed prompt for user confirmation before calling the API. Saves images to `art/character-art/` with kebab-case timestamped filenames. Default size: 1024x1024.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-art-character a rogue archer with dark cloak and glowing arrows
    /scaffold-art-character scaffold/design/design-doc.md
    /scaffold-art-character

**See Also**

`/scaffold-art-concept`, `/scaffold-art-sprite`

---

### /scaffold-art-environment

Generate environment art using DALL-E, informed by the project's style guide and color system.

**Synopsis**

    /scaffold-art-environment [prompt or document-path]

**Description**

Generates environment art using DALL-E, grounded in the project's visual identity. Reads `design/style-guide.md` and `design/color-system.md` to build a style context, plus checks the design doc for world/setting descriptions. Focuses on depth, atmosphere, lighting, scale, and walkable vs decorative space. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts environment descriptions) modes. Shows the composed prompt for user confirmation before calling the API. Saves images to `art/environment-art/` with kebab-case timestamped filenames. Default size: 1792x1024.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-art-environment a misty forest clearing with ancient ruins
    /scaffold-art-environment scaffold/design/systems/SYS-003-exploration.md
    /scaffold-art-environment

**See Also**

`/scaffold-art-concept`, `/scaffold-art-promo`

---

### /scaffold-art-sprite

Generate sprite art using DALL-E, informed by the project's style guide and color system.

**Synopsis**

    /scaffold-art-sprite [prompt or document-path]

**Description**

Generates sprite art using DALL-E, grounded in the project's visual identity. Reads `design/style-guide.md` and `design/color-system.md` to build a style context focused on pixel art style, limited palette, clean edges, and small-size readability. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts sprite subjects) modes. Shows the composed prompt for user confirmation before calling the API. Saves images to `art/sprite-art/` with kebab-case timestamped filenames. Default size: 1024x1024.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-art-sprite warrior idle animation frame, 16-color palette
    /scaffold-art-sprite scaffold/design/systems/SYS-001-combat.md
    /scaffold-art-sprite

**See Also**

`/scaffold-art-concept`, `/scaffold-art-character`

---

### /scaffold-art-icon

Generate icon art using DALL-E, informed by the project's UI kit, color system, and style guide.

**Synopsis**

    /scaffold-art-icon [prompt or document-path]

**Description**

Generates icon art using DALL-E, grounded in the project's visual identity. Reads `design/ui-kit.md`, `design/color-system.md`, and `design/style-guide.md` to build a style context focused on square format, simple silhouette, high contrast, and icon-size readability. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts icon subjects) modes. Shows the composed prompt for user confirmation before calling the API. Saves images to `art/icon-art/` with kebab-case timestamped filenames. Default size: 1024x1024.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-art-icon health potion icon, red liquid in glass vial
    /scaffold-art-icon scaffold/reference/entity-components.md
    /scaffold-art-icon

**See Also**

`/scaffold-art-ui-mockup`, `/scaffold-art-concept`

---

### /scaffold-art-promo

Generate promotional art using DALL-E, informed by the project's style guide and color system.

**Synopsis**

    /scaffold-art-promo [prompt or document-path]

**Description**

Generates promotional art using DALL-E, grounded in the project's visual identity. Reads `design/style-guide.md` and `design/color-system.md` to build a style context, plus checks the design doc for identity and vision. Focuses on dramatic composition, marketing appeal, text-safe space for title/logo overlay, and landscape orientation. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts visual themes) modes. Shows the composed prompt for user confirmation before calling the API. Saves images to `art/promo-art/` with kebab-case timestamped filenames. Default size: 1792x1024.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-art-promo epic hero banner with dark forest background, text-safe left third
    /scaffold-art-promo scaffold/design/design-doc.md
    /scaffold-art-promo

**See Also**

`/scaffold-art-concept`, `/scaffold-art-environment`

---

## Audio

Skills for generating audio assets informed by the project's style guide, color system, and design doc.

---

### /scaffold-audio-music

Generate music tracks using ElevenLabs, informed by the project's style guide and design doc mood/tone.

**Synopsis**

    /scaffold-audio-music [prompt or document-path]

**Description**

Generates music tracks using ElevenLabs, grounded in the project's tonal identity. Reads `design/style-guide.md` and `design/design-doc.md` to build a musical direction (genre, tempo, mood, instrumentation). Supports two modes: freeform (text prompt) and document-driven (reads a scaffold doc and extracts musical elements). Shows the composed prompt for user confirmation before calling the API. Saves audio to `audio/music/` with kebab-case timestamped filenames. Output format: `.mp3`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-audio-music upbeat chiptune battle theme, loopable, 120 BPM
    /scaffold-audio-music scaffold/design/design-doc.md
    /scaffold-audio-music

**See Also**

`/scaffold-audio-sfx`, `/scaffold-audio-ambience`, `/scaffold-audio-voice`

---

### /scaffold-audio-sfx

Generate sound effects using ElevenLabs, informed by the project's style guide and design doc game feel.

**Synopsis**

    /scaffold-audio-sfx [prompt or document-path]

**Description**

Generates sound effects using ElevenLabs, grounded in the project's tonal identity. Reads `design/style-guide.md` and `design/design-doc.md` to build a sound design direction (intensity, style, audio character). Focuses on clarity, impact, timing, and game-appropriate intensity. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts sound-worthy events) modes. Shows the composed prompt for user confirmation before calling the API. Saves audio to `audio/sfx/` with kebab-case timestamped filenames. Output format: `.mp3`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-audio-sfx sword slash impact, metallic ring, medium weight
    /scaffold-audio-sfx scaffold/design/systems/SYS-001-combat.md
    /scaffold-audio-sfx

**See Also**

`/scaffold-audio-music`, `/scaffold-audio-ambience`, `/scaffold-audio-voice`

---

### /scaffold-audio-ambience

Generate ambient audio loops using ElevenLabs, informed by the project's style guide, color system mood, and design doc world/setting.

**Synopsis**

    /scaffold-audio-ambience [prompt or document-path]

**Description**

Generates ambient audio loops using ElevenLabs, grounded in the project's world and atmosphere. Reads `design/style-guide.md`, `design/color-system.md`, and `design/design-doc.md` to build an atmospheric direction (environment type, mood, depth, spatial character). Uses the `sfx` subcommand with `--loop` for seamless looping. Focuses on atmosphere, depth, layering, and loop seamlessness. Supports freeform (text prompt) and document-driven (reads a scaffold doc and extracts environment descriptions) modes. Shows the composed prompt for user confirmation before calling the API. Saves audio to `audio/ambience/` with kebab-case timestamped filenames. Output format: `.mp3`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text prompt, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-audio-ambience misty forest clearing with distant birdsong and gentle wind
    /scaffold-audio-ambience scaffold/design/systems/SYS-003-exploration.md
    /scaffold-audio-ambience

**See Also**

`/scaffold-audio-music`, `/scaffold-audio-sfx`, `/scaffold-audio-voice`

---

### /scaffold-audio-voice

Generate voice audio using OpenAI TTS, informed by the project's style guide and design doc characters/narrative.

**Synopsis**

    /scaffold-audio-voice [prompt or document-path]

**Description**

Generates voice audio using OpenAI TTS, grounded in the project's narrative identity. Reads `design/style-guide.md` and `design/design-doc.md` to build a voice direction (vocal register, energy, pacing, emotional range). Supports selecting from OpenAI TTS voices (alloy, echo, fable, onyx, nova, shimmer) based on character personality. Supports freeform (text to speak) and document-driven (reads a scaffold doc and extracts dialogue/narration) modes. Shows the text and voice parameters for user confirmation before calling the API. Saves audio to `audio/voice/` with kebab-case timestamped filenames. Output format: `.mp3`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `prompt or document-path` | No | Freeform text to speak, or a path to a scaffold doc for document-driven mode. If omitted, asks interactively. |

**Examples**

    /scaffold-audio-voice "The ancient forest holds secrets older than memory."
    /scaffold-audio-voice scaffold/design/design-doc.md
    /scaffold-audio-voice

**See Also**

`/scaffold-audio-music`, `/scaffold-audio-sfx`, `/scaffold-audio-ambience`


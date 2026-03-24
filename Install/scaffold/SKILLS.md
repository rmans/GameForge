# Skills Reference

> Man-page reference for all 10 scaffold slash commands. Each entry shows synopsis, description, arguments, examples, and related skills.
>
> **When to use each skill** — see [WORKFLOW.md](WORKFLOW.md) for the step-by-step pipeline order.

---

## Quick Reference

| Skill | Arguments | What it does |
|-------|-----------|-------------|
| **Seed** | | |
| `/scaffold-seed` | `<layer> [--target scope] [--single "name"]` | Dependency-aware document generation for any layer (design, systems, references, engine, style, input, phases, slices, specs, tasks, roadmap). Bulk or single doc creation. Orchestrated by seed.py. |
| **Fix** | | |
| `/scaffold-fix` | `<layer> [target] [--sections "..."] [--iterations N]` | Mechanical cleanup for any layer (design, systems, spec, task, slice, phase, roadmap, references, style, input, engine, cross-cutting). Orchestrated by local-review.py with per-layer YAML configs. |
| **Iterate** | | |
| `/scaffold-iterate` | `<layer> [target] [--topics "1,3"] [--focus "..."] [--iterations N]` | Adversarial per-topic review for any layer (design, systems, spec, task, slice, phase, roadmap, references, style, input, engine). Orchestrated by iterate.py with per-layer YAML configs. |
| **Revise** | | |
| `/scaffold-revise` | `<layer> [--source PHASE-###\|SLICE-###] [--signals ADR-###,KI:keyword]` | Detect drift and revise any layer from implementation feedback. Classifies signals, auto-applies safe changes, escalates dangerous changes, dispatches restabilization. Orchestrated by revise.py with per-layer YAML configs. |
| **Triage** | | |
| `/scaffold-triage` | `<layer> <SLICE-###>` | Resolve human-required issues from review passes. Decision checklists for splits, merges, reassignments. |
| **Implement** | | |
| `/scaffold-implement` | `<TASK-###> [--max-retries N] [--cri N]` | Implement task end-to-end: plan, code (one step at a time, including tests), build, review, sync, complete. All mechanical ops in Python (utils.py). Code review via iterate.py --reviewer code. |
| **Validate** | | |
| `/scaffold-validate` | `[--scope refs\|design\|systems\|foundation\|roadmap\|phases\|slices\|specs\|tasks\|engine\|style\|input\|all]` | Normalize markdown formatting, then run cross-reference validation across scaffold docs |
| **Decisions** | | |
| `/scaffold-file-decision` | `--type adr\|ki\|dd "title"` | File an ADR, Known Issue, or Design Debt entry with cross-references |
| **Playtest** | | |
| `/scaffold-playtest` | `<log\|review> [session-date]` | Log playtest sessions and review feedback patterns |

---

## Create

Skills for initializing individual documents from templates. All create skills ask one section at a time, write answers immediately, and set Status to Draft.


### /scaffold-seed roadmap

Create the project roadmap.

**Synopsis**

    /scaffold-seed roadmap

**Description**

Creates the project roadmap by copying Core Fantasy from the design doc as the Vision Checkpoint, then walking through phase definition. Asks about goals, deliverables, and outcome orientation for each phase. Typical progression: Foundation → Systems → Content → Polish → Ship. Reports the completed roadmap overview.

**Examples**

    /scaffold-seed roadmap

**See Also**

`/scaffold-seed phases --single`

---

### /scaffold-seed phases --single

Create a phase scope gate with automatic ID assignment.

**Synopsis**

    /scaffold-seed phases --single [phase-name]

**Description**

Creates a phase scope gate at `phases/PHASE-###-<name>.md` with automatic sequential ID assignment. Reads the roadmap, design doc, all systems, and all ADRs for impact analysis before defining the phase. Walks through Goal, Entry Criteria (with specific IDs), In Scope, Out of Scope, Deliverables, Exit Criteria, and Dependencies. Registers in `phases/_index.md`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `phase-name` | No | Name for the phase. If omitted, asks interactively. |

**Examples**

    /scaffold-seed phases --single foundation
    /scaffold-seed phases --single content-pipeline
    /scaffold-seed phases --single

**See Also**

`/scaffold-seed slices --single`

---

### /scaffold-seed slices --single

Create a vertical slice with automatic ID assignment.

**Synopsis**

    /scaffold-seed slices --single [slice-name]

**Description**

Creates a vertical slice at `slices/SLICE-###-<name>.md` with automatic sequential ID assignment. Reads the slice template, slices index, phase files, systems, and interfaces. Asks which phase the slice belongs to (or infers from context). Walks through Goal, Specs Included (marked TBD), Integration Points (referencing `interfaces.md`), Done Criteria, and Demo Script. Registers in `slices/_index.md`.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `slice-name` | No | Name for the slice. If omitted, asks interactively. |

**Examples**

    /scaffold-seed slices --single core-combat-loop
    /scaffold-seed slices --single inventory-ui
    /scaffold-seed slices --single

**See Also**

`/scaffold-seed slices`, `/scaffold-seed specs --single`

---

### /scaffold-seed systems --single

Create a single system design document with automatic ID assignment.

**Synopsis**

    /scaffold-seed systems --single [system-name] [--split-from SYS-###] [--trigger ADR-###|KI:keyword]

**Description**

Creates a single system design at `design/systems/SYS-###-<name>_draft.md` with automatic sequential ID assignment. Reads the design doc (invariants, simulation depth, system domains), all existing systems, authority table, and ADRs. Audits for overlap, authority conflicts, invariant violations, simulation depth compliance, authority flow, and necessity (required vs premature vs redundant) before defining the system. Walks through all 18 template sections interactively (including observability and performance characteristics), pre-filling from context. Runs an identity check after definition (one-sentence, absorption, core-concept tests). Enforces authority registration as a gate when owned state is defined. Registers in both `design/systems/_index.md` and the design doc System Design Index. When `--split-from` is provided, also updates the parent system's Non-Responsibilities and dependency tables.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `system-name` | No | Name for the system. If omitted, asks interactively. |
| `--split-from` | No | SYS-### ID of a parent system being split. Pre-fills context from parent. |
| `--trigger` | No | ADR-### or KI:keyword that motivated the new system. Reads the trigger for context. |

**Examples**

    /scaffold-seed systems --single mood-resolution
    /scaffold-seed systems --single task-scheduling --split-from SYS-005
    /scaffold-seed systems --single zone-management --trigger ADR-018
    /scaffold-seed systems --single

**See Also**

`/scaffold-seed systems`, `/scaffold-fix systems`, `/scaffold-iterate systems`

---

### /scaffold-seed specs --single

Create a behavior spec with automatic ID assignment.

**Synopsis**

    /scaffold-seed specs --single [spec-name]

**Description**

Creates a behavior spec at `specs/SPEC-###-<name>.md` with automatic sequential ID assignment. Reads the spec template, parent slice, parent system design, state transitions, and all ADRs for impact check. Pre-fills from system design where possible (Behavior from Player Actions, Edge Cases from system Edge Cases). Walks through Summary, Preconditions, Behavior, Postconditions, Edge Cases, and Acceptance Criteria. Registers in `specs/_index.md` and parent slice's table.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `spec-name` | No | Name for the spec. If omitted, asks interactively. |

**Examples**

    /scaffold-seed specs --single player-attack
    /scaffold-seed specs --single item-pickup
    /scaffold-seed specs --single

**See Also**

`/scaffold-seed specs`, `/scaffold-seed tasks --single`

---

### /scaffold-seed tasks --single

Create an implementation task with automatic ID assignment.

**Synopsis**

    /scaffold-seed tasks --single [task-name]

**Description**

Creates an implementation task at `tasks/TASK-###-<name>.md` with automatic sequential ID assignment. Reads the task template, parent spec, parent system, engine docs, signal registry, entity components, and all ADRs for impact check. Pre-fills implementation steps from spec Behavior, translating to engine patterns. Walks through Objective, Steps, Files Affected, Verification, and Notes. Registers in `tasks/_index.md` and parent slice's Tasks table.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `task-name` | No | Name for the task. If omitted, asks interactively. |

**Examples**

    /scaffold-seed tasks --single implement-attack-resolution
    /scaffold-seed tasks --single wire-inventory-ui
    /scaffold-seed tasks --single

**See Also**

`/scaffold-seed tasks`, `utils.py complete`

---

## Bulk Seed

Skills for bulk-populating multiple documents from source documents. All bulk seed skills present proposed content for user confirmation and set Status to Draft.

---

### /scaffold-seed style

Seed all 6 Step 5 visual/UX docs from upstream context.

**Synopsis**

    /scaffold-seed style

**Description**

Reads the design doc, system designs, and supporting docs to seed `style-guide.md`, `color-system.md`, `ui-kit.md`, `interaction-model.md`, `feedback-system.md`, and `audio-direction.md` in 6 phases. Auto-writes high-confidence sections directly, tags medium-confidence sections with rationale in the changelog, and leaves low-confidence sections as TODOs. Only pauses for user confirmation on ambiguous style direction, competing visual interpretations, major UX model choices, or decisions that would materially change downstream docs. Skips already-authored docs. Reports confidence breakdown, assumptions made, unresolved questions, and cross-doc tensions.

**Examples**

    /scaffold-seed style

---

### /scaffold-fix style

Mechanical cleanup for all 6 Step 5 visual/UX docs.

**Synopsis**

    /scaffold-fix style [--target doc.md] [--iterate N]

**Description**

Formatter and linter for Step 5 docs: style-guide, color-system, ui-kit, interaction-model, feedback-system, and audio-direction. Auto-fixes structural issues (missing sections, template text, terminology drift, token normalization, hex formatting, duplicate entries). Detects design signals (tone mismatches, component gaps, priority conflicts, scope creep, boundary violations) for adversarial review. Enforces cross-doc consistency: style-guide → color-system → ui-kit, interaction-model ↔ feedback-system, audio-direction derives priority from feedback-system. Supports `--target` for single-doc focus (cross-doc checks still run, only target is edited). Iterates until clean, human-only, stable, or limit reached.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `--target` | No | Single doc to fix (e.g., `style-guide.md`, `ui-kit.md`). Omit to fix all 6. |
| `--iterate N` | No | Max passes (default: 10). |

**Examples**

    /scaffold-fix style
    /scaffold-fix style --target ui-kit.md
    /scaffold-fix style --target feedback-system.md --iterate 5

**See Also**

`/scaffold-seed style`, `/scaffold-iterate style`

---

### /scaffold-iterate style

Adversarial per-topic review of all 6 Step 5 visual/UX docs.

**Synopsis**

    /scaffold-iterate style [--target doc.md] [--topics "1,2,5"] [--focus "concern"] [--iterations N]

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

    /scaffold-iterate style
    /scaffold-iterate style --target feedback-system.md
    /scaffold-iterate style --topics "5,7" --focus "priority hierarchy"
    /scaffold-iterate style --signals "tone mismatch, component gap"

**See Also**

`/scaffold-fix style`, `/scaffold-seed style`

---

### /scaffold-seed systems

Seed glossary and system stubs from the design doc.

**Synopsis**

    /scaffold-seed systems

**Description**

Reads the completed design doc and bulk-seeds the glossary and system design stubs. Phase 1 extracts candidate glossary terms. Phase 2 identifies systems from Player Verbs, Core Loop, Meta Loop, and Failure States. Phase 3 bulk-creates system files with SYS-### IDs, pre-filling Purpose and Player Intent. Registers in both system index and design doc.

**Examples**

    /scaffold-seed systems

**See Also**

`/scaffold-fix systems`, `/scaffold-iterate systems`

---

### /scaffold-seed references

Seed all 7 reference docs from system designs.

**Synopsis**

    /scaffold-seed references

**Description**

Reads all completed system designs and bulk-populates 7 companion docs in order: authority table, interface contracts, state transitions, entity components, resource definitions, signal registry, and balance parameters. Each phase presents proposed entries to user for confirmation. Reports what was added and flags any gaps (systems that didn't contribute, orphaned references).

**Examples**

    /scaffold-seed references

**See Also**

`/scaffold-fix references`, `/scaffold-iterate references`

---

### /scaffold-seed engine

Select engine, then seed all 5 engine docs.

**Synopsis**

    /scaffold-seed engine

**Description**

Asks which engine the project uses (Godot 4, Unity, Unreal 5, or custom), then creates all 5 engine docs from templates with engine-specific pre-filled conventions. Reads design, style, and UI docs for context. Creates `[engine]-coding`, `-ui`, `-input`, `-scene-architecture`, and `-performance` docs. Updates the engine index.

**Examples**

    /scaffold-seed engine

**See Also**

`/scaffold-fix engine`, `/scaffold-iterate engine`

---

### /scaffold-seed input

Seed all 5 input docs from the design doc.

**Synopsis**

    /scaffold-seed input

**Description**

Reads the completed design doc and bulk-seeds all 5 input documents in 5 sequential phases. Phase 1 extracts player verbs and proposes action-map entries with namespaces. Phase 2 derives input philosophy from the design doc's Input Feel and Accessibility sections. Phase 3 proposes default keyboard/mouse bindings from the action-map. Phase 4 proposes default gamepad bindings. Phase 5 proposes UI navigation model and focus flow from the action-map and UI kit. Presents each phase to user for confirmation; writes confirmed content only.

**Examples**

    /scaffold-seed input

**See Also**

`/scaffold-fix style`, `/scaffold-seed input`

---

### /scaffold-seed slices

Seed slice stubs from phases, systems, and interfaces.

**Synopsis**

    /scaffold-seed slices

**Description**

Reads all phases, system designs, and interface contracts to bulk-create vertical slice stubs. Identifies slice candidates by grouping In Scope items into end-to-end experiences. Presents all candidates to user for confirmation. Creates SLICE-### files with pre-filled Goals, Integration Points from `interfaces.md`, and suggested specs. Registers in `slices/_index.md`.

**Examples**

    /scaffold-seed slices

**See Also**

`/scaffold-seed slices --single`

---

### /scaffold-seed specs

Seed spec stubs from slices, systems, and state transitions.

**Synopsis**

    /scaffold-seed specs

**Description**

Reads all slices, system designs, and state transitions to bulk-create behavior spec stubs. Extracts spec candidates from slice Specs Included tables and system Player Actions. Checks ADRs for behavior changes. Presents all candidates to user for confirmation. Creates SPEC-### files with pre-filled Summary, Behavior, Edge Cases, and Acceptance Criteria. Registers in `specs/_index.md` and slice tables.

**Examples**

    /scaffold-seed specs

**See Also**

`/scaffold-seed specs --single`

---

### /scaffold-seed tasks

Seed task stubs from specs, engine docs, and signal registry.

**Synopsis**

    /scaffold-seed tasks

**Description**

Reads all specs, engine docs, and signal registry to bulk-create implementation task stubs. Translates each spec to implementation tasks using engine patterns. Determines task ordering within slices (foundational files → core logic → wiring → UI/feedback). Checks ADRs for implementation approach changes. Presents all candidates to user for confirmation. Creates TASK-### files with pre-filled Objective, Steps, and Files Affected. Registers in `tasks/_index.md` and slice Tasks tables.

**Examples**

    /scaffold-seed tasks

**See Also**

`/scaffold-seed tasks --single`


## Complete

Mark planning-layer documents as Complete with automatic upward rippling.

---

### /scaffold-complete

Mark a planning doc as Complete; ripple status upward through parents.

**Synopsis**

    utils.py complete [document-path|ID]

**Description**

Marks planning-layer documents (tasks, specs, slices, phases) as Complete with automatic upward rippling. Applies only to the planning layer — design, style, reference, engine, and theory docs use Approved status and are not eligible.

For tasks: direct Complete (leaf nodes, no children check). For specs, slices, and phases: verifies all children are Complete first (specs check tasks, slices check specs, phases check slices). Sets document status to Complete, then ripples upward — if the target's parent now has all children Complete, auto-marks the parent Complete and continues up the hierarchy. Stops rippling when a parent still has incomplete children. Idempotent: already-Complete docs report status and do nothing.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `document-path\|ID` | No | Document to complete (e.g., `TASK-001`, `SPEC-003`, or file path). If omitted, asks interactively. |

**Examples**

    utils.py complete TASK-001
    utils.py complete SPEC-003
    utils.py complete phases/P1-001-foundation.md
    /scaffold-complete

**See Also**

`/scaffold-iterate task`, `utils.py complete`

---

## Edit

Targeted edits to any scaffold document with automatic cross-reference updates.

---

### /scaffold-update-doc

Add, remove, or modify entries in any scaffold document.

**Synopsis**

    direct file editing [doc-name|path]

**Description**

Makes targeted edits to any scaffold document (add, remove, or modify entries or sections). Identifies the target by doc-name, SYS-### ID, or file path. Asks for the action (Add/Remove/Modify) if not specified. For table docs: validates format, maintains ordering (alphabetical for glossary, grouped for balance params). For section docs: replaces TODOs with content. For state machines: manages blocks. Handles complex edits (issue tracking, state machines).

Updates cross-references automatically: glossary term renames propagate, system add/remove/rename updates both indexes, signal/entity/resource changes check related docs. Confirms proposed edit before writing. Reports what changed and any cross-references flagged for manual attention. Never silently breaks references.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `doc-name\|path` | No | Target document (e.g., `glossary`, `SYS-001`, or file path). If omitted, asks interactively. |

**Examples**

    direct file editing glossary
    direct file editing SYS-001
    direct file editing reference/signal-registry.md
    /scaffold-update-doc

---

### /scaffold-sync-glossary

Scan scaffold docs for domain terms missing from the glossary.

**Synopsis**

    utils.py sync-glossary [--scope all|design|systems|references|style|input] [--dry-run]

**Description**

Scans scaffold docs for domain terms that should be in the glossary but aren't. Extracts candidates from structured doc fields with source weighting (Strong vs Advisory). Normalizes variants (case, hyphens, plurals) and deduplicates. Applies a glossary worthiness gate (cross-layer usage, player-facing, authority-significant, disambiguating). Checks for ambiguity with existing terms (near-equivalents, prefix variants, cross-layer confusion). Assigns confidence tiers (High/Medium/Low). Presents candidates with per-term decisions: Canonical (new term), Alias (redirect to existing), NOT (discouraged synonym), or Reject. Also detects stale glossary terms no longer referenced in current docs. Blocks Draft-only provisional terms until upstream stabilizes.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `--scope` | No | Which doc layers to scan. Default: `all`. Options: `design`, `systems`, `references`, `style`, `input`. Comma-separated for multiple. |
| `--dry-run` | No | Report candidate terms without writing anything. |

**Examples**

    /scaffold-sync-glossary
    utils.py sync-glossary --scope references
    utils.py sync-glossary --scope style,input
    utils.py sync-glossary --dry-run

**See Also**

`/scaffold-seed systems` (initial glossary seeding), `/scaffold-validate` (glossary coverage check), `direct file editing glossary` (manual edits)

---

## Validate

Cross-reference validation across the entire scaffold.

---

### /scaffold-validate

Run cross-reference validation across all scaffold documents.

**Synopsis**

    /scaffold-validate

**Description**

Runs `validate.py` with per-scope YAML configs to check structural integrity and referential integrity across all scaffold documents. Normalizes markdown formatting, then runs deterministic checks: broken references, missing registrations, glossary NOT-column violations, orphaned entries, section structure, content health, cross-doc consistency, and more. Supports scoped validation (`--scope refs|design|systems|foundation|roadmap|phases|slices|specs|tasks|engine|style|input|all`).

Presents results as a summary table with PASS/FAIL per check and lists each failing issue with file, line, and message. Suggests specific fixes for each issue. Read-only — does not modify any files.

**Examples**

    /scaffold-validate

**See Also**

direct file editing

---

## Playtest

Skills for capturing and analyzing playtester feedback. Observations are logged with `/scaffold-playtest log` and analyzed with `/scaffold-playtest review`.

---

### /scaffold-playtest log

Log playtester observations into the feedback tracker.

**Synopsis**

    /scaffold-playtest log [session-type]

**Description**

Captures playtester observations into `decisions/playtest-feedback.md`. Creates or identifies a playtest session, then walks through observations one at a time — Type, Observation, System/Spec, Severity, Frequency. Checks for duplicates before adding (aggregates frequency if the same issue is already logged). After all observations are entered, scans for entries with 3+ reports and prompts to promote them to Patterns per the Rule of Three. Reports entries logged, duplicates merged, and patterns promoted.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `session-type` | No | Session type hint (e.g., `in-person`, `remote`, `self-play`). If omitted, asks interactively. |

**Examples**

    /scaffold-playtest log in-person
    /scaffold-playtest log remote
    /scaffold-playtest log

**See Also**

`/scaffold-playtest review`, direct file editing

---

### /scaffold-playtest review

Analyze playtest feedback patterns with severity x frequency grid.

**Synopsis**

    /scaffold-playtest review

**Description**

Read-only analysis of `decisions/playtest-feedback.md`. Groups feedback by system to identify hot spots, classifies entries into a severity x frequency priority grid (ACT NOW / WATCH CLOSELY / MONITOR / NOTE & MOVE ON), recommends actions for high-priority entries, cross-references with known issues, design debt, and ADRs for overlaps, checks for stale entries, and produces a delight inventory of positive observations to protect. Does not modify any files.

**Examples**

    /scaffold-playtest review

**See Also**

`/scaffold-playtest log`, `/scaffold-seed phases --single`



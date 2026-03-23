# CLAUDE.md

This project uses ClaudeScaffold — a document-driven pipeline for game development. Every design decision, system behavior, and implementation constraint lives in `scaffold/` as a versioned markdown file with a clear authority rank.

## Rules

1. **Document authority is law.** When documents conflict, the higher-ranked document wins. Code must never "work around" higher-level intent. If an implementation would violate a design document, the implementation is wrong — file an ADR via `/scaffold-file-decision --type adr` to change the document instead.
2. **Design defines WHAT, engine defines HOW.** Documents in `scaffold/design/` describe what the game is. Documents in `scaffold/engine/` describe how to build it. Never mix layers.
3. **Single writer per variable.** Every piece of game data has exactly one owning system defined in `scaffold/design/authority.md`. No system may write to another system's data without an ADR filed via `/scaffold-file-decision --type adr`.
4. **Use canonical terminology.** Terms defined in `scaffold/design/glossary.md` are mandatory. Use the exact term — never synonyms from the NOT column.
5. **Systems are behavior, not implementation.** System designs in `scaffold/design/systems/` describe player-visible behavior. No signals, methods, nodes, or class names in system docs.
6. **Theory informs, never dictates.** Documents in `scaffold/theory/` provide advisory context. Read them when creating or reviewing, but they carry no authority.
7. **ADRs are the feedback mechanism.** When implementation conflicts with design, file an ADR via `/scaffold-file-decision --type adr`. ADRs feed back into upcoming phases, specs, and tasks. Never silently deviate from the plan.
8. **Keep VERSION.md updated.** After every meaningful commit (task completion, doc creation, system changes, bug fixes), bump the PATCH segment in `VERSION.md` and add a changelog entry. Do not batch — bump after each commit. See the Project Version section below for format rules.

## Retrieval Protocol

Never load entire directories. Follow this protocol:

1. Start at `scaffold/_index.md` to locate the correct directory.
2. Open the directory's `_index.md` to find the specific document.
3. Read only the document(s) you need.
4. If two documents conflict, the higher-authority document wins (see `scaffold/doc-authority.md`).

## Authority Chain (highest wins)

| Rank | Document | Layer |
|------|----------|-------|
| 1 | `design/design-doc.md` | Canon — core vision |
| 2 | `design/style-guide.md`, `color-system.md`, `ui-kit.md`, `glossary.md`, `interaction-model.md`, `feedback-system.md`, `audio-direction.md` | Canon — visual identity, terminology, interaction, feedback, audio |
| 3 | `inputs/*` | Canon — input actions and bindings |
| 4 | `design/architecture.md`, `design/interfaces.md`, `design/authority.md` | Canon — engineering conventions, contracts, data ownership |
| 5 | `design/systems/SYS-###`, `design/state-transitions.md` | Canon — systems, states |
| 6 | `reference/*` | Reference — data tables |
| 7 | `phases/roadmap.md`, `phases/PHASE-###` | Scope — roadmap and phase gates |
| 8 | `slices/SLICE-###` | Integration — vertical slice contracts |
| 9 | `specs/SPEC-###` | Behavior — atomic specs |
| 10 | `engine/*` | Implementation — engine constraints |
| 11 | `tasks/TASK-###` | Execution — implementation steps |
| — | `theory/*` | Advisory only — no authority |
| — | `decisions/*` | Pipeline influence — drives changes to ranked docs (see `scaffold/doc-authority.md` Decision Influence Model) |

## Key Directories

- `scaffold/design/` — What the game is: vision, style, colors, UI, glossary, systems, interfaces, authority, states
- `scaffold/inputs/` — Player input definitions: action maps, bindings, navigation, input philosophy
- `scaffold/reference/` — Canonical data tables: signals, entities, resources, balance
- `scaffold/decisions/` — ADRs, known issues, design debt, playtest feedback
- `scaffold/phases/` — Roadmap and phase scope gates
- `scaffold/specs/` — Atomic behavior specs tied to slices
- `scaffold/tasks/` — Implementation tasks tied to specs
- `scaffold/slices/` — Vertical slice contracts within phases
- `scaffold/engine/` — Engine-specific constraints (seeded from templates)
- `scaffold/theory/` — Advisory reference: game design, UX, architecture patterns (no authority)
- `scaffold/decisions/review/` — Adversarial review logs from `/scaffold-iterate`
- `scaffold/assets/` — All production art and audio, organized by entity (entities/, ui/, environment/, music/, shared/, concept/, promo/)
- `scaffold/templates/` — Templates for all document types and engine docs

## When Creating or Modifying Systems

- **Use `/scaffold-seed systems` to create systems from the design doc.** For individual systems, use `/scaffold-new-system`. Both use the template, assign IDs, and register in indexes automatically.
- If creating manually: use the template at `scaffold/templates/system-template.md`, assign sequential SYS-### IDs (never skip or reuse), and register in both `scaffold/design/systems/_index.md` AND the System Design Index in `scaffold/design/design-doc.md`.
- Write in player-visible behavior only. Technical contracts belong in `scaffold/design/interfaces.md` and `scaffold/reference/signal-registry.md`.

## When Planning (Phases, Slices, Specs, Tasks)

- Follow the order: Roadmap → Phases → Slices → Specs → Tasks.
- **Use seed skill to create planning docs:** `/scaffold-seed phases`, `/scaffold-seed slices`, `/scaffold-seed specs`, `/scaffold-seed tasks`. For individual docs, use `/scaffold-new-phase`, `/scaffold-new-slice`, `/scaffold-new-spec`, `/scaffold-new-task`.
- Before creating a phase, spec, or task, read all ADRs filed during prior work. ADRs may change scope.
- Before creating a phase, read `scaffold/decisions/playtest-feedback/` for Pattern-status entries. Playtest patterns may affect phase scope alongside ADRs.
- Slices define vertical end-to-end chunks within a phase. Specs define behavior within a slice. Tasks implement specs.
- Specs describe BEHAVIOR (what it does). Tasks describe IMPLEMENTATION (how to build it in the engine).
- After completing a phase, follow the Phase Transition Protocol in `scaffold/phases/roadmap.md` to update the roadmap.

## Document Status

Every scaffold document carries a `> **Status:**` field in its blockquote header. Values: `Draft | Review | Approved | Complete | Deprecated`.

- **Draft** — set automatically when a document is created (via templates and create/seed skills).
- **Review** — set manually by the user when the document is ready for adversarial review.
- **Approved** — set automatically by `/scaffold-iterate` after a successful adversarial review (consensus reached, no unresolved HIGH issues).
- **Complete** — set by `/scaffold-complete` when implementation is done and verified. Applies to planning-layer docs only (phases, slices, specs, tasks). Ripples upward: when all tasks for a spec are Complete, the spec becomes Complete, and so on through slices and phases.
- **Deprecated** — set via ADR (filed with `/scaffold-file-decision --type adr`) when a document is no longer active. The document remains in its directory (IDs are permanent) but reviews flag references to it.

ADRs use their own status lifecycle (`Proposed | Accepted | Deprecated | Superseded`) and are not part of this system.

### Document Date Tracking

Every scaffold document carries `> **Created:**`, `> **Last Updated:**`, and `> **Changelog:**` fields in its blockquote header (ADRs use `> **Date:**` instead of `> **Created:**`).

**When creating a document** (seed, new, init skills): set `Created` and `Last Updated` to today's date. Add an initial Changelog entry: `- YYYY-MM-DD: Created.`

**When editing a document** (fix, revise, iterate, triage, approve, complete, update-doc, implement-task, code-review skills): update `Last Updated` to today's date. Append a Changelog entry describing what changed and **which decision doc triggered the change**: `- YYYY-MM-DD: [brief description] ([decision doc reference]).` Keep entries concise — one line per change, not per line edited. The decision doc reference closes the traceability loop: decision docs point to which ranked docs changed, ranked docs point back to which decision doc caused the change.

**Changelog entry examples:**
- `- 2026-03-18: Created.`
- `- 2026-03-19: Fixed authority.md alignment — added NeedsSystem as mood reader (REVISION-references-2026-03-19).`
- `- 2026-03-20: Status → Approved after iterate-spec pass (ITERATE-spec-SPEC-042-2026-03-20).`
- `- 2026-03-21: Resolved constrained TODO — tick model locked in architecture.md (ADR-004).`
- `- 2026-03-22: Added save format versioning section (KI-011 resolution).`
- `- 2026-03-23: Narrowed scope — removed expedition system (DD-005 payoff, TRIAGE-SLICE-009-2026-03-23).`

**Do not back-fill dates on existing docs.** Documents created before this rule will gain these fields naturally when next edited by a skill. Skills should add the fields if they're missing during any edit pass.

### Document Influence Map

Before creating or revising any scaffold document, check the **Document Influence Map** in `scaffold/doc-authority.md` to identify what upstream docs should be read as context. The map defines "Influenced By" (what to read) and "Influences" (what reads this doc) for every document type. Skills with explicit Context Files tables may be a subset — the influence map is the complete reference. When in doubt, read the map.

## Workflow

Follow the step-by-step recipe in `scaffold/WORKFLOW.md` for the full 24-step pipeline from design doc to implementation.

## External Review Setup

The `/scaffold-iterate` skill uses an external LLM for adversarial review via `scaffold/tools/iterate.py` (which calls `scaffold/tools/adversarial-review.py`). Configuration lives in `scaffold/tools/review_config.json`:

- **Primary provider:** Set `"provider"` (default: `"openai"`).
- **Fallback chain:** Set `"fallback_order"` (default: `["openai", "anthropic"]`). If the primary provider fails with a billing/quota error, the script automatically tries the next provider. If all providers are exhausted, iterate skills fall back to self-review (Claude reviews directly, weaker but functional).
- **API keys:** Set `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` as environment variables or in `scaffold/.env`.
- **Formatting pass:** `/scaffold-validate` runs a markdown formatting pass (whitespace, blank lines, heading spacing, table alignment) before validation checks. This normalizes all scaffold docs automatically.

## When Resolving Conflicts

- Higher-ranked document always wins.
- **Always use `/scaffold-file-decision` to file decision documents.** This is the canonical way to create ADRs, Known Issues, and Design Debt entries — it assigns sequential IDs, fills templates, registers in indexes, and cross-references affected documents.
  - ADR (architecture decision): `/scaffold-file-decision --type adr "title"`
  - KI (known issue): `/scaffold-file-decision --type ki "title"`
  - DD (design debt): `/scaffold-file-decision --type dd "title"`
- Do not manually create ADR/KI/DD files or append to known-issues.md / design-debt.md directly.

## Project Version

The project version is tracked in `VERSION.md` in the project root. Format: `MAJOR.PHASE.SLICE.PATCH`

| Segment | When to bump | Examples |
|---------|-------------|----------|
| **MAJOR** | Full release / ship | 1.0.0.0 — v1 release |
| **PHASE** | Phase completion (`/scaffold-complete` on a phase) | 0.1.0.0 — Phase 1 complete |
| **SLICE** | Slice completion (`/scaffold-complete` on a slice) | 0.1.1.0 — first slice of Phase 1 complete |
| **PATCH** | Task completion, bug fixes, doc creation, any other incremental work | 0.1.1.1 — first patch after slice |

**Rules:**
- Bump PATCH after every meaningful commit (task completion, doc creation, bug fix).
- Bump SLICE and reset PATCH to 0 when a slice is completed.
- Bump PHASE and reset SLICE + PATCH to 0 when a phase is completed.
- Bump MAJOR and reset all others to 0 on a full release.
- When bumping the version, update the `**Current:**` line and add a new changelog entry.
- Changelog entries use the format: `### X.X.X.X — Short Title` followed by a bullet list of changes.
- Keep entries concise — one bullet per meaningful change, not per file edited.
- Group related changes under a single version bump (e.g., don't bump PATCH three times in one commit).

**VERSION.md vs doc changelogs:** Individual scaffold docs have their own `Changelog` fields tracking per-file edits and which decision doc caused the change. `VERSION.md` is different — it is the **project-level changelog** that tells the story of how the project evolved over time. Write entries at the project level: what milestone was reached, what capability was added, what was fixed, what shifted. Not which files were touched — that's what doc changelogs and git history are for.

**Changelog entry categories** — prefix each bullet with a category tag:
- `[Added]` — new features, systems, docs, capabilities
- `[Changed]` — modifications to existing behavior or design decisions
- `[Fixed]` — bug fixes, issue resolutions, corrections
- `[Removed]` — removed features, deprecated systems, descoped content
- `[Balanced]` — tuning changes, balance parameter adjustments
- `[Resolved]` — closed known issues, addressed ADR feedback, resolved design debt

## Cross-Reference Checklist

When creating or modifying scaffold documents, check and update these related files as appropriate. Most of these are handled automatically by skills, but manual edits should follow the same discipline.

### Design Layer (Steps 1–3)

| When you change... | Also update... |
|---------------------|---------------|
| `design/design-doc.md` (Core Fantasy, Pillars, Invariants) | `design/style-guide.md` tone registers, `design/glossary.md` if new terms introduced |
| `design/design-doc.md` System Design Index | `design/systems/_index.md` — must match bidirectionally |
| `design/systems/SYS-###` (new system) | `design/systems/_index.md`, `design/design-doc.md` System Design Index, `design/authority.md` (owned state), `design/interfaces.md` (if it interacts with other systems) |
| `design/systems/SYS-###` (Owned State changed) | `design/authority.md`, `reference/entity-components.md` |
| `design/systems/SYS-###` (dependencies/consequences changed) | `design/interfaces.md`, `reference/signal-registry.md` |
| `design/systems/SYS-###` (State Lifecycle changed) | `design/state-transitions.md`, `reference/enums-and-statuses.md` |
| `design/architecture.md` | Engine docs that implement the changed section (scene-architecture, simulation-runtime, coding-best-practices) |
| `design/authority.md` (ownership changed) | `reference/entity-components.md` Authority column |
| `design/interfaces.md` (new contract) | `reference/signal-registry.md` if Realization Path is signal/intent |
| `design/state-transitions.md` (states added) | `reference/enums-and-statuses.md`, `design/color-system.md` (state tokens) |
| `design/glossary.md` (new term or NOT-column entry) | All docs — validate checks compliance |

### Visual/UX Layer (Step 5)

| When you change... | Also update... |
|---------------------|---------------|
| `design/style-guide.md` (tone, pillars) | `design/color-system.md` palette mood, `design/audio-direction.md` mood |
| `design/color-system.md` (tokens added/renamed) | `design/ui-kit.md` token references, `design/feedback-system.md` visual column |
| `design/ui-kit.md` (components added/removed) | `design/interaction-model.md` if interactive, `design/feedback-system.md` UI column |
| `design/interaction-model.md` (actions added) | `design/feedback-system.md` Event-Response Table, `design/ui-kit.md` affordances |
| `design/feedback-system.md` (events added) | `design/audio-direction.md` sound categories, `design/color-system.md` if new priority tokens needed |
| `design/feedback-system.md` (priority hierarchy changed) | `design/audio-direction.md` hierarchy must match |

### Reference Layer (Step 3 data)

| When you change... | Also update... |
|---------------------|---------------|
| `reference/entity-components.md` (new entity) | `design/style-guide.md` visual description, `design/ui-kit.md` display component |
| `reference/resource-definitions.md` (new resource) | `design/ui-kit.md` resource representation |
| `reference/signal-registry.md` (new signal) | `design/feedback-system.md` Event-Response Table if player-visible |
| `reference/balance-params.md` (new parameter) | Specs and tasks that use the parameter |

### Planning Layer (Steps 7–11)

| When you change... | Also update... |
|---------------------|---------------|
| `phases/roadmap.md` | `phases/_index.md` must match Phase Overview |
| `phases/PHASE-###` (new phase) | `phases/_index.md`, `phases/roadmap.md` Phase Overview and Capability Ladder |
| `slices/SLICE-###` (new slice) | `slices/_index.md`, parent phase file Slice Strategy section |
| `specs/SPEC-###` (new spec) | `specs/_index.md`, parent slice Specs table |
| `tasks/TASK-###` (new task) | `tasks/_index.md`, parent slice Tasks table |
| Any planning doc status change | Filename suffix must match (`_draft`, `_approved`, `_complete`), parent tables must reflect new status |

### Decision Layer

| When you change... | Also update... |
|---------------------|---------------|
| `decisions/architecture-decision-record/ADR-###` accepted | The upstream doc the ADR modifies, `VERSION.md` changelog |
| `decisions/known-issues/KI-###` resolved | The doc that was blocked, remove blocking reference |
| `decisions/design-debt/DD-###` paid off | The affected docs, `VERSION.md` changelog |
| Task/spec/slice/phase completed | `VERSION.md` — bump appropriate version segment |

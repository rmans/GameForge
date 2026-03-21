# ClaudeScaffold — Installation

This is the installable overlay. Copy its contents into any game project to give Claude Code a structured document pipeline, strict design authority, and 77 skills that automate the workflow from concept to code.

## What Gets Installed

```
your-project/
├── .claude/skills/       ← 77 slash commands (create, seed, fix, iterate, revise, approve, implement, art, audio)
├── scaffold/             ← Document pipeline with indexes and templates
└── CLAUDE.md             ← Rules that tell Claude Code how to use the scaffold
```

**`CLAUDE.md`** — Teaches Claude Code the scaffold rules: document authority, layer separation, retrieval protocol, and conflict resolution. This is what makes Claude follow the pipeline instead of guessing.

**`scaffold/`** — A structured document hierarchy with 11 authority ranks. Every design decision, style rule, system behavior, interface contract, and implementation constraint has a home. Start at `scaffold/_index.md` — it's the master entry point.

**`.claude/skills/`** — 77 slash commands that automate document creation, bulk seeding, mechanical fixes, adversarial iteration, revision, approval gates, implementation, art/audio generation, completion tracking, and editing. Skills read higher-authority documents to pre-fill lower ones, check ADRs before scoping new work, and cross-reference everything.

## Prerequisites

- [Claude Code CLI](https://claude.ai/code)
- A game project (new or existing)

## Install

Download and run — no need to clone the repo:

```bash
# Download claudescaffold.py (once)
curl -O https://raw.githubusercontent.com/rmans/ClaudeScaffold/main/claudescaffold.py

# Install into your project
python claudescaffold.py --install /path/to/your/project
```

## Upgrade

Replace infrastructure (skills, templates, theory, tools) while preserving your design work:

```bash
python claudescaffold.py --upgrade /path/to/your/project
```

Upgrade replaces `theory/`, `templates/`, `tools/`, root index files, and all scaffold skills. Your `design/`, `inputs/`, `reference/`, `decisions/`, `phases/`, `specs/`, `tasks/`, `slices/`, and `engine/` directories are never touched.

## Remove

Remove the scaffold from a project (creates a backup zip first):

```bash
python claudescaffold.py --remove --force /path/to/your/project
```

This backs up everything to `claudescaffold-backup-YYYYMMDD-HHMMSS.zip`, then removes `scaffold/`, scaffold skills, `CLAUDE.md`, and the version stamp. Your `.claude/settings.local.json` and non-scaffold skills are preserved.

## Options

- `--install` — first-time installation
- `--upgrade` — upgrade infrastructure, preserve user content
- `--remove` — remove scaffold (requires `--force`)
- `--version` — print version and exit
- `--branch <name>` — download a specific branch or tag (default: `main`)
- `--dry-run` — preview what would happen without making changes
- `--force` — overwrite existing `scaffold/` (install) or confirm removal (remove)
- `--verbose` — list every file as it's copied

**Manual alternative** (requires cloning the repo):

```bash
git clone https://github.com/rmans/ClaudeScaffold.git
cp -r ClaudeScaffold/Install/.claude /path/to/your/project/
cp -r ClaudeScaffold/Install/scaffold /path/to/your/project/
cp ClaudeScaffold/Install/CLAUDE.md /path/to/your/project/
```

## After Installing

Follow the pipeline in order. Each step builds on the last.

### Phase 1 — Define the game

```
/scaffold-init-design               ← core vision, pillars, mechanics, loops, scope
/scaffold-fix-design                 ← mechanical cleanup
/scaffold-iterate-design             ← adversarial review
/scaffold-validate --scope design    ← gate check
```

Then seed the rest of the pipeline:

```
/scaffold-bulk-seed-systems          ← glossary + system stubs from design doc
/scaffold-bulk-seed-references       ← extract signals, entities, resources, balance params
/scaffold-bulk-seed-engine           ← select your engine, seed engine docs
/scaffold-bulk-seed-style            ← seed style-guide, color-system, ui-kit, interaction-model, feedback-system, audio-direction
/scaffold-bulk-seed-input            ← seed input docs
```

Each seeded layer follows the same stabilization loop: `fix → iterate → validate`.

### Phase 2 — Foundation gate

```
/scaffold-revise-foundation          ← verify Steps 1-6 are stable
/scaffold-fix-cross-cutting          ← resolve cross-document issues
/scaffold-validate --scope foundation
```

### Phase 3 — Plan and build

```
/scaffold-new-roadmap                ← define phases from start to ship
/scaffold-bulk-seed-phases           ← seed phase scope gates from roadmap
/scaffold-approve-phases             ← lifecycle gate for the first phase
```

For each approved phase:

```
/scaffold-bulk-seed-slices           ← seed vertical slices from phase
/scaffold-approve-slices             ← lifecycle gate for the first slice
/scaffold-bulk-seed-specs            ← seed behavior specs from slice
/scaffold-bulk-seed-tasks            ← seed implementation tasks from specs
/scaffold-approve-specs              ← lifecycle gate
/scaffold-approve-tasks              ← lifecycle gate
/scaffold-implement-task             ← code, test, review, complete
```

See `scaffold/WORKFLOW.md` for the full 24-step recipe.

## All 77 Skills

| Category | Skills |
|----------|--------|
| **Init** | `init-design` |
| **Bulk seed** | `bulk-seed-style`, `bulk-seed-systems`, `bulk-seed-references`, `bulk-seed-engine`, `bulk-seed-input`, `bulk-seed-phases`, `bulk-seed-slices`, `bulk-seed-specs`, `bulk-seed-tasks` |
| **Create** | `new-roadmap`, `new-phase`, `new-slice`, `new-spec`, `new-task`, `new-system` |
| **Fix** | `fix-design`, `fix-style`, `fix-systems`, `fix-references`, `fix-engine`, `fix-input`, `fix-roadmap`, `fix-phase`, `fix-slice`, `fix-spec`, `fix-task`, `fix-cross-cutting` |
| **Iterate** | `iterate-design`, `iterate-style`, `iterate-systems`, `iterate-references`, `iterate-engine`, `iterate-input`, `iterate-roadmap`, `iterate-phase`, `iterate-slice`, `iterate-spec`, `iterate-task` |
| **Revise** | `revise-design`, `revise-systems`, `revise-references`, `revise-engine`, `revise-style`, `revise-input`, `revise-foundation`, `revise-roadmap`, `revise-phases`, `revise-slices` |
| **Approve** | `approve-phases`, `approve-slices`, `approve-specs`, `approve-tasks` |
| **Triage** | `triage-specs`, `triage-tasks`, `reorder-tasks` |
| **Implement** | `implement-task`, `build-and-test`, `code-review`, `add-regression-tests` |
| **Complete** | `complete` |
| **Edit** | `update-doc`, `sync-reference-docs`, `sync-glossary` |
| **Validate** | `validate` |
| **Decisions** | `file-decision` |
| **Playtest** | `playtest-log`, `playtest-review` |
| **Art** | `art-concept`, `art-ui-mockup`, `art-character`, `art-environment`, `art-sprite`, `art-icon`, `art-promo` |
| **Audio** | `audio-music`, `audio-sfx`, `audio-ambience`, `audio-voice` |

All skill names are prefixed with `/scaffold-` (e.g., `/scaffold-init-design`).

## Key Directories

| Directory | Layer | What Goes Here |
|-----------|-------|---------------|
| `design/` | Canon (ranks 1–5) | Vision, style, colors, UI, glossary, architecture, interaction model, feedback system, audio direction, systems, interfaces, authority, states |
| `inputs/` | Canon (rank 3) | Action map, key bindings, gamepad bindings, navigation, input philosophy |
| `reference/` | Reference (rank 6) | Signals, entities, resources, balance params, enums/statuses |
| `decisions/` | History | ADRs, known issues, design debt, playtest feedback, cross-cutting findings, code reviews, revision logs, triage logs |
| `phases/` | Scope (rank 7) | Roadmap, phase scope gates |
| `slices/` | Integration (rank 8) | Vertical slice contracts |
| `specs/` | Behavior (rank 9) | Atomic behavior specs |
| `engine/` | Implementation (rank 10) | Engine-specific best practices and constraints |
| `tasks/` | Execution (rank 11) | Implementation tasks |
| `theory/` | Advisory | 16 docs on game design, UX, architecture — no authority |
| `assets/` | Content | All production art and audio — organized by entity (entities/, ui/, environment/, music/, shared/, concept/, promo/) |
| `templates/` | Meta | Templates for all document types |

## Customization

- **Engine layer:** Seeded from templates based on your selected engine. Works with Godot, Unity, Unreal, or any other engine.
- **Design doc:** All sections are prompts with TODO markers. Fill in what applies, skip what doesn't.
- **Templates:** Edit `scaffold/templates/` to match your project's conventions.
- **Theory:** Add your own theory docs to `scaffold/theory/` for domain-specific advisory context.

## Troubleshooting

- Skills require the `scaffold/` directory to exist at the project root.
- If Claude ignores the pipeline, check that `CLAUDE.md` was copied to the project root.
- If documents conflict, the higher-ranked document always wins — see `scaffold/doc-authority.md`.

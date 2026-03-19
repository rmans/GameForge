# ClaudeScaffold

A document-driven pipeline that gives Claude Code long-term memory, strict design authority, and a structured workflow for building games from concept to code.

## The Problem

LLMs forget. Over a long project, Claude Code loses track of design decisions, contradicts earlier choices, drifts from the original vision, and makes up answers when it should be reading a spec. The longer the project runs, the worse it gets.

Ad-hoc prompting doesn't scale. You can't keep saying "remember, the inventory uses slots not weight" in every conversation. And CLAUDE.md files help, but they're flat — there's no hierarchy, no conflict resolution, no pipeline.

## The Solution

ClaudeScaffold installs a structured document pipeline into your project. Instead of relying on conversation memory, Claude Code reads canonical documents that define **what** the game is, **how** it's built, and **what to do next**.

Every design decision, visual style rule, system behavior, interface contract, and implementation constraint lives in a versioned markdown file with a clear authority rank. When documents conflict, the higher-ranked document wins — automatically. Claude Code never has to guess.

**Key properties:**

- **Document authority replaces memory.** Claude reads the design doc, not yesterday's conversation. The source of truth is always a file, never a chat.
- **11-rank precedence chain.** When a system design says one thing and a task says another, the system design wins. No ambiguity.
- **Genre-agnostic design, engine-specific implementation.** The design layer works for any game. The engine layer adapts to Godot, Unity, Unreal, or anything else.
- **ADR feedback loop.** When implementation reality conflicts with the plan, Architecture Decision Records capture why and feed back into upcoming phases, specs, and tasks.
- **Two-loop stabilization.** Every document type follows the same pattern: create → fix → iterate → validate (initial), then revise → fix → iterate → validate (after implementation feedback). Foundation architecture is gated before planning begins.
- **Draft → Review → Approved → Complete lifecycle.** Documents start as `Draft`, move through adversarial review via `/scaffold-iterate-*`, are set to `Approved` by approval gates, and marked `Complete` by `/scaffold-complete` when implementation is done. Completion ripples up from tasks through specs, slices, and phases.
- **Token-efficient retrieval.** Index files in every directory let Claude find what it needs without loading entire folders.
- **72 skills automate the pipeline.** Create, seed, fix, iterate, revise, approve, implement, generate art/audio, and edit documents with slash commands — no manual file wrangling.

## How It Works

### The Pipeline

The scaffold follows a two-loop pipeline from vision to code:

```
OUTER LOOP (architecture stability)
├─ Design → Systems → References → Engine → Visual/UX → Inputs
├─ Foundation Architecture Gate
│
├─ INNER LOOP (per phase, per slice)
│   Roadmap → Phases → Slices → Specs → Tasks → Implementation
│   ↑                                                |
│   └──────── ADR / Triage / Revision Feedback ──────┘
│
└─ Foundation Recheck → next phase
```

1. **Design** — Define the game: vision, pillars, mechanics, loops, scope
2. **Systems** — Design each system as player-visible behavior (no engine code)
3. **References** — Extract data tables: signals, entities, resources, balance params, architecture
4. **Engine** — Define how to build it in your target engine
5. **Visual/UX** — Lock in visual identity, interaction model, feedback system, audio direction
6. **Inputs** — Define player input actions and bindings
7. **Foundation Gate** — Verify Steps 1–6 are architecturally stable before planning
8. **Plan** — Create a roadmap, break it into phases, slice each phase vertically
9. **Spec** — Write atomic behavior specs for each slice
10. **Build** — Create implementation tasks, write code, run adversarial code review
11. **Feedback** — ADRs, triage logs, and revision loops update the roadmap and re-scope upcoming work

Each step has skills that automate it. Each document has a clear authority rank. Nothing is ad-hoc.

### Document Authority

When documents conflict, the higher-ranked document wins. Lower documents conform to higher documents. Code never "works around" higher-level intent.

| Rank | Document | What It Controls |
|------|----------|-----------------|
| 1 | Design doc | Core vision, non-negotiables |
| 2 | Style guide, color system, UI kit, glossary, interaction model, feedback system, audio direction | Visual identity, terminology, interaction, audio |
| 3 | Input docs | Player actions and bindings |
| 4 | Architecture, interfaces, authority table | Engineering conventions, contracts, data ownership |
| 5 | System designs, state machines | Per-system behavior |
| 6 | Reference tables | Signals, entities, resources, balance |
| 7 | Roadmap, phase gates | Scope and milestones |
| 8 | Slice contracts | Vertical integration |
| 9 | Behavior specs | Atomic testable behaviors |
| 10 | Engine docs | Engine-specific constraints |
| 11 | Implementation tasks | How to build each spec |
| — | Theory docs | Advisory only — no authority |

### Layer Separation

Documents are separated into layers. No document may mix layers.

| Layer | Question It Answers | Directory |
|-------|-------------------|-----------|
| Design | What is the game? | `design/` |
| Inputs | How does the player interact? | `inputs/` |
| Reference | What are the canonical data shapes? | `reference/` |
| Decisions | Why did we change the plan? | `decisions/` |
| Phases | What are we building and when? | `phases/` |
| Specs | What should this behavior do? | `specs/` |
| Tasks | How do we implement this spec? | `tasks/` |
| Slices | What proves this phase works end-to-end? | `slices/` |
| Engine | How do we build in this engine? | `engine/` |
| Theory | What do experts recommend? | `theory/` |
| Content | What does the game look/sound like? | `art/`, `audio/` |

### Theory as Advisory Context

The `theory/` directory contains 16 documents covering game design principles, common pitfalls, genre conventions, UX heuristics, color theory, architecture patterns, and more. These are Rank 11 — they carry **no authority**. Skills read them for context when creating and reviewing documents, but they never dictate design decisions. Theory informs; it doesn't override.

## Installation

Download and run the installer — no need to clone the repo:

```bash
# Download claudescaffold.py (once)
curl -O https://raw.githubusercontent.com/rmans/ClaudeScaffold/main/claudescaffold.py

# Install into your project
python claudescaffold.py --install /path/to/your/project

# Upgrade infrastructure (preserves your design work)
python claudescaffold.py --upgrade /path/to/your/project

# Remove scaffold (creates backup zip first)
python claudescaffold.py --remove --force /path/to/your/project
```

Options:
- `--install` — first-time installation into a project
- `--upgrade` — replace infrastructure (skills, templates, theory, tools) while preserving user content
- `--remove` — remove scaffold from the project (requires `--force`, creates backup zip)
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

This gives your project:

```
.claude/skills/       ← 72 Claude Code skills
scaffold/             ← Document pipeline with templates and indexes
CLAUDE.md             ← Instructions that tell Claude Code how to use the scaffold
```

See [Install/README.md](Install/README.md) for full installation details.

## Skills

72 slash commands organized by workflow:

| Category | Skills |
|----------|--------|
| **Init** | `init-design` |
| **Bulk seed (9)** | `bulk-seed-style`, `bulk-seed-systems`, `bulk-seed-references`, `bulk-seed-engine`, `bulk-seed-input`, `bulk-seed-phases`, `bulk-seed-slices`, `bulk-seed-specs`, `bulk-seed-tasks` |
| **Create (5)** | `new-roadmap`, `new-phase`, `new-slice`, `new-spec`, `new-task` |
| **Fix (12)** | `fix-design`, `fix-style`, `fix-systems`, `fix-references`, `fix-engine`, `fix-roadmap`, `fix-phase`, `fix-slice`, `fix-spec`, `fix-task`, `fix-foundation`, `fix-cross-cutting` |
| **Iterate (9)** | `iterate-design`, `iterate-systems`, `iterate-references`, `iterate-engine`, `iterate-roadmap`, `iterate-phase`, `iterate-slice`, `iterate-spec`, `iterate-task` |
| **Revise (8)** | `revise-design`, `revise-systems`, `revise-references`, `revise-engine`, `revise-foundation`, `revise-roadmap`, `revise-phases`, `revise-slices` |
| **Approve (4)** | `approve-phases`, `approve-slices`, `approve-specs`, `approve-tasks` |
| **Triage (3)** | `triage-specs`, `triage-tasks`, `reorder-tasks` |
| **Implement (4)** | `implement-task`, `build-and-test`, `code-review`, `add-regression-tests` |
| **Complete (1)** | `complete` |
| **Edit (2)** | `update-doc`, `sync-reference-docs` |
| **Validate (1)** | `validate` |
| **Playtest (2)** | `playtest-log`, `playtest-review` |
| **Art (7)** | `art-concept`, `art-ui-mockup`, `art-character`, `art-environment`, `art-sprite`, `art-icon`, `art-promo` |
| **Audio (4)** | `audio-music`, `audio-sfx`, `audio-ambience`, `audio-voice` |

All skill names are prefixed with `/scaffold-` (e.g., `/scaffold-init-design`).

### Recommended Workflow

```
1.  /scaffold-init-design              ← fill out the design doc
2.  /scaffold-fix-design               ← mechanical cleanup
3.  /scaffold-iterate-design           ← adversarial review
4.  /scaffold-bulk-seed-systems        ← glossary + system stubs
5.  Fill in each system design
6.  /scaffold-bulk-seed-references     ← populate reference docs
7.  /scaffold-bulk-seed-engine         ← select engine, seed engine docs
8.  /scaffold-bulk-seed-style          ← seed visual/UX docs
9.  /scaffold-revise-foundation        ← verify architecture stability
10. /scaffold-new-roadmap              ← create the project roadmap
11. /scaffold-bulk-seed-phases         ← seed phases from roadmap
12. /scaffold-approve-phases           ← gate first phase
13. Per phase: seed slices → approve → seed specs/tasks → approve → implement
```

See `scaffold/WORKFLOW.md` for the full 24-step recipe.

## Scaffold Structure

```
scaffold/
├── _index.md                        # Master index + retrieval protocol
├── doc-authority.md                 # Precedence rules (ranks 1–11)
├── WORKFLOW.md                      # Step-by-step pipeline recipe (24 steps)
│
├── design/                          # CANON: what the game is
│   ├── design-doc.md                #   Core vision, pillars, loops, mechanics (rank 1)
│   ├── style-guide.md               #   Visual art style (rank 2)
│   ├── color-system.md              #   Color palette and rules (rank 2)
│   ├── ui-kit.md                    #   UI component definitions (rank 2)
│   ├── glossary.md                  #   Canonical terminology + NOT column (rank 2)
│   ├── interaction-model.md         #   Player interaction patterns (rank 2)
│   ├── feedback-system.md           #   Game feel and feedback coordination (rank 2)
│   ├── audio-direction.md           #   Audio philosophy and sound categories (rank 2)
│   ├── architecture.md              #   Engineering conventions (rank 4)
│   ├── interfaces.md                #   System interface contracts (rank 4)
│   ├── authority.md                 #   Data ownership per variable (rank 4)
│   ├── state-transitions.md         #   All state machines (rank 5)
│   └── systems/                     #   Individual system designs (rank 5)
│
├── inputs/                          # CANON: input control definitions (rank 3)
├── reference/                       # Canonical data tables (rank 6)
│
├── decisions/                       # Decision tracking
│   ├── architecture-decision-record/ #   ADRs (ADR-###)
│   ├── known-issues/                #   TBDs, gaps, conflicts (KI-###)
│   ├── design-debt/                 #   Intentional compromises (DD-###)
│   ├── playtest-feedback/           #   Playtester observations (PF-###)
│   ├── cross-cutting-finding/       #   Cross-doc integrity issues (XC-###)
│   ├── code-review/                 #   Adversarial code review logs
│   ├── revision-log/                #   Drift detection records
│   ├── triage-log/                  #   Triage decision records
│   └── review/                      #   Adversarial document review logs
│
├── phases/                          # Scope gates (rank 7)
├── slices/                          # Vertical slice contracts (rank 8)
├── specs/                           # Atomic behavior specs (rank 9)
├── engine/                          # Engine-specific constraints (rank 10)
├── tasks/                           # Implementation steps (rank 11)
├── theory/                          # Advisory only — no authority
├── art/                             # Generated art assets
├── audio/                           # Generated audio assets
├── templates/                       # Document + engine templates (44 total)
└── tools/                           # Scripts and utilities
```

## License

MIT License. See [LICENSE](LICENSE) for details.

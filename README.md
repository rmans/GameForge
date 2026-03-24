# GameForge

A document-driven build system for game development. Python orchestrates, Claude judges, external LLMs review. Design decisions live in versioned markdown with strict authority ranks — not in conversation memory.

## The Problem

LLMs forget. Over a long project, Claude Code loses track of design decisions, contradicts earlier choices, drifts from the original vision, and invents answers when it should be reading a spec. Ad-hoc prompting doesn't scale. CLAUDE.md files help, but they're flat — no hierarchy, no conflict resolution, no pipeline.

## The Solution

GameForge installs a structured document pipeline into your project. Every design decision, system behavior, interface contract, and implementation constraint lives in a versioned markdown file with a clear authority rank. When documents conflict, the higher-ranked document wins. Claude never guesses.

### Architecture

The system is a **deterministic/LLM hybrid**:

- **Python orchestrators** handle control flow, queues, session state, file scanning, dependency graphs, convergence detection, build/test, and completion ripple. Python never forgets steps.
- **Claude** handles one focused judgment call at a time via sub-skills — propose one candidate, adjudicate one issue, write one code step. Claude never sees the full queue.
- **External LLM** (OpenAI/Anthropic) performs adversarial review — catches design weaknesses that self-review misses.
- **YAML configs** define per-layer review questions, mechanical checks, context rules, and coverage criteria. 46 configs across iterate/fix/seed.
- **Hierarchical context** loads only what each review call needs: section extraction instead of whole files, budget-limited, per-heading context selection.

```
Python (orchestration)          Claude (judgment)           External LLM (review)
├── seed.py                     ├── seed-propose            ├── adversarial-review.py
├── local-review.py (fix)       ├── review-adjudicate       └── code-review.py
├── iterate.py                  ├── review-apply
├── review.py (chains fix→iterate→validate)  ├── review-scope-check
├── validate.py                 ├── implement-plan
├── implement.py                ├── implement-code
├── revise.py                   └── seed-verify
├── utils.py (complete, build, sync)
└── context.py (hierarchical context resolution)
```

### Four Propagation Paths

```
1. PRODUCTION (user-driven):     seed → review → approve → implement → complete
2. SIGNAL (feed-forward):        ADR/KI → revise → affected layers → restabilize
3. RIPPLE (automatic):           task✓ → spec✓ → slice✓ → phase✓ → roadmap
4. DEPENDENCY (enforcement):     topo sort, preflight blocks, cycle detection
```

### Document Authority

When documents conflict, the higher-ranked document wins:

| Rank | Document | Controls |
|------|----------|----------|
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

### Pipeline

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

Each step: **seed → review (fix → iterate → validate) → approve**. Review uses per-section context with budget limits. Iterate uses three-pass adversarial review (L3 subsections → L2 sections → L1 document). Mechanical issues auto-apply without adjudication.

### Asset Pipeline

Art and audio flow through the same document chain:

```
Design doc (Entity Presentation) → System designs (Asset Needs)
  → Specs (Asset Requirements) → Task seeding auto-generates art/audio tasks
    → Implement checks if assets exist → auto-completes when delivered
```

Art/audio tasks include file paths, dimensions, and generation prompts built from the style guide and color system. The user creates assets externally and places them at the listed paths.

## Installation

```bash
# Download installer (once)
curl -O https://raw.githubusercontent.com/rmans/GameForge/main/gameforge.py

# Install into your project
python gameforge.py --install /path/to/your/project

# Upgrade infrastructure (preserves your design work)
python gameforge.py --upgrade /path/to/your/project
```

Options: `--install`, `--upgrade`, `--remove --force`, `--version`, `--branch <name>`, `--dry-run`, `--force`, `--verbose`

Install runs meta-validate automatically — checks that all YAML config heading references match actual template headings. Catches config drift at install time.

This gives your project:

```
.claude/skills/       ← 18 Claude Code skills (10 user-facing + 8 sub-skills)
scaffold/             ← Document pipeline with templates, tools, and configs
CLAUDE.md             ← Instructions that tell Claude Code how to use the scaffold
```

## Skills

10 slash commands. Each is a thin dispatcher backed by a Python orchestrator:

| Skill | Orchestrator | What it does |
|-------|-------------|-------------|
| `/scaffold-seed` | seed.py | Dependency-aware document generation. Design layer interviews; other layers propose from upstream docs. Heading extraction, not raw content. |
| `/scaffold-fix` | local-review.py | Mechanical cleanup. Regex/pattern checks in Python, judgment calls routed to Claude. |
| `/scaffold-iterate` | iterate.py | Adversarial review via external LLM. Three-pass (L3→L2→L1). Per-section context with budget. Mechanical issues auto-accept. |
| `/scaffold-review` | review.py | Chains fix → iterate → validate automatically. |
| `/scaffold-revise` | revise.py | Reads ADR/KI/triage signals, classifies one-at-a-time, auto-applies safe changes, escalates dangerous ones. Impact preview before classification. Dispatches scoped restabilization. |
| `/scaffold-validate` | validate.py | Read-only structural gate. Upstream freshness FAIL enforcement. |
| `/scaffold-triage` | — | Resolve human-required issues from review passes. Decision checklists. |
| `/scaffold-implement` | implement.py | One code step at a time. Build/test in Python. Code review via external LLM. Art/audio tasks: check asset delivery, auto-complete. |
| `/scaffold-file-decision` | — | File ADR/KI/DD with cross-references. |
| `/scaffold-playtest` | — | Log sessions and review feedback patterns. |

### Workflow

```
1.  /scaffold-seed design            ← interview: fill out the design doc
2.  /scaffold-review design          ← fix → iterate → validate
3.  /scaffold-seed systems           ← glossary + system stubs from design doc
4.  /scaffold-review systems         ← per-system adversarial review
5.  /scaffold-seed references        ← architecture, authority, interfaces, etc.
6.  /scaffold-seed engine            ← engine convention docs
7.  /scaffold-seed style             ← visual/UX docs
8.  /scaffold-seed input             ← input docs
9.  /scaffold-revise foundation      ← verify architecture stability
10. /scaffold-seed roadmap           ← create project roadmap
11. /scaffold-seed phases            ← seed phases from roadmap
12. /scaffold-approve phases PHASE-001
13. Per phase: seed slices → approve → seed specs/tasks → approve → implement
```

See `scaffold/WORKFLOW.md` for the full pipeline. See `scaffold/FULL-WALKTHROUGH.md` for a complete code-level trace of every command.

## Scaffold Structure

```
scaffold/
├── _index.md                        # Master index + retrieval protocol
├── doc-authority.md                 # Precedence rules (ranks 1–11)
├── WORKFLOW.md                      # Step-by-step pipeline recipe
├── FULL-WALKTHROUGH.md              # Complete code trace: start to finish
├── ART-WORKFLOW.md                  # Art production guidelines
├── AUDIO-WORKFLOW.md                # Audio production guidelines
│
├── design/                          # CANON: what the game is (ranks 1–5)
├── inputs/                          # CANON: input definitions (rank 3)
├── reference/                       # Canonical data tables (rank 6)
├── decisions/                       # ADRs, KIs, design debt, reviews, triage
├── phases/                          # Scope gates (rank 7)
├── slices/                          # Vertical slice contracts (rank 8)
├── specs/                           # Atomic behavior specs (rank 9)
├── engine/                          # Engine-specific constraints (rank 10)
├── tasks/                           # Implementation steps (rank 11)
├── theory/                          # Advisory only — 16 reference docs
├── assets/                          # All production art and audio
├── templates/                       # Document + engine templates
└── tools/                           # Python orchestrators, configs, utilities
    ├── seed.py, iterate.py, local-review.py, review.py, validate.py
    ├── implement.py, revise.py, utils.py, context.py, meta-validate.py
    ├── adversarial-review.py, code-review.py
    └── configs/                     # 46 YAML configs (iterate/, fix/, seed/, validate/, revise/)
```

## License

MIT License. See [LICENSE](LICENSE) for details.

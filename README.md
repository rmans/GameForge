<p align="center">
  <h1 align="center">⚒️ GameForge</h1>
  <p align="center">
    <strong>A document-driven build system for game development.</strong><br>
    Python orchestrates. Claude judges. External LLMs review.<br>
    Design decisions live in versioned markdown with strict authority ranks — not in conversation memory.
  </p>
  <p align="center">
    <a href="#installation">Installation</a> · <a href="#skills">Skills</a> · <a href="#how-it-works">How It Works</a> · <a href="Install/scaffold/FULL-WALKTHROUGH.md">Full Walkthrough</a>
  </p>
</p>

---

## The Problem

LLMs forget. Over a long project, Claude Code loses track of design decisions, contradicts earlier choices, drifts from the original vision, and invents answers when it should be reading a spec. Ad-hoc prompting doesn't scale. CLAUDE.md files help, but they're flat — no hierarchy, no conflict resolution, no pipeline.

## The Solution

GameForge installs a structured document pipeline into your project. Every design decision, system behavior, interface contract, and implementation constraint lives in a versioned markdown file with a clear authority rank. When documents conflict, the higher-ranked document wins. Claude never guesses.

---

## How It Works

### 🏗️ Architecture

The system is a **deterministic/LLM hybrid** with clear responsibility boundaries:

| Layer | Responsibility | Never does |
|-------|---------------|------------|
| **Python orchestrators** | Control flow, queues, session state, dependency graphs, convergence, build/test, completion ripple | Judgment calls, creative writing |
| **Claude (sub-skills)** | One focused judgment at a time — propose, adjudicate, apply, code | Orchestration, remembering state |
| **External LLM** | Adversarial review — catches what self-review misses | Editing files, making decisions |
| **YAML configs** | Per-layer review questions, checks, context rules | — |
| **Context resolver** | Section extraction, budget limits, per-heading loading | — |

```
┌─────────────────────────┐  ┌───────────────────────┐  ┌──────────────────────┐
│   Python (orchestration) │  │   Claude (judgment)    │  │  External LLM        │
│                         │  │                       │  │  (adversarial review) │
│  seed.py                │  │  seed-propose         │  │                      │
│  local-review.py        │◄─┤  review-adjudicate    │  │  adversarial-        │
│  iterate.py        ─────┼──┤  review-apply         │  │    review.py         │
│  review.py              │  │  review-scope-check   │  │  code-review.py      │
│  validate.py            │  │  implement-plan       │  │                      │
│  implement.py           │  │  implement-code       │  │                      │
│  revise.py              │  │  seed-verify          │  │                      │
│  utils.py               │  │                       │  │                      │
│  context.py             │  │                       │  │                      │
└─────────────────────────┘  └───────────────────────┘  └──────────────────────┘
```

### 🔄 Four Propagation Paths

| Path | Trigger | How it works |
|------|---------|-------------|
| **Production** | User command | `seed → review → approve → implement → complete` |
| **Signal** | ADR/KI filed during implementation | `revise → classify signals → auto-apply safe changes → escalate dangerous → restabilize affected layers` |
| **Ripple** | Last child completes | `task✓ → spec✓ → slice✓ → phase✓ → roadmap` (automatic, deterministic) |
| **Dependency** | Execution order | Topo sort, preflight blocks, cycle detection (blocks, does not propagate) |

### 📋 Document Authority

When documents conflict, the higher-ranked document wins. Lower documents conform. Code never "works around" higher-level intent.

| Rank | Document | Controls |
|:----:|----------|----------|
| 1 | Design doc | Core vision, non-negotiables |
| 2 | Style guide · Color system · UI kit · Glossary · Interaction model · Feedback system · Audio direction | Visual identity, terminology, interaction, audio |
| 3 | Input docs | Player actions and bindings |
| 4 | Architecture · Interfaces · Authority table | Engineering conventions, contracts, data ownership |
| 5 | System designs · State machines | Per-system behavior |
| 6 | Reference tables | Signals, entities, resources, balance |
| 7 | Roadmap · Phase gates | Scope and milestones |
| 8 | Slice contracts | Vertical integration |
| 9 | Behavior specs | Atomic testable behaviors |
| 10 | Engine docs | Engine-specific constraints |
| 11 | Implementation tasks | How to build each spec |
| — | Theory docs | Advisory only — no authority |

### 🔁 Pipeline

```
OUTER LOOP (architecture stability)
│
├─ Steps 1–6: Design → Systems → References → Engine → Visual/UX → Inputs
├─ Step 7:    Foundation Architecture Gate
│
├─ INNER LOOP (per phase, per slice)
│   │
│   │  Step 8:  Roadmap
│   │  Step 9:  Phases ──→ approve
│   │  Step 10: Slices ──→ approve
│   │  Step 11: Specs  ──→ approve
│   │  Step 12: Tasks  ──→ approve
│   │  Step 13: Implement ──→ complete ──→ ripple up
│   │     ↑                                    │
│   │     └──── ADR / Triage / Revision ───────┘
│   │
│   └─ Slice done → revise remaining slices → next slice
│
├─ Phase done → revise foundation → revise roadmap → revise phases
└─ Approve next phase → re-enter inner loop
```

> Each step follows the same pattern: **seed → review (fix → iterate → validate) → approve**.
> Review uses per-section context with budget limits. Iterate runs three-pass adversarial review (L3 subsections → L2 sections → L1 document). Mechanical issues auto-apply without adjudication.

### 🎨 Asset Pipeline

Art and audio flow through the same document chain:

```
Design doc                    System designs              Specs
┌─────────────────────┐      ┌──────────────────┐      ┌───────────────────────┐
│ ### Entity           │      │ ### Asset Needs   │      │ ### Asset Requirements │
│ Presentation         │ ───► │                   │ ───► │                       │
│                      │      │ Colonist walk     │      │ | Walk cycle | Sprite │
│ Colonists: 3D,      │      │ cycle, pickaxe    │      │ | ... | Needed |      │
│ walk/run/mine anims  │      │ impact SFX, ...   │      │                       │
└─────────────────────┘      └──────────────────┘      └───────────┬───────────┘
                                                                    │
                                                          seed.py auto-generates
                                                                    │
                                                                    ▼
                                                       ┌───────────────────────┐
                                                       │ TASK-005_art          │
                                                       │                       │
                                                       │ Asset Delivery:       │
                                                       │ | file path | prompt  │
                                                       │                       │
                                                       │ /scaffold-implement   │
                                                       │ checks if files exist │
                                                       │ → auto-completes      │
                                                       └───────────────────────┘
```

---

## Installation

```bash
# Download installer (once)
curl -O https://raw.githubusercontent.com/rmans/GameForge/main/gameforge.py

# Install into your project
python gameforge.py --install /path/to/your/project

# Upgrade infrastructure (preserves your design work)
python gameforge.py --upgrade /path/to/your/project
```

<details>
<summary><strong>All options</strong></summary>

| Option | Description |
|--------|-------------|
| `--install` | First-time installation |
| `--upgrade` | Replace infrastructure, preserve user content |
| `--remove --force` | Remove scaffold (creates backup zip) |
| `--version` | Print version and exit |
| `--branch <name>` | Download specific branch/tag (default: `main`) |
| `--dry-run` | Preview without changes |
| `--force` | Overwrite existing scaffold |
| `--verbose` | List every file |

</details>

Install runs **meta-validate** automatically — checks that all YAML config heading references match actual template headings. Catches config drift at install time.

```
your-project/
├── .claude/skills/       ← 18 skills (10 user-facing + 8 sub-skills)
├── scaffold/             ← Document pipeline + templates + tools + configs
└── CLAUDE.md             ← Instructions for Claude Code
```

---

## Skills

10 slash commands. Each is a thin dispatcher backed by a Python orchestrator:

| Skill | Backed by | Purpose |
|-------|-----------|---------|
| **`/scaffold-seed`** | `seed.py` | Generate docs from upstream context. Design interviews; other layers propose. |
| **`/scaffold-fix`** | `local-review.py` | Mechanical cleanup. Pattern checks in Python, judgment routed to Claude. |
| **`/scaffold-iterate`** | `iterate.py` | Adversarial review via external LLM. Three-pass, per-section context. |
| **`/scaffold-review`** | `review.py` | Chains fix → iterate → validate. |
| **`/scaffold-revise`** | `revise.py` | Signal-driven drift detection. Impact preview → classify → apply → restabilize. |
| **`/scaffold-validate`** | `validate.py` | Structural gate. Upstream freshness enforcement. |
| **`/scaffold-triage`** | — | Resolve human-required issues. Decision checklists. |
| **`/scaffold-implement`** | `implement.py` | One code step at a time. Build/test/review. Art tasks: check delivery. |
| **`/scaffold-file-decision`** | — | File ADR / KI / DD with cross-references. |
| **`/scaffold-playtest`** | — | Log sessions, review feedback patterns. |

### Workflow

```
 1.  /scaffold-seed design            ← interview: define the game
 2.  /scaffold-review design          ← fix → adversarial review → validate
 3.  /scaffold-seed systems           ← system stubs from design doc
 4.  /scaffold-review systems         ← per-system adversarial review
 5.  /scaffold-seed references        ← architecture, authority, interfaces
 6.  /scaffold-seed engine            ← engine convention docs
 7.  /scaffold-seed style             ← visual/UX docs
 8.  /scaffold-seed input             ← input docs
 9.  /scaffold-revise foundation      ← verify architecture stability
10.  /scaffold-seed roadmap           ← project roadmap
11.  /scaffold-seed phases            ← phase scope gates
12.  /scaffold-approve phases PHASE-001
13.  Per phase: seed slices → specs → tasks → approve → implement
```

> See [`scaffold/WORKFLOW.md`](Install/scaffold/WORKFLOW.md) for the full pipeline recipe.
> See [`scaffold/FULL-WALKTHROUGH.md`](Install/scaffold/FULL-WALKTHROUGH.md) for a complete code-level trace.

---

## Scaffold Structure

<details>
<summary><strong>Full directory tree</strong></summary>

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
└── tools/                           # Python orchestrators + configs
    ├── seed.py                      #   Document generation
    ├── iterate.py                   #   Adversarial review orchestration
    ├── local-review.py              #   Mechanical fix orchestration
    ├── review.py                    #   Fix → iterate → validate chain
    ├── validate.py                  #   Structural validation gate
    ├── implement.py                 #   Task implementation pipeline
    ├── revise.py                    #   Drift detection + revision
    ├── utils.py                     #   Complete, build, sync, reorder
    ├── context.py                   #   Hierarchical context resolution
    ├── meta-validate.py             #   Config/template drift checker
    ├── adversarial-review.py        #   External LLM reviewer
    ├── code-review.py               #   External LLM code reviewer
    └── configs/                     #   46 YAML configs
        ├── iterate/                 #     20 adversarial review configs
        ├── fix/                     #     19 mechanical fix configs
        ├── seed/                    #     10 document generation configs
        ├── validate/                #     20 structural validation configs
        └── revise/                  #     10 drift detection configs
```

</details>

---

## License

MIT License. See [LICENSE](LICENSE) for details.

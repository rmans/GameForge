# Tools — Index

> **Purpose:** Scripts and utilities that support the scaffold pipeline.

## Tools

| File | Description |
|------|-------------|
| `adversarial-review.py` | Adversarial document reviewer — multi-provider (OpenAI / Anthropic) |
| `review_config.json` | Configuration for adversarial-review.py (provider, model, temperature) |
| `code-review.py` | Adversarial code review — multi-provider LLM review for implementation code |
| `iterate.py` | Iterate orchestrator — manages adversarial review sessions for scaffold documents (used by `/scaffold-iterate`) |
| `local-review.py` | Local review orchestrator — runs mechanical checks (regex, patterns, template diffs) and routes judgment calls for scaffold documents (used by `/scaffold-fix`) |
| `configs/iterate/*.yaml` | Per-layer review configs for iterate.py (topics, hierarchical context, scope guards, bias packs) |
| `configs/fix/*.yaml` | Per-layer fix configs for local-review.py (mechanical checks, judgment checks, hierarchical context) |
| `review.py` | Review orchestrator — chains local-review.py (fix) then iterate.py (adversarial) for full document review (used by `/scaffold-review`) |
| `validate.py` | Validate orchestrator — runs deterministic structural checks from per-scope YAML configs (used by `/scaffold-validate`) |
| `seed.py` | Seed orchestrator — dependency-aware document generation from upstream context (used by `/scaffold-seed`) |
| `configs/validate/*.yaml` | Per-scope validation configs for validate.py (checks, thresholds, activation rules) |
| `configs/seed/*.yaml` | Per-layer seed configs for seed.py (upstream sources, dependency checks, coverage rules) |
| `implement.py` | Implement orchestrator — step-by-step task implementation with file manifest tracking (used by `/scaffold-implement`) |
| `utils.py` | Shared utilities — complete, build-test, reorder, sync-refs, sync-glossary. Callable standalone or imported by orchestrators. |
| `revise.py` | Revise orchestrator — detect drift, classify signals, auto-apply safe changes, escalate dangerous changes (used by `/scaffold-revise`) |
| `configs/revise/*.yaml` | Per-layer revise configs (feedback sources, safe/escalation patterns) |
| `context.py` | Hierarchical context resolver — budget-aware, section-extracting context loading for all orchestrators |
| `meta-validate.py` | Config drift checker — verifies YAML config heading references match actual template headings. Run at install/upgrade. |

## context.py

Hierarchical context resolver that loads precisely the right context for each review call. Used by iterate.py, local-review.py, implement.py, and seed.py.

### Problem It Solves

Without context.py, every review call loaded the same flat list of whole files — the design doc, glossary, authority, interfaces, all ADRs. For a subsection review of `### Purpose`, that meant sending 10+ full documents to the external LLM when only the design doc's Identity section was relevant. This burned tokens, diluted reviewer attention, and made reviews worse.

### Context Hierarchy

Context is resolved at four levels, from broadest to narrowest:

| Level | When loaded | Example |
|-------|------------|---------|
| **base** | Every review call | design-doc.md (## Identity only) |
| **per_target** | Based on target doc metadata | Parent system's ### Purpose + ### Owned State |
| **per_section** | Only when reviewing a specific heading | authority.md's ## Authority Table for ### Owned State |
| **on_demand** | Escalation if reviewer flags ambiguity | glossary.md, doc-authority.md |

### Section Extraction

Instead of loading whole files, entries can specify `sections` — a list of headings to extract:

```yaml
- file: design/design-doc.md
  class: canonical
  sections: ["## Identity", "## Control"]
  priority: 1
```

This loads only those sections from the design doc, not the entire file.

### Context Classes

Each entry has a `class` that describes its role:

| Class | Purpose | Drop order |
|-------|---------|-----------|
| `canonical` | Source of truth (design doc, roadmap) | Last dropped |
| `constraint` | Rules, authority, style, glossary | 4th |
| `upstream` | Parent docs (spec, system, slice) | 3rd |
| `adjacent` | Directly interacting docs (peer systems) | 2nd |
| `evidence` | Specific extracted sections, indexes | First dropped |

### Budget Enforcement

Each config sets a `budget` (default 50000 chars). When total context exceeds the budget, entries are dropped by priority (5 first), then by class (evidence first, canonical last).

### YAML Config Format

```yaml
context:
  budget: 30000

  base:
    - file: design/design-doc.md
      class: canonical
      sections: ["## Identity"]
      priority: 1

  per_target:
    - type: parent_system          # resolved from target's System: SYS-### field
      sections: ["### Purpose", "### Owned State"]
      priority: 2
      class: upstream
    - type: parent_spec            # resolved from target's Implements: SPEC-### field
      sections: ["### Acceptance Criteria"]
      priority: 2
      class: upstream
    - type: interaction_partners   # systems in target's dependency tables
      sections: ["### Purpose"]
      priority: 3
      class: adjacent
    - type: referenced_engine      # engine docs matched by task type
      priority: 2
      class: constraint

  per_section:
    "### Owned State":
      - file: design/authority.md
        class: constraint
        sections: ["## Authority Table"]
        priority: 1
    "### Steps":
      - file: design/architecture.md
        class: constraint
        sections: ["## Foundation Areas"]
        priority: 2
        condition: exists           # only load if file exists

  on_demand:
    - file: design/glossary.md
      class: constraint
      sections: ["## Terms"]
      priority: 4
```

### Per-Target Types

| Type | Resolves from | What it loads |
|------|--------------|---------------|
| `parent_system` | Target's `System: SYS-###` field | System design file |
| `parent_spec` | Target's `Implements: SPEC-###` field | Spec file |
| `parent_slice` | Slice containing the target spec/task | Slice file |
| `parent_phase` | Target's `Phase: PHASE-###` field | Phase file |
| `interaction_partners` | SYS-### IDs in target's content | Peer system files |
| `referenced_engine` | Target's `Task Type` field | Engine docs by type |
| `adjacent_phases` | Prior/next phases in roadmap order | Phase files |

### Conditions

Entries can be gated with `condition`:
- `exists` — only load if the file exists
- `task_type:foundation` — only load for foundation tasks
- `has_field:system` — only load if target has a System field
- `not_task_type:art` — exclude for art tasks

### API

```python
from context import resolve, resolve_as_text, resolve_as_files

# Full resolution — returns list of {file, text, class, priority}
entries = resolve(config, "specs/SPEC-003-wall-placement_approved.md", "### Owned State")

# As concatenated string (for passing to reviewer)
text = resolve_as_text(config, target_path, section_heading)

# As file paths only (loses section extraction)
files = resolve_as_files(config, target_path)
```

### Dependencies

None — uses Python standard library only (`pathlib`, `re`).

## adversarial-review.py

Adversarial document reviewer that sends scaffold documents to an external LLM for review, then supports multi-turn back-and-forth conversations until consensus. Used by `/scaffold-iterate`.

### Commands

| Command | Description |
|---------|-------------|
| `review <path>` | Start a fresh review iteration — returns structured issues JSON |
| `respond <path>` | Continue conversation within an iteration (inner loop exchange) |
| `consensus <path>` | Request final consensus summary after discussion |
| `check-config` | Verify configuration and API key |

### Loop Structure

```
Outer Loop (iterations — fresh review of updated doc)
└── Inner Loop (exchanges — back-and-forth conversation)
    ├── Reviewer raises issues (structured JSON)
    ├── Claude evaluates, pushes back, or agrees
    ├── Reviewer counter-responds
    └── ... until consensus or max exchanges
```

### Usage

```
python scaffold/tools/adversarial-review.py review <path> --iteration 1 --context-files <file1> <file2>
python scaffold/tools/adversarial-review.py respond <path> --iteration 1 --message-file <file>
python scaffold/tools/adversarial-review.py consensus <path> --iteration 1
python scaffold/tools/adversarial-review.py check-config
```

### Doc Type Auto-Detection

The script detects document type from its path. Use `--type` to override. Supported types: design, style, system, reference, engine, input, roadmap, phase, slice, spec, task.

### Review Tiers

| Tier | Max Iter | Max Exchanges | Severity | Doc Types |
|------|----------|---------------|----------|-----------|
| Full | 5 | 5 | All | design, style, system, roadmap, phase, spec |
| Lite | 1 | 3 | HIGH only | engine, input, slice, task |
| Lint | 1 | 2 | HIGH only | reference |

### Configuration

Configured via `review_config.json` in the same directory. Supports OpenAI and Anthropic providers. API key is read from the environment variable specified in config, or from `scaffold/.env`.

### Dependencies

None — uses Python standard library only (`urllib`, `json`, `argparse`).

## code-review.py

Adversarial code reviewer that sends source code to an external LLM for review across 7 sequential topics, with multi-turn conversation until consensus. Used by `iterate.py --reviewer code`.

### Topics

| # | Topic | Focus |
|---|-------|-------|
| 1 | Architecture | System responsibilities and boundaries |
| 2 | Code Structure | Class layout, function organization, coupling |
| 3 | Simulation Design | Pipeline robustness, edge cases, state machines |
| 4 | Performance | Scaling, tick cost, hot paths |
| 5 | Project Org | File placement, repo conventions |
| 6 | Engine Correctness | Memory, signals, node lifecycle |
| 7 | Maintainability | Long-term health, readability, growth resilience |

### Commands

| Command | Description |
|---------|-------------|
| `review <path>` | Start a fresh review for a specific topic — returns structured issues JSON |
| `respond <path>` | Continue conversation within a topic (inner loop exchange) |
| `consensus <path>` | Request final consensus summary for a topic |
| `check-config` | Verify configuration and API key |

### Usage

```
python scaffold/tools/code-review.py review <path> --topic 1 --iteration 1 --context-files <file1> <file2>
python scaffold/tools/code-review.py respond <path> --topic 1 --iteration 1 --message-file <file>
python scaffold/tools/code-review.py consensus <path> --topic 1 --iteration 1
python scaffold/tools/code-review.py check-config
```

### Configuration

Uses `review_config.json` (shared with adversarial-review.py). Supports OpenAI and Anthropic providers. Conversation state is saved to `.reviews/` so exchanges can continue across calls.

### Dependencies

None — uses Python standard library only (`urllib`, `json`, `argparse`).

## iterate.py

Iterate orchestrator that manages adversarial review sessions for scaffold documents. Coordinates between Claude (adjudicator) and adversarial-review.py (external LLM reviewer). Handles one document at a time — the calling skill handles range loops. Used by `/scaffold-iterate`.

### Commands

| Command | Description |
|---------|-------------|
| `preflight` | Check if a layer is ready for review |
| `start` | Begin a topic review — calls adversarial-review.py, returns first issue |
| `adjudicate` | Record Claude's decision on an issue, return next issue |
| `respond` | Send pushback to the reviewer, return counter-argument |
| `scope-check` | Run mechanical scope guard tests on a proposed change |
| `apply` | Apply all accepted fixes for the current session |
| `convergence` | Check if another iteration is needed |
| `report` | Generate the review log and report summary |

### Usage

```
python scaffold/tools/iterate.py preflight --layer design
python scaffold/tools/iterate.py start --layer systems --target design/systems/SYS-005-construction.md --topic 1 --iteration 1
python scaffold/tools/iterate.py adjudicate --session <id> --outcome accept --reasoning "Valid concern"
python scaffold/tools/iterate.py respond --session <id> --message "Counter-argument here"
python scaffold/tools/iterate.py scope-check --session <id> --change "proposed change description"
python scaffold/tools/iterate.py apply --session <id>
python scaffold/tools/iterate.py convergence --session <id>
python scaffold/tools/iterate.py report --session <id>
```

### Layer Configs

Per-layer YAML configs in `configs/iterate/` define topics, context files, scope guards, bias packs, identity checks, and report templates for each document layer:

| Config | Layer | Target Type |
|--------|-------|-------------|
| `design.yaml` | Design document | Fixed (design-doc.md) |
| `systems.yaml` | System designs | Range (SYS-###) |
| `spec.yaml` | Behavior specs | Range (SPEC-###) |
| `task.yaml` | Implementation tasks | Range (TASK-###) |
| `roadmap.yaml` | Roadmap | Fixed (roadmap.md) |
| `phase.yaml` | Phase scope gates | Range (PHASE-###) |
| `slice.yaml` | Vertical slices | Range (SLICE-###) |
| `references.yaml` | Reference/architecture docs | Multi-doc |
| `style.yaml` | Style/UX docs | Multi-doc |
| `input.yaml` | Input docs | Multi-doc |
| `engine.yaml` | Engine convention docs | Multi-doc |

### Session State

Session state is saved to `.reviews/iterate/` as JSON files. Sessions track: layer, target, current topic/iteration, issues, adjudication results, review lock (resolved root causes), and changes to apply.

### Dependencies

None — uses Python standard library only (`json`, `subprocess`, `argparse`, `pathlib`, `re`). Calls `adversarial-review.py` as a subprocess.

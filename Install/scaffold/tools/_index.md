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
| `configs/iterate/*.yaml` | Per-layer review configs for iterate.py (topics, context files, scope guards, bias packs) |
| `configs/fix/*.yaml` | Per-layer fix configs for local-review.py (mechanical checks, judgment checks, signals) |
| `review.py` | Review orchestrator — chains local-review.py (fix) then iterate.py (adversarial) for full document review (used by `/scaffold-review`) |
| `validate.py` | Validate orchestrator — runs deterministic structural checks from per-scope YAML configs (used by `/scaffold-validate`) |
| `seed.py` | Seed orchestrator — dependency-aware document generation from upstream context (used by `/scaffold-seed`) |
| `configs/validate/*.yaml` | Per-scope validation configs for validate.py (checks, thresholds, activation rules) |
| `configs/seed/*.yaml` | Per-layer seed configs for seed.py (upstream sources, dependency checks, coverage rules) |
| `implement.py` | Implement orchestrator — step-by-step task implementation with file manifest tracking (used by `/scaffold-implement`) |
| `utils.py` | Shared utilities — complete, build-test, reorder, sync-refs, sync-glossary. Callable standalone or imported by orchestrators. |
| `revise.py` | Revise orchestrator — detect drift, classify signals, auto-apply safe changes, escalate dangerous changes (used by `/scaffold-revise`) |
| `configs/revise/*.yaml` | Per-layer revise configs (feedback sources, safe/escalation patterns) |

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

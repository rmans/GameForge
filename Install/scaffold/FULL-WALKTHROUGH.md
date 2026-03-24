# Full Pipeline Walkthrough — Start to Finish

> Every command, every action.json exchange, every sub-skill call. From empty project to implemented task.
>
> **Legend:**
> - `USER` = you type this
> - `PYTHON` = orchestrator runs in Python (deterministic, never forgets)
> - `CLAUDE` = Claude handles this via sub-skill (judgment, creativity)
> - `LLM` = external LLM (adversarial-review.py or code-review.py)
> - `→` = writes action.json / `←` = writes result.json
> - `✅` = implemented / `🔧` = planned, not yet wired end-to-end

---

## Reference: Propagation Architecture

The walkthrough below is a **linear execution trace** — it shows the sequence of commands. This section shows the **control architecture** — how changes propagate through the system.

### Four Propagation Paths

```
1. PRODUCTION PATH (linear, user-driven)
   seed → review (fix → iterate → validate) → approve → implement → complete

2. SIGNAL PATH (feed-forward, targeted)
   Implementation friction → ADR/KI/triage → revise.py → affected layers only → restabilize
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ Signal sources:                                                        │
   │   ADRs (architecture decisions during implementation)                  │
   │   KIs (known issues discovered during implementation)                  │
   │   Triage logs (human decisions from review passes)                     │
   │   Sync findings (new signals/entities detected in code)                │
   │   Code review friction (implementation conflicts with design)          │
   │   Playtest patterns (3+ reports of same observation)                   │
   │                                                                        │
   │ Dispatcher: revise.py                                                  │
   │   Reads signals → classifies one-at-a-time → auto-update or escalate  │
   │   Dispatches ONLY to layers with matching signals                      │
   │   Each affected layer: review (fix → iterate → validate)              │
   │                                                                        │
   │ NOT a graph traversal. Signal-driven, not artifact-driven.             │
   └─────────────────────────────────────────────────────────────────────────┘

3. RIPPLE PATH (automatic, deterministic)
   task Complete → spec Complete → slice Complete → phase Complete → roadmap updated
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ Executor: utils.py complete_doc + _ripple_complete                     │
   │ Trigger: last child completes (requires ≥1 child at each level)       │
   │ Actions: status update, file rename, index update, parent table update │
   │ Fully automatic — no user action needed                                │
   └─────────────────────────────────────────────────────────────────────────┘

4. DEPENDENCY PATH (enforcement, not propagation)
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ seed.py: topological sort of candidates by depends_on                  │
   │ implement.py: preflight blocks on incomplete dependencies              │
   │ reorder-tasks: builds dep graph, detects cycles, proposes order        │
   │ approve: checks entry criteria, single-active discipline              │
   │                                                                        │
   │ Dependencies BLOCK execution. They do not PROPAGATE changes.           │
   │ "TASK-008 depends on TASK-005" means 008 waits — it does NOT mean     │
   │ changes to 005 automatically re-seed or re-review 008.                 │
   └─────────────────────────────────────────────────────────────────────────┘
```

### Impact Preview ✅

Before classifying signals, revise.py scans all scaffold docs and shows what's affected:

```
PYTHON: _build_impact_preview(feedback)
  → extracts signal IDs (ADR-###, KI-###) from feedback
  → scans all scaffold docs for references to those IDs
  → returns: { "ADR-012": ["design/systems/SYS-003.md", "specs/SPEC-023.md", ...] }

action.json: {
  action: "impact_preview",
  signal_count: 3,
  impact: { "ADR-012": [...], "KI-005": [...] },
  message: "3 signals found. Impact: 7 docs reference these signals. Proceed?"
}
```

The user sees the blast radius before any classification begins.

### Upstream Freshness Enforcement ✅

Validate checks whether a doc was last updated AFTER its upstream doc was modified. If upstream is newer → **FAIL** (not WARN). Forces restabilization before the pipeline can proceed.

| Doc type | Upstream checked |
|----------|-----------------|
| Systems | design-doc.md |
| Specs | parent system (System: field) |
| Tasks | parent spec (Implements: field) |
| Slices | parent phase (Phase: field) |
| Phases | roadmap.md |
| Engine | architecture.md |
| Style | design-doc.md |
| Input | design-doc.md |

### What Is NOT Automated

| Capability | Status | How it works instead |
|------------|--------|---------------------|
| Full downstream artifact graph traversal | Not built | Signal-driven revise targets affected layers; impact preview shows blast radius |
| Automatic re-review when upstream changes | Not built | Validate upstream freshness FAILS; user must restabilize |
| Automatic re-seed when a doc is revised | Not built | User re-runs seed if new docs needed |
| Real-time drift detection | Not built | Batch detection via `revise foundation --mode recheck` at phase boundaries |

These are intentional non-goals at game-project scale (10-20 systems, ~50 specs, ~100 tasks). The signal-driven approach covers the same need without the complexity of a generalized propagation graph.

---

## Reference: Document State Machine

Every scaffold document follows this lifecycle:

```
Draft ──→ Review ──→ Approved ──→ Complete
  │          │          │            │
  │          │          ├→ Revised → (stays Approved, re-reviewed)
  │          │          │
  └──────────┴──────────┴→ Deprecated (via ADR)
```

| State | Set by | Meaning |
|-------|--------|---------|
| **Draft** | Template / seed skill | Created, not yet reviewed |
| **Review** | User (manual) | Ready for adversarial review |
| **Approved** | iterate.py (after convergence) | Passed adversarial review |
| **Complete** | utils.py complete (with ripple) | Implementation done and verified |
| **Deprecated** | ADR acceptance | No longer active (ID preserved) |

ADRs use their own lifecycle: `Proposed → Accepted → Deprecated → Superseded`

---

## Reference: Context Precedence Rules ✅

When resolving context for a review call, these rules apply in order:

1. **Target doc first** — always included, never dropped
2. **Direct upstream sections** — parent spec ACs, parent system Purpose/Owned State
3. **Direct dependencies** — interface contracts, authority table for ownership questions
4. **Authority/style/glossary** — only when the review question requires them
5. **Peers** — only if consistency/comparison is the point (interaction partners)
6. **Whole docs** — only when extracted headings are insufficient
7. **Budget enforced** — if total exceeds budget, drop by priority (5→1), then by class (evidence → adjacent → constraint → upstream → canonical)

---

## Reference: Budget Overflow Behavior ✅

Each config sets a char budget (default 50K). When exceeded:

1. Keep target doc (always)
2. Keep priority-1 extracted sections (essential)
3. Drop priority-5 entries (nice-to-have: glossary, doc-authority)
4. Drop priority-4 entries (on-demand: signal registry, entity components)
5. Drop by class: evidence → adjacent → constraint → upstream
6. Truncate oversized entries with `[...truncated by budget]`
7. If required context alone exceeds budget → load truncated, no silent failure

---

## Reference: Convergence Rules ✅

### Fix (local-review.py)

- **Converged** = a re-run of mechanical checks produces zero auto-fixes AND zero remaining judgment checks (excluding already-rejected ones)
- **Changes tracked per-iteration** — `changes_this_iteration` resets each pass, prevents false convergence from cumulative totals
- **Rejected judgments excluded** — if user rejects a judgment check, it's never re-queued
- **Max iterations** from config (default 10)

### Iterate (iterate.py)

- **Stable** = a verification pass of changed sections produces zero new issues not already in `resolved_root_causes`
- **New issue** = different root cause than any previously resolved. Reworded duplicates deduped by `_extract_root_cause()`
- **Verification scope** = only sections that had changes applied (not full re-review)
- **Max iterations** from config (default 10)
- **Escalation** = CRITICAL issues rejected twice → stop iteration, report as blocking 🔧

### Issue Auto-Categorization ✅

Not every issue needs full adjudication:

| Category | Criteria | Flow |
|----------|----------|------|
| **Mechanical** | LOW severity + concrete suggestion, or `category: "mechanical"` | Auto-accept → batch apply (skip adjudication) |
| **Quality** | MEDIUM/HIGH with suggestion, description has no cross-doc keywords | Adjudicate → apply (scope-check skipped) |
| **Architecture-affecting** | Description contains: ownership, authority, contract, interface, cross-system, cross-doc, upstream, violat | Adjudicate → scope-check → apply |
| **Critical** | Severity CRITICAL | Adjudicate → scope-check always → apply. Rejected twice → stop iteration, report as blocking 🔧 |
| **Ambiguous** | No suggestion, unclear fix | Escalate to user |

### Verification Blast Radius ✅

When a section changes during iterate, verification re-checks more than just that section:

1. **The changed section** itself (always)
2. **Sibling sections** under the same `##` parent (always — change in `### Owned State` also re-checks `### Upstream Dependencies`)
3. **Explicitly linked sections** from the config's `linked_sections` map (e.g., `### Simulation Responsibility` links to `### Purpose`)
4. **Parent `##` section** (L2 re-review)
5. **L1 whole document** (always re-runs after verification)

### Root Cause Deduplication ✅

Issues are deduped by root cause to prevent the same problem from cycling:

1. **Preferred:** reviewer provides explicit `root_cause` tag (e.g., `"purpose_is_generic"`, `"ownership_conflict_with_SYS-003"`)
2. **Fallback:** section name + first 8 words of description (stable, coarse)
3. Once a root cause is resolved, any reworded variant is filtered out

---

## Reference: Write Boundaries

| Write type | Who does it | Examples |
|------------|------------|---------|
| **Authoritative content** | Claude via sub-skill | Spec behavior, system design, task steps |
| **Derived bookkeeping** | Python (utils.py) | Index updates, status changes, file renames, upstream table rows |
| **Safe generated sync** | Python → user review | Signal registry entries, entity properties (presented as suggestions, not auto-applied). Currently only detects concrete declarations (ADD_SIGNAL, bind_method) — these are always surfaced. ✅ |
| **Architecture suggestions** | Python → user → ADR | Architecture changes from sync-refs are findings, NOT auto-writes. File as drift finding or ADR. ✅ |

---

## Step 1 — Design Definition

### 1a — Seed the design doc

```
USER: /scaffold-seed design
```

**Preflight:**
```
PYTHON: seed.py preflight --layer design
  → loads configs/seed/design.yaml
  → checks required_files from config (empty for design — always passes)
  → checks check_existing=true: if design/design-doc.md already exists on disk → blocks
    with message "Design doc already exists. Use /scaffold-review design to review it."
  → status: ready (if doc doesn't exist yet)
```

**Session init:**
```
PYTHON: seed.py next-action --layer design
  → _build_inventory()
    scans: project.godot, *.gdextension, SConstruct, *.gd, *.cpp
    scans: addons/gut, .gdlintrc, .github/workflows/
    scans: src/, game/, tests/, data/
  → _extract_upstream_requirements() → empty (design has no upstream)
  → _analyze_existing() → checks if design-doc.md already has content
  → detects has_interview=true (design.yaml has project_context.interview_sections)
  → creates session, phase: confirm_inventory
  → action.json: {
      action: "confirm_inventory",
      session_id: "...", layer: "design",
      detected: { gut: true, "lint.gdlint": true },
      not_found: ["pytest", "jest", ...],
      engine_config: { "godot4.project_file": true, "godot4.gdextension": true, ... },
      file_system: { src: true, game: true, ... },
      message: "Review detected project state..."
    }
```

**Dispatch loop:**

```
CLAUDE reads action.json → presents inventory to user:
  "I detected: Godot 4.3, GDExtension (C++), SConstruct, GUT tests, gdlint. Correct?"

USER: confirms or corrects

CLAUDE ← result.json: { corrections: {}, additions: {} }
PYTHON: seed.py resolve
  → if existing docs found → phase: review_existing (present delta first)
  → else → phase: interview (because has_interview=true: interview_sections populated AND no upstream requirements)
```

Design uses an **interview** phase instead of propose — seed.py sends one section group at a time from `design.yaml`'s `project_context.interview_sections`: ✅

```
PYTHON → action.json: {
  action: "interview",
  group: "Identity",
  subsections: ["Core Fantasy", "Design Invariants", "Elevator Pitch", "Core Pillars", "Core Design Tension", "Unique Selling Points"],
  questions: ["What is the one-sentence fantasy?", "What must NEVER be violated?", ...],
  group_index: 0, total_groups: 8,
  inventory: {...}, template: "scaffold/templates/design-doc-template.md",
  target: "design/design-doc.md"
}

CLAUDE: interviews user for Identity sections, writes answers to design-doc.md
CLAUDE ← result.json: { group: "Identity" }
PYTHON: seed.py resolve → interview_index: 1

PYTHON → action.json: { action: "interview", group: "Shape", ... group_index: 1 }
CLAUDE: interviews user, writes answers
... repeats for Control, World, Presentation (incl Entity Presentation), Content,
  System Domains, Philosophy, Scope (Technical Stack pre-filled from scan) ...
9 groups total
```

**Verify + Report:**
```
PYTHON: all 9 groups interviewed → phase: verify
PYTHON → action.json: { action: "verify" }
CLAUDE: /scaffold-seed-verify → checks all sections filled, governance populated
CLAUDE ← result.json: { gaps: [] }

If gaps found → review_gaps → user decides fill/defer/dismiss → fill_gaps loop → re-verify

PYTHON → action.json: { action: "report" }
CLAUDE: /scaffold-review-report → summary
CLAUDE ← result.json: { report_summary: "..." }
PYTHON: seed.py resolve → action: "done"
```

**Result:** `design/design-doc.md` — Status: Draft, all sections filled.

---

### 1b — Review the design doc (fix + iterate + validate)

```
USER: /scaffold-review design
```

**Preflight:**
```
PYTHON: review.py preflight --layer design --target design/design-doc.md
  → runs local-review.py preflight (checks doc exists, critical sections present)
  → runs iterate.py preflight (same checks + review freshness)
  → both pass → status: ready
```

#### Phase 1: Fix (local-review.py)

```
PYTHON: review.py next-action → delegates to local-review.py
PYTHON: local-review.py loads fix/design.yaml
  → runs mechanical checks in Python:
    - template_diff: any sections still have template text?
    - governance_format: invariants follow Invariant/Rule/Reason/Implication?
    - glossary_not_column: any NOT-column terms used?
    - system_index_sync: system index matches systems/_index.md?
  → builds queue: [auto_apply, judgment, judgment_apply, convergence, report]
```

**Auto-apply loop:**
```
PYTHON → action.json: { action: "apply", changes: [{section: "### Design Invariants", fix: "Reformat to governance template"}] }
CLAUDE: /scaffold-review-apply → edits design-doc.md
CLAUDE ← result.json: { applied: 3 }
PYTHON: local-review.py resolve → next queue item
```

**Judgment checks (if any):**
```
PYTHON → action.json: { action: "adjudicate", issue: {description: "Core Fantasy is vague", question: "Is this specific enough?"} }
CLAUDE: /scaffold-review-adjudicate → decides: accept fix / reject / escalate
CLAUDE ← result.json: { decision: "accept", fix_description: "..." }
PYTHON: resolve → apply accepted fix → re-run checks → converge or iterate
```

**Fix report:**
```
PYTHON → action.json: { action: "report", auto_fixed: 5, judgment_fixed: 1, signals: 2 }
CLAUDE: /scaffold-review-report → writes FIX-design-YYYY-MM-DD.md
PYTHON → action.json: { action: "phase_complete", message: "Fix complete. Starting adversarial review..." }
```

#### Phase 2: Iterate (iterate.py → adversarial-review.py)

```
PYTHON: review.py next-action → delegates to iterate.py
PYTHON: iterate.py loads iterate/design.yaml
  → builds L3 queue: [### Core Fantasy, ### Design Invariants, ### Elevator Pitch, ...]
    (30+ subsections from design-doc template)
```

**L3 pass (one subsection at a time):**
```
PYTHON: for "### Core Fantasy":
  → context.py resolves context for this section:
    base: [] (design doc is self-reviewing)
    per_section: none defined for Core Fantasy
    → writes ctx file with just the section content
  → calls adversarial-review.py with section + questions:
    "Does this describe what the player feels, not what they do?"
    "Is it specific enough to guide every downstream decision?"

LLM: returns issues: [{ severity: "HIGH", description: "Core Fantasy is generic", suggestion: "Name the specific emotional arc" }]

PYTHON → action.json: { action: "adjudicate", issue: {...}, section: "### Core Fantasy" }
CLAUDE: /scaffold-review-adjudicate → accept / reject / pushback
CLAUDE ← result.json: { decision: "accept" }

PYTHON: stashes accepted issue → scope check
PYTHON → action.json: { action: "scope_check", change: {...} }
CLAUDE: /scaffold-review-scope-check → is this in scope?
CLAUDE ← result.json: { in_scope: true }

PYTHON: queues for apply → moves to next L3 section
```

Repeat for every ### subsection. Some return no issues:
```
PYTHON → action.json: { action: "no_issues", section: "### Elevator Pitch", message: "Clean" }
PYTHON: resolve → next section
```

**L3 apply:**
```
PYTHON → action.json: { action: "apply", changes: [all accepted L3 issues] }
CLAUDE: /scaffold-review-apply → edits design-doc.md
```

**L2 pass (one ## section at a time):**
```
Same pattern but reviewing entire ## sections (Identity, Shape, Control, World, Presentation, Content, System Domains, Philosophy, Scope). Questions are holistic:
  "Does the Identity section tell a coherent story from fantasy to invariants?"
```

**L1 pass (whole document):**
```
One review call for the entire doc. Questions:
  "Does the design doc read as a unified vision?"
  "Are there contradictions between sections?"
```

**Convergence:**
```
If issues remain after L1, iterate.py loops back to targeted L3 verification of changed sections only. Continues until clean or max iterations.
```

**Iterate report:**
```
PYTHON → action.json: { action: "report", issues_found: 12, issues_resolved: 11, remaining: 1 }
CLAUDE: /scaffold-review-report → writes ITERATE-design-YYYY-MM-DD.md
  → if converged: sets design-doc.md Status → Approved
PYTHON → action.json: { action: "phase_complete", message: "Adversarial review complete. Running validation..." }
```

#### Phase 3: Validate (validate.py)

```
PYTHON: review.py → delegates to validate.py
PYTHON: validate.py run --scope design
  → runs 13 deterministic checks (Python, no LLM):
    - doc exists ✓
    - 10 core sections present ✓
    - weighted health score (Complete=1.0, Partial=0.5, Empty=0) ✓
    - governance format (invariants, anchors, pressure tests) ✓
    - system index sync ✓
    - glossary compliance ✓
    - ADR consistency ✓
    - review freshness ✓
  → verdict: PASS / CONDITIONAL / FAIL

PYTHON → action.json: { action: "done", verdict: "PASS", fix_report: "...", iterate_report: "...", validate_report: {...} }
```

**Result:** `design/design-doc.md` — Status: Approved. Ready for Step 2.

---

## Step 2 — System Definition

### 2a — Seed systems

```
USER: /scaffold-seed systems
```

```
PYTHON: seed.py preflight --layer systems
  → loads configs/seed/systems.yaml → required_files: [design/design-doc.md]
  → checks design-doc.md exists on disk
PYTHON: seed.py next-action --layer systems
  → _build_inventory()
  → _extract_upstream_requirements() → reads design-doc.md
    extract_sections: ["## Identity", "## Control", "## System Domains", "## Content"]
    (heading extraction — not raw 3000 chars)
  → _analyze_existing() → checks for existing SYS-*-*.md files

  → action.json: { action: "confirm_inventory" }
```

**Propose loop (one requirement at a time):**
```
PYTHON → action.json: { action: "propose", requirement: { source: "design-doc.md", content: "## System Domains: Major System Domains..." } }

CLAUDE: /scaffold-seed-propose
  → reads design invariants, player control model, system domains, simulation depth
  → proposes: "SYS-001 — BuildingSystem: owns construction lifecycle"
  → checks: overlap with other candidates? missing coverage? invariant conflicts?
CLAUDE ← result.json: { candidates: [{ proposed_id: "SYS-001", name: "BuildingSystem", ... }] }
```

Repeat for each section of the design doc that produces systems. Claude also seeds glossary terms.

**Confirm → Create → Verify → Report** (same pattern as Step 1a)

Each system file gets the template with:
- Purpose, Simulation Responsibility, Player Intent
- Design Constraints (from invariants)
- Player Actions, System Resolution, Feel & Feedback, **Asset Needs**
- Owned State, State Lifecycle
- Dependencies, Consequences
- Edge Cases, Open Questions

**Result:** `design/systems/SYS-001-building.md` through `SYS-00N-*.md` — all Draft.

### 2b — Review systems

```
USER: /scaffold-review systems SYS-001-SYS-00N
```

For each system in the range, runs the same 3-phase pipeline:

**Fix:** mechanical checks per fix/systems.yaml (structure, terminology, registration, dependency asymmetry)

**Iterate:** L3 → L2 → L1 per iterate/systems.yaml
- Context is per-section now:
  - `### Purpose` gets design-doc Identity + Simulation Depth Target
  - `### Owned State` gets authority.md Authority Table
  - `### Asset Needs` gets design-doc Entity Presentation
  - Interaction partners get ### Purpose + ### Owned State only (not full docs)

**Validate:** 16 deterministic checks (index sync, owned-state overlap, dependency cycles, etc.)

**Result:** All system docs — Status: Approved.

### 2c — Manual review

User reviews Edge Cases and Open Questions. If design doc needs updating, re-run Step 1 stabilization.

---

## Step 3 — Reference Model

### 3a — Seed references

```
USER: /scaffold-seed references
```

```
PYTHON: seed.py → reads all system designs
  extract_sections: ["### Purpose", "### Player Actions", "### Owned State", "### State Lifecycle", "### Asset Needs"]
  → also reads design-doc.md: ["## Identity", "## Control", "## System Domains"]
```

Seeds 9 docs: architecture.md, authority.md, interfaces.md, state-transitions.md, entity-components.md, resource-definitions.md, signal-registry.md, balance-params.md, enums-and-statuses.md

### 3b-3d — Review + Validate

Same 3-phase pipeline with refs-specific context. Iterate uses per-section context:
- `### System Representation` → architecture Foundation Areas
- `## Authority Table` → systems index
- `## Signal Wiring Map` → interfaces

---

## Steps 4-6 — Engine, Style, Input

Each follows the same pattern:

| Step | Command | Creates | Context source |
|------|---------|---------|---------------|
| 4a | `/scaffold-seed engine` | 15 engine docs | architecture + systems |
| 4b | `/scaffold-review engine` | fix → iterate → validate | architecture sections per-heading |
| 5a | `/scaffold-seed style` | 6 style/UX docs | design-doc Presentation + Entity Presentation + systems |
| 5b | `/scaffold-review style` | fix → iterate → validate | peer style docs per-heading |
| 6a | `/scaffold-seed input` | 5 input docs | design-doc Control + interaction model |
| 6b | `/scaffold-review input` | fix → iterate → validate | interaction model + action map |

Each seed uses heading extraction (not raw content). Each iterate uses per-section context with budgets.

---

## Step 7 — Foundation Architecture Gate

```
USER: /scaffold-revise foundation --mode initial
```

**Revise (initial mode):** Python checks Steps 1-6 completed their pipelines. Reports readiness per layer. No revisions needed yet.

```
USER: /scaffold-validate --scope foundation
```

**Validate:** 8 checks — foundation area coverage, area status (Locked/Partial/Deferred), authority consistency, interface completeness.

If cross-cutting findings → `/scaffold-fix cross-cutting`

Gate: PASS / CONDITIONAL / FAIL. Must pass before planning.

---

## Step 8 — Roadmap

### 8a — Seed the roadmap

```
USER: /scaffold-seed roadmap
```

```
PYTHON: seed.py → reads design-doc.md ["## Identity", "## System Domains", "## Scope"]
  → reads systems/_index.md
  → proposes phase skeleton, maps systems to phases
  → user confirms
  → creates phases/roadmap.md
```

### 8b-8d — Review + Validate

```
USER: /scaffold-review roadmap
USER: /scaffold-validate --scope roadmap
```

---

## Step 9 — Phases

### 9a — Seed phases

```
USER: /scaffold-seed phases
```

```
PYTHON: seed.py → reads roadmap ["### Phase Overview", "### Capability Ladder", "### System Coverage Map"]
  → reads design-doc ["## Identity", "## System Domains", "## Content"]
  → reads systems ["### Purpose", "### Owned State"]
  → proposes phase stubs → user confirms → creates PHASE-001, PHASE-002, ...
  → updates roadmap Phase Overview table
```

### 9b-9e — Review + Validate + Approve

```
USER: /scaffold-review phase PHASE-001-PHASE-00N
USER: /scaffold-validate --scope phases
USER: /scaffold-approve phases PHASE-001
```

Approve checks 9 preconditions: validation passed, single-active, roadmap order, entry criteria, review freshness, no pending ADRs, content readiness. Renames file (`_draft` → `_approved`), updates index.

---

## Step 10 — Slices

### 10a — Seed slices

```
USER: /scaffold-seed slices
```

```
PYTHON: seed.py → reads PHASE-001 ["### Objective", "### Slice Strategy", "### Exit Criteria"]
  → reads system designs ["### Purpose", "### Player Actions", "### Owned State"]
  → reads interfaces.md
  → proposes vertical slices → user confirms → creates SLICE-001, SLICE-002, ...
  → updates PHASE-001 Slice Strategy table
```

### 10b-10e — Review + Validate + Approve

```
USER: /scaffold-review slice SLICE-001
USER: /scaffold-validate --scope slices
USER: /scaffold-approve slices SLICE-001
```

---

## Step 11 — Specs

### 11a — Seed specs

```
USER: /scaffold-seed specs
```

```
PYTHON: seed.py → reads SLICE-001 ["### Goal", "### Proof Value", "### Specs Included", "### Done Criteria"]
  → reads system designs ["### Purpose", "### Player Actions", "### System Resolution", "### Owned State", "### State Lifecycle", "### Asset Needs"]
  → reads state-transitions.md
  → proposes specs → user confirms → creates SPEC-001, SPEC-002, ...
  → updates SLICE-001 Specs Included table
```

Each spec includes **Asset Requirements** table populated from the parent system's Asset Needs section.

### 11b — Review specs

```
USER: /scaffold-review spec SPEC-001-SPEC-00N
```

Iterate context per-section:
- `### Preconditions` → authority.md Authority Table
- `### Steps` → state-transitions.md
- `### Secondary Effects` → interfaces.md
- `### Asset Requirements` → design-doc Entity Presentation

### 11c — Triage

```
USER: /scaffold-triage specs SLICE-001
```

Collects unresolved issues from fix + iterate. Presents as decision checklists: split, merge, reassign, defer. Writes triage log.

### 11d — Stabilize

Repeat 11b-11c until stable (no new issues, no new specs, two clean passes).

### 11e-11f — Validate + Approve

```
USER: /scaffold-validate --scope specs
USER: /scaffold-approve specs SLICE-001
```

---

## Step 12 — Tasks

### 12a — Seed tasks

```
USER: /scaffold-seed tasks
```

```
PYTHON: seed.py next-action --layer tasks
  → _build_inventory() (engine, test tools, file system)
  → _extract_upstream_requirements()
    reads specs: extract_sections: ["### Acceptance Criteria", "### Steps", "### Asset Requirements", "### Out of Scope"]
    reads engine: extract_sections: ["## Conventions", "## Patterns", "## Rules"]
    reads architecture: extract_sections: ["## Foundation Areas", "## Core API Boundary", "## Tick Order"]

  → _extract_asset_requirements_from_specs() ✅
    scans each approved spec's ### Asset Requirements table
    finds rows with Status: Needed
    SPECIFICITY GATE: skips vague entries (description <10 chars, "TODO", "TBD", "...")
      → vague assets reported in confirm phase as warnings, not synthesized into tasks
    groups specific entries: art assets (Sprite, Mesh, Icon...) vs audio assets (SFX, Music...)
    creates synthetic candidates:
      { name: "Wall Placement Art", task_type: "art", _synthetic: true,
        assets: [{requirement: "Wall sprite", type: "Sprite", description: "32x32 sandstone wall tile..."}],
        prompt_context_docs: ["design/style-guide.md", "design/color-system.md"] }

  → session created with synthetic asset candidates pre-seeded in candidates list
```

**Propose loop (Claude adds code tasks):**
```
PYTHON → action.json: { action: "propose", requirement: { source: "SPEC-003", content: "### Acceptance Criteria\n..." } }

CLAUDE: /scaffold-seed-propose
  → sees existing asset candidates for SPEC-003
  → proposes code tasks: TASK-007 (behavior), TASK-008 (wiring, depends on art task)
CLAUDE ← result.json: { candidates: [{proposed_id: "TASK-007", ...}, {proposed_id: "TASK-008", depends_on: ["TASK-005"], ...}] }
```

**Confirm (asset + code tasks together):**
```
PYTHON: topological sort → art/audio tasks first (no deps), then behavior, then wiring
PYTHON → action.json: {
  action: "confirm",
  candidates: [
    { name: "Wall Placement Art", task_type: "art", _synthetic: true, ... },
    { name: "Combat SFX", task_type: "audio", _synthetic: true, ... },
    { name: "Implement wall validation", task_type: "behavior", ... },
    { name: "Wire wall sprites", task_type: "wiring", depends_on: ["TASK-005", "TASK-007"], ... },
  ]
}

USER: confirms candidate list
```

**Create loop:**

For a **synthetic art task** (`_synthetic: true`):
```
PYTHON → action.json: { action: "create", candidate: { _synthetic: true, task_type: "art", assets: [...], prompt_context_docs: [...] } }

CLAUDE: reads style-guide.md + color-system.md
  → creates TASK-005-wall-placement_art_draft.md with:
    - Task Type: art
    - Asset Delivery table with file paths, dimensions, generation prompts
    - Style Context section
    - Delivery Checklist
    - NO Implementation section (deleted)
```

For a **code task**:
```
PYTHON → action.json: { action: "create", candidate: { task_type: "behavior", ... } }

CLAUDE: reads spec ACs, engine docs, architecture
  → creates TASK-007-wall-validation_draft.md with:
    - Full Implementation section (Steps, Files, Testing)
    - Verification Mapping to spec ACs
```

After each create, Python updates the parent slice's Tasks table.

**Verify:**
```
PYTHON → action.json: { action: "verify", requirements: [...], created_docs: [...], coverage_rules: [...] }
CLAUDE: /scaffold-seed-verify → checks coverage rules
CLAUDE ← result.json: { gaps: [...] }

If gaps found:
  PYTHON → action.json: { action: "review_gaps", gaps: [...] }
  USER: decides each gap — fill / defer / dismiss
  CLAUDE ← result.json: { fill: [...], deferred: [...], dismissed: [...] }
  → fill gaps loop: propose → confirm → create → re-verify

If no gaps:
  PYTHON → action.json: { action: "report" }
  CLAUDE: /scaffold-review-report → summary
  PYTHON → done
```

### 12b-12h — Review + Triage + Validate + Reorder + Approve

```
USER: /scaffold-review task TASK-001-TASK-00N
```

Task iterate context:
- Parent spec ACs + Steps + Out of Scope (not full spec)
- Parent system Purpose + Owned State (not full system)
- Engine docs by task type (not all engine docs)
- Architecture Foundation Areas + Core API only when reviewing ### Steps

```
USER: /scaffold-triage tasks SLICE-001
USER: /scaffold-validate --scope tasks
USER: /scaffold-reorder-tasks SLICE-001
USER: /scaffold-approve tasks SLICE-001
```

---

## Step 13 — Implement

### For an art/audio task:

```
USER: /scaffold-implement TASK-005
```

```
PYTHON: implement.py preflight --task TASK-005
  → reads task file
  → detects Task Type: art
  → _check_asset_delivery():
    parses Asset Delivery table for file paths
    checks if each file exists on disk
```

**If assets missing:**
```
PYTHON → { status: "blocked", message: "3/5 assets delivered. Missing:\n  - scaffold/assets/entities/wall/wall-base.png\n  - scaffold/assets/entities/wall/wall-damaged.png\n  - scaffold/assets/ui/wall-icon.png" }
```

User creates assets externally (DALL-E, Photoshop, Blender, etc.) using the prompts from the Asset Delivery table. Places files at listed paths.

```
USER: /scaffold-implement TASK-005  (again, after placing assets)
```

**If all assets present:**
```
PYTHON: _check_asset_delivery() → all 5 files exist
  → imports utils.py
  → calls complete_doc("tasks/TASK-005-wall-placement_art_draft.md")
    → sets Status: Complete
    → renames file (_draft → _complete)
    → updates tasks/_index.md
    → _ripple_complete(): checks if all tasks for parent spec are done
      → if yes: spec → Complete, then checks slice, then phase

PYTHON → { status: "complete", message: "All 5 assets delivered. Task marked Complete with upstream ripple." }
```

Dependent wiring tasks now unblock.

### For a code task:

```
USER: /scaffold-implement TASK-007
```

**Preflight:**
```
PYTHON: implement.py preflight --task TASK-007
  → status: Draft or Approved ✓
  → Task Type: behavior ✓ (not art/audio)
  → dependencies: TASK-001 Complete ✓
  → status: ready
```

**Session init:**
```
PYTHON: implement.py next-action --task TASK-007
  → _load_task_context("tasks/TASK-007-wall-validation_draft.md")
    structured resolution:
      1. parent spec (SPEC-003) → loads it
      2. parent system (from spec's System field) → loads SYS-001
      3. task_type in (foundation, behavior, integration) → loads architecture.md
      4. task_type = behavior → loads engine/*coding*.md + *simulation-runtime*.md
      5. Steps section mentions "signal-registry" or "signal_registry" → loads it
      6. Steps section mentions "interfaces.md" or "interface.*contract" → loads it
      7. Steps section doesn't mention "entity-components" → skips it
  → _extract_task_steps() → [Step 1, Step 2, Step 3, ...]
  → creates session, phase: plan
```

**Phase 1: Plan**
```
PYTHON → action.json: {
  action: "plan",
  task_info: { task_type: "behavior", implements: "SPEC-003", ... },
  context_docs: ["specs/SPEC-003...", "design/systems/SYS-001...", "design/architecture.md", "engine/godot4-coding..."],
  steps: ["Step 1: Create wall validation...", "Step 2: Wire signals...", "Step 3: Add tests..."]
}

CLAUDE: /scaffold-implement-plan → reads context, outputs 5-10 line outline
CLAUDE ← result.json: { plan: "1. Create WallValidator class...\n2. Add can_place()...\n3. Wire to BuildingSystem...\n4. Tests..." }

PYTHON: resolve → phase: code, step_index: 0
```

**Phase 2: Code (one step at a time)**
```
PYTHON → action.json: {
  action: "code",
  step: "Step 1: Create WallValidator class with can_place() method",
  step_number: 1,
  total_steps: 3,
  context_docs: [...],
  file_manifest: []
}

CLAUDE: /scaffold-implement-code
  → writes src/systems/building/wall_validator.cpp
  → writes src/systems/building/wall_validator.h
CLAUDE ← result.json: { files_created: ["src/systems/building/wall_validator.cpp", "..."], files_modified: [] }

PYTHON: resolve → updates file_manifest → step_index: 1
PYTHON → action.json: { action: "code", step: "Step 2: Wire to BuildingSystem...", file_manifest: ["wall_validator.cpp", "..."] }

CLAUDE: /scaffold-implement-code → edits existing files
... repeats for all steps ...
```

**Phase 3: Test**
```
PYTHON → action.json: {
  action: "code",
  step_number: "test",
  step: "Add regression tests for all implemented functionality",
  file_manifest: [...]
}

CLAUDE: /scaffold-implement-code → writes test functions
```

**Phase 4: Build (Python — no skill)**
```
PYTHON: utils.py build-test
  → runs: scons (compile)
  → runs: gdlint (lint)
  → runs: regression test suite
  → runs: GUT tests

If FAIL (retries remain):
  PYTHON → action.json: { action: "build_failed", attempt: 1, max: 3, errors: ["wall_validator.cpp:42 — undeclared identifier..."] }
  CLAUDE: /scaffold-implement-code → fixes the error
  PYTHON: rebuild → retry

If FAIL (max retries exceeded): ✅
  PYTHON → action.json: {
    action: "stuck", phase: "build", attempts: 3,
    escalation_options: [
      "1. Fix manually — edit code, then resolve the session",
      "2. File a Known Issue — /scaffold-file-decision --type ki 'Build failure in TASK-007'",
      "3. Revise the task — /scaffold-review task TASK-007 to reconsider approach",
      "4. Skip — mark as blocked, continue with independent tasks"
    ]
  }

If PASS:
  PYTHON: resolve → phase: review
```

**Phase 5: Code Review (iterate.py --reviewer code)**
```
PYTHON: iterate.py --reviewer code --target src/systems/building/wall_validator.cpp
  → context.py resolves: architecture Foundation Areas + Core API
  → calls code-review.py with file content + questions:
    "Does this follow the architecture's data ownership rules?"
    "Are signals wired correctly per the signal registry?"

LLM: reviews code, returns issues
CLAUDE: adjudicates each issue (accept/reject)
CLAUDE: applies accepted fixes
  ... up to --cri 10 iterations, stops early when stable ...
```

**Phase 6: Rebuild (conditional)**
```
If code review changed files:
  PYTHON: utils.py build-test → verify still passes
```

**Phase 7: Sync docs (Python → user review) ✅**
```
PYTHON: utils.py sync-refs → scans changed files for new signals, entities, properties
  → returns findings (does NOT auto-edit docs)

If findings > 0:
  PYTHON → action.json: {
    action: "sync_findings",
    findings: [
      { doc: "reference/signal-registry.md", type: "new_signal", detail: "Signal 'wall_placed' found in wall_validator.cpp but not in registry" },
      { doc: "design/architecture.md", type: "new_pattern", detail: "New validation pattern in BuildingSystem" }
    ],
    message: "2 reference doc updates suggested. Review each: registries → apply directly. Architecture → file as drift finding or ADR."
  }

  CLAUDE: presents findings to user
  USER: approves signal registry update, defers architecture change
  CLAUDE ← result.json: { applied: ["signal-registry"], deferred: ["architecture"] }
  PYTHON: resolve → phase: complete

If findings == 0:
  PYTHON: → phase: complete directly
```

**Phase 8: Complete (Python)**
```
PYTHON: utils.py complete tasks/TASK-007-wall-validation_draft.md
  → _complete_single(): Status → Complete, rename _draft → _complete, update tasks/_index.md
  → _ripple_complete():
    updates slice Tasks table → TASK-007 Complete
    checks: all tasks with Implements: SPEC-003 Complete? (requires ≥1 task)
    → if yes: SPEC-003 → Complete, updates specs/_index.md, updates slice Specs table
      checks: all specs in SLICE-001 Specs Included table Complete? (requires ≥1 spec)
      → if yes: SLICE-001 → Complete, updates slices/_index.md, updates phase table
        checks: all slices with Phase: PHASE-001 Complete? (requires ≥1 slice)
        → if yes: PHASE-001 → Complete, updates roadmap table + completion date

PYTHON → action.json: { action: "done", task: "TASK-007", files_created: [...], files_modified: [...], build: "PASS", review: "converged after 3 iterations" }
```

---

## Step 14 — The Two-Loop Cycle

### Inner loop (within a phase)

After TASK-007 completes, continue with remaining tasks in the slice:

```
USER: /scaffold-implement TASK-008
USER: /scaffold-implement TASK-009
... until all tasks in SLICE-001 are Complete ...
```

When the last task completes, `utils.py complete` ripples upward:
```
PYTHON: complete_doc("tasks/TASK-009-...md")
  → _complete_single(): Status → Complete, rename file, update tasks/_index.md
  → _ripple_complete():

  1. TASK → SPEC:
     updates parent slice's Tasks table (TASK-009 → Complete)
     finds Implements: SPEC-003
     _all_children_complete(): scans ALL tasks with Implements: SPEC-003
       → all Complete? (requires ≥1 task — zero tasks = NOT complete)
       → yes → _complete_single(SPEC-003): Status → Complete, rename, update index
       → updates parent slice's Specs table (SPEC-003 → Complete)

  2. SPEC → SLICE:
     _all_specs_in_slice_complete(): reads SLICE-001's ### Specs Included table
       → extracts SPEC IDs from that section only (not whole file)
       → all Complete? (requires ≥1 spec)
       → yes → _complete_single(SLICE-001): Status → Complete, rename, update index
       → updates parent phase's table (SLICE-001 → Complete)

  3. SLICE → PHASE:
     _all_children_complete_by_phase(): scans all slices with Phase: PHASE-001
       → all Complete? (requires ≥1 slice)
       → yes → _complete_single(PHASE-001): Status → Complete, rename, update index
       → _update_roadmap_phase_status(): updates roadmap table + adds completion date

  4. PHASE → ROADMAP:
     updates roadmap.md Phase Overview table: PHASE-001 → Complete (2026-03-23)
```

**Revise remaining slices:**
```
USER: /scaffold-revise slices --source SLICE-001
```

```
PYTHON: revise.py preflight --layer slices --source SLICE-001
PYTHON: revise.py next-action --layer slices --source SLICE-001
  → _gather_feedback():
    reads decisions/architecture-decision-record/ADR-*.md (from SLICE-001 implementation)
    reads decisions/known-issues/KI-*.md
    reads decisions/triage-log/TRIAGE-SLICE-001.md
  → builds signal list (e.g., ADR-003 changed ownership model, KI-005 flagged performance concern)

  → action.json: { action: "classify", signal: { type: "ADR", id: "ADR-003", ... } }
```

For each signal, one at a time:
```
CLAUDE: /scaffold-review-adjudicate
  → classifies: auto-update (safe to apply) | escalate (user must decide) | skip (not relevant to remaining slices)
CLAUDE ← result.json: { classification: "auto_update", target_doc: "slices/SLICE-002...", change: "Update integration points to reflect new ownership" }
```

After all signals classified:
```
PYTHON → action.json: { action: "apply", auto_updates: [...] }
CLAUDE: /scaffold-review-apply → edits remaining Draft slices
```

If escalations exist:
```
PYTHON → action.json: { action: "escalate", escalations: [{ signal: "ADR-003", impact: "SLICE-003 goal may need revision", options: [...] }] }
USER: decides each escalation
```

Then restabilize the next slice:
```
USER: /scaffold-review slice SLICE-002
USER: /scaffold-validate --scope slices
USER: /scaffold-approve slices SLICE-002
```

**Seed specs + tasks for the newly approved slice:**
```
USER: /scaffold-seed specs           ← for SLICE-002
USER: /scaffold-review spec SPEC-00N-SPEC-00M
USER: /scaffold-triage specs SLICE-002
USER: /scaffold-validate --scope specs
USER: /scaffold-approve specs SLICE-002
USER: /scaffold-seed tasks           ← for SLICE-002 (includes new art/audio tasks)
USER: /scaffold-review task TASK-00N-TASK-00M
USER: /scaffold-triage tasks SLICE-002
USER: /scaffold-validate --scope tasks
USER: /scaffold-reorder-tasks SLICE-002
USER: /scaffold-approve tasks SLICE-002
```

Back to implementing. Repeat until all slices in the phase are Complete.

---

### Outer loop (between phases)

After all slices in PHASE-001 complete:

**Step 14a — Foundation recheck:**
```
USER: /scaffold-revise foundation --mode recheck
```

```
PYTHON: revise.py → reads all ADRs, KIs, triage logs, code review findings from PHASE-001
  → identifies which foundation areas drifted:
    "ADR-003 changed data ownership → Step 3 (authority.md) needs update"
    "KI-005 flagged performance concern → Step 4 (engine performance-budget.md) needs review"
    "No Step 1/2/5/6 drift detected"

  → dispatches revision loops ONLY to affected layers:
    /scaffold-revise references --signals ADR-003
    /scaffold-revise engine --signals KI-005

  → each dispatched revise follows the same classify → apply → escalate → restabilize pattern
```

After dispatched revisions:
```
USER: /scaffold-validate --scope foundation
```

If cross-cutting findings:
```
USER: /scaffold-fix cross-cutting
```

**Step 14b — Revise roadmap:**

PHASE-001 is already Complete (rippled up from the last task → spec → slice → phase by `utils.py complete`). The revise step updates the **roadmap document** to reflect this:

```
USER: /scaffold-revise roadmap --source PHASE-001
```

```
PYTHON: revise.py →
  → updates roadmap.md: moves PHASE-001 entry to Completed Phases section with delivery notes, completion date, friction rating (LOW/MEDIUM/HIGH)
  → updates Current Phase pointer to PHASE-002 (earliest Approved phase)
  → logs ADR feedback with dedupe
  → adds Revision History entry
  → surfaces roadmap-level observations (confidence: Stable/Decreased/Improved)
```

```
USER: /scaffold-review roadmap
USER: /scaffold-validate --scope roadmap
```

**Step 14c — Revise remaining phases:**
```
USER: /scaffold-revise phases --source PHASE-001
```

```
PYTHON: revise.py →
  → reads ADRs, KIs, playtest patterns, triage logs, foundation recheck results from PHASE-001
  → four-tier classification:
    - safe refinement → direct-apply (no pause)
    - scope widening → confirmation required
    - milestone weakening → confirmation required
    - scope invalidation → ADR required
  → Approved phases stay Approved — no status regression
```

```
USER: /scaffold-review phase PHASE-002
USER: /scaffold-validate --scope phases
USER: /scaffold-approve phases PHASE-002
```

**Step 14d — Seed slices for the next phase, re-enter inner loop:**
```
USER: /scaffold-seed slices           ← for PHASE-002
USER: /scaffold-review slice SLICE-00N
USER: /scaffold-validate --scope slices
USER: /scaffold-approve slices SLICE-00N
```

→ Back to inner loop: seed specs → seed tasks → implement → complete → revise slices → next slice.

---

### What revision does NOT do

Revise is a **one-shot** pass that reads decisions and updates docs. It does not:
- Loop or iterate on itself
- Oscillate between upstream and downstream
- Re-run automatically

Each revise call reads specific signals (ADRs, KIs, DDs) from a completed phase/slice and applies them to future docs so the next cycle of work accounts for what was learned. It's a **feed-forward** mechanism, not a feedback loop.

---

## Context Budget Summary

| Skill | What it loads (old) | What it loads (new) | Budget |
|-------|-------|-------|--------|
| iterate systems ### Owned State | 10+ whole docs | authority.md § Authority Table + design-doc § Identity/Control + partner systems § Purpose/Owned State | 35K |
| iterate spec ### Steps | 7 whole docs | parent system § Purpose/Owned State + state-transitions.md | 30K |
| iterate task ### Steps | 6 whole docs | parent spec § ACs + architecture § Foundation Areas | 30K |
| implement TASK-### | architecture.md always + keyword matching | architecture only for foundation/behavior/integration + engine by type + refs only if Steps references them | — |
| seed tasks upstream | first 3000 chars of each spec | spec § ACs + Steps + Asset Requirements + Out of Scope | — |

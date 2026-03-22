---
name: scaffold-fix-systems
description: Mechanical cleanup pass for system designs — auto-fix structural issues (template text, missing sections, terminology drift, registration gaps, stale markers), detect design signals (ownership conflicts, invariant violations, layer breaches) for adversarial review. Supports single system or range. All fix loops run in parallel.
argument-hint: SYS-### or SYS-###-SYS-###
allowed-tools: Read, Edit, Grep, Glob
---

# Fix Systems

Mechanical cleanup and signal detection for system designs: **$ARGUMENTS**

This skill is the **formatter and linter** for system docs — not the design reviewer. It normalizes structure, repairs mechanical inconsistencies, and detects design signals. It does not interpret or resolve design issues — that is the job of `iterate-systems` (adversarial review) which runs immediately after this skill.

**What fix-systems does:** normalize docs so adversarial review doesn't waste time on trivial issues.
**What fix-systems does NOT do:** evaluate whether the system's design is good, resolve ownership conflicts, or make architecture decisions.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SYS-###` or `SYS-###-SYS-###` | Yes | — | Single system or range. Range processes all systems with IDs in the numeric range. |
| `--iterate N` | No | `10` | Maximum review-fix passes per system. Stops early on convergence — if a pass produces no new issues, iteration ends. |

## Parallelization

Individual fix loops are local to each system doc — all systems in a range can run their fix loops in parallel. The only cross-system write (dependency symmetry) appends rows and doesn't affect another system's fix loop.

After all individual fix loops complete, a single cross-system pass (Step 5) runs on the full range to catch inter-system signals.

## Step 1 — Gather Context

For each system:
1. Locate the system file: glob `design/systems/SYS-###-*.md`.
2. Read the system file.
3. Read the **canonical system template** at `scaffold/templates/system-template.md` — this defines the expected section structure.
4. Read `design/design-doc.md` — specifically Design Invariants, Player Control Model, Design Boundaries, Major System Domains, Simulation Depth Target.
5. Read `design/glossary.md` for canonical terminology.
6. Read `scaffold/doc-authority.md` for document authority ranking, same-rank conflict resolution rules, deprecation protocol.
7. Read `design/systems/_index.md` to verify registration.
8. Read the System Design Index in `design/design-doc.md` to verify bidirectional registration.
9. Read `design/authority.md` (if exists) for ownership rules. Skip authority-dependent checks if missing.
10. Read `design/interfaces.md` (if exists) for cross-system contracts. Skip interface-dependent checks if missing.
11. Read `design/state-transitions.md` (if exists) for relevant state machines. Skip state-machine checks if missing.
12. Read accepted ADRs that reference this system.
13. Read `decisions/known-issues.md` for constraints affecting this system.

## Step 2 — Review

For each system, run two categories of checks: **mechanical checks** (structure, formatting, registration) and **design signal detection** (governance, ownership, boundaries).

### Mechanical Checks

#### Completeness
- All sections from the canonical system template are present: Purpose, Simulation Responsibility, Player Intent, Design Constraints, Visibility to Player, Player Actions, System Resolution, State Lifecycle, Failure / Friction States, Owned State, Upstream Dependencies, Downstream Consequences, Non-Responsibilities, Edge Cases & Ambiguity Killers, Feel & Feedback, Open Questions.
- `<!-- SEEDED -->` markers on sections that now have authored content — marker should be removed.

#### Terminology & Registration
- **Glossary compliance** — system doc does not use NOT-column terms from glossary as authoritative design terms, table labels, owned-state names, or repeated system terminology. Do not replace terms inside examples, quotes, ADR references, changelog text, or explicitly comparative language.
- **Index registration** — system is registered in `design/systems/_index.md`.
- **Status sync** — filename suffix matches internal Status field.
- **ID format** — file follows `SYS-###-name_status.md` convention.

#### Structural Quality
- **Purpose is concise and immediately scannable** — not buried in prose.
- **Player Actions are structured** — numbered steps or clear bullet sequence, not paragraphs.
- **System Resolution describes observable consequences** — not just "the system processes the request."
- **State Lifecycle explicitly communicates transitions** — not just a state list without flows.
- **Edge Cases answer specific questions** — not vague "what if something goes wrong."
- **Owned State entries have Description and Persistence columns filled.**

#### Implementation Language
- No signals, methods, nodes, classes, engine constructs, file paths, or code patterns. Those belong in specs, tasks, interfaces.md, or engine docs.
- No detailed UI layout, animation timing, color values, icon specifications. Those belong in Step 4 docs.
- No key mappings, controller buttons, or input action names. Those belong in Step 5 docs.

### Design Signal Detection

These are **detected and reported**, not resolved. The adversarial review skill interprets them.

#### Governance Signals
- **Invariant signal** — system's purpose, player actions, or resolution may imply mechanics that conflict with a Design Invariant. Flagged for review.
- **Boundary signal** — system's scope may exceed Design Boundaries. Flagged for review.
- **Control model signal** — Player Actions may not match the Player Control Model. Flagged for review.
- **Simulation depth signal** — system complexity may exceed the Simulation Depth Target. Flagged for review.

#### Ownership Signals
- **Owned State is gameplay state** — no caches, engine nodes, scene references, registries, or data-structure choices. Implementation structures flagged for removal.
- **Single writer signal** — identical or semantically equivalent state name appears in the Owned State *table* of multiple systems. Explicit table match only — don't flag state mentioned in prose descriptions or dependency context. Flagged as potential ownership conflict.
- **Authority consistency signal** — if `authority.md` exists, system's Owned State doesn't match authority.md entries. Flagged for reconciliation.

#### Cross-System Signals
- **Dependency asymmetry** — System A lists System B as upstream, but B doesn't list A as downstream (or vice versa). Flagged; may be auto-fixable (see Step 3).
- **Interface coverage signal** — two systems interact per dependency tables but `interfaces.md` has no contract for them. Flagged as WARN.
- **Orphan signal** — system has zero entries in both Upstream Dependencies and Downstream Consequences tables, and its purpose implies simulation participation or authoritative state exchange. Flagged for review. Not flagged for player-facing UI/oversight systems (alerts, colony summary, risk tracking) that legitimately have one-sided or minimal dependencies.

#### Layer Boundary Signals
- **Implementation detail** — system doc contains substantial engine/code-level detail. Flagged for extraction to specs/tasks/engine docs.
- **Presentation detail** — system doc contains detailed UI/visual/audio specifications. Flagged for extraction to Step 4 docs.

Record all issues found.

## Step 3 — Classify Issues

### Auto-Fixable (apply immediately)

| Category | Fix | Condition |
|----------|-----|-----------|
| **Missing sections** | Add section heading with template comment from system-template.md | Section is required by the canonical template and genuinely absent |
| **Stale SEEDED markers** | Remove `<!-- SEEDED -->` from sections with authored content | Section has more than one authored sentence or non-comment text beyond the template marker |
| **Terminology drift** | Replace NOT-column terms with canonical terms | Term is used as authoritative design terminology, not inside examples/quotes/comparative text |
| **Registration gaps** | Add to `design/systems/_index.md` | System missing from index |
| **Implementation language** | Replace engine constructs with design language ("emit signal" → "notify dependent systems") | Construct is clearly engine-layer, not design-layer |
| **Dependency asymmetry** | Add missing reciprocal entry to the other system's table | ONLY when the missing relation is directly inferable from an explicit dependency table, interface contract, or owned-state consequence. Never infer from prose alone. Within processed range only. |
| **Owned State missing columns** | Add empty Description/Persistence cells | Table structure incomplete |
| **Stale ADR reference** | Update to current ADR status | ADR status changed since system was last edited |

### Mechanically Detected, User-Confirmed

| Category | Action |
|----------|--------|
| **Template defaults remaining** | Section still at template/default level. Report for human completion — skill cannot invent authored content. |
| **Status-filename mismatch** | Flag for rename with `git mv`. User confirms before applying. |
| **Design doc System Design Index missing entry** | Flag for human action. This skill does not auto-edit `design/design-doc.md`. |
| **Vague Non-Responsibilities** | Append "(owned by SYS-###)" ONLY when ownership is explicitly established in authority.md, an accepted ADR, or an unambiguous Owned State entry. If multiple candidate owners exist, or ownership is inferred from dependency tables or name similarity alone, report for human clarification instead. |

### Design Signals (for adversarial review)

These are reported in the output but not acted on. They feed directly into the adversarial review skill that runs after fix-systems.

| Signal | Context |
|--------|---------|
| Invariant signal | System may conflict with Design Invariant [ShortName] |
| Boundary signal | System scope may exceed Design Boundary [boundary] |
| Control model signal | Player Actions may not match [direct/indirect] control model |
| Simulation depth signal | System complexity may exceed stated depth target |
| Ownership conflict signal | Owned State overlaps with SYS-### |
| Authority mismatch signal | Owned State doesn't match authority.md |
| Orphan signal | System has no interactions but implies simulation participation |
| Layer breach signal | System contains [implementation/presentation/input] detail |
| State machine signal | System lifecycle doesn't match state-transitions.md |

## Step 4 — Apply Auto-Fixes

For each auto-fixable issue:
1. Apply the fix to the system file using Edit.
2. Record what was changed and why.

**Safety rules:**
- **Never change the system's purpose, simulation responsibility, or design constraints.** Only tighten wording or fix structure.
- **Never add new behavior or owned state.** Only clarify or restructure what's already there.
- **Never infer missing design intent.** When multiple plausible interpretations exist, report the issue instead of auto-fixing.
- **Never edit systems outside the current range** for dependency symmetry fixes — flag as cross-range issues.
- **Never edit design-doc.md, authority.md, interfaces.md, or other upstream documents.** Flag mismatches for human resolution.
- **No speculative fixes.** If resolving an issue requires guessing the author's intended behavior, do not auto-fix — report the issue instead.

## Step 5 — Cross-System Pass (range only)

After all individual systems in the range have been fixed, run one cross-system pass:

- **Re-check dependency symmetry** across the full range — individual fixes may have introduced new asymmetries.
- **Detect dependency cycles** — build a directed graph from all Upstream Dependencies and Downstream Consequences tables. Run cycle detection (depth-first traversal). Report any cycles found as signals for iterate-systems to interpret (legitimate feedback loop vs design confusion).
- **Check for Owned State conflicts** — re-verify single-writer rule across the full set.
- **Check for redundant systems** — do any two systems in the range have overlapping purpose, similar owned state, or near-identical player actions? Flag potential merges.
- **Missing system coverage** — check design doc's Core Loop steps, Major Mechanics, and Major System Domains against the full system set. Flag uncovered mechanics. This is an architecture-level signal, not an auto-fixable issue — only meaningful when the system set is intended to be comprehensive.

All cross-system pass results are reported as signals, not auto-fixed.

## Step 6 — Re-review and Iterate

After applying fixes, re-review each system. Continue iterating until one of:
- **Clean** — no issues remain.
- **Human-only** — only human-required issues and design signals remain.
- **Stable** — same issues persist across two consecutive passes (matched by category + section + issue subject).
- **Iteration limit** — `--iterate N` reached.

## Step 7 — Report

For a single system:
```
## Fix-System Summary: SYS-### — [Name]

| Metric | Value |
|--------|-------|
| Passes | N |
| Auto-fixed | N issues |
| User-confirmed pending | N issues |
| Design signals | N issues |
| Final status | Clean / Human-only / Stable / Limit |

### Auto-Fixes Applied
| # | Category | What Changed |
|---|----------|-------------|
| 1 | Terminology | Replaced "worker" with "colonist" |
| 2 | Dependency symmetry | Added reciprocal entry in SYS-### Relationships > Downstream Consequences |
| ... | ... | ... |

### User-Confirmed Actions Pending
| # | Category | Action Required |
|---|----------|----------------|
| 1 | Template defaults | Simulation Responsibility section needs authored content |
| 2 | Design doc index | Add SYS-### to design-doc.md System Design Index |
| ... | ... | ... |

### Design Signals (for adversarial review)
| # | Signal | Detail |
|---|--------|--------|
| 1 | Invariant signal | Player Actions may conflict with Invariant: IndirectControl |
| 2 | Ownership conflict | Both SYS-### and SYS-### claim mood state |
| ... | ... | ... |
```

For a range, add a summary table:
```
### Range Summary
| System | Auto-fixed | User-pending | Design Signals | Status |
|--------|-----------|-------------|----------------|--------|
| SYS-### — Construction | 3 | 1 | 0 | Clean |
| SYS-### — Colony Needs | 1 | 0 | 2 | Human-only |
| ... | ... | ... | ... | ... |

### Cross-System Signals
| # | Systems Involved | Signal | Detail |
|---|-----------------|--------|--------|
| 1 | SYS-###, SYS-### | Dependency asymmetry | A→B exists, B→A missing |
| 2 | SYS-###, SYS-### | Ownership conflict | Both claim "mood" state |
| ... | ... | ... | ... |
```

## Rules

- **This skill is a formatter and linter, not a design reviewer.** It normalizes docs and detects signals. Design evaluation belongs to the adversarial review skill.
- **Never change system purpose or simulation responsibility.** Auto-fixes tighten wording and fix structure. They never alter what the system owns or does.
- **Systems describe BEHAVIOR, not IMPLEMENTATION.** Replace implementation language with design language.
- **Never infer missing design intent.** When multiple plausible interpretations exist, report — do not auto-fix.
- **No speculative fixes.** If resolving an issue requires guessing what the author meant, report instead.
- **Design signals are detected, not resolved.** Governance, ownership, and boundary signals are reported for the adversarial review pass — not acted on by this skill.
- **Dependency symmetry fixes require explicit evidence.** Only auto-fix reciprocal entries when the relationship is directly inferable from an explicit dependency table, interface contract, or owned-state consequence. Never infer from prose alone.
- **Terminology fixes respect context.** Only replace NOT-column terms when used as authoritative design terminology. Don't replace inside examples, quotes, ADR references, changelog text, or comparative language.
- **Registration fixes are bounded.** Add to `_index.md` (auto-fixable). Do not auto-edit `design/design-doc.md` System Design Index — flag for human action.
- **All individual fix loops run in parallel.** Cross-system signals are caught in the post-loop cross-system pass.
- **Cross-system pass results are signals, not fixes.** Nothing in Step 5 is auto-applied.

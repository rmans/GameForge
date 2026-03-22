---
name: scaffold-fix-phase
description: Review-fix loop for phases — auto-fix mechanical issues (template text, vague criteria, broken references, terminology drift), surface strategic issues for human decision. Supports single phase or range.
argument-hint: [P#-### or P#-###-P#-###] [--iterate N]
allowed-tools: Read, Edit, Grep, Glob
---

# Fix Phase

Iteratively review and auto-fix mechanical issues in: **$ARGUMENTS**

Reviews the phase, classifies issues as auto-fixable or human-required, applies safe fixes, and re-reviews until clean. This skill wraps the same checklist as `/scaffold-review-phase` but adds write capability for mechanical fixes.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `P#-###` or `P#-###-P#-###` | Yes | — | Single phase or range. |
| `--iterate N` | No | `10` | Maximum review-fix passes before stopping. Stops early on convergence — if a pass produces no new issues, iteration ends. |

## Execution

**If range:**
1. Extract start and end numbers. Build ordered list.
2. For each phase in order, run the full review-fix pipeline. **Parallelization:** Extract phase IDs matching pattern `P#-###` from Entry Criteria and Dependencies sections — only those IDs count for scheduling (ignore SYS-### references). Phases whose dependency phase IDs are all already processed can run in parallel. See WORKFLOW.md Range Parallelization for the full pattern.
3. Between each phase, output a horizontal rule (`---`).
4. Skip missing phase files with a note: `**P#-###: No file found — skipping.**`
5. After all phases, output a summary table.

**If single phase or no argument:** Run the full review-fix pipeline for the selected phase.

## Step 1 — Locate and Read Context

**Resolve the phase target:**
- If a P#-### ID is given, Glob `scaffold/phases/P#-###-*.md`.
- If the phase file doesn't exist, skip (range) or stop (single).

**Read the phase file first**, then **validate required sections exist**: Goal, Entry Criteria, In Scope, Out of Scope, Deliverables, Exit Criteria, Dependencies. If any required section is completely missing (not just empty — structurally absent), report as `Blocked (malformed phase structure)` and skip. The repair loop cannot operate on a document missing structural sections.

**Read context** (same as `/scaffold-review-phase`):
1. Read the roadmap at `scaffold/phases/roadmap.md`.
2. Read the design doc at `scaffold/design/design-doc.md`.
3. Read the systems index at `scaffold/design/systems/_index.md`.
4. Read all ADRs with status `Accepted`.
5. Read known issues at `scaffold/decisions/known-issues.md`.
6. Read the slices index at `scaffold/slices/_index.md` for downstream coverage.
7. Read `scaffold/design/glossary.md` for canonical terminology.

## Step 2 — Review

Run the full review checklist from `/scaffold-review-phase` — completeness, quality (entry/exit criteria specificity, scope items, deliverables, goal orientation), system alignment, ADR impact, known issue impact, registration, and downstream coverage. Do not duplicate the checklist here — refer to the review-phase skill for the authoritative checks.

Record all issues found.

## Step 3 — Classify Issues

### Auto-Fixable

Issues where the correct fix is unambiguous and local to this phase file:

| Category | Example |
|----------|---------|
| **Template text / TODOs** | `<!-- TODO: fill in -->` or template defaults still present → replace with content derived from roadmap/design context |
| **Vague entry criteria** | "When ready" → tighten to specific phase ID or system ID reference. Auto-fix only when the intended prerequisite is unambiguous from roadmap ordering. Otherwise human-required. |
| **Vague exit criteria** | "Phase complete" → tighten to falsifiable condition. Auto-fix only when the Goal contains explicit outcome language AND the fix tightens wording without adding new functionality. Otherwise human-required. Exit criteria must be observable in a playtest, dev demo, UI display, or test scenario. |
| **Missing Depends on field** | Dependencies section empty but entry criteria imply specific phases → add them |
| **Terminology drift** | Uses NOT-column glossary term → replace with canonical term. Only replace when the glossary explicitly lists the term as a synonym (NOT column). Never assume two similar-sounding terms are equivalent. |
| **Missing ADR reflection** | Accepted ADR affects this phase's systems but isn't noted → add to scope or deliverables |
| **Missing KI reflection** | Open known issue constrains this phase but isn't noted → add to dependencies or scope notes |
| **System reference broken** | In Scope lists a SYS-### that doesn't exist → auto-fix only if unambiguous rename. Otherwise human-required. |
| **Registration gap (in phase file)** | Phase reference inside the file is inconsistent → correct internal references. Index edits are human-required. |

### Human-Required

Issues that require judgment or cross-file coordination. Present using the Human Decision Presentation pattern (see WORKFLOW.md) — grouped by category, numbered, with concrete options (a/b/c) per issue:

| Category | Why |
|----------|-----|
| **Goal is task-oriented** | "Implement 5 systems" vs "Prove core loop works" — reframing requires understanding intent |
| **Scope too broad** | Phase tries to deliver too much — splitting is a planning decision |
| **Scope too narrow** | Phase doesn't deliver a meaningful milestone — merging is a planning decision |
| **Entry/exit chain broken** | Prior phase's exit criteria don't satisfy this phase's entry criteria — cross-phase coordination |
| **ADR contradicts scope** | ADR removes something this phase plans to deliver — scope redesign needed |
| **Downstream coverage gap** | Slices exist but don't cover scope items — slice seeding decision |
| **Duplicate scope** | Multiple phases claim the same deliverables — planning decision |
| **Registration gap (index/roadmap)** | Index or roadmap edits involve cross-file coordination |
| **Playtest pattern conflict** | ACT NOW pattern affects systems in scope but scope doesn't address it |
| **Capability not demonstrable** | Capability Unlocked section is vague, task-oriented ("implement systems"), or can't be tested by QA without reading code |
| **Risk over-concentration** | Phase contains multiple core-risk systems (architecturally novel or untested) — risk should be spread across phases |
| **Authority layer mixing** | Phase mixes systems from different authority layers (e.g., colony + world) without explicit cross-layer integration purpose |
| **Over-coupling** | Entry criteria depend on >3 prior phases — pipeline becomes brittle if any earlier phase slips |
| **Scope too many systems** | In Scope contains more than 5 systems — likely over-scoped, needs splitting |
| **Downstream scope drift** | A slice assigned to this phase covers systems not present in the phase's In Scope — scope leak from slice layer |
| **Entry/exit chain mismatch** | Prior phase's exit criteria wording doesn't match this phase's entry criteria wording (e.g., exit says "prototype demo", entry says "system implemented") — cross-phase misalignment |
| **Undocumented system in scope** | A system appears in phase In Scope but doesn't exist in the systems index or design doc — prevents spec creep from undocumented systems |

## Step 4 — Apply Auto-Fixes

For each auto-fixable issue:
1. Read the relevant section of the phase file.
2. Apply the fix using the Edit tool.
3. Record what was changed and why.

**Fix rules:**
- **Only edit the target phase file.** Never edit the roadmap, indexes, slices, or other phases.
- Preserve the phase template structure.
- Fixes must be minimal — change only what's needed.
- When tightening criteria, derive wording from the roadmap and design doc, not invented.
- Never change what the phase delivers — only how clearly it expresses the scope.

## Step 5 — Re-Review

After applying fixes, re-read the phase file and run the full review checklist again.

Compare issues with the previous pass:
- **Resolved** — record as fixed.
- **New issues** — classify and fix if auto-fixable.
- **Persistent human-required** — carry forward.
- **No new issues, no remaining auto-fixable** — stop.

## Step 6 — Iterate

**Stop conditions** (any one stops iteration):
- **Clean** — no issues found.
- **Human-only** — only human-required issues remain.
- **Stable** — remaining issue set unchanged from previous pass.
- **Limit** — iteration limit reached.

## Step 7 — Output

```
## Phase Fix: P#-### — [Name]

### Summary
| Field | Value |
|-------|-------|
| Roadmap position | [N of M phases] |
| Passes | N completed / M max [early stop: yes/no] |
| Issues per pass | [e.g., 9 → 4 → 1 (healthy) or 9 → 8 → 8 (stuck)] |
| Auto-fixed | N issues |
| Human-required | N issues |
| Final status | Clean / Needs human input |

### Fixes Applied
| # | Category | What Changed | Section |
|---|----------|-------------|---------|
| 1 | Template text | Replaced TODO with roadmap-derived goal | Goal |
| 2 | Vague entry criteria | "When ready" → "P1-001 Complete" | Entry Criteria |
| ... | ... | ... | ... |

### Human-Required Issues
| # | Category | Issue | Why Auto-Fix Cannot Resolve |
|---|----------|-------|----------------------------|
| 1 | Scope too broad | 8 systems in scope for one phase | Split boundaries need human decision |
| ... | ... | ... | ... |

### Review Freshness
**Invalidated by fixes** — rerun `/scaffold-iterate phase` before approval.
```

If no issues found:
```
## Phase Fix: P#-### — [Name]

**Status: Clean** — no issues found. No changes made. Existing review/iterate freshness remains unchanged.
```

## Rules

- **Only fix mechanical, local issues.** Never make judgment calls about phase scope, ordering, or milestone design.
- **Only edit the phase file.** Never edit the roadmap, indexes, slices, or other phases.
- **Derive fixes from context, don't invent.** Tightened criteria come from the roadmap and design doc.
- **Preserve phase structure.** Don't reorganize sections.
- **Stop when stable.** If remaining issues are unchanged, stop iterating.
- **Registration fixes are human-required.** Index and roadmap edits involve cross-file coordination.
- **Goal meaning is sacred.** Auto-fixes may tighten wording but never change what the phase delivers.
- **Range processing detects cross-phase issues.** Entry/exit chain breaks, duplicate scope, and ordering problems surface when reviewing multiple phases. Always classified as human-required.

---
name: scaffold-fix-slice
description: Review-fix loop for slices — auto-fix mechanical issues (template text, vague done criteria, broken references, stale dependencies, terminology drift), surface strategic issues for human decision. Supports single slice or range.
argument-hint: [SLICE-### or SLICE-###-SLICE-###] [--iterate N]
allowed-tools: Read, Edit, Grep, Glob
---

# Fix Slice

Iteratively review and auto-fix mechanical issues in: **$ARGUMENTS**

Reviews the slice, classifies issues as auto-fixable or human-required, applies safe fixes, and re-reviews until clean. This skill wraps the same checklist as `/scaffold-review-slice` but adds write capability for mechanical fixes.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLICE-###` or `SLICE-###-SLICE-###` | Yes | — | Single slice or range. Range processes all slices with IDs in the numeric range. |
| `--iterate N` | No | `10` | Maximum review-fix passes before stopping. Stops early on convergence — if a pass produces no new issues, iteration ends. |

## Execution

**If range:**
1. Extract start and end numbers. Build ordered list.
2. For each slice in order, run the full review-fix pipeline. **Parallelization:** Slices whose `Depends on` fields are satisfied (all dependencies already processed or have no dependencies) can run in parallel. Slices with unmet dependencies wait until those dependencies complete. See WORKFLOW.md Range Parallelization for the full pattern.
3. Between each slice, output a horizontal rule (`---`).
4. Skip missing slice files with a note: `**SLICE-###: No file found — skipping.**`
5. After all slices, output a summary table:

```
## Range Fix Summary: SLICE-### through SLICE-###

| Slice | Status | Passes | Auto-Fixed | Human-Required | Final |
|-------|--------|--------|------------|----------------|-------|
| SLICE-### — Name | Clean | 2/3 | 3 fixes | 0 | Clean |
| SLICE-### — Name | Needs human | 3/3 | 1 fix | 2 issues | Blocked |
| SLICE-### — Name | Skipped (no file) | — | — | — | — |
```

**If single slice or no argument:** Run the full review-fix pipeline for the selected slice.

## Step 1 — Locate and Read Context

**Resolve the slice target:**
- If a SLICE-### ID is given, Glob `scaffold/slices/SLICE-###-*.md`.
- If a range is given, resolve each slice in order (per Execution above).
- If the slice file doesn't exist, skip it (range mode) or report and stop (single mode).

**Read the slice file first**, then **validate slice metadata:** Verify it has a `> **Phase:**` reference and a Goal section. If malformed, report as `Blocked (malformed slice metadata)` and skip.

**Read context** (same as `/scaffold-review-slice`):

1. Read the parent phase — follow the Phase reference in the slice header.
2. Read the interfaces doc at `scaffold/design/interfaces.md`.
3. Read the authority doc at `scaffold/design/authority.md`.
4. Read the systems index at `scaffold/design/systems/_index.md`.
5. Read system designs for all systems listed in the slice's Systems Covered section.
6. Read the specs index at `scaffold/specs/_index.md` to check spec coverage.
7. Read the tasks index at `scaffold/tasks/_index.md` to check task coverage.
8. Read relevant ADRs — filter to ADRs that reference systems in Systems Covered.
9. Read known issues at `scaffold/decisions/known-issues.md`.
10. Read `scaffold/design/glossary.md` for canonical terminology.

## Step 2 — Review

Run the full review checklist from `/scaffold-review-slice` — completeness, goal quality, dependency declaration, integration quality, done criteria quality, phase alignment, ADR/KI impact, spec/task status, registration, hidden prerequisites, coverage symmetry, demo realism, end-state fidelity, proof value, and terminology. Do not duplicate the checklist here — refer to the review-slice skill for the authoritative checks.

Record all issues found.

## Step 3 — Classify Issues

For each issue, classify as:

### Auto-Fixable

Issues where the correct fix is unambiguous and local to this slice file:

| Category | Example |
|----------|---------|
| **Template text / TODOs** | `<!-- TODO: fill in -->` or template defaults still present → replace with content derived from phase/system context |
| **Vague Done Criteria** | "Slice works" → tighten to falsifiable condition. Auto-fix only when the Goal and Integration Points already make the expected observable outcome explicit. Otherwise classify as human-required — the tool should not invent precision where the slice itself is vague. |
| **Missing Depends on field** | Field absent → add `> **Depends on:** —` to header |
| **Stale dependency reference (unambiguous rename)** | Depends on lists a SLICE-### that doesn't exist but resolves to exactly one renamed slice → update the reference. Otherwise classify as human-required — removal or replacement is a design decision. |
| **Broken interface reference (unambiguous)** | Integration Points cites an interface not in interfaces.md → auto-fix only if the correction is an unambiguous typo (pluralization, casing, or exact rename). Otherwise classify as human-required. |
| **Missing Systems Covered (unambiguous)** | System is already explicitly referenced in Integration Points or Demo Script but merely omitted from Systems Covered → add it. If the missing system would materially widen the slice boundary, classify as human-required. |
| **Phantom system listed (unambiguous)** | System in Systems Covered is absent from Goal, Integration Points, Demo Script, Done Criteria, and Notes/Blockers → remove it. If the system seems plausibly intended but weakly expressed, classify as human-required. |
| **Terminology drift** | Uses NOT-column glossary term → replace with canonical term |
| **Missing ADR reflection** | Accepted ADR affects this slice's systems but isn't noted → add to Notes/Blockers |
| **Missing KI reflection** | Open known issue constrains this slice but isn't noted → add to Notes/Blockers |
| **Phase reference mismatch (unambiguous)** | Phase reference inside the slice file doesn't match the actual parent phase → auto-fix only when the intended phase is unambiguous from filename and index registration. Otherwise classify as human-required — the slice may actually be in the wrong phase. |
| **Starting Conditions empty** | Starting Conditions section is empty or has template placeholder → populate from Goal/Assumptions/Preconditions. Starting Conditions is a first-class section separate from Demo Script. |
| **Proof Value empty** | Proof Value section is empty or has template placeholder → derive from Goal and Integration Points (what uncertainty does this slice reduce?) |
| **Assumptions empty** | Assumptions section is empty or has template placeholder → derive from Systems Covered, Depends on, and Integration Points |
| **Failure Modes empty** | Failure Modes This Slice Should Catch section is empty or has template placeholder → derive from Integration Points and Done Criteria (what breakage should be visible if this slice fails?) |
| **Visible Proof empty** | Visible Proof section is empty or has template placeholder → derive from Done Criteria and Demo Script (what should the tester visibly see?) |
| **Demo missing expected results** | Demo step has action but no observable outcome → add expected result derived from Done Criteria |
| **Status-filename mismatch** | File says `_draft` but Status says `Approved` (or vice versa) → update the internal `> **Status:**` field only to match the filename suffix. Filename is source of truth for fix-slice because it avoids hidden lifecycle drift and keeps this skill from implying renames. File rename must be handled by the lifecycle gate (`approve-slices`, `complete`) or `/scaffold-update-doc`. |

### Human-Required

Issues that require judgment, scope decisions, or changes outside this slice. Present using the Human Decision Presentation pattern (see WORKFLOW.md) — grouped by category, numbered, with concrete options (a/b/c) per issue:

| Category | Why |
|----------|-----|
| **Goal is horizontal** | Redesigning the goal is a strategic decision |
| **Goal is not player-visible** | Reframing requires understanding the proof intent |
| **Boundary design wrong** | Slice scope too narrow or too broad — needs planning judgment |
| **Proof value unclear** | What uncertainty this slice reduces is ambiguous — user decides |
| **Missing dependency** | Goal/demo assumes behavior from an earlier slice not declared in Depends on — user decides if dependency is real |
| **Unnecessary dependency** | Depends on lists a slice whose proof isn't actually required — user decides |
| **Phase-scope drift** | Slice covers functionality outside parent phase's scope |
| **Demo doesn't prove goal** | Gap between what the demo exercises and what the goal claims — structural rewrite needed |
| **Done criteria don't cover goal** | Aspects of the goal have no corresponding done criterion — user decides scope |
| **Duplicate proof** | This slice proves something another slice already proves — merge/remove decision |
| **End-state fidelity** | Slice validates temporary scaffolding instead of final architecture — design decision |
| **Spec/task coverage gap** | Specs or tasks exist but don't cover the slice's proof goal — triage decision |
| **Cross-slice ordering** | Slice-order sanity issue — depends on unproven earlier behavior |
| **Registration gap** | Slice not in `_index.md` or index entry mismatched — fix via `/scaffold-update-doc` (indexes are global planning state) |
| **Stale dependency (ambiguous)** | Depends on lists a SLICE-### that doesn't exist and cannot be resolved to a unique rename — removal or replacement is a design decision |
| **Broken interface (ambiguous)** | Integration Points cites an interface not in interfaces.md and correction is not an unambiguous typo — wrong guess could silently corrupt the slice |
| **Hidden prerequisite unresolved** | Infrastructure assumed but not proven by any completed slice or declared dependency |

Before applying fixes, output a brief classification summary:

```
Pass N: X auto-fixable, Y human-required
```

## Step 4 — Apply Auto-Fixes

For each auto-fixable issue:

1. Read the relevant section of the slice file.
2. Apply the fix using the Edit tool.
3. Record what was changed and why.

**Fix rules:**
- **Only edit the target slice file.** Never edit phases, specs, tasks, system designs, indexes, or other slices. If a fix requires changes outside the slice file, classify it as human-required.
- Preserve the slice template structure — don't reorganize sections.
- Fixes must be minimal — change only what's needed to resolve the issue.
- When tightening Done Criteria or Demo steps, derive wording from the Goal and Integration Points, not invented.
- When adding systems or interfaces, verify they exist in the referenced docs before adding.
- Never change the Goal's meaning — only tighten wording or fix terminology.
- Never change what the slice proves — only how clearly it expresses the proof.

## Step 5 — Re-Review

After applying fixes, re-read the slice file and run the full review checklist again on the updated content.

Compare issues with the previous pass:
- **Resolved** — issue no longer appears. Record as fixed.
- **New issues** — the fix may have exposed a deeper issue, or the fix itself introduced a problem. Classify and fix if auto-fixable.
- **Persistent human-required** — still present. Carry forward.
- **No new issues, no remaining auto-fixable issues** — stop. The slice is as clean as auto-fixing can make it.

## Step 6 — Iterate

Continue the review-fix cycle until a stop condition is met.

**Stop conditions** (any one stops iteration):
- **Clean** — no issues found on a pass.
- **Human-only** — only human-required issues remain, no auto-fixable issues left.
- **Stable** — the remaining issue set is unchanged from the previous pass.
- **Limit** — iteration limit reached.

## Step 7 — Output

```
## Slice Fix: SLICE-### — [Name]

### Summary
| Field | Value |
|-------|-------|
| Phase | P#-### — [Name] |
| Depends on | [SLICE-### IDs or "—"] |
| Passes | N completed / M max [early stop: yes/no] |
| Auto-fixed | N issues |
| Human-required | N issues |
| Final status | Clean / Needs human input |

### Fixes Applied
| # | Category | What Changed | Section |
|---|----------|-------------|---------|
| 1 | Template text | Replaced TODO placeholder with goal-derived content | Done Criteria |
| 2 | Vague Done Criteria | "Slice works" → "Player can place wall and see room detection update within 1 tick" | Done Criteria |
| 3 | Terminology | Replaced "creature" with "colonist" | Demo Script |
| ... | ... | ... | ... |

### Human-Required Issues
| # | Category | Issue | Why Auto-Fix Cannot Resolve |
|---|----------|-------|----------------------------|
| 1 | Goal horizontal | Goal only exercises BuildingSystem with no cross-boundary effects | Goal redesign requires understanding proof intent |
| 2 | Hidden prerequisite | Demo assumes pathfinding exists but no earlier slice proves it | User decides if dependency should be declared |
| ... | ... | ... | ... |

### Final Review
[Brief final review status — which checklist areas are now clean, which still have issues]

### Review Freshness
**Invalidated by fixes** — rerun `/scaffold-review-slice` and `/scaffold-iterate slice` before approval.
```

If no issues were found on the first pass:

```
## Slice Fix: SLICE-### — [Name]

**Status: Clean** — no issues found. No changes made. Existing review/iterate freshness remains unchanged.
```

## Rules

- **Only fix mechanical, local issues.** Never make judgment calls about slice scope, boundary design, goal quality, or proof value.
- **Only edit the slice file.** Never edit phases, specs, tasks, system designs, indexes, engine docs, or other slices. If a fix requires changes outside the slice file, classify it as human-required.
- **Derive fixes from context, don't invent.** Tightened Done Criteria come from the Goal. Demo expected results come from Done Criteria. Added systems come from the Goal/Integration Points. Never fabricate content.
- **Preserve slice structure.** Don't reorganize sections or reformat beyond what the fix requires.
- **Stop when stable.** If the remaining issue set is unchanged from the previous pass, do not continue iterating.
- **Surface human-required issues clearly.** The user needs to know what still needs their attention and why.
- **Goal meaning is sacred.** Auto-fixes may tighten Goal wording or fix terminology, but never change what the slice proves. If the Goal is fundamentally wrong, that's human-required.
- **Registration fixes are human-required.** Index and slice table edits involve cross-file coordination — report them, don't attempt them. Fixing the Phase reference *inside the slice file* is auto-fixable; editing `_index.md` is not.
- **Range processing detects cross-slice issues.** When processing a range, additionally check for: duplicate proof across slices, dependency order contradictions, hidden prerequisites satisfied only by a later slice in the range, and overlapping Systems Covered suggesting a slice merge. These are always classified as human-required.

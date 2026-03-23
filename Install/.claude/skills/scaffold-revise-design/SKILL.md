---
name: scaffold-revise-design
description: Detect design drift from implementation feedback and apply safe updates or dispatch to init-design for decisions. Reads ADRs, known issues, playtest patterns, and downstream friction to identify when the design doc no longer matches what the project is actually building. Use after a phase or slice completes, or when revise-foundation detects Step 1 drift.
argument-hint: [--source PHASE-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:entry,PT:pattern,TRIAGE:action]
allowed-tools: Read, Edit, Grep, Glob
---

# Revise Design

Detect design drift and update the design document from implementation feedback: **$ARGUMENTS**

The design doc is the highest authority for player-facing intent and non-breakable design rules. But it is a living document — implementation reveals truths that design couldn't anticipate. This skill reads implementation feedback, classifies what changed, applies safe mechanical updates directly, and dispatches to `init-design` for decisions that require human judgment.

This is distinct from:
- **`init-design --mode reconcile`** — interactive contradiction resolution (this skill detects *what* needs reconciling and dispatches there)
- **`init-design --mode refresh`** — re-interviews sections when vision evolves (this skill detects *which* sections need refreshing)
- **`fix-design`** — repairs mechanical issues (this skill identifies *design-level* drift, not formatting)
- **`iterate-design`** — adversarial review of coherence (this skill processes *implementation signals*, not reviewer critique)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source` | No | auto-detect | What triggered the revision: `PHASE-###` (phase completed), `SLICE-###` (slice completed), `foundation-recheck` (dispatched from revise-foundation). If omitted, scans all recent feedback. |
| `--signals` | No | — | Comma-separated list of specific drift signals to process. When provided, skip the broad feedback scan (Step 1) and process only these items. Accepted formats: `ADR-###` (specific ADR), `KI:description` (known-issue entry keyword), `PT:pattern-name` (playtest pattern), `TRIAGE:action-keyword` (triage upstream action). This is the primary dispatch mechanism — `revise-foundation` identifies which signals affect the design doc and passes them here so revise-design doesn't re-scan everything. |

## Preconditions

1. **Design doc exists** — verify `design/design-doc.md` exists and is not at template defaults. If missing, stop: "No design doc to revise. Run `/scaffold-seed design` first."
2. **Design doc has been through Step 1 pipeline** — verify at least one iterate or fix log exists in `scaffold/decisions/review/`. If no logs exist, stop: "Design doc hasn't been stabilized yet. Run the Step 1 pipeline (init → fix → iterate → validate) first."
3. **Implementation feedback exists** — if `--signals` is provided, at least one signal must resolve to a real source document (see signal resolution rules in Step 1). If none resolve, report: "No valid implementation signals found. Nothing to revise." If `--signals` is not provided, at least one of: accepted ADRs, known issues entries, playtest patterns, triage logs, or revision logs must exist. If none exist, report: "No implementation feedback found. Nothing to revise."

## Step 1 — Gather Implementation Feedback

**If `--signals` is provided:** Skip the broad scan. Read only the specific documents referenced by the signal list. For each signal, resolve it to the source document:
- `ADR-###` → read `scaffold/decisions/ADR-###-*.md`
- `KI:keyword` → search `scaffold/decisions/known-issues.md` for the matching entry
- `PT:pattern-name` → search `scaffold/decisions/playtest-feedback.md` for the matching pattern
- `TRIAGE:keyword` → search triage logs for the matching upstream action

This is the expected path when dispatched from `revise-foundation`, which has already identified which signals affect the design doc. Proceed directly to Step 2 with the resolved signals.

**Signal resolution rules:**
- **Single match** → proceed normally with the resolved document/entry.
- **No match** → WARN: "Signal [X] could not be resolved to a source document. Skipping." Continue with remaining signals.
- **Multiple matches** → use the most recent match by date. If dates are ambiguous, present the matches to the user and ask which to process.

**If `--signals` is not provided:** Run the broad scan below. This is the expected path for manual invocation or `--source PHASE-###`/`SLICE-###`.

Read feedback sources relevant to the `--source` argument:

### 1a. ADRs

Glob `scaffold/decisions/ADR-*.md`. Filter to accepted ADRs. For each, check:
- Does it explicitly reference the design doc or a design doc section?
- Does it change a player-facing mechanic, rule, resource, or interaction?
- Does it supersede a design decision?

Technical ADRs that only affect implementation (engine patterns, data structures, performance optimizations) are not design drift — skip them.

### 1b. Known issues

Read `scaffold/decisions/known-issues.md`. Check for entries that:
- Identify design assumptions that proved wrong
- Flag mechanics that couldn't be implemented as designed
- Note player-experience problems discovered during implementation

### 1c. Playtest feedback

Read `scaffold/decisions/playtest-feedback.md`. Check for Pattern or ACT NOW entries that:
- Suggest the core loop doesn't produce the intended experience
- Indicate players don't understand the control model
- Reveal information model failures (players can't make decisions the design expects)
- Show stable-state boredom or crisis dependency

### 1d. Prototype findings

- Disprove a design assumption
- Reveal a mechanic doesn't work as designed
- Suggest a different approach to a core design element

### 1e. Triage and revision logs

Glob `scaffold/decisions/triage-logs/TRIAGE-*.md` and `scaffold/decisions/revision-logs/REVISION-*.md`. Check for upstream actions that:
- Escalate design-level questions
- Note spec/task friction caused by unclear or incorrect design intent
- Flag recurring issues traceable to a design doc section

### 1f. Downstream document drift

If `--source` is `foundation-recheck` or if scanning broadly:
- Check system designs for mechanics not described in the design doc (design decision escalation rule)
- Check specs for behavior that violates Design Invariants
- Check if implemented systems imply a different player experience than the design doc describes

Only check docs that exist — skip missing sources silently.

### 1g. Silent drift detection (broad scan only)

When running a broad scan (no `--signals`), perform these additional checks that detect drift even when no explicit signal was filed. These catch the five most common ways design docs rot silently:

**Mechanic expansion** — compare system designs against the design doc's Major Mechanics and System Domains sections. If a system defines player-facing mechanics (skill systems, trait systems, economic subsystems) not mentioned anywhere in the design doc, flag as silent expansion. One unmentioned mechanic is normal growth; multiple unmentioned mechanics across systems is scope drift.

**Pillar erosion** — for each Core Pillar, check whether implemented mechanics reinforce or pull away from it. Example: if a pillar says "indirect control" but implementation has added direct task assignment, priority buttons, and manual overrides, the pillar is eroding even though no individual change violates an invariant. Flag when the aggregate direction of implemented mechanics contradicts a pillar.

**Player role drift** — compare the Player Control Model and Player Mental Model against the control surfaces implied by implemented systems. If the design doc says "overseer" but systems provide fine-grained direct manipulation, the player role has drifted. Check: what does the player actually *do* based on the systems, vs what the design doc says they do?

**Governance becoming decorative** — for each Design Invariant, check whether any spec or system design references it (by ShortName). Invariants that are defined but never cited by any downstream document may no longer be enforcing anything. Flag as WARN: "Invariant [ShortName] is not referenced by any spec or system — it may be decorative."

**Scope creep vs Scope Reality Check** — compare the total system count, mechanic breadth, and content categories implied by all system designs against the Scope Reality Check section. If the design doc claims "moderate simulation" but 15+ interconnected systems exist, flag the mismatch. Also check: does the Simulation Depth Target still match the actual depth implied by implemented systems?

These checks produce drift signals that flow into Step 2 classification like any other signal. They are not auto-updated — they are classified and escalated normally.

Silent drift detections are low-to-medium confidence signals. A single silent drift signal should usually be corroborated by another signal or a repeated pattern before driving major design revision.

## Step 2 — Classify Drift Signals

For each feedback item, classify it against the design doc:

### 2a. Design section mapping

Map each drift signal to the specific design doc section(s) it affects:

| Signal type | Likely affected sections |
|-------------|------------------------|
| Core loop doesn't work as designed | Core Loop, Secondary Loops, Session Shape |
| Player can't do what design promises | Player Control Model, Player Verbs, Player Mental Model |
| Players don't understand consequences | Player Information Model, Simulation Transparency Policy, Information Clarity Principle |
| Mechanic violates an invariant | Design Invariants (specific ShortName) |
| New mechanic not in design doc | System Domains, Major Mechanics, or the section group where it belongs |
| Scope proved unrealistic | Scope Reality Check, Simulation Depth Target, Content Structure |
| Tone/world doesn't match implementation | Tone, Narrative Wrapper, Aesthetic Pillars |
| Progression doesn't work | Progression Arc, Player Goals, Replayability Model |

### 2b. Severity classification

| Severity | Meaning | Action |
|----------|---------|--------|
| **Cosmetic** | Wording is slightly imprecise but intent is clear and downstream docs are correct | Auto-update: tighten wording |
| **Stale reference** | Design doc references an ADR, system, or mechanic that was renamed/restructured | Auto-update: update reference |
| **Governance format normalization** | Governance structure/format drifted but meaning is unchanged (e.g., missing `Rule:` label, anchor not in single-line format, invariant missing `Invariant:` prefix) | Auto-update: fix format only |
| **Governance semantic drift** | Governance mechanism wording no longer matches what it actually protects or resolves in practice | Escalate: governance meaning changes require user confirmation |
| **Section outdated (design-led)** | A section's content no longer matches what was actually built, and the change was intentional (ADR-backed or user-approved) | Dispatch: `init-design --mode reconcile --sections [affected]` |
| **Section outdated (implementation-led)** | Implementation diverged from design without explicit approval — the build wandered off design | Escalate: design doc should not move to match unapproved divergence; present to user |
| **Design assumption wrong** | Implementation or playtesting proved a design assumption incorrect (mechanic doesn't work, scope unrealistic, player experience differs) | Dispatch: `init-design --mode refresh --sections [affected]` |
| **Invariant violation** | An implemented feature violates a Design Invariant | Escalate: present to user — either fix the feature or change the invariant |
| **Unescalated mechanic** | Downstream docs introduced a player-facing mechanic not in the design doc | Escalate: present to user — either add to design doc or remove from implementation |

### 2b-ii. Design-led vs implementation-led

Before acting on any drift signal, determine its origin:

- **Design-led change** — the team intentionally chose a new direction (backed by an accepted ADR, user decision, or playtest-driven pivot). The design doc should catch up to the new reality. → Reconcile or refresh.
- **Implementation-led divergence** — the build wandered away from the design without explicit approval. The design doc should *not* automatically update to match unapproved drift. → Escalate; the user decides whether to accept the divergence or correct the implementation.

This distinction protects design authority. Without it, the design doc silently absorbs every implementation accident as if it were intentional.

### 2c. Governance mechanism impact

For each drift signal, check whether it affects governance mechanisms:
- Does it invalidate a Design Invariant?
- Does it contradict a Decision Anchor?
- Would it cause a Pressure Test to fail?
- Does it push the game in a direction not listed in Design Gravity?

Governance impacts are always escalated — never auto-fixed.

## Step 3 — Apply Safe Updates

For each **Cosmetic**, **Stale reference**, and **Governance format normalization** item:

1. Read the affected section of the design doc.
2. Apply the fix using the Edit tool.
3. Record what was changed, why, and what feedback triggered it.

**Auto-fix rules:**
- Only edit the design doc. Never edit system designs, reference docs, or downstream documents.
- Preserve design doc structure — don't reorganize.
- Fixes must be minimal — change only what's needed.
- Never change what the game is — only update how the doc expresses accepted project reality (built behavior, approved pivots, validated findings).
- Never weaken governance mechanisms. If an invariant needs weakening, escalate.
- Preserve `<!-- PROVISIONAL -->` markers if the section is still uncertain.

## Step 4 — Dispatch Reconciliation

For each **Section outdated (design-led)** item:
- Present the drift to the user: "Section [X] says [old]. ADR-### changed this to [new]. Reconcile?"
- If the user confirms, dispatch: `init-design --mode reconcile --sections [affected group]`

For each **Section outdated (implementation-led)** and **Governance semantic drift** item:
- Present the divergence to the user: "Section [X] says [design intent]. Implementation does [actual behavior]. This divergence was not ADR-backed."
- User decides: accept the divergence (update design), correct the implementation, or defer.

For each **Design assumption wrong** item:
- Present the finding: "Section [X] assumed [assumption]. Implementation/playtest showed [reality]."
- If the user agrees the section needs refreshing, dispatch: `init-design --mode refresh --sections [affected group]`

## Step 5 — Escalate Governance Issues

For each **Invariant violation** and **Unescalated mechanic**:

Present using the Human Decision Presentation pattern (see WORKFLOW.md):

```
### Design Escalation #N

**Signal:** [source — ADR-###, playtest pattern, triage action, etc.]
**Affected section:** [design doc section]
**Current design says:** [what the design doc states]
**Implementation reality:** [what was actually built or observed]

**Options:**
a) Update the design doc to match implementation — [implication]
b) file via `/scaffold-file-decision --type adr` to change the implementation to match design — [implication]
c) Defer — file via `/scaffold-file-decision --type ki` for future resolution
```

Wait for the user's decision on each escalation before proceeding.

## Step 6 — Update Revision History

After all actions in this run (auto-updates applied, reconciliations dispatched, and escalation resolutions), append a revision entry to a persistent log:

**Log location:** `scaffold/decisions/revision-logs/REVISION-design-YYYY-MM-DD.md`

```markdown
# Design Revision: YYYY-MM-DD

**Source:** [PHASE-### completed / SLICE-### completed / foundation-recheck / broad scan]
**Feedback items processed:** N
**Auto-updated:** N
**Reconciled:** N sections
**Escalated:** N issues
**Deferred:** N issues

## Changes Applied
| # | Section | Change | Trigger |
|---|---------|--------|---------|
| 1 | Core Loop | Updated wording to match ADR-### | ADR-### |
| 2 | Design Invariants | Tightened phrasing of Invariant: X | Spec friction |

## Reconciliations Dispatched
| # | Section Group | Mode | Reason |
|---|--------------|------|--------|
| 1 | Shape | reconcile | Core Loop rewritten per ADR-### |

## Escalations
| # | Type | Section | Resolution |
|---|------|---------|------------|
| 1 | Invariant violation | Invariant: X | User chose option (a) — updated invariant |
| 2 | Unescalated mechanic | System Domains | User chose option (c) — deferred to KI |

## Deferred Issues
| # | Section | Issue | Reason |
|---|---------|-------|--------|
| 1 | Scope Reality Check | Simulation depth may be unrealistic | Needs more implementation data |
```

## Step 7 — Report

```
## Design Revised

### Summary
| Field | Value |
|-------|-------|
| Source | [PHASE-### / SLICE-### / foundation-recheck / broad scan] |
| Feedback items | N processed |
| Auto-updated | N |
| Reconciled | N sections dispatched to init-design |
| Escalated | N issues (N resolved, N deferred) |
| Governance impacts | N (invariant: N, anchor: N, pressure test: N) |
| Section groups changed | [comma-separated list, e.g., "Shape, Philosophy"] |

### Design Health Delta
| Metric | Before | After |
|--------|--------|-------|
| Sections at risk | N | N |
| Governance mechanisms intact | N/N | N/N |
| PROVISIONAL markers | N | N |

### Design Confidence
**Stable / Decreased / Improved** — [Based on: number and severity of drift signals, governance mechanism integrity, number of escalations vs auto-updates.]

### Next Steps
- Run `/scaffold-fix design` to clean up any mechanical issues from edits
- Run `/scaffold-iterate design --sections "[changed groups]"` to review only the changed areas (converges early if clean)
- Run `/scaffold-validate --scope design` to confirm structural readiness
```

If no drift detected:
```
## Design Revised

**Status: No drift detected** — design doc is consistent with implementation feedback. No changes made.
```

## Rules

- **Only edit the design doc.** Never edit system designs, reference docs, glossary, engine docs, ADRs, or downstream documents.
- **Design intent is sacred until the user changes it.** Auto-updates tighten wording to match accepted project reality — they never change what the game is. If implementation diverged from design intent, that's an escalation, not an auto-update.
- **Core Fantasy and Core Pillars cannot be modified by revise-design.** These sections define the identity of the game. If drift signals suggest the identity has shifted, escalate to the user and recommend `init-design --mode refresh --sections Identity`. Revise-design reconciles details; it does not change identity.
- **Governance semantic changes are always escalated.** Never auto-update an invariant's meaning, an anchor's tradeoff, a pressure test's scenario, or a gravity direction. These are the design's load-bearing structure. Format-only normalization that preserves meaning exactly (adding missing labels, fixing structure to match template format) may be auto-updated.
- **ADR supersedence is rare and explicit.** Only ADRs that explicitly supersede a design decision trigger section updates. Technical ADRs do not override game design.
- **Playtest feedback is a high-value drift signal.** If players consistently experience something different from what the design doc describes, investigate whether the issue is design intent, implementation quality, onboarding, or information clarity before revising the design doc. The design may be correct but poorly expressed in the build.
- **Do not invent new design to fill gaps.** If implementation revealed a gap, flag it for the user. Don't silently add mechanics, loops, or governance rules.
- **Dispatch, don't duplicate.** For reconciliation and refresh, dispatch to init-design's existing modes. Don't re-implement those workflows here.
- **Only accepted or observed signals count as drift.** Do not revise the design doc based on speculative proposals, unaccepted ADRs, triage options that were discussed but not chosen. Proposed ≠ accepted. Explored ≠ decided.
- **Classify before acting.** Every feedback item must be classified before any edits occur. This prevents auto-updating something that should be escalated.
- **Deferred issues are routed by type.** When the user chooses to defer an escalation: active risks or mismatches go to `scaffold/decisions/known-issues.md`; purely strategic deferred decisions (revisit-later questions with no current risk) may remain in the revision log only or be captured as ADR follow-up items. Not every deferral belongs in known-issues — that file tracks live risks, not a backlog of open questions.
- **Always write a revision log.** Every run produces a dated record in `scaffold/decisions/revision-logs/`.
- **Confidence heuristic.** Improved: mostly auto-updates, governance intact, no escalations. Stable: mix of auto-updates and reconciliations, governance intact. Decreased: multiple escalations, governance mechanisms affected, or invariant violations.

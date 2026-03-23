---
name: scaffold-revise-input
description: Detect Step 6 input doc drift from implementation feedback and apply safe updates or escalate for decisions. Reads ADRs, known issues, spec/task friction, code review findings, interaction model changes, and Step 5 doc changes to identify when input docs no longer match what was actually built or what upstream docs now define. Use after a phase or slice completes, or when revise-foundation detects Step 6 drift.
argument-hint: [--source PHASE-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword,TRIAGE:action,SPEC:keyword,CODE-REVIEW:keyword,STYLE:doc-changed] [--target doc.md]
allowed-tools: Read, Edit, Grep, Glob
---

# Revise Input

Detect input doc drift and update from implementation feedback: **$ARGUMENTS**

Input docs are the mapping layer between design intent (what the player does) and implementation reality (what keys/buttons/navigation paths exist). Implementation reveals realities that initial design couldn't anticipate: new actions are needed, bindings conflict in practice, navigation breaks on certain screens, philosophy principles prove infeasible, and upstream docs (interaction model, ui-kit) change in ways that invalidate input assumptions.

This skill reads implementation feedback, classifies what changed, applies safe evidence-backed updates directly, and escalates design-level changes for human decision.

This is distinct from:
- **`fix-input`** — repairs mechanical structure (this skill identifies *design-level* drift, not formatting)
- **`iterate-input`** — adversarial design review (this skill processes *implementation signals*, not reviewer critique)
- **`seed input`** — creates input docs from scratch (this skill updates existing docs from feedback)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source` | No | auto-detect | What triggered the revision: `PHASE-###` (phase completed), `SLICE-###` (slice completed), `foundation-recheck` (dispatched from revise-foundation). If omitted, scans all recent feedback. |
| `--signals` | No | — | Comma-separated list of specific drift signals to process. When provided, skip the broad feedback scan and process only these items. This is the primary dispatch mechanism — `revise-foundation` identifies which signals affect input docs and passes them here. |
| `--target` | No | all | Target a single input doc by filename (e.g., `--target action-map.md`). When set, only edit that doc; flag cross-doc implications for fix-input. |

**Signal resolution:**

| Signal format | Resolves to |
|--------------|-------------|
| `ADR-###` | Read `scaffold/decisions/ADR-###-*.md` |
| `KI:keyword` | Search `scaffold/decisions/known-issues.md` for matching entry |
| `TRIAGE:keyword` | Search triage logs for matching upstream action |
| `SPEC:keyword` | Search spec files for friction notes matching the keyword |
| `CODE-REVIEW:keyword` | Search code review logs for findings matching the keyword |
| `STYLE:doc-changed` | Read the named Step 5 doc for changes that affect input (interaction-model changes are highest priority) |

**Signal resolution rules:**
- **Single match** → proceed normally.
- **No match** → WARN: "Signal [X] could not be resolved. Skipping." Continue with remaining signals.
- **Multiple matches** → use most recent by date. If ambiguous, present matches to user.

## Preconditions

1. **Input docs exist** — verify at least `inputs/action-map.md` exists and is not at template defaults. If no input docs exist, stop: "No input docs to revise. Run `/scaffold-seed input` first."
2. **Input docs have been through Step 6 pipeline** — verify at least one fix or iterate log exists in `scaffold/decisions/review/` matching `FIX-input-*` or `ITERATE-input-*`. If no logs exist, stop: "Input docs haven't been stabilized yet. Run the Step 6 pipeline (seed → fix → iterate) first."
3. **Implementation feedback exists** — if `--signals` is provided, at least one signal must resolve to a real source document. If `--signals` is not provided, at least one of: accepted ADRs, known issues entries, triage logs, code review findings, spec/task friction signals, or upstream doc changes must exist. If none exist, report: "No implementation feedback found. Nothing to revise."

### Context Files

| Context File | Why |
|-------------|-----|
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules |
| `scaffold/design/interaction-model.md` | Rank 2 authority: what the player does. Primary upstream for input docs. |
| `scaffold/design/design-doc.md` | Player Verbs, Core Loop, Input Feel |
| `scaffold/design/ui-kit.md` | Component references for navigation (if exists) |
| `scaffold/design/glossary.md` | Canonical terminology |

## Step 1 — Gather Implementation Feedback

**If `--signals` is provided:** Skip the broad scan. Read only the specific documents referenced by the signal list.

**If `--signals` is not provided:** Run the broad scan below.

### 1a. ADRs

Glob `scaffold/decisions/ADR-*.md`. Filter to accepted ADRs. For each, check:

| ADR affects | Input docs likely affected |
|------------|--------------------------|
| Player verbs or interaction model | action-map (new/changed/removed actions) |
| Input feel or responsiveness | input-philosophy (targets, constraints) |
| Device support or accessibility | input-philosophy, both binding docs |
| UI panels or screens | ui-navigation (focus flow, navigation model) |
| Game modes (build, zone, inspect) | action-map (mode actions), both binding docs, ui-navigation |
| Control model (direct vs indirect) | input-philosophy, action-map (granularity) |

### 1b. Known issues

Read `scaffold/decisions/known-issues.md`. Check for entries that:
- Identify input behaviors that proved wrong during implementation
- Flag binding conflicts encountered during gameplay
- Note navigation failures on specific screens
- Describe accessibility issues discovered during testing

### 1c. Interaction model changes

Read `scaffold/design/interaction-model.md`. Compare against the input docs' last known baseline (from the most recent `REVISION-input-YYYY-MM-DD.md` that lists the doc in `Docs affected`). Check for:
- New player actions added to the interaction model with no corresponding action ID
- Removed or renamed interactions that still have action IDs
- Changed selection/command/mode behaviors that affect bindings or navigation
- New UI components in the interaction model that navigation doesn't cover

### 1d. UI-kit changes

If `scaffold/design/ui-kit.md` exists, check for:
- New screens or panels that navigation doesn't reference
- Removed components that navigation still references
- Changed component states that affect interaction patterns

### 1e. Spec/task friction

Search completed specs and tasks for explicit input drift evidence. Only treat an artifact as a drift signal if it contains one of:
- Explicit friction note tied to an input action, binding, or navigation element
- Explicit note stating an action ID was missing or incorrect during implementation
- Explicit binding conflict encountered during implementation
- Explicit navigation failure noted during testing

Normal implementation detail is not friction. The signal must be explicit, not inferred.

### 1f. Code review findings

Search code review logs for:
- Input wiring that doesn't match action-map IDs
- Binding assumptions in code that contradict binding docs
- Navigation implementations that differ from ui-navigation
- Hardcoded input checks that should use action IDs

**Evidence threshold:** Code review findings alone indicate divergence but are not sufficient authority for design-led updates unless backed by an accepted ADR, resolved triage decision, completed spec, or explicit user decision. Treat as WARN-level signals that corroborate other evidence.

### 1g. Triage and revision logs

Glob triage logs and revision logs. Check for:
- Upstream actions that escalated input-level questions
- Spec/task changes that imply input docs are outdated
- Recurring friction traceable to specific input definitions

### 1h. Early exit check

After gathering all signals, filter to those that actually map to input docs. If no signals survived filtering, report: "No input-impacting drift detected from [source]. No changes made." and exit.

Only read docs that exist — skip missing sources silently.

## Step 2 — Classify Drift Signals

### 2a. Map signals to docs

| Signal type | Likely affected doc(s) | Likely affected section(s) |
|-------------|----------------------|--------------------------|
| New player verb / interaction | action-map | Actions table (new rows), Source column |
| Removed/renamed interaction | action-map | Actions table (deprecation), binding docs (orphan cleanup) |
| Action split/merge/repurpose | action-map, binding docs, ui-navigation | Actions table (old→new mapping), binding migration, navigation references |
| Binding conflict in implementation | default-bindings-kbm/gamepad | Binding tables |
| New screen or panel | ui-navigation | Focus Flow, Navigation Actions |
| Navigation failure | ui-navigation | Focus Flow, Mouse Behavior |
| Accessibility issue | input-philosophy | Accessibility section, binding docs |
| Responsiveness problem | input-philosophy | Responsiveness section |
| Mode change (build/zone/inspect) | action-map, ui-navigation, binding docs | Namespace groups, mode-specific bindings, focus rules |
| Device parity gap | input-philosophy, binding docs | Device support, missing bindings |
| Engine constraint discovered | input-philosophy | Constraints section |

### 2b. Evidence precedence

Conflicts between signals are resolved by evidence rank:

1. Accepted ADR (highest)
2. User decision (triage/revision log)
3. Higher-authority doc updated through approved pipeline (interaction-model change)
4. Completed spec/task
5. Code review / friction evidence
6. Known issue note (lowest)

Lower-ranked evidence cannot override higher-ranked. Conflicting same-rank evidence escalates automatically.

### 2c. Severity classification

| Severity | Meaning | Action |
|----------|---------|--------|
| **Stale reference** | Input doc references renamed/restructured upstream doc | Auto-update: fix reference |
| **Missing action** | Interaction model or ADR adds a new player action with no action ID | Auto-update: add action row with Source traceability |
| **Orphan binding** | Action removed/deprecated but binding still exists | Auto-update: remove orphan binding |
| **Binding doc alignment** | New action added to action-map needs default binding | Auto-update: propose binding based on namespace conventions |
| **Navigation reference update** | UI-kit added/renamed a component that navigation references | Auto-update: fix component reference |
| **Terminology drift** | Glossary term changed, input docs still use old term | Auto-update: replace term |
| **New action (design-led)** | ADR or interaction model intentionally added behavior not in action-map | Escalate: add action with user confirmation on ID and namespace |
| **Action mutation** | Existing action split, merged, or repurposed (e.g., `player_interact` → `player_interact_primary` + `player_interact_secondary`) | Escalate: present old→new mapping, binding migration plan, navigation impact. Both old and new actions coexist until migration is confirmed. |
| **Action removal (design-led)** | ADR or interaction model removed a behavior | Escalate: deprecate action, update bindings, confirm with user |
| **Degraded usability** | Action technically works but bindings violate ergonomics, require awkward hand positions, or contradict philosophy intent (e.g., core action on a modifier combo) | Escalate (HIGH): action "works" but player experience is degraded — propose rebinding or philosophy amendment |
| **Binding redesign** | Implementation revealed current bindings are unusable | Escalate: propose new bindings with user confirmation |
| **Philosophy violation** | Implementation reality contradicts philosophy principle | Escalate: update philosophy or change implementation |
| **Navigation model change** | New screens or modes require fundamentally different navigation | Escalate: update navigation model with user confirmation |
| **Device parity gap** | Implementation works on one device but not another | Escalate: add bindings or document exclusion |
| **Accessibility change** | Implementation revealed accessibility gap or new requirement | Escalate: update philosophy and bindings |
| **Complexity overflow** | Input system exceeds complexity constraints: too many actions per context, too many modifier combos, too many mode switches required for core flows | Escalate (HIGH): propose simplification, action consolidation, or mode reduction |

### 2d. Design-led vs implementation-led

Before acting on any drift signal, determine its origin:
- **Design-led change** — backed by an accepted ADR, interaction model update, or user approval. Input docs should catch up.
- **Implementation-led divergence** — the build wandered from the input docs without approval. Input docs should *not* automatically update. Escalate.

**Repeated divergence:** If the same divergence appears in 2+ prior revision logs for the same doc and section, escalate as "Forced decision required" — present only options (a) or (b), not defer. Repeated deferral on the same issue creates permanent drift.

**Divergence equivalence key:** (affected doc, affected section, topic).

## Step 3 — Apply Safe Updates

For each **auto-update-category** item:

1. Read the affected input doc.
2. Apply the update using the Edit tool.
3. Record what was changed, why, and what feedback triggered it.

**Auto-update safety rules:**

- **Only edit input docs.** Never edit interaction-model, design-doc, ui-kit, feedback-system, system designs, reference docs, engine docs, or planning docs.
- **Respect upstream authority.** interaction-model (Rank 2) and design-doc (Rank 1) govern input docs (Rank 3). Never auto-update input docs in a direction that contradicts upstream.
- **New actions must have Source traceability.** When adding an action row, always include a Source column entry tracing to the specific design artifact that backs it.
- **New actions must follow naming convention.** `lowercase_snake_case` with correct namespace prefix.
- **Binding additions follow namespace conventions.** When auto-adding a binding for a new action, propose a binding consistent with the namespace's existing patterns. If no clear convention exists, escalate instead.
- **Orphan cleanup is safe.** Removing bindings for deprecated/removed actions is always auto-fixable.
- **Navigation reference updates are safe.** Fixing component references to match renamed ui-kit components is always auto-fixable.
- **Terminology drift is safe.** Replacing NOT-column terms with canonical terms follows glossary rules. Do not normalize inside code blocks, examples, or quoted text.
- Mark auto-updated content with `<!-- REVISED: [date] — [trigger] -->` so fix/iterate passes know what was changed from feedback vs original authoring.
- **When `--target` is set, only edit the targeted doc.** Flag cross-doc implications for fix-input.

## Step 4 — Escalate Design-Level Changes

For each drift signal classified as non-auto-fixable — including **new action (design-led)**, **action removal**, **binding redesign**, **philosophy violation**, **navigation model change**, **device parity gap**, and **accessibility change**:

Present using the Human Decision Presentation pattern:

```
### Input Escalation #N

**Signal:** [source — ADR-###, interaction model change, spec friction, code review finding]
**Affected doc(s):** [action-map / input-philosophy / bindings / ui-navigation]
**Section(s):** [Actions table, Bindings, Focus Flow, etc.]
**Current input doc says:** [what the doc states]
**Implementation/upstream reality:** [what was actually built or what changed upstream]
**Design-led or implementation-led:** [backed by ADR/interaction-model, or unapproved divergence]

**Options:**
a) Update input doc to match — [implications, cross-doc effects]
b) Keep input doc, update implementation/upstream — [implications]
c) Defer — file via `/scaffold-file-decision --type ki` for future resolution

**Likely follow-up:** [fix-input / iterate-input --topics N / validate --scope input / none]
```

**Escalation severity weighting:**

| Severity | Examples |
|----------|---------|
| **CRITICAL** | Accessibility change, device parity gap affecting core gameplay |
| **HIGH** | Philosophy violation, navigation model change, action removal |
| **MEDIUM** | Binding redesign, new action requiring namespace decision |

Present CRITICAL first, then HIGH, then MEDIUM.

**For action removals:** present the full impact — which bindings reference the action, which navigation elements depend on it, which specs reference it.

**For philosophy violations:** present the principle and the implementation reality side by side. Likely follow-up: iterate-input Topic 2.

**For navigation model changes:** present the current model and what screens/modes need different navigation. Likely follow-up: iterate-input Topic 4.

## Step 5 — Cross-Doc Consistency Check

After applying updates and resolving escalations, verify cross-doc alignment:

1. **Action-map → Bindings** — every non-excluded action has bindings in both docs. New actions added in Step 3 need bindings.
2. **Action-map → Navigation** — `ui_` actions used in navigation exist in action-map. New `ui_` actions need navigation references.
3. **Bindings ↔ Philosophy** — updated bindings don't violate philosophy constraints. If a new binding introduces a modifier combo and philosophy says "no chords," flag it.
4. **Navigation → UI-kit** — if ui-kit changed and navigation was updated, verify component references still resolve.
5. **Action-map → Interaction model** — action IDs still cover all interaction model actions. If interaction model changed, verify no gaps.
6. **All → Glossary** — terminology updated during revision uses canonical terms.

**Apply deterministic alignment updates** within input docs only (adding a binding for a newly added action, fixing a stale component reference). Escalate or log as advisory for semantic choices (which key to bind, which navigation model to use).

**Do not auto-heal around unresolved escalations** — if an inconsistency depends on a pending escalation from Step 4, don't align yet.

**Block propagation on CRITICAL inconsistency** — if any CRITICAL-severity escalation is unresolved (accessibility change, device parity gap affecting core gameplay), skip ALL downstream alignment updates in this step. Only report and escalate. Spreading alignment updates when a critical assumption is broken risks propagating bad state across all 5 docs.

## Step 5b — Input Simulation Check

After cross-doc consistency and before writing the revision log, simulate a core gameplay loop using the current state of all input docs. This catches gaps that document-level checks miss.

1. **Select a representative flow** from the interaction model — ideally one that spans multiple modes (gameplay → build → menu → gameplay) and includes error handling.
2. **Walk the flow through input docs:**
   - For each player intent in the flow, verify a corresponding action exists in action-map.
   - For each action, verify reachable bindings exist in both KBM and gamepad docs (or documented exclusions).
   - For each UI transition, verify navigation covers the focus change.
   - For each mode switch, verify actions are available in the new context.
3. **Flag simulation breaks:**
   - **Dead end** — a required player intent has no action, no binding, or no navigation path.
   - **Mode gap** — switching modes leaves the player with no way to perform a required action.
   - **Return failure** — after entering a sub-flow (build mode, menu), there's no clear path back.

4. **Check complexity constraints:**
   - Count actions per context (namespace). If any context exceeds a reasonable threshold (varies by game — colony sims typically 15-20 per context), flag as complexity overflow.
   - Count modifier-dependent actions. If more than a third of actions in a context require modifiers, flag.
   - Count mode switches required to complete the simulated flow. If the flow requires 3+ mode switches for a common task, flag.

If any simulation breaks or complexity overflows are found, add them to the escalation list as HIGH severity. These are interaction-level failures, not document-level — they only appear when tracing flows end-to-end.

This check is advisory for `--target` runs (single-doc edits may not capture flow breaks). It is mandatory for broad scans and `--source` runs.

## Step 6 — Update Revision History

After all actions (auto-updates, escalation resolutions), append a revision entry to a persistent log:

**Log location:** `scaffold/decisions/revision-logs/REVISION-input-YYYY-MM-DD.md`

```markdown
# Input Revision: YYYY-MM-DD

**Revision Timestamp:** YYYY-MM-DDTHH:MM:SSZ
**Source:** [PHASE-### completed / SLICE-### completed / foundation-recheck / broad scan]
**Feedback items processed:** N
**Auto-updated:** N
**Escalated:** N issues
**Deferred:** N issues
**Docs affected:** [list]

**Per-doc baselines used:**
| Doc | Baseline from |
|-----|--------------|
| action-map.md | REVISION-input-YYYY-MM-DD (or "first revision") |
| input-philosophy.md | REVISION-input-YYYY-MM-DD (or "first revision") |
| default-bindings-kbm.md | REVISION-input-YYYY-MM-DD (or "first revision") |
| default-bindings-gamepad.md | REVISION-input-YYYY-MM-DD (or "first revision") |
| ui-navigation.md | REVISION-input-YYYY-MM-DD (or "first revision") |

## Updates Applied
| # | Doc | Section/Entry | Change | Trigger | Classification |
|---|-----|--------------|--------|---------|----------------|
| 1 | action-map.md | Actions / player_ | Added `player_zone_paint` | ADR-023 | Missing action |
| 2 | default-bindings-kbm.md | player_ Bindings | Added binding for `player_zone_paint`: Click+Drag | ADR-023 | Binding doc alignment |

## Escalations
| # | Severity | Type | Doc(s) | Resolution |
|---|----------|------|--------|------------|
| 1 | HIGH | Philosophy violation | input-philosophy | User chose option (a) — updated "no chords" to allow Shift+Click for multi-select |
| 2 | MEDIUM | Binding redesign | default-bindings-gamepad | User chose option (c) — deferred to KI |

## Deferred Issues
| # | Doc | Issue | Reason |
|---|-----|-------|--------|
| 1 | default-bindings-gamepad | Button exhaustion for zone tools | Needs gameplay testing data |

## Drift Trend
| Direction | Count this revision | Cumulative (all revisions) |
|----------|-------------------|--------------------------|
| Design-led → input catches up | N | N |
| Implementation-led → escalated | N | N |

*If implementation-led count exceeds 3 cumulative in the same domain (action coverage, bindings, navigation, philosophy), flag: "Design no longer reflects reality in [domain] — upstream revision required via `/scaffold-revise-style` targeting interaction-model."*

## Advisory Drift Deferred
| # | Upstream Doc | Affected Input Doc | Reason Suppressed |
|---|-------------|-------------------|-------------------|
| 1 | ui-kit.md (Draft) | ui-navigation.md | Upstream not yet Approved — advisory only |
```

## Step 7 — Report

**If drift detected:**

```
## Input Docs Revised

### Summary
| Field | Value |
|-------|-------|
| Source | [PHASE-### / SLICE-### / foundation-recheck / broad scan] |
| Feedback items | N processed |
| Auto-updated | N |
| Escalated | N issues (N resolved, N deferred) |
| Docs affected | N |

### Input Confidence
**Stable / Decreased / Improved** — [Based on: number and severity of drift signals, whether action coverage held, whether device parity is intact, whether philosophy principles survived implementation.]

### Next Steps
- Run `/scaffold-fix input [--target doc]` to clean up mechanical issues from updates
- Run `/scaffold-iterate input [--topics "affected-topics"]` to review changed areas
- Run `/scaffold-validate --scope input` to confirm structural readiness
```

**If no drift detected:**

```
## Input Docs Revised

**Status: No drift detected** — input docs are consistent with implementation feedback. No changes made.
```

**Confidence heuristic (advisory only):**
- **Improved:** mostly auto-updates, action coverage maintained, philosophy principles intact, bindings stable
- **Stable:** mix of auto-updates and escalations, device parity intact, some binding adjustments
- **Decreased:** philosophy violations, action removals, navigation model changes, device parity gaps, accessibility issues

## Rules

- **Only edit input docs.** Never edit interaction-model, design-doc, ui-kit, feedback-system, system designs, reference docs, engine docs, or planning docs.
- **Respect upstream authority.** interaction-model (Rank 2) and design-doc (Rank 1) govern input docs (Rank 3). Input docs catch up to upstream, never the reverse.
- **When `--target` is set, only edit that doc.** Flag cross-doc implications for fix-input.
- **Action IDs are sacred until the user changes them.** Never auto-rename action IDs. Renaming is a breaking change that requires an ADR.
- **Philosophy principles are sacred until the user changes them.** Never auto-update principles, responsiveness targets, or accessibility commitments. Those define the input contract.
- **Navigation model is sacred until the user changes it.** Never auto-change the navigation model (spatial/tab-order/hybrid). Model changes are design decisions.
- **Only accepted or corroborated signals count as drift.** Do not revise input docs based on speculative proposals, unaccepted ADRs, or triage options that were discussed but not chosen.
- **Design-led changes catch up. Implementation-led divergence escalates.** If the team intentionally changed direction (ADR-backed, interaction model updated), input docs should update. If the build wandered without approval, escalate.
- **New actions require Source traceability.** Every new action added to action-map must have a Source column entry. No actions without traceable design canon backing.
- **Binding additions follow conventions.** When adding bindings for new actions, follow the namespace's existing binding patterns. If no clear pattern exists, escalate.
- **Device parity gaps are always escalated.** Never auto-exclude an action from a device. Exclusions require explicit user decision.
- **Accessibility changes are always escalated.** Never auto-weaken an accessibility commitment. Changes to accessibility require explicit user confirmation.
- **Repeated divergence forces a decision.** If the same divergence appears in 2+ prior revision logs, present only options (a) and (b) — no defer. Repeated deferral creates permanent drift.
- **Evidence precedence resolves conflicts.** Accepted ADR > user decision > upstream doc change > completed spec > code review > known issue.
- **Cross-doc updates follow authority.** action-map drives bindings and navigation. Philosophy constrains bindings. Interaction model governs action-map. Changes flow downstream, never upstream.
- **Revision suppression when upstream is unstable.** If interaction-model is Draft or under active revision, suppress non-referential auto-updates to input docs. Flag as advisory drift. Referential breakage (stale component names, missing action references) still auto-fixes.
- **Do not auto-heal around unresolved escalations.** If a cross-doc inconsistency depends on a pending escalation, don't align yet.
- **Always write a revision log.** Every run produces a dated record in `scaffold/decisions/revision-logs/`.
- **Action mutations are always escalated.** Splits, merges, and repurposing of existing actions require explicit old→new mapping, binding migration plan, and navigation impact assessment. Old and new actions coexist until migration is confirmed.
- **Degraded usability is drift, not acceptance.** An action that "works" but violates ergonomics or philosophy intent is a HIGH-severity escalation, not a pass.
- **Simulation check is mandatory for broad scans.** Every non-targeted revision run must walk at least one core gameplay flow through all input docs end-to-end. Advisory for `--target` runs.
- **CRITICAL inconsistencies block propagation.** Unresolved CRITICAL escalations halt all downstream alignment updates. Don't spread bad state.
- **Complexity overflow is tracked.** If the input system grows beyond reasonable complexity constraints (actions per context, modifier density, mode switch depth), escalate for simplification.
- **Drift direction is tracked cumulatively.** If implementation-led divergence exceeds 3 cumulative in the same domain, flag that design no longer reflects reality and recommend upstream revision.
- **Confidence heuristic is advisory only.** It helps humans prioritize review effort. It does not block or gate anything.

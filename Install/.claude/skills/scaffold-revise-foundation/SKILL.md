---
name: scaffold-revise-foundation
description: Detect foundation drift from implementation feedback and dispatch revision loops to affected Step 1-6 docs. On initial pass, verifies foundational doc layers completed their normal stabilization pipeline. On recheck, reads ADRs/KIs/triage/spec-task friction to identify which docs need updating, then dispatches their normal stabilization pipeline.
argument-hint: [--mode initial|recheck]
allowed-tools: Read, Grep, Glob
---

# Revise Foundation

Detect foundation drift and dispatch revision loops to affected docs: **$ARGUMENTS**

This skill is the entry point for Step 7's pipeline. It has two modes:

- **Initial mode** (`--mode initial`, default) — On first pass after Steps 1–6, there is no implementation feedback to revise from. The skill verifies that Steps 1–6 each completed their normal stabilization pipeline (create/seed → review/fix → iterate → validate), reports their status, and proceeds. This is effectively a readiness check, not a revision.

- **Recheck mode** (`--mode recheck`) — After a phase completes, reads implementation feedback to identify which foundation docs need updating, then dispatches the appropriate revision loop for each affected doc.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--mode` | No | `initial` | `initial` for first pass (readiness check), `recheck` for post-implementation. |

### Context Files

| Context File | Why |
|-------------|-----|
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |

## Initial Mode

### Verify Steps 1–6 readiness

For each Step 1–6 doc layer, check the expected stabilization pipeline completed:

| Step | Doc Layer | Expected Pipeline | Validation Gate |
|------|-----------|-------------------|-----------------|
| 1 | Design | init-design → fix-design → iterate-design → validate --scope design | `validate --scope design` passes |
| 2 | Systems | bulk-seed-systems → fix-systems → iterate-systems → validate --scope systems | `validate --scope systems` passes |
| 3 | References | bulk-seed-references → fix-references → iterate-references → validate --scope refs | `validate --scope refs` passes |
| 4 | Engine | bulk-seed-engine → fix-engine → iterate-engine | fix + iterate passes |
| 5 | Visual/UX | bulk-seed-style → fix-style → iterate-style | fix + iterate passes |
| 6 | Inputs | bulk-seed-input → fix-input → iterate-input → validate --scope input | `validate --scope input` passes |

For each layer, verify:
- Do the documents exist and have non-placeholder content? (not stubs or template defaults)
- Did the appropriate review/fix/iterate pass run? (check for review logs, iterate logs, or fix logs)
- Did validation pass where applicable? (Step 1: `validate --scope design`, Step 2: `validate --scope systems`, Step 3: `validate --scope refs`, Step 6: `validate --scope input`)
- Are there unresolved structural issues, failed validations, or placeholder-heavy docs?

Report status per layer:

```
## Foundation Readiness

| Step | Doc Layer | Status | Pipeline | Notes |
|------|-----------|--------|----------|-------|
| 1 | Design | Ready | init → fix → iterate → validate | All 13 design checks pass |
| 2 | Systems | Partial | seed → fix → iterate | 2 systems still stubs |
| 3 | References | Ready | seed → fix → validate | Reviewed, validated |
| 4 | Engine | Ready | seed → fix → iterate | Reviewed, iterated |
| 5 | Visual/UX | Ready | seed → fix → iterate | Reviewed, iterated |
| 6 | Inputs | Ready | seed → fix → iterate → validate | All input checks pass |

**Proceed to validate --scope foundation (7b):** Yes / No — [reason if no]
```

If any doc layer is not ready (missing, all stubs, never reviewed), stop and direct back to the appropriate step.

## Recheck Mode

### Step 1 — Gather implementation feedback

Read:
- ADRs filed during implementation (created/accepted since last foundation gate pass)
- `known-issues.md` deltas
- Triage logs and upstream actions
- Prototype findings
- Phase/roadmap revision notes and revision logs
- Playtest feedback patterns
- Implementation friction signals
- Code review findings that suggest foundation drift
- Spec/task friction signals (repeated triage, blocked tasks, recurring spec conflicts that suggest underlying architecture misalignment)

### Step 1.5 — Normalize and deduplicate signals

Different sources often describe the same underlying issue differently:
- ADR-015: "Changed handle lifecycle"
- KI: "Stale entity references after load"
- Task friction: "Entity lookup failing in save/load path"

These are the same signal. Processing them separately risks duplicate or conflicting revisions.

1. **Group signals by root cause.** Cluster signals that describe the same underlying issue (same entity/concept, same doc area, same behavioral symptom) into unified drift entries.
2. **Classify each unified signal:**
   - **Structural** — doc structure, references, or registration changed
   - **Behavioral** — gameplay behavior, ownership, or contracts changed
   - **Performance** — scaling, budget, or efficiency assumptions changed
   - **Usability** — player-facing interaction, accessibility, or input assumptions changed
3. **Assign impact scope:**
   - **Local** — affects a single doc within one layer
   - **Layer-wide** — affects multiple docs within one layer
   - **Cross-layer** — affects docs across 2+ layers
4. **Assign severity:**
   - **Critical** — breaks system integrity (ownership violation, authority contradiction, identity model conflict)
   - **High** — blocks workflow (missing registrations, contract gaps, unresolvable references)
   - **Medium** — degrades quality (stale references, terminology drift, coverage gaps)
   - **Low** — cosmetic (formatting, template markers, minor wording)
5. **Deduplicate.** If two signals map to the same root cause and same affected docs, merge into one entry. Keep all source references for traceability.
6. **Assign signal IDs and persist the mapping.** Every normalized signal gets a sequential ID (SIG-001, SIG-002, ...) and is tracked through the full dispatch lifecycle:

```
### Normalized Signals

| Signal ID | Root Cause | Type | Severity | Scope | Affected Layers | Source(s) | Status |
|----------|------------|------|----------|--------|-----------------|-----------|--------|
| SIG-001 | Handle lifecycle change | Behavioral | Critical | Cross-layer | Systems, References | ADR-015, KI-22 | Active |
| SIG-002 | Stale UI component ref | Structural | Medium | Local | Inputs | SPEC-042 friction | Active |
```

This table persists in the revision report and is updated as layers are dispatched. Status values: **Active** (not yet addressed), **Dispatched** (revision running), **Resolved** (revision confirmed fix), **Unresolved** (revision ran but signal persists — blocks completion).

Impact scope controls dispatch: only dispatch to layers within the signal's scope. A local signal in Step 5 does not cascade to Step 2 unless the scope is explicitly cross-layer.

### Step 2 — Identify affected foundation areas

For each of the 6 foundation areas, check whether any feedback item implies drift:

| Area | Drift signal examples |
|------|----------------------|
| Identity/handles | ADR changes entity lifecycle, KI about stale handles, code review found handle misuse |
| Content-definition | ADR changes enum→registry boundary, new content type added without ID policy |
| Storage | ADR changes container type, performance issue with iteration, KI about stale references |
| Save/load | ADR changes serialization, KI about migration |
| Spatial | ADR changes tile convention, KI about map size, system added spatial queries differently |
| API boundaries | ADR changes ownership, triage moved authority, code review found cross-system mutation |

**A single drift signal may affect multiple foundation areas.** For example, an ADR that changes handle lifecycle may affect identity, storage, and save/load simultaneously. Map each signal to all areas it touches.

### Step 3 — Identify affected docs

Map affected foundation areas to the Step 1–6 docs that need revision:

| Affected doc layer | When to revise | Dispatch skill | Stabilization loop |
|-------------------|----------------|----------------|-------------------|
| Design doc (Step 1) | Vision, core loop, governance, or player-facing assumptions changed | `/scaffold-revise-design --source foundation-recheck --signals [signals]` | revise-design → fix-design → iterate-design → validate --scope design |
| Systems (Step 2) | Ownership, dependencies, or interfaces changed | `/scaffold-revise-systems --source foundation-recheck --signals [signals]` | revise-systems → fix-systems → iterate-systems → validate --scope systems |
| References (Step 3) | Authority, signals, entities, or states changed | `/scaffold-revise-references --source foundation-recheck --signals [signals]` | revise-references → fix-references → iterate-references → validate --scope refs |
| Engine (Step 4) | Engine constraints or viability assumptions changed | `/scaffold-revise-engine --source foundation-recheck --signals [signals]` | revise-engine → fix-engine → iterate-engine → validate --scope engine |
| Visual/UX (Step 5) | UI architecture, presentation rules, or interaction model changed | `/scaffold-revise-style --source foundation-recheck --signals [signals]` | revise-style → fix-style → iterate-style → validate --scope style |
| Inputs (Step 6) | Input architecture or action model changed | `/scaffold-revise-input --source foundation-recheck --signals [signals]` | revise-input → fix-input → iterate-input → validate --scope input |

### Step 4 — Dispatch revision loops

**Dispatch in dependency order.** Revise upstream conceptual docs before downstream derivative docs. When multiple layers need revision, process them in authority order (design → systems → references → engine → visual/UX → inputs). This prevents stale-content loops — a system revision that depends on an updated design doc must wait for the design revision to complete first.

Only dispatch to layers that are actually affected by detected drift — don't re-run all Steps 1–6.

For each affected layer, run the following skills in sequence. Wait for each skill to complete before running the next.

**Halt-on-escalation rule:** If any revision step returns unresolved escalations (pending user decisions), HALT the dispatch pipeline. Do NOT proceed to downstream layers. Report the blocking issues and wait for resolution. Downstream layers that revise against an unstable upstream will produce incorrect results. Only resume dispatch after all escalations in the current layer are resolved.

```
Layer N revision → escalation pending?
├── No  → proceed to Layer N+1
└── Yes → HALT
         → report blocking escalations
         → report revision state (what completed, what's blocked, what hasn't started)
         → wait for user resolution
         → re-validate Layer N
         → resume dispatch at Layer N+1
```

**Track revision state throughout dispatch.** At any point — including mid-pipeline halts — the current state of every layer must be reportable:

| Status | Meaning |
|--------|---------|
| **Complete** | Stabilization loop finished, validate passed |
| **In progress** | Currently running revision/fix/iterate/validate |
| **Blocked** | Halted on unresolved escalation — waiting for user |
| **Not started** | Downstream of a blocked layer, not yet dispatched |
| **Skipped** | No drift detected for this layer |

**Resume logic:** When dispatch resumes after a resolved escalation:
1. Re-validate the layer that was blocked (the resolved escalation may have changed doc state that invalidates the prior validate result).
2. Resume from the first incomplete layer in authority order (design → systems → references → engine → visual/UX → inputs).
3. Do not re-dispatch layers that already completed and whose validate still passes.

**Revalidation rule:** Any resolved escalation invalidates the blocked layer's "Complete" status. That layer's validate must re-pass before downstream dispatch resumes. If the escalation resolution changed an upstream doc (e.g., user chose to update the design doc), re-validate all completed downstream layers as well — their results may be stale.

#### Step 1 — Design doc (if affected)

**Why:** Vision, core loop, governance, or player-facing assumptions changed. The design doc is the highest-authority document — if it needs updating, it must be revised first so all downstream layers revise against current design intent.

**Skills to run:**

1. `/scaffold-revise-design --source foundation-recheck --signals [signals]`
   - **What:** Reads only the specific drift signals passed via `--signals`. Classifies each as design-led vs implementation-led. Auto-updates safe mechanical changes. Dispatches to `init-design --mode reconcile/refresh` for design decisions. Escalates governance impacts.
   - **Why:** Targeted revision — doesn't re-scan the universe, just processes signals this skill identified.
2. `/scaffold-fix-design`
   - **What:** Auto-fixes template text, governance format normalization, terminology drift, system index mismatches. Surfaces contradictions, drift, and layer violations.
   - **Why:** Revise-design may have changed sections — fix catches mechanical issues introduced by those changes.
3. `/scaffold-iterate design --sections "[changed groups]"`
   - **What:** Adversarial review scoped to only the topics relevant to the changed sections, with early convergence stopping. Uses the `--sections` argument from revise-design's report (e.g., if revise-design changed Shape and Philosophy, iterate runs Topics 1, 2, 4, 5 — not all 5 topics). Section-to-topic mapping is defined in iterate-design's `--sections` argument. Default max 10 iterations, but stops early when no new issues are found.
   - **Why:** Revise + fix may have shifted section content. Scoped iterate catches coherence issues in the changed areas without re-reviewing untouched sections.
   - **When to skip:** If revise-design made no changes (only auto-updated references or found no drift), skip iterate to save cost.
4. `/scaffold-validate --scope design`
   - **What:** 13 deterministic structural checks: section health, governance format, glossary compliance, ADR consistency, review freshness.
   - **Why:** Final gate confirming the design doc is structurally ready to govern downstream work again.

#### Step 2 — Systems (if affected)

**Why:** Ownership, dependencies, or system interfaces changed.

**Skills to run:**

1. `/scaffold-revise-systems --source foundation-recheck --signals [signals]`
   - **What:** Reads only the specific drift signals passed via `--signals`. Classifies each as design-led vs implementation-led. Auto-updates safe changes (dependency entries, edge cases). Escalates ownership shifts and authority violations.
   - **Why:** Targeted revision — doesn't re-scan everything, just processes signals this skill identified.
2. `/scaffold-fix-systems SYS-###-SYS-###`
   - **What:** Mechanical cleanup pass on affected systems. Normalizes structure, detects design signals.
   - **Why:** Revise-systems may have changed sections — fix catches mechanical issues introduced by those changes.
3. `/scaffold-iterate systems --topics "[affected topics]" SYS-###-SYS-###`
   - **What:** Adversarial review scoped to affected topics and systems, with early convergence.
   - **Why:** Revise + fix may have shifted system content. Scoped iterate catches design issues in changed areas.
   - **When to skip:** If revise-systems made no changes (only found no drift), skip iterate.
4. `/scaffold-validate --scope systems --range SYS-###-SYS-###`
   - **What:** 16 deterministic structural checks on affected systems.
   - **Why:** Final gate confirming system docs are structurally ready.

#### Step 3 — References (if affected)

**Why:** Authority, signals, entities, or state transitions changed.

**Skills to run:**

1. `/scaffold-revise-references --source foundation-recheck --signals [signals]`
   - **What:** Reads only the specific drift signals passed via `--signals`. Classifies each as design-led vs implementation-led. Auto-updates safe changes (missing registrations, stale references, column updates). Escalates authority changes, architecture changes, contract changes, and state machine changes.
   - **Why:** Targeted revision — doesn't re-scan everything, just processes signals this skill identified. Respects canonical direction (authority→entity, interfaces→signals, states→enums).
2. `/scaffold-fix-references --target [affected-doc.md]`
   - **What:** Mechanical cleanup targeted at the specific doc(s) that were revised. Per-doc structural checks plus cross-doc consistency against all 9 Step 3 docs. Auto-fixes alignment issues. Detects design signals.
   - **Why:** Revise may have changed authority entries, interface contracts, or state names — fix-references catches mechanical inconsistencies introduced by those changes and propagates alignment fixes.
   - **Target selection:** If drift affected authority.md, target authority.md. If multiple docs affected, run without `--target` to fix all.
3. `/scaffold-iterate references --target [affected-doc.md] --topics "[affected topics]"`
   - **What:** Adversarial review scoped to the affected doc and relevant topics. Uses `--target` to auto-select topics.
   - **Why:** Fix-references catches mechanical issues; iterate-references catches conceptual drift, cross-doc contradictions, and design quality issues.
   - **When to skip:** If revise-references and fix-references found no issues and no design signals, skip iterate.
4. `/scaffold-validate --scope refs`
   - **What:** Deterministic validation — Python script (9 checks) plus expanded checks (33+ checks covering structure, values, cross-doc consistency).
   - **Why:** Programmatic gate — reference docs must be structurally consistent before foundation integration runs.

#### Step 4 — Engine (if affected)

**Why:** Engine constraints, viability assumptions, or platform rules changed. Step 3 docs were revised and engine docs must catch up.

**Skills to run:**

1. `/scaffold-revise-engine --source foundation-recheck --signals [signals]`
   - **What:** Detects engine doc drift from Step 3 changes, ADRs, code review findings, and implementation friction. Auto-applies safe updates (stale references, Step 3 alignment, constrained TODO resolution). Escalates convention changes and performance budget revisions.
   - **Why:** Engine docs are Rank 9 — they implement Step 3 decisions. When Step 3 changes, engine docs must follow. revise-engine classifies drift and applies safe changes directly.
2. `/scaffold-fix-engine` (if revise-engine made changes)
   - **What:** Mechanical cleanup after revision — cross-engine consistency, template structure, terminology.
   - **When to skip:** If revise-engine made no changes (only found no drift), skip fix.
3. `/scaffold-iterate engine --target [affected-doc] --topics "1,2"` (for specifically affected engine docs)
   - **What:** Adversarial review focused on architecture implementation fidelity and authority compliance for the revised doc(s).
   - **When to skip:** If revise-engine and fix-engine found no issues and no design signals, skip iterate.
4. `/scaffold-validate --scope engine`
   - **What:** Deterministic structural gate — Step 3 alignment, authority compliance, cross-engine consistency, template drift, review freshness.
   - **Why:** Final gate confirming engine docs are structurally ready after revision.

#### Step 5 — Visual/UX (if affected)

**Why:** UI architecture, presentation rules, interaction model, or visual identity assumptions changed.

**Skills to run:**

1. `/scaffold-revise-style --source foundation-recheck --signals [signals]`
   - **What:** Reads only the specific drift signals passed via `--signals`. Classifies each as design-led, playtest-led, or implementation-led. Auto-updates safe changes (missing tokens, stale references, new feedback entries, cross-doc alignment). Escalates aesthetic direction changes, interaction model changes, priority hierarchy changes, accessibility changes, and component removals.
   - **Why:** Targeted revision — doesn't re-scan everything, just processes signals this skill identified. Respects Step 5 authority flow (style-guide → color-system → ui-kit; feedback-system → audio-direction).
2. `/scaffold-fix-style --target [affected-doc.md]`
   - **What:** Mechanical cleanup targeted at the specific doc(s) that were revised. Per-doc structural checks plus cross-doc consistency across all 6 Step 5 docs. Auto-fixes alignment issues. Detects design signals.
   - **Why:** Revise may have added tokens, feedback entries, or interaction mappings — fix-style catches mechanical inconsistencies introduced by those changes and propagates alignment fixes.
   - **Target selection:** If drift affected a single doc, target it. If multiple docs affected, run without `--target` to fix all.
3. `/scaffold-iterate style --target [affected-doc.md] --topics "[affected topics]"`
   - **What:** Adversarial review focused on the revised areas of the affected Step 5 doc(s).
   - **Why:** Revise and fix catch mechanical issues; iterate catches conceptual drift in aesthetic direction, interaction design, and feedback coherence.
   - **When to skip:** If revise-style and fix-style found no issues and no design signals, skip iterate.
4. `/scaffold-validate --scope style`
   - **What:** Deterministic structural gate — section health, token resolution, boundary compliance, accessibility coherence, feedback coverage, design intent alignment.
   - **Why:** Final gate confirming Step 5 docs are structurally ready after revision.

#### Step 6 — Inputs (if affected)

**Why:** Input architecture, action model, or binding assumptions changed.

**Skills to run:**

1. `/scaffold-revise-input --source foundation-recheck --signals [signals]`
   - **What:** Reads implementation feedback, classifies drift (design-led vs implementation-led), auto-updates safe changes (stale references, missing actions from upstream, orphan bindings), escalates design-level changes (philosophy violations, navigation model changes, device parity gaps).
   - **Why:** Detects misalignment between input docs and the (potentially revised) interaction model, design doc, and ui-kit.
   - **When to skip:** If revise-input made no changes (only found no drift), skip iterate.
2. `/scaffold-fix-input` (if revise-input made changes)
   - **What:** Mechanical cleanup after revision edits.
3. `/scaffold-iterate input --topics "[affected topics]"` (if revise-input surfaced design signals)
   - **What:** Adversarial review of changed areas.
   - **When to skip:** If revise-input and fix-input made no changes.
4. `/scaffold-validate --scope input`
   - **What:** Deterministic structural gate — action ID conventions, traceability, binding coverage, collision detection, navigation completeness, upstream alignment, philosophy compliance, device parity.
   - **Why:** Final gate confirming input docs are structurally ready.

#### After all dispatched revisions complete

**Global convergence requirement.** Individual layer validates confirm per-layer health, but they do not verify cross-layer coherence. After all dispatched revisions:

1. `/scaffold-validate --scope all` — full cross-layer validation including cross-cutting and cross-layer integrity checks.
2. `/scaffold-fix-cross-cutting` — if validate surfaces cross-cutting findings, resolve them interactively.

If validate fails, the revision cycle is incomplete. Report the failures and recommend targeted re-revision of the affected layers.

This is not optional — skipping it means per-layer revisions may have introduced new cross-layer contradictions that no individual validate scope catches.

### Step 5 — Signal Resolution & Closure

After all dispatched revisions and global convergence, close the loop on every normalized signal. This is what turns the pipeline from open-loop (dispatch and hope) to closed-loop (dispatch, verify, confirm).

For each signal in the Normalized Signals table:

1. **Verify resolution:**
   - Was the root cause addressed by the dispatched revision(s)?
   - Are all affected docs updated?
   - Does the final validate (--scope all) confirm no remaining failures tied to this signal?

2. **Update signal status:**
   - **Resolved** — root cause addressed, all layers updated, validate confirms. Link to the specific doc changes and revision log entries that resolved it.
   - **Partially Resolved** — some layers addressed but others still show drift, OR validate still flags related issues. Record what was fixed and what remains. The signal stays Active for the next revision cycle.
   - **Unresolved** — revision ran but the root cause persists, OR the signal required an escalation that was deferred. Escalate as a blocking issue if severity is Critical or High.

3. **Persist the final signal registry** in the revision log:

```
### Signal Registry (Final State)

| Signal ID | Root Cause | Severity | Status | Resolution | Affected Docs Changed |
|----------|------------|----------|--------|------------|----------------------|
| SIG-001 | Handle lifecycle change | Critical | Resolved | authority.md updated, entity-components aligned | authority.md, entity-components.md, SYS-003 |
| SIG-002 | Stale UI component ref | Medium | Resolved | ui-navigation component ref fixed | ui-navigation.md |
| SIG-003 | Philosophy-binding conflict | High | Partially Resolved | KBM bindings updated, gamepad still pending | default-bindings-kbm.md |
```

**Completion gate:** The revision cycle is complete only when ALL signals are either Resolved or explicitly deferred with tracking (filed via `/scaffold-file-decision --type ki` with the Signal ID reference). Partially Resolved and Unresolved signals of severity High or Critical block completion.

### Step 6 — Report

```
## Foundation Revision: Post-Implementation

**Mode:** Recheck
**Foundation areas checked:** 6
**Areas with drift:** N
**Docs revised:** N
**Feedback sources:** N ADRs, N KIs, N triage actions, N spec/task friction signals

### Revision State
| Layer | Status | Blocking Issue |
|-------|--------|---------------|
| Design (Step 1) | Complete / Blocked / Skipped / Not started | [escalation detail if blocked] |
| Systems (Step 2) | Complete / Blocked / Skipped / Not started | — |
| References (Step 3) | Complete / Blocked / Skipped / Not started | — |
| Engine (Step 4) | Complete / Blocked / Skipped / Not started | — |
| Visual/UX (Step 5) | Complete / Blocked / Skipped / Not started | — |
| Inputs (Step 6) | Complete / Blocked / Skipped / Not started | — |

### Drift Detected
| Foundation Area | Drift Signal | Severity | Scope | Affected Docs |
|----------------|-------------|---------------|
| Identity | ADR-### changed handle semantics | Critical | Cross-layer | systems, references |
| API boundaries | Triage moved ownership of X | High | Layer-wide | authority, systems |

### Revisions Dispatched
| Doc Layer | Dispatch Command | Signals Passed | Status |
|-----------|-----------------|----------------|--------|
| Design (Step 1) | revise-design --source foundation-recheck --signals ADR-015,KI:colonist-autonomy | ADR-015, KI:colonist-autonomy | Complete |
| Systems (Step 2) | revise-systems --source foundation-recheck --signals ADR-015 | ADR-015 | Complete |
| References (Step 3) | revise-references --source foundation-recheck --signals SYSTEM:SYS-003-changed | SYSTEM:SYS-003-changed | Complete |

### No Drift
| Foundation Area |
|----------------|
| Content-definition |
| Storage |
| Save/load |
| Spatial |

**Proceed to validate --scope foundation (7b):** Yes — dispatched revisions complete
```

If no drift is detected in any area:
```
## Foundation Revision: Post-Implementation

**Mode:** Recheck
**Foundation areas checked:** 6
**Areas with drift:** 0
**Drift detected:** None
**Detection confidence:** High / Medium / Low

### Confidence Assessment
| Factor | Value |
|--------|-------|
| Feedback sources scanned | N |
| ADRs checked | N |
| Known issues checked | N |
| Triage logs checked | N |
| Spec/task friction signals | N |
| Code review findings | N |

No foundation docs require revision. Proceed directly to validate --scope foundation (7b) for structural verification.
```

**If detection confidence is Low** (fewer than 3 feedback sources scanned, or key sources like ADRs or triage logs were empty or missing), warn: "Possible undetected drift — limited feedback sources available. Consider running `/scaffold-validate --scope all` to verify foundation health independently."

## Rules

- **This skill never edits docs directly.** It dispatches revision loops to the appropriate Step 1–6 pipelines.
- **Only revise affected docs.** Don't re-run the full Steps 1–6 pipeline on every recheck.
- **Dispatch in dependency order.** Revise upstream conceptual docs before downstream derivative docs, using the project's document authority and dependency chain (design → systems → references → engine → visual/UX → inputs) to prevent stale-content loops.
- **Initial mode is a readiness check, not a revision.** If Steps 1–6 aren't ready, stop — don't try to compensate.
- **Recheck mode prioritizes concrete signals** (ADRs, KIs, triage logs, review notes, spec/task friction) when detecting drift.
- **A single signal may affect multiple areas.** Map each signal to all foundation areas it touches, not just the most obvious one.
- **After dispatched revisions complete, validate --scope all must run.** Individual doc revisions may introduce new cross-layer contradictions. Follow with fix-cross-cutting if cross-cutting findings are surfaced. This is mandatory, not optional.
- **Halt on unresolved escalations.** If any layer's revision returns pending escalations, stop the dispatch pipeline. Do not proceed to downstream layers until all escalations in the current layer are resolved. Downstream layers revising against an unstable upstream produce incorrect results.
- **Normalize signals before mapping.** Deduplicate overlapping signals from different sources that describe the same root cause. Assign impact scope (local/layer-wide/cross-layer). Only dispatch to layers within the signal's scope.
- **Impact scope controls dispatch reach.** A local signal within one layer does not cascade to other layers unless the scope is explicitly cross-layer. This prevents over-revision from small changes.
- **Detect revision loops.** Track the origin of each signal through the dispatch chain. If a revision in a downstream layer (e.g., Step 5 style) produces a signal that would re-trigger revision in an upstream layer (e.g., Step 1 design), flag it as a loop: "Loop detected: [downstream layer] revision produced signal that affects [upstream layer]. Escalate instead of auto-dispatching." Do not auto-dispatch upstream revisions from downstream signals — escalate for user decision.
- **No-drift confidence is assessed.** When no drift is detected, report confidence based on the number and breadth of feedback sources scanned. Low confidence (few sources, key sources missing) triggers a warning recommending independent validation.
- **Severity drives dispatch behavior.** Critical signals force full cross-layer validation after each affected layer completes. High signals require the iterate step (cannot be skipped even if revise+fix made no changes). Medium signals follow normal flow. Low signals may be batched or deferred to the next revision cycle.
- **Signals must be confirmed resolved.** After each layer's stabilization loop completes, check every signal dispatched to that layer: was the root cause addressed? Are all affected docs updated? Does validate confirm resolution? If a signal remains unresolved after its layer completes, it stays Active and blocks final completion.
- **Resolved escalations invalidate downstream.** Any resolved escalation that changed doc state invalidates the blocked layer's "Complete" status. That layer must re-validate before dispatch resumes. If the resolution changed an upstream doc, all completed downstream layers must also re-validate.
- **Resume from first incomplete layer.** When dispatch resumes after a halt, start from the first non-Complete layer in authority order. Do not re-dispatch layers that already completed and whose validate still passes.
- **Execution cost control.** If revise + fix made no changes for a layer, skip iterate and validate unless the dispatched signal severity is High or Critical. Low and Medium no-change layers can proceed without the full stabilization loop.
- **Regression detection after each layer.** After a layer completes its stabilization loop, re-run validate on all previously completed upstream layers. If any upstream validate that previously passed now fails, a regression was introduced — escalate immediately with the specific failure and the change that caused it. Do not proceed to the next downstream layer until the regression is resolved. This catches cases where a downstream revision invalidates an upstream layer's state.
- **Signal closure is mandatory.** The revision cycle is only complete when every normalized signal is Resolved or explicitly deferred with tracking in known-issues.md. Partially Resolved or Unresolved signals of severity High or Critical block completion.

---
name: scaffold-revise-engine
description: Detect engine doc drift from implementation feedback and apply safe updates or escalate for decisions. Reads ADRs, known issues, spec/task friction, code review findings, and Step 3 doc changes to identify when engine docs no longer match what was actually built or what Steps 1-3 now define. Use after a phase or slice completes, or when revise-foundation detects Step 4 drift.
argument-hint: [--source P#-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword] [--target doc-stem]
allowed-tools: Read, Edit, Grep, Glob
---

# Revise Engine Docs

Detect engine doc drift and update Step 4 docs from implementation feedback: **$ARGUMENTS**

Engine docs (Rank 9) describe HOW to implement the game in the chosen engine. But implementation reveals realities that initial engine docs couldn't anticipate: new Godot patterns emerge, performance constraints change, coding conventions evolve, task implementations establish patterns not captured in engine docs, and Step 3 reference docs get revised. This skill reads implementation feedback, classifies what changed, applies safe evidence-backed updates directly, and escalates convention-level changes for human decision.

This is distinct from:
- **`fix-engine`** — repairs mechanical structure (this skill identifies *convention-level* drift, not formatting)
- **`iterate-engine`** — adversarial design review (this skill processes *implementation signals*, not reviewer critique)
- **`bulk-seed-engine`** — creates docs from scratch (this skill updates existing docs from feedback)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source` | No | auto-detect | What triggered the revision: `P#-###` (phase completed), `SLICE-###` (slice completed), `foundation-recheck` (dispatched from revise-foundation). If omitted, scans all recent feedback. |
| `--signals` | No | — | Comma-separated list of specific drift signals to process. When provided, skip the broad feedback scan and process only these items. Accepted formats: `ADR-###`, `KI:keyword`, `TRIAGE:action-keyword`, `SPEC:friction-keyword`, `CODE-REVIEW:finding-keyword`, `REFS:doc-changed`. This is the primary dispatch mechanism — `revise-foundation` identifies which signals affect engine docs and passes them here. |
| `--target` | No | all | Target a single engine doc by stem (e.g., `--target coding-best-practices`). When set, only that doc is edited. Cross-engine implications are flagged but not applied to other engine docs. |

### Signal Resolution Table

| Signal Format | Resolves To | Search Scope |
|--------------|-------------|-------------|
| `ADR-###` | Exact ADR file by ID | `scaffold/decisions/ADR-###-*.md` |
| `KI:keyword` | Known issue entries matching keyword | Grep `scaffold/decisions/known-issues.md` title and body |
| `TRIAGE:keyword` | Triage log entries matching keyword | Grep `scaffold/decisions/triage-logs/TRIAGE-*.md` Decisions + Upstream Actions tables |
| `SPEC:keyword` | Spec/task friction notes matching keyword | Grep completed specs and task files for friction comments |
| `CODE-REVIEW:keyword` | Code review findings matching keyword | Grep `scaffold/decisions/review/*code-review*` logs only |
| `REFS:doc-stem` | Exact Step 3 doc by filename stem | `scaffold/design/<doc-stem>.md` or `scaffold/reference/<doc-stem>.md` — not fuzzy, not section-level |

## Preconditions

1. **Engine docs exist** — verify at least 5 engine docs exist in `scaffold/engine/`. If fewer, stop: "Engine docs not ready. Run `/scaffold-bulk-seed-engine` first."
2. **Engine docs have been through pipeline** — verify at least one fix-engine or iterate-engine log exists in `scaffold/decisions/review/`. If none, stop: "Engine docs haven't been stabilized yet. Run the Step 4 pipeline first."
3. **Implementation feedback exists** — if `--signals` is provided, at least one signal must resolve. If not provided, at least one feedback source must exist (ADRs, KIs, code review findings, Step 3 doc changes, task completions). If none exist, report: "No implementation feedback found. Nothing to revise."

### Context Files

| Context File | Why |
|-------------|-----|
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules |
| `scaffold/design/architecture.md` | Architecture decisions engine docs must implement |
| `scaffold/design/authority.md` | Ownership rules engine docs must respect |
| `scaffold/design/interfaces.md` | Contracts engine docs must implement |
| `scaffold/design/state-transitions.md` | State machines engine docs must implement |
| `scaffold/reference/signal-registry.md` | Signal contracts engine docs must reference |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/engine/_index.md` | Engine doc registration and template mapping |
| `scaffold/decisions/known-issues.md` | Known gaps and constraints |
| ADRs with status `Accepted` | Decision compliance |

## Step 1 — Gather Implementation Feedback

**If `--signals` is provided:** Skip the broad scan. Read only the specific documents referenced by the signal list.

**If `--signals` is not provided:** Run the broad scan below.

### 1a. ADRs

Glob accepted ADRs. For each, check:
- Does it change tick model, boot order, or simulation runtime semantics? → simulation-runtime, scene-architecture
- Does it change identity/handle model? → coding-best-practices, save-load-architecture
- Does it change data storage or content pipeline patterns? → data-and-content-pipeline, save-load-architecture
- Does it change cross-system communication patterns? → coding-best-practices, scene-architecture
- Does it add/change input handling patterns? → input-system
- Does it introduce new performance constraints? → performance-budget
- Does it change task/reservation execution model? → ai-task-execution
- Does it change UI patterns or framework approach? → ui-best-practices
- Does it change localization conventions? → localization
- Does it affect debugging/observability patterns? → debugging-and-observability
- Does it change build/test configuration? → build-and-test-workflow

### 1b. Known issues

Read `scaffold/decisions/known-issues.md`. Check for entries that reference engine docs or imply engine-layer changes.

### 1c. Step 3 doc changes

**Baseline mechanism:** Use the `Revision Timestamp` field from the latest `REVISION-engine-YYYY-MM-DD.md` as the canonical baseline (not the filename date — the machine-readable timestamp inside the log). Treat Step 3 docs with modification dates after that timestamp as candidates for drift scan. If no revision log exists, treat all Step 3 docs as candidates (first revision pass after initial seed).

**Change detection method:** The baseline determines which Step 3 docs are *candidates* (modified after last revision timestamp). The actual comparison determines whether engine docs are *stale relative to current upstream state* — not a historical diff of Step 3 against itself. For each candidate Step 3 doc:
1. Read the doc and identify its `##` section headings.
2. For each section that maps to an engine doc (per the mapping below), read the corresponding engine doc section and check whether it still correctly implements the current Step 3 content. A section counts as "drifted" if: (a) a new heading was added to Step 3 with no engine counterpart, (b) table rows were added/removed/modified and the engine doc doesn't reflect them, (c) rule text was added/changed and the engine doc still references the old version, or (d) a Constrained TODO was resolved but the engine doc still marks it constrained. Ignore: whitespace-only changes, comment additions, and provenance markers (`<!-- REVISED -->`).
3. Only sections that both map to an engine doc AND show a mismatch between current Step 3 and current engine doc produce drift signals. Unmapped sections are ignored.

Compare current Step 3 docs against this baseline. For each Step 3 doc where relevant sections changed:
- architecture.md Scene Tree Layout changed → scene-architecture may be stale
- architecture.md Tick Processing Order changed → simulation-runtime may be stale
- architecture.md Signal Wiring Map changed → coding-best-practices signal patterns may be stale
- architecture.md Data Flow Rules changed → coding-best-practices data access patterns may be stale
- architecture.md Entity Identity changed → coding-best-practices handle patterns, save-load-architecture may be stale
- architecture.md Boot Order changed → scene-architecture init sequence may be stale
- architecture.md Failure & Recovery Patterns changed → coding-best-practices error handling may be stale
- authority.md ownership changed → any engine doc claiming ownership must update
- interfaces.md contracts changed → coding-best-practices, simulation-runtime contract implementations may be stale
- state-transitions.md changed → ai-task-execution task lifecycle may be stale
- signal-registry.md signals changed → coding-best-practices signal examples may be stale

This is the most important drift source for engine docs — Step 3 docs are upstream authority.

### 1d. Code review findings

Search code review logs for findings that suggest engine doc drift:
- Patterns used in reviewed code that aren't documented in engine docs
- Naming conventions that diverged from coding-best-practices
- Signal wiring patterns that differ from what engine docs describe
- Performance patterns that outperform or invalidate performance-budget assumptions
- Error handling patterns that differ from coding-best-practices

**Evidence threshold:** Code review findings corroborate other evidence, not standalone authority. A code review finding alone does not justify an engine doc change — it must align with an ADR, completed task, or Step 3 change.

### 1e. Spec/task friction

Search completed specs and tasks for explicit friction tied to engine docs:
- "Engine doc says X but we had to do Y"
- "coding-best-practices doesn't cover this pattern"
- "performance-budget doesn't account for this system"
- "No engine guidance for this type of implementation"

Only treat explicit friction as drift signals, not inferred patterns.

### 1f. Implementation patterns discovered

Search completed tasks for patterns that should be captured in `implementation-patterns.md`:
- Repeated solutions to similar problems across multiple tasks
- Workarounds that became standard practice
- Engine-specific gotchas discovered during implementation

This is unique to engine revision — `implementation-patterns.md` grows from implementation rather than being pre-filled.

### 1g. Cross-engine convention drift (broad scan only)

**Naming drift** — check completed code files against coding-best-practices naming rules. If the codebase has consistently diverged from a stated convention (and the new convention is backed by accepted code reviews), the engine doc may need updating.

**Signal pattern drift** — check signal wiring in implemented code against coding-best-practices signal policy. If the actual wiring pattern differs from what the engine doc says.

**Language boundary drift** — check which logic is in C++ vs GDScript against the coding-best-practices boundary. If tasks have consistently placed logic in a different layer.

### 1h. Early exit check

After gathering all signals from Steps 1a–1g, filter to those that actually map to engine docs (using the Step 2a mapping table). If no valid engine-impacting drift signals remain after filtering, exit early:

"No engine-impacting drift detected from provided signals. No changes made."

Do not proceed to Steps 2–7. Write a minimal revision log noting the scan was clean.

## Step 2 — Classify Drift Signals

### 2a. Map signals to engine docs

| Signal type | Likely affected engine docs |
|-------------|---------------------------|
| Architecture scene tree changed | scene-architecture |
| Architecture tick order changed | simulation-runtime |
| Architecture signal wiring changed | coding-best-practices |
| Architecture data flow changed | coding-best-practices |
| Architecture identity model changed | coding-best-practices, save-load-architecture |
| Architecture boot order changed | scene-architecture |
| Architecture failure patterns changed | coding-best-practices |
| Authority ownership changed | any engine doc referencing the affected system |
| Interface contracts changed | coding-best-practices, simulation-runtime |
| State machine changed | ai-task-execution |
| Signal registry changed | coding-best-practices signal examples |
| New pattern discovered | implementation-patterns |
| Performance reality differs from budget | performance-budget |
| Convention consistently violated in approved code | coding-best-practices |
| New Godot gotcha discovered | relevant engine doc |
| Build/test configuration changed | build-and-test-workflow |

### 2b. Evidence precedence

Same as revise-references:

1. **Accepted ADR** — explicit project decision
2. **User decision** recorded in triage or revision log
3. **Step 3 doc change** (higher-authority, approved through pipeline)
4. **Completed spec/task** showing implemented and approved reality
5. **Code review finding** — corroborative, not authoritative
6. **Known issue note** — weakest signal

### 2c. Severity classification

| Severity | Meaning | Action |
|----------|---------|--------|
| **Stale reference** | Engine doc references renamed system, signal, entity, or Step 3 section | Auto-update: fix reference |
| **Step 3 alignment update** | Step 3 doc changed and the engine doc's implementation of that decision is now stale — but the engine doc just needs to track the upstream change, not make a new decision | Auto-update: align with upstream |
| **Example/pattern update** | Code examples, signal names, or convention examples in engine docs don't match current reality | Auto-update: fix example |
| **New pattern registration** | Implementation discovered a reusable pattern not yet in implementation-patterns.md | Auto-update: add pattern entry |
| **Constrained TODO resolution** | A previously constrained TODO's blocking Step 3 decision was resolved | Auto-update: fill the section with the decided content |
| **Convention change** | A stated coding/naming/wiring convention needs to change based on implementation evidence | Escalate: convention changes affect all future code |
| **Performance budget revision** | Performance targets or per-system budgets need updating | Escalate: budget changes affect implementation decisions |
| **Architecture implementation change** | How the engine doc implements a Step 3 decision needs to change (not just track upstream — genuinely different implementation approach) | Escalate: may affect downstream tasks and code |
| **New engine doc section** | Implementation revealed a topic area the engine doc should cover but doesn't | Escalate: adding scope to an engine doc |
| **Deprecation** | An engine convention, pattern, or approach is no longer used | Escalate: must verify nothing still depends on it |

### 2d. Design-led vs implementation-led

- **Design-led change** — backed by Step 3 update, accepted ADR, or triage decision. Engine docs should catch up to upstream authority.
- **Implementation-led divergence** — code wandered from engine docs without approval. Engine docs should *not* automatically update. Escalate to determine whether the code or the doc is wrong.

**Repeated divergence escalation:** If the same implementation-led divergence appears in 2+ revision runs (check prior revision logs), escalate severity to **"Forced decision required"** — the user must choose option (a) or (b), not (c) defer. Repeated divergence means the project is living with an unresolved contradiction, which degrades trust in the engine docs over time.

**Divergence equivalence key:** Two divergences are "the same" if they share all three components: (1) affected engine doc, (2) affected section, (3) underlying conflict topic. Example: `coding-best-practices :: Signal Naming :: implemented signals use present-tense instead of past-tense`. If that same key appears in 2+ revision logs' Deferred Issues or Escalations tables, it triggers forced decision.

## Step 3 — Apply Safe Updates

For each **Stale reference**, **Step 3 alignment update**, **Example/pattern update**, **New pattern registration**, and **Constrained TODO resolution** item:

1. Read the affected engine doc.
2. Apply the update using the Edit tool.
3. Record what was changed, why, and what feedback triggered it.
4. Add provenance: `<!-- REVISED: [date] — [trigger] -->`

**Safety rules:**
- **Engine docs implement Step 3, not the reverse.** When Step 3 changes, the engine doc aligns. Never update the engine doc in a way that contradicts the new Step 3 decision.
- **When `--target` is set, only edit the targeted engine doc.** Flag cross-engine implications for fix-engine.
- **Never change Step 3 decisions.** If the engine doc's implementation needs to change because Step 3 changed, update the engine doc. If the engine doc appears correct and Step 3 appears wrong, flag for revise-references — do not edit Step 3.
- **Never change conventions without escalation.** Auto-updates may fix examples, references, and alignment — but naming conventions, signal patterns, error handling patterns, and language boundaries are convention-level changes that must escalate.
- **Constrained TODO resolution must verify the decision.** Before filling a constrained TODO, read the Step 3 doc that was blocking it and confirm the decision is explicit and locked (not still Draft or TBD).
- **Implementation patterns are additive only.** Auto-add new patterns to implementation-patterns.md. Never auto-remove or auto-modify existing patterns — they may still be in use.
- **Scope collapse guard applies.** Same three tests as iterate-engine: ownership test, flexibility preservation test, "would this survive Step 3 rewrite?" test. Auto-updates that would fail these tests escalate instead.
- **No duplicate patterns.** Before adding to implementation-patterns.md, check if an equivalent pattern already exists. **Similarity guard:** if the new pattern's problem statement and solution structure overlap significantly with an existing pattern (same domain, same trigger conditions, similar approach), escalate instead of auto-adding. Present both patterns side by side and let the user decide: merge into existing, add as distinct, or skip. This prevents implementation-patterns.md from silently bloating with near-duplicate entries.

## Step 4 — Escalate Design-Level Changes

For each **Convention change**, **Performance budget revision**, **Architecture implementation change**, **New engine doc section**, and **Deprecation** item:

**Escalation severity weighting:** Not all escalations are equal. Tag each with a priority level:

| Priority | Escalation Types | Meaning |
|----------|-----------------|---------|
| **CRITICAL** | Architecture implementation change, Performance budget revision | Affects fundamental implementation approach or resource constraints. Resolve before continuing implementation. |
| **HIGH** | Convention change | Affects all future code. Resolve before next task implementation. |
| **MEDIUM** | New engine doc section, Deprecation | Expands or contracts engine doc scope. Can proceed with current work but resolve before next phase. |

Present CRITICAL escalations first, then HIGH, then MEDIUM. The revision log records priority alongside each escalation.

Present using the Human Decision Presentation pattern:

```
### Engine Escalation #N

**Signal:** [source — ADR-###, Step 3 doc change, code review finding, task friction]
**Affected doc(s):** [coding-best-practices, simulation-runtime, etc.]
**Current engine doc says:** [what the engine doc states]
**Implementation reality:** [what was actually built or what Step 3 now requires]
**Design-led or implementation-led:** [backed by Step 3 change/ADR, or unapproved divergence]

**Options:**
a) Update engine doc to match — [implication, what changes, any downstream task impact]
b) Keep engine doc, update implementation — [implication, what code needs changing]
c) Defer — file via `/scaffold-file-decision --type ki` for future resolution

**Likely follow-up:** [fix-engine --target X / iterate-engine --target X / validate --scope engine / none]
```

**For convention changes:** show the old and new convention side by side. Note that convention changes affect all future code — not just the triggering task. List which other engine docs reference the convention.

**For performance budget revisions:** show the old and new numbers. Note which systems are affected. If the budget math no longer adds up, flag that explicitly.

**For architecture implementation changes:** note that these may cascade to tasks that were built against the old implementation approach. List any Approved or in-progress tasks that reference the affected engine doc section.

**For deprecation:** verify no Approved/in-progress tasks reference the deprecated convention. List any that do.

## Step 5 — Cross-Engine Consistency Check

After applying updates and resolving escalations, verify:

- **coding-best-practices ↔ all engine docs** — if naming/signal/error conventions changed, do other engine docs' examples still comply?
- **scene-architecture ↔ simulation-runtime** — if scene tree or boot order changed, does the tick orchestration still match?
- **coding-best-practices ↔ save-load-architecture** — if handle patterns or identity conventions changed, does save/load still match?
- **ai-task-execution ↔ simulation-runtime** — if task lifecycle or tick model changed, do they still agree?
- **performance-budget ↔ all engine docs** — if budget numbers changed, do per-system patterns still fit within budget?

Apply safe alignment updates within engine docs following the coding-best-practices-as-convention-source pattern. Flag cross-layer updates (Step 3 docs, system docs) for human action.

**Do not auto-heal around unresolved escalations.** If a cross-engine inconsistency depends on an unresolved escalation from Step 4, do not auto-align yet.

**Reference integrity after update:** After all consistency edits, verify that updated engine docs still have valid:
- `Conforms to` links (targets still exist)
- Cross-engine references (other engine docs cited still have the referenced sections)
- Signal names (any signal names in examples still exist in signal-registry.md)
- System references (any SYS-### or system names still resolve)

This is a lightweight post-edit validation, not a full `/scaffold-validate --scope engine` run. It catches breakage introduced by the revision itself.

## Step 6 — Update Revision History

**Log location:** `scaffold/decisions/revision-logs/REVISION-engine-YYYY-MM-DD.md`

```markdown
# Engine Revision: YYYY-MM-DD

**Revision Timestamp:** YYYY-MM-DDTHH:MM:SSZ
**Source:** [P#-### completed / SLICE-### completed / foundation-recheck / broad scan]
**Feedback items processed:** N
**Auto-updated:** N
**Escalated:** N issues
**Deferred:** N issues
**Docs affected:** [list]

## Updates Applied
| # | Doc | Section | Change | Trigger | Classification |
|---|-----|---------|--------|---------|----------------|
| 1 | coding-best-practices | Signal Conventions | Updated signal examples to match registry | signal-registry.md revised | Step 3 alignment |
| 2 | implementation-patterns | Hauling Pattern | Added two-phase hauling pattern | TASK-033 completion | New pattern |

## Escalations
| # | Type | Doc(s) | Resolution |
|---|------|--------|------------|
| 1 | Convention change | coding-best-practices | User chose option (a) |
| 2 | Performance revision | performance-budget | User chose option (c) — deferred |

## Deferred Issues
| # | Doc | Issue | Reason |
|---|-----|-------|--------|
| 1 | performance-budget | System budget math needs rebalancing | Needs profiling data from SLICE-009 |

## Advisory Drift Deferred
| # | Step 3 Doc | Affected Engine Doc | Reason Suppressed |
|---|-----------|--------------------|--------------------|
| 1 | architecture.md | simulation-runtime | Step 3 doc is Draft — advisory only until Approved |
| 2 | authority.md | coding-best-practices | Unresolved CRITICAL escalation in revise-references |
```

## Step 7 — Report

```
## Engine Docs Revised

### Summary
| Field | Value |
|-------|-------|
| Source | [P#-### / SLICE-### / foundation-recheck / broad scan] |
| Feedback items | N processed |
| Auto-updated | N |
| Escalated | N issues (N resolved, N deferred) |
| Docs affected | N |

### Engine Layer Confidence
**Stable / Decreased / Improved** — [Based on: number and severity of drift signals, whether conventions held, whether cross-engine consistency is intact, how many constrained TODOs were resolved.]

### Next Steps
- Run `/scaffold-fix-engine [--target X]` to clean up mechanical issues from updates
- Run `/scaffold-iterate-engine [--target X --topics "affected"]` to review changed areas
- Run `/scaffold-validate --scope engine` to confirm structural readiness
```

If no drift detected:
```
## Engine Docs Revised

**Status: No drift detected** — engine docs are consistent with implementation feedback and Step 3 docs. No changes made.
```

## Rules

- **Only edit engine docs.** Never edit Step 3 docs, system designs, design doc, specs, tasks, or planning docs.
- **Engine docs follow Step 3, not the reverse.** When Step 3 changes, update the engine doc to match. If the engine doc seems right and Step 3 seems wrong, flag for revise-references.
- **When `--target` is set, only edit the targeted engine doc.** Cross-engine implications are flagged for fix-engine.
- **Conventions are sacred until the user changes them.** Never auto-change naming conventions, signal patterns, error handling approaches, language boundaries, or any rule in a Rules section. These are project-wide decisions.
- **Performance budgets are sacred until the user changes them.** Never auto-change frame budgets, per-system budgets, or escalation criteria. Present the evidence and let the user decide.
- **Implementation patterns are additive only.** Add new patterns freely. Never modify or remove existing patterns without escalation.
- **Only accepted or corroborated signals count as drift.** Same rule as revise-references: accepted decisions count directly, observed implementation counts only when corroborated.
- **Design-led changes catch up. Implementation-led divergence escalates.** If Step 3 changed (design-led), the engine doc follows. If code diverged from the engine doc without authority (implementation-led), escalate to decide which is right.
- **Scope collapse guard applies to all updates.** Every auto-update must pass the three tests: ownership (does this introduce decisions Step 3 didn't define?), flexibility preservation (does this collapse options Step 3 left open?), survival (would this survive a Step 3 rewrite?). Failures escalate.
- **Constrained TODO resolution requires confirmed decisions.** Only fill constrained TODOs when the blocking Step 3 decision is explicitly locked (Approved status, not still Draft or TBD). A Partial foundation area is not sufficient — the specific decision must be resolved.
- **Deletion is riskier than addition.** Never delete engine conventions, patterns, or sections without ADR backing. Prefer marking as deprecated over deleting.
- **Evidence precedence resolves conflicts.** When sources disagree: accepted ADR > user decision > Step 3 doc change > completed spec/task > code review > known issue. Lower-ranked evidence cannot override higher-ranked.
- **Cross-engine updates follow coding-best-practices as convention source.** The coding doc defines project conventions. Other engine docs conform to it, not the reverse.
- **Revision suppression when Step 3 is unstable.** If architecture.md or authority.md have unresolved escalations (from revise-references), suppress auto-updates to engine docs that depend on those decisions. Wait for Step 3 to stabilize first. **Partial instability:** if a Step 3 doc changed but is not fully stabilized (Status is Draft or Review, not Approved), treat drift signals from that doc as **advisory only** — log them in the revision history but do not auto-update engine docs. A partially revised Step 3 doc may change again before stabilizing, and premature engine alignment creates false consistency.
- **Always write a revision log.** Every run produces a dated record.
- **Confidence heuristic.** Improved: mostly auto-updates, conventions held, constrained TODOs resolved. Stable: mix of auto-updates and escalations, cross-engine consistency intact. Decreased: convention changes, performance budget revisions, or multiple docs affected by the same Step 3 drift signal.

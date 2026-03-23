---
name: scaffold-revise-references
description: Detect reference/architecture drift from implementation feedback and apply safe updates or escalate for decisions. Reads ADRs, known issues, spec/task friction, code review findings, and system doc changes to identify when Step 3 docs no longer match what was actually built. Use after a phase or slice completes, or when revise-foundation detects Step 3 drift.
argument-hint: [--source PHASE-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword] [--target doc.md]
allowed-tools: Read, Edit, Grep, Glob
---

# Revise References

Detect reference/architecture drift and update Step 3 docs from implementation feedback: **$ARGUMENTS**

Step 3 docs are the reference layer — they define architecture, authority, contracts, data shapes, signals, states, resources, parameters, and shared vocabulary. But implementation reveals realities that design couldn't anticipate: new signals emerge, authority boundaries shift, state machines gain states, entity fields change, and balance parameters get discovered. This skill reads implementation feedback, classifies what changed, applies safe evidence-backed updates directly, and escalates design-level changes for human decision.

This is distinct from:
- **`fix-references`** — repairs mechanical structure (this skill identifies *design-level* drift, not formatting)
- **`iterate-references`** — adversarial design review (this skill processes *implementation signals*, not reviewer critique)
- **`seed references`** — creates docs from scratch (this skill updates existing docs from feedback)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source` | No | auto-detect | What triggered the revision: `PHASE-###` (phase completed), `SLICE-###` (slice completed), `foundation-recheck` (dispatched from revise-foundation). If omitted, scans all recent feedback. |
| `--signals` | No | — | Comma-separated list of specific drift signals to process. When provided, skip the broad feedback scan and process only these items. Accepted formats: `ADR-###`, `KI:keyword`, `TRIAGE:action-keyword`, `SPEC:friction-keyword`, `CODE-REVIEW:finding-keyword`, `SYSTEM:SYS-###-changed`. This is the primary dispatch mechanism — `revise-foundation` identifies which signals affect reference docs and passes them here. |
| `--target` | No | all | Target a single doc by filename (e.g., `--target authority.md`). When set, only that doc is edited. Cross-doc implications are flagged but not applied to other docs. |

## Preconditions

1. **Step 3 docs exist** — verify at least architecture.md and authority.md exist and are not at template defaults. If neither exists, stop: "No reference docs to revise. Run `/scaffold-seed references` first."
2. **Step 3 docs have been through pipeline** — verify at least one fix-references or iterate-references log exists. If no logs exist, stop: "Reference docs haven't been stabilized yet. Run the Step 3 pipeline first."
3. **Implementation feedback exists** — if `--signals` is provided, at least one signal must resolve. If not provided, at least one feedback source must exist (ADRs, KIs, triage logs, code review findings, system doc changes). If none exist, report: "No implementation feedback found. Nothing to revise."

### Context Files

| Context File | Why |
|-------------|-----|
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |

## Step 1 — Gather Implementation Feedback

**If `--signals` is provided:** Skip the broad scan. Read only the specific documents referenced by the signal list. Same resolution rules as revise-systems.

**If `--signals` is not provided:** Run the broad scan below.

### 1a. ADRs

Glob accepted ADRs. For each, check:
- Does it change entity identity, storage, or handle semantics? → architecture.md, entity-components.md
- Does it change state ownership? → authority.md, entity-components.md
- Does it add/remove/change cross-system contracts? → interfaces.md, signal-registry.md
- Does it add/remove states to a state machine? → state-transitions.md, enums-and-statuses.md
- Does it add/change resources or production chains? → resource-definitions.md
- Does it introduce new tunable parameters? → balance-params.md

### 1b. Known issues

Read `scaffold/decisions/known-issues.md`. Check for entries that reference Step 3 docs or imply reference-layer changes.

### 1c. System doc changes

**Baseline mechanism:** Use the latest `REVISION-references-YYYY-MM-DD.md` timestamp as the baseline. Treat system docs with modification dates after that timestamp as candidates for drift scan. If no revision log exists, treat all system docs as candidates (first revision pass after initial seed).

Compare current system docs against this baseline. For each system where Owned State, Upstream Dependencies, or Downstream Consequences changed:
- New Owned State entries → may need authority.md and entity-components.md entries
- New dependencies → may need interfaces.md contracts
- New consequences → may need signal-registry.md entries
- Changed State Lifecycle → may need state-transitions.md updates

This is the most common source of reference drift — system docs evolve during implementation but reference docs don't catch up.

### 1d. Spec/task friction

Search completed specs and tasks for explicit friction tied to reference docs:
- "authority.md doesn't list this variable"
- "no interface contract for this interaction"
- "state machine missing this state"
- "signal not in registry"

Only treat explicit friction as drift signals, not inferred patterns.

### 1e. Code review findings

Search code review logs for findings that suggest reference doc drift:
- New signals emitted that aren't in signal-registry.md
- New entity fields not in entity-components.md
- Cross-system interactions not covered by interfaces.md

**Evidence threshold:** Same as revise-systems — code review findings corroborate other evidence, not standalone authority.

### 1f. Architectural drift detection (broad scan only)

**Authority drift** — compare authority.md entries against system doc Owned State sections. If a system's Owned State changed but authority.md didn't, flag as authority drift.

**Interface drift** — compare interfaces.md contracts against system doc dependencies/consequences. If system interactions changed but contracts didn't, flag as interface drift.

**Signal drift** — compare signal-registry.md entries against system doc Downstream Consequences. If new signals are implied but not registered, flag.

**State drift** — compare state-transitions.md machines against system doc State Lifecycle sections. If states were added/removed/changed, flag.

**Entity drift** — compare entity-components.md fields against system doc Owned State. If new fields are implied but not registered, flag.

**Balance drift** — compare balance-params.md entries against system doc numeric behaviors. If new tunable parameters are implied, flag.

**Architecture drift** — if scene tree, dependency graph, or tick order in architecture.md no longer matches the actual system set, flag.

## Step 2 — Classify Drift Signals

### 2a. Map signals to docs

| Signal type | Likely affected docs |
|-------------|---------------------|
| New owned state in system doc | authority.md, entity-components.md |
| New system dependency | interfaces.md |
| New system consequence/signal | signal-registry.md, interfaces.md |
| State machine changed | state-transitions.md, enums-and-statuses.md |
| New resource/chain discovered | resource-definitions.md |
| New tunable parameter | balance-params.md |
| System added/removed from scene tree | architecture.md |
| Tick order changed | architecture.md |
| Identity/handle model changed | architecture.md, entity-components.md |
| Boot/init order changed | architecture.md |

### 2b. Evidence precedence

When multiple sources provide conflicting information about the same drift signal, resolve using this precedence (highest wins):

1. **Accepted ADR** — explicit project decision
2. **User decision** recorded in triage or revision log
3. **Higher-authority project doc** updated through approved pipeline
4. **Completed spec/task** showing implemented and approved reality
5. **Code review / friction evidence** — corroborative, not authoritative
6. **Known issue note** — weakest signal, indicates awareness not resolution

Lower-ranked evidence cannot override higher-ranked evidence. Conflicting evidence at the same rank escalates automatically.

### 2c. Severity classification

| Severity | Meaning | Action |
|----------|---------|--------|
| **Stale reference** | Doc references renamed/restructured system, ADR, or entity | Auto-update: fix reference |
| **Missing registration** | New system/signal/entity field/state reader/parameter exists in implementation but isn't registered — AND the underlying design change is already approved (ADR-backed, approved system doc change, completed spec). The entry is implied by an approved source, not a genuinely new design construct. | Auto-update: add entry with provenance |
| **Column/field update** | An existing entry needs a column value updated (e.g., new Readers in authority, new Consumer in signal-registry) | Auto-update: update column |
| **Deprecation drift** | Old name, signal, enum, parameter, or resource still present after canonical rename or removal. The replacement is explicit and approved. | Auto-update: mark deprecated or update to new name |
| **New cross-doc entry** | A genuinely new interface contract, state machine, entity, or resource that is NOT clearly implied by an already-approved design change. This is a new design construct, not a missing registration. | Escalate: requires user confirmation before adding |
| **Removal/retirement** | A signal, state, entity field, parameter, or resource is no longer used and should be removed or marked deprecated | Escalate: deletion is riskier than addition — only remove if backed by ADR or higher-authority doc change. Otherwise mark as deprecated. |
| **Authority change** | Ownership moved between systems | Escalate: update authority.md and entity-components.md with user confirmation |
| **Architecture change** | Scene tree, dependency graph, tick order, data flow rules, identity model, or boot order changed | Escalate: architecture changes affect everything downstream |
| **Contract change** | Interface direction, timing, realization path, or failure guarantee changed | Escalate: contract changes affect signal-registry and system expectations |
| **State machine change** | States added/removed, transitions changed, timing changed | Escalate: state changes affect entity-components, enums, and system designs |

### 2d. Design-led vs implementation-led

Same classification as revise-systems:
- **Design-led change** — backed by accepted ADR, triage decision, or user approval. Reference docs should catch up.
- **Implementation-led divergence** — build wandered without approval. Reference docs should *not* automatically update. Escalate.

## Step 3 — Apply Safe Updates

For each **Stale reference**, **Missing registration**, **Column/field update**, and **Deprecation drift** item:

1. Read the affected doc.
2. Apply the update using the Edit tool.
3. Record what was changed, why, and what feedback triggered it.
4. Add provenance: `<!-- REVISED: [date] — [trigger] -->`

**Safety rules:**
- **Respect canonical direction.** When updating cross-doc entries: authority.md is canonical for ownership. interfaces.md is canonical for contracts. state-transitions.md is canonical for state names. Update the canonical doc first; downstream docs (entity-components, signal-registry, enums) follow.
- **When `--target` is set, only edit the targeted doc.** Flag cross-doc implications for fix-references.
- **Never change architecture decisions.** Auto-updates may add entries (new signal, new authority row, new entity field) but must not change architectural rules, forbidden patterns, data flow rules, or tick order.
- **Never change contract direction or timing.** Adding a new consumer to a signal is safe. Changing Push to Pull is not.
- **Never change state machine structure.** Adding a cross-system reader is safe. Adding/removing states or transitions is not.
- **Never change authority ownership.** Adding a new Readers entry is safe. Changing Owning System is not.
- **Missing registrations must have explicit evidence.** Only add entries when backed by a system doc change, ADR, or completed spec. Never add entries based on inference from code alone.
- **No duplicate entries.** Before adding any entry, check equivalence keys (same rules as seed references and fix-references).

## Step 4 — Escalate Design-Level Changes

For each **New cross-doc entry**, **Removal/retirement**, **Authority change**, **Architecture change**, **Contract change**, and **State machine change**:

Present using the Human Decision Presentation pattern:

```
### Reference Escalation #N

**Signal:** [source — ADR-###, system doc change, spec friction, code review]
**Affected doc(s):** [architecture.md, authority.md, etc.]
**Current doc says:** [what the reference doc states]
**Implementation reality:** [what was actually built or observed]
**Design-led or implementation-led:** [backed by ADR/triage, or unapproved divergence]

**Options:**
a) Update reference doc to match implementation — [implication, cross-doc effects]
b) file via `/scaffold-file-decision --type adr` to correct the implementation — [implication]
c) Defer — file via `/scaffold-file-decision --type ki` for future resolution

**Likely follow-up:** [fix-references --target X / iterate-references --target X / validate --scope refs / none]
```

**For authority changes:** show the old and new ownership side by side, including which entity-components entries would need updating.

**For architecture changes:** note that architecture changes cascade to all downstream docs. Likely follow-up: fix-references (full, not targeted) → iterate-references → validate --scope refs.

**For contract changes:** note that interface changes require matching signal-registry updates. Present both sides.

## Step 5 — Cross-Doc Consistency Check

After applying updates and resolving escalations, verify:

- **Authority → Entity-Components** — if authority.md was updated, does entity-components.md still match?
- **Interfaces → Signal Registry** — if interfaces.md was updated, do signal-registry entries still match?
- **State-Transitions → Enums** — if state-transitions.md was updated, does enums-and-statuses.md still match?
- **Architecture → All** — if architecture.md was updated, do scene tree, tick order, and signal wiring still match the other docs?

Apply safe alignment updates within Step 3 docs following canonical direction. Flag cross-layer updates (system docs, engine docs) for human action.

**Do not auto-heal around unresolved escalations.** If a cross-doc inconsistency depends on an unresolved escalation from Step 4, do not auto-align the downstream doc yet. Otherwise Step 5 could accidentally create fake consistency on top of a pending authority or architecture decision.

## Step 6 — Update Revision History

**Log location:** `scaffold/decisions/revision-logs/REVISION-references-YYYY-MM-DD.md`

```markdown
# Reference Revision: YYYY-MM-DD

**Source:** [PHASE-### completed / SLICE-### completed / foundation-recheck / broad scan]
**Feedback items processed:** N
**Auto-updated:** N
**Escalated:** N issues
**Deferred:** N issues
**Docs affected:** [list]

## Updates Applied
| # | Doc | Section/Entry | Change | Trigger | Classification |
|---|-----|--------------|--------|---------|----------------|
| 1 | authority.md | Time & Calendar | Added game_day readers | SYS-001 Owned State change | Missing registration |
| 2 | signal-registry.md | Signals | Added zone_filter_changed | TASK-072 completion | Missing registration |

## Escalations
| # | Type | Doc(s) | Resolution |
|---|------|--------|------------|
| 1 | Authority change | authority.md, entity-components.md | User chose option (a) |
| 2 | Architecture change | architecture.md | User chose option (c) — deferred |

## Deferred Issues
| # | Doc | Issue | Reason |
|---|-----|-------|--------|
| 1 | interfaces.md | New contract needed for X→Y | Needs more implementation data |
```

## Step 7 — Report

```
## References Revised

### Summary
| Field | Value |
|-------|-------|
| Source | [PHASE-### / SLICE-### / foundation-recheck / broad scan] |
| Feedback items | N processed |
| Auto-updated | N |
| Escalated | N issues (N resolved, N deferred) |
| Docs affected | N |

### Reference Model Confidence
**Stable / Decreased / Improved** — [Based on: number and severity of drift signals, whether authority boundaries held, whether cross-doc consistency is intact.]

### Next Steps
- Run `/scaffold-fix references [--target X]` to clean up mechanical issues from updates
- Run `/scaffold-iterate references [--target X --topics "affected"]` to review changed areas
- Run `/scaffold-validate --scope refs` to confirm structural readiness
```

If no drift detected:
```
## References Revised

**Status: No drift detected** — reference docs are consistent with implementation feedback. No changes made.
```

## Rules

- **Only edit Step 3 docs.** Never edit system designs, design doc, engine docs, specs, tasks, or planning docs.
- **Respect canonical direction.** authority.md → entity-components. interfaces.md → signal-registry. state-transitions.md → enums. Update canonical docs first; downstream follows.
- **When `--target` is set, only edit the targeted doc.** Cross-doc implications are flagged for fix-references.
- **Architecture is sacred until the user changes it.** Never auto-update architecture rules, forbidden patterns, data flow rules, tick order, identity model, or boot order. Those define the project's engineering foundation.
- **Authority ownership is sacred until the user changes it.** Never auto-change Owning System. Adding Readers is safe. Changing who writes is not.
- **Contract semantics are sacred until the user changes it.** Never auto-change Direction, Timing, or Realization Path. Adding consumers is safe. Changing the contract shape is not.
- **State machine structure is sacred until the user changes it.** Never auto-add/remove states or transitions. Adding cross-system readers is safe. Changing the machine is not.
- **Only accepted or corroborated signals count as drift.** Accepted decisions (ADR, triage, user approval) count directly. Observed implementation reality (completed spec, code review finding) counts only when corroborated by approved evidence or explicit completed artifacts — not from observation alone. Proposed ≠ accepted, explored ≠ decided, observed ≠ proven.
- **Design-led changes catch up. Implementation-led divergence escalates.** Same rule as revise-systems.
- **Missing registrations require explicit evidence.** Only add entries backed by system doc changes, ADRs, or completed specs. Never from inference alone.
- **No duplicate entries.** Check equivalence keys before adding.
- **Deletion is riskier than addition.** Never delete entries without ADR or higher-authority doc change backing the removal. Prefer marking entries as deprecated over deleting them. Deprecation drift (safe rename/update) is auto-fixable; removal/retirement always escalates.
- **Evidence precedence resolves conflicts.** When sources disagree: accepted ADR > user decision > higher-authority doc > completed spec > code review > known issue. Lower-ranked evidence cannot override higher-ranked. Conflicting same-rank evidence escalates.
- **Cross-doc updates follow canonical direction.** Never "split the difference" between ranked docs. Higher-rank doc is always right.
- **Revision suppression when architecture is unstable.** If architecture.md itself has unresolved escalations, suppress auto-updates to downstream docs until the architecture is stable. Same pattern as revise-systems' identity-unstable suppression.
- **Always write a revision log.** Every run produces a dated record.
- **Confidence heuristic.** Improved: mostly auto-updates, authority boundaries held. Stable: mix of auto-updates and escalations, architecture intact. Decreased: authority shifts, architecture changes, or multiple docs affected by the same drift signal.

---
name: scaffold-revise-style
description: Detect Step 5 visual/UX doc drift from implementation feedback and apply safe updates or escalate for decisions. Reads ADRs, known issues, spec/task friction, code review findings, system doc changes, and Step 3 doc changes to identify when style docs no longer match what was actually built or what upstream docs now define. Use after a phase or slice completes, or when revise-foundation detects Step 5 drift.
argument-hint: [--source P#-###|SLICE-###|foundation-recheck] [--signals ADR-###,KI:keyword] [--target doc.md]
allowed-tools: Read, Edit, Grep, Glob
---

# Revise Style

Detect visual/UX doc drift and update Step 5 docs from implementation feedback: **$ARGUMENTS**

Step 5 docs are the visual identity and UX layer — they define aesthetic direction, color tokens, UI components, interaction patterns, feedback responses, and audio direction. But implementation reveals realities that initial style docs couldn't anticipate: new entity states need color tokens, new player actions need feedback entries, interaction patterns evolve during playtesting, UI components get added or removed, and upstream docs (design doc, systems, Step 3 references) get revised. This skill reads implementation feedback, classifies what changed, applies safe evidence-backed updates directly, and escalates aesthetic/UX-level changes for human decision.

This is distinct from:
- **`fix-style`** — repairs mechanical structure (this skill identifies *design-level* drift, not formatting)
- **`iterate-style`** — adversarial design review (this skill processes *implementation signals*, not reviewer critique)
- **`bulk-seed-style`** — creates docs from scratch (this skill updates existing docs from feedback)

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source` | No | auto-detect | What triggered the revision: `P#-###` (phase completed), `SLICE-###` (slice completed), `foundation-recheck` (dispatched from revise-foundation). If omitted, scans all recent feedback. |
| `--signals` | No | — | Comma-separated list of specific drift signals to process. When provided, skip the broad feedback scan and process only these items. Accepted formats: `ADR-###`, `KI:keyword`, `TRIAGE:action-keyword`, `SPEC:friction-keyword`, `CODE-REVIEW:finding-keyword`, `SYSTEM:SYS-###-changed`, `REFS:doc-changed`, `PLAYTEST:keyword`. This is the primary dispatch mechanism — `revise-foundation` identifies which signals affect style docs and passes them here. |
| `--target` | No | all | Target a single doc by filename (e.g., `--target style-guide.md`, `--target ui-kit.md`). When set, only that doc is edited. Cross-doc implications are flagged but not applied to other docs. |

### Valid --target values

| Target | Doc Path | Template |
|--------|----------|----------|
| `style-guide.md` | `design/style-guide.md` | `templates/style-guide-template.md` |
| `color-system.md` | `design/color-system.md` | `templates/color-system-template.md` |
| `ui-kit.md` | `design/ui-kit.md` | `templates/ui-kit-template.md` |
| `interaction-model.md` | `design/interaction-model.md` | `templates/interaction-model-template.md` |
| `feedback-system.md` | `design/feedback-system.md` | `templates/feedback-system-template.md` |
| `audio-direction.md` | `design/audio-direction.md` | `templates/audio-direction-template.md` |

### Signal Resolution Table

| Signal Format | Resolves To | Search Scope |
|--------------|-------------|-------------|
| `ADR-###` | Exact ADR file by ID | `scaffold/decisions/ADR-###-*.md` |
| `KI:keyword` | Known issue entries matching keyword | Grep `scaffold/decisions/known-issues.md` title and body |
| `TRIAGE:keyword` | Triage log entries matching keyword | Grep `scaffold/decisions/triage-logs/TRIAGE-*.md` Decisions + Upstream Actions tables |
| `SPEC:keyword` | Spec/task friction notes matching keyword | Grep completed specs and task files for friction comments |
| `CODE-REVIEW:keyword` | Code review findings matching keyword | Grep `scaffold/decisions/review/*code-review*` logs only |
| `SYSTEM:SYS-###-changed` | Exact system file by ID | `scaffold/design/systems/SYS-###-*.md` |
| `REFS:doc-stem` | Exact Step 3 doc by filename stem | `scaffold/design/<doc-stem>.md` or `scaffold/reference/<doc-stem>.md` |
| `PLAYTEST:keyword` | Playtest feedback entries matching keyword | Grep `scaffold/decisions/playtest-feedback.md` |

## Preconditions

1. **Step 5 docs exist** — if `--target` is set, verify the targeted doc exists. If not set, verify at least 1 Step 5 doc exists. If none exist, stop: "No style docs to revise. Run `/scaffold-bulk-seed-style` first." Cross-doc checks that require a missing peer doc are downgraded to partial coverage warnings (e.g., "color-system not found — skipping token resolution checks").
2. **Step 5 docs have been through pipeline** — verify at least one fix-style or iterate-style log exists in `scaffold/decisions/review/`. If none, stop: "Style docs haven't been stabilized yet. Run the Step 5 pipeline first."
3. **Implementation feedback exists** — if `--signals` is provided, at least one signal must resolve. If not provided, at least one feedback source must exist (ADRs, KIs, system doc changes, Step 3 doc changes, playtest feedback, task completions). If none exist, report: "No implementation feedback found. Nothing to revise."

### Context Files

| Context File | Why |
|-------------|-----|
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules |
| `scaffold/design/design-doc.md` | Core Fantasy, Failure Philosophy, Player Control Model — upstream aesthetic intent |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/design/systems/_index.md` | Registered system IDs and names |
| `scaffold/design/state-transitions.md` | Entity states that map to color tokens and feedback |
| `scaffold/reference/entity-components.md` | Entity types for icon/visual coverage |
| `scaffold/reference/resource-definitions.md` | Resources for UI representation |
| `scaffold/reference/signal-registry.md` | Signals that may trigger feedback events |
| `scaffold/decisions/known-issues.md` | Known gaps and constraints |
| `scaffold/decisions/playtest-feedback.md` | Player-reported UX issues |
| ADRs with status `Accepted` | Decision compliance |

## Step 1 — Gather Implementation Feedback

**If `--signals` is provided:** Skip the broad scan. Read only the specific documents referenced by the signal list.

**If `--signals` is not provided:** Run the broad scan below.

### 1a. ADRs

Glob accepted ADRs. For each, check:
- Does it change visual identity, art direction, or aesthetic pillars? → style-guide
- Does it add/change/remove entity states that need color representation? → color-system
- Does it add/change UI components or interaction affordances? → ui-kit
- Does it change player control model, input patterns, or interaction approach? → interaction-model
- Does it change how the game communicates events to the player? → feedback-system
- Does it change audio direction, sound categories, or priority hierarchy? → audio-direction
- Does it change accessibility requirements? → color-system, feedback-system, interaction-model

### 1b. Known issues

Read `scaffold/decisions/known-issues.md`. Check for entries that reference Step 5 docs or imply visual/UX-layer changes.

### 1c. Playtest feedback

Read `scaffold/decisions/playtest-feedback.md`. Check for Pattern-status entries (3+ reports) that relate to:
- Visual clarity — players can't distinguish states or priorities
- Feedback confusion — players miss events or misinterpret signals
- Interaction friction — players struggle with controls or don't discover actions
- Audio overload or absence — too many sounds at once, or missing audio cues
- Accessibility barriers — color-only information, hover-only cues

Playtest patterns are a unique feedback source for Step 5 — player-visible issues directly affect style doc accuracy.

### 1d. Design doc changes

**Baseline mechanism:** Use the latest `REVISION-style-YYYY-MM-DD.md` for baselines. The global `Revision Timestamp` field sets the overall baseline. Additionally, the `Docs affected` list and `Updates Applied` table track which Step 5 docs were actually revised in each run. For per-doc staleness, use the last revision log that lists the specific Step 5 doc in its `Docs affected` — not just the global timestamp. This prevents masking per-doc staleness when only some docs were revised in the latest run. If no revision log exists, treat all docs as candidates (first revision pass).

Compare current design doc against baseline. For sections that changed:
- Core Fantasy changed → style-guide tone registers may be stale
- Failure Philosophy changed → feedback-system Critical event handling may be stale
- Player Control Model changed → interaction-model complexity may be stale
- Presentation section changed → style-guide, color-system, audio-direction may be stale
- Content section changed → ui-kit component coverage may be stale

### 1e. System doc changes

**Baseline mechanism:** Same per-doc-aware mechanism as 1d — for each Step 5 doc that would be affected by a system change, use that Step 5 doc's last revision baseline (the most recent revision log that lists it in `Docs affected`), not just the global revision timestamp. A system doc change is a candidate only if it post-dates the relevant Step 5 doc's baseline.

Compare current system docs against baseline. For each system where relevant sections changed:
- New Player Actions → interaction-model may need new commands, feedback-system may need new events. **Gate:** only if the action is explicitly marked as player-facing in the system doc and the system doc is Approved. Internal, conditional, or provisional actions are logged as advisory drift, not auto-update candidates.
- New Owned State entries → color-system may need new state tokens
- New Visibility to Player content → ui-kit may need new display components
- New Failure / Friction States → feedback-system may need new error/warning events
- New Feel & Feedback descriptions → feedback-system and audio-direction may need new entries

### 1f. Step 3 doc changes

**Baseline mechanism:** Same per-doc-aware mechanism as 1d — for each Step 5 doc that would be affected by a Step 3 change, use that Step 5 doc's last revision baseline, not the global timestamp.

Compare current Step 3 docs against baseline. For sections that changed:
- state-transitions.md states added/changed → color-system state tokens may be stale
- entity-components.md entities added/changed → style-guide and ui-kit visual coverage may be stale
- resource-definitions.md resources added/changed → ui-kit resource representation may be stale
- signal-registry.md signals added/changed → feedback-system Event-Response Table may be stale
- interfaces.md contracts changed → interaction-model may need updates if player-facing

### 1g. Spec/task friction

Search completed specs and tasks for explicit friction tied to Step 5 docs:
- "No color token for this state"
- "feedback-system doesn't cover this event"
- "interaction-model doesn't describe how the player does X"
- "ui-kit has no component for this"
- "audio-direction doesn't define a category for this sound"

Only treat explicit friction as drift signals, not inferred patterns.

### 1h. Code review findings

Search code review logs for findings that suggest Step 5 doc drift:
- UI implementations that don't match ui-kit component definitions
- Color values used in code that don't match color-system tokens
- Feedback events implemented without matching feedback-system entries
- Interaction patterns in code that aren't documented in interaction-model

**Evidence threshold:** Code review findings are **candidate drift only** — they cannot independently justify auto-editing Step 5 docs. A code review finding upgrades to actionable drift only when paired with at least one of: an approved upstream change (ADR, system doc, Step 3 doc), a completed and approved implementation artifact (spec, task), or a playtest pattern (3+ reports). Without corroboration, code review findings are logged as advisory in the revision log but do not trigger auto-updates or escalations.

### 1i. Early exit check

After gathering all signals from Steps 1a–1h, filter to those that actually map to Step 5 docs (using the Step 2a mapping table). If no valid style-impacting drift signals remain after filtering, exit early:

"No style-impacting drift detected from provided signals. No changes made."

Do not proceed to Steps 2–7. Write a minimal revision log noting the scan was clean.

## Step 2 — Classify Drift Signals

### 2a. Map signals to docs

| Signal type | Likely affected Step 5 docs |
|-------------|---------------------------|
| Core Fantasy / aesthetic direction changed | style-guide |
| New entity state in state-transitions.md | color-system |
| New entity type in entity-components.md | style-guide (visual description), ui-kit (display component) |
| New resource in resource-definitions.md | ui-kit (resource display) |
| New signal in signal-registry.md | feedback-system (Event-Response Table) |
| New player action in system design (explicitly player-facing, approved, and intended to remain in the player contract) | interaction-model, feedback-system |
| New system with player visibility | ui-kit, feedback-system |
| Failure Philosophy changed | feedback-system (Critical event handling) |
| Player Control Model changed | interaction-model |
| Accessibility requirement changed | color-system, feedback-system, interaction-model |
| Playtest pattern: visual clarity | color-system, style-guide |
| Playtest pattern: feedback confusion | feedback-system, audio-direction |
| Playtest pattern: interaction friction | interaction-model, ui-kit |
| Audio direction or priority changed | audio-direction, feedback-system |
| UI component added/removed in implementation | ui-kit |

### 2b. Evidence precedence

1. **Accepted ADR** — explicit project decision
2. **User decision** recorded in triage or revision log
3. **Higher-authority project doc** updated through approved pipeline (design doc, systems, Step 3)
4. **Playtest pattern** (3+ reports) — player-reported UX reality
5. **Completed spec/task** showing implemented and approved reality
6. **Code review / friction evidence** — corroborative, not authoritative
7. **Known issue note** — weakest signal

Lower-ranked evidence cannot override higher-ranked evidence. Conflicting evidence at the same rank escalates automatically.

**Playtest pattern note:** Playtest patterns rank higher than individual specs/tasks because they represent observed player experience across multiple sessions. A player repeatedly misunderstanding a visual cue is stronger evidence than a single task's implementation choice.

**Playtest upstream anchor rule:** Playtest patterns can justify additive documentation of already-approved behavior (e.g., adding a missing feedback entry for an event that already exists in signal-registry.md). Playtest patterns cannot create new semantic categories, gameplay-significant event types, or interaction primitives unless the underlying behavior already exists upstream. If the playtest pattern implies a new concept not yet defined in systems or Step 3, escalate — the upstream definition must come first.

### 2c. Severity classification

| Severity | Meaning | Action |
|----------|---------|--------|
| **Stale reference** | Doc references renamed system, state, entity, or signal | Auto-update: fix reference |
| **Missing token/entry** | New state, entity, resource, or signal exists upstream but has no Step 5 representation — AND the upstream change is already approved | Auto-update: add entry with provenance |
| **Token value update** | An existing token's upstream reference changed (e.g., state renamed, entity restructured) | Auto-update: update to match upstream |
| **Cross-doc alignment** | One Step 5 doc changed and a peer doc has a deterministic reference to sync (e.g., renamed token reference, new token that fills an existing reference slot) | Auto-update only for deterministic reference sync. Escalate if alignment requires semantic assignment (choosing which token, priority, or affordance pattern). |
| **Feedback table entry** | New signal or player action needs a feedback-system Event-Response Table row | Auto-update: add row with constrained defaults if upstream is approved AND a closely analogous existing row exists in the same table. Escalate if no analogous pattern exists. |
| **Aesthetic direction change** | Core Fantasy, tone, or visual identity shifted — affects style-guide pillars, tone registers, or overall direction | Escalate: aesthetic changes are subjective and affect all downstream docs |
| **Interaction model change** | Player control model or interaction approach changed fundamentally | Escalate: interaction changes affect ui-kit, feedback-system, and audio-direction |
| **Priority hierarchy change** | Feedback priority ordering or audio hierarchy needs restructuring | Escalate: priority changes affect how the player perceives event importance |
| **Component removal** | A ui-kit component, color token, or feedback entry is no longer used | Escalate: removal risks breaking downstream references |
| **Accessibility change** | Contrast requirements, redundancy rules, or input accessibility requirements changed | Escalate: accessibility changes have compliance implications |
| **Token system restructure** | Color-system token naming, categorization, or semantic grouping needs reorganization | Escalate: token restructure affects every doc that references tokens |

### 2d. Design-led vs implementation-led

- **Design-led change** — backed by accepted ADR, design doc update, system doc change, or triage decision. Step 5 docs should catch up to upstream authority.
- **Implementation-led divergence** — UI/UX code wandered from Step 5 docs without approval. Step 5 docs should *not* automatically update. Escalate to determine whether the code or the doc is wrong.
- **Playtest-led change** — backed by playtest pattern (3+ reports). Stronger than pure implementation-led but still requires user confirmation for aesthetic/interaction changes. Auto-update is allowed for additive entries (new feedback row, new token) but not for modifications to existing aesthetic direction.

**Repeated divergence escalation:** If the same implementation-led divergence appears in 2+ revision runs (check prior revision logs), escalate severity to **"Forced decision required"** — the user must choose option (a) or (b), not (c) defer.

**Divergence equivalence key:** Two divergences are "the same" if they share all three components: (1) affected Step 5 doc, (2) affected section/table, (3) underlying conflict topic.

## Step 3 — Apply Safe Updates

For each **Stale reference**, **Missing token/entry**, **Token value update**, **Cross-doc alignment**, and **Feedback table entry** item:

1. Read the affected Step 5 doc.
2. Apply the update using the Edit tool.
3. Record what was changed, why, and what feedback triggered it.
4. Add provenance: `<!-- REVISED: [date] — [trigger] -->`

**Safety rules:**
- **Step 5 docs follow upstream for referential truth, not aesthetic wholesale.** When design doc changes creative intent (Core Fantasy, tone, player experience), Step 5 aligns aesthetically. When systems or Step 3 docs change factual data (state names, entity names, signal names, resource names, approved player actions), Step 5 aligns referentially. Never let a lower-ranked doc's change drive Step 5 aesthetic or UX decisions — only vocabulary and data updates propagate automatically.
- **Respect the Step 5 authority flow.** style-guide → color-system → ui-kit. interaction-model and feedback-system are peers. audio-direction derives priority from feedback-system. When updating, follow this direction — never let a downstream doc's change propagate backward.
- **When `--target` is set, only edit the targeted doc.** Flag cross-doc implications for fix-style.
- **Never change aesthetic direction without escalation.** Auto-updates may add tokens, entries, and references — but tone registers, aesthetic pillars, visual identity decisions, and interaction philosophy are aesthetic-level changes that must escalate.
- **Never change priority hierarchies without escalation.** Adding a new feedback entry with a reasonable priority is safe. Restructuring the priority hierarchy is not.
- **New tokens follow existing naming patterns.** When auto-adding a color token, follow the existing token naming convention in color-system (prefix pattern, semantic grouping). If the naming pattern is unclear, escalate.
- **New feedback entries use constrained defaults.** Auto-adding an Event-Response Table row is only safe when a closely analogous row already exists in the table (same event category, similar trigger pattern). Copy the analogous row's structure with: non-critical priority, low or medium severity, single conservative channel. Never auto-add a Critical event. Never auto-assign priority that would reshuffle the existing hierarchy. If no analogous row exists, escalate — the skill should not invent feedback patterns.
- **No duplicate tokens or entries.** Before adding any entry, check for existing entries with the same semantic meaning (exact name match or same state/entity/signal reference).
- **Cross-doc alignment follows canonical direction.** color-system is canonical for token definitions. ui-kit references tokens, not the reverse. feedback-system is canonical for event-response mappings. audio-direction references feedback priorities, not the reverse.

## Step 4 — Escalate Design-Level Changes

For each **Aesthetic direction change**, **Interaction model change**, **Priority hierarchy change**, **Component removal**, **Accessibility change**, and **Token system restructure**:

**Escalation severity weighting:**

| Priority | Escalation Types | Meaning |
|----------|-----------------|---------|
| **CRITICAL** | Accessibility change | Affects compliance and player inclusion. Resolve before continuing implementation. |
| **HIGH** | Aesthetic direction change, Interaction model change, Priority hierarchy change | Affects player perception across the game. Resolve before next slice. |
| **MEDIUM** | Component removal, Token system restructure | Affects Step 5 doc organization. Can proceed with current work but resolve before next phase. |

Present CRITICAL escalations first, then HIGH, then MEDIUM. The revision log records priority alongside each escalation.

Present using the Human Decision Presentation pattern:

```
### Style Escalation #N

**Signal:** [source — ADR-###, design doc change, system doc change, playtest pattern, spec friction]
**Affected doc(s):** [style-guide, color-system, ui-kit, interaction-model, feedback-system, audio-direction]
**Current doc says:** [what the Step 5 doc states]
**Implementation/upstream reality:** [what changed upstream or what was actually built]
**Design-led, playtest-led, or implementation-led:** [backed by upstream change/ADR, player feedback pattern, or unapproved divergence]

**Options:**
a) Update style doc to match — [implication, cross-doc effects, which other Step 5 docs need updating]
b) Keep style doc, update implementation — [implication, what code/upstream needs changing]
c) Defer — file via `/scaffold-file-decision --type ki` for future resolution

**Likely follow-up:** [fix-style --target X / iterate-style --target X --topics "affected" / validate --scope style / none]
```

**For aesthetic direction changes:** show the old and new direction side by side. Note that aesthetic changes cascade through all 6 Step 5 docs. List which downstream docs would need updating.

**For interaction model changes:** note that interaction changes affect ui-kit (affordances), feedback-system (event coverage), and audio-direction (sound categories). Present the full impact chain.

**For priority hierarchy changes:** show the old and new ordering. Note that priority changes affect both feedback-system and audio-direction simultaneously.

**For accessibility changes:** note compliance implications. Present WCAG level targets if applicable. List which docs are affected (typically color-system for contrast, feedback-system for redundancy, interaction-model for input alternatives).

**For component removal:** verify no specs, tasks, engine docs, or other Step 5 docs reference the component. Specifically check: interaction-model affordances that imply the component, feedback-system UI channel entries that reference it, style-guide visual language examples that describe it, and color-system tokens scoped to it. List all references found.

## Step 5 — Cross-Doc Consistency Check

After applying updates and resolving escalations, verify:

- **style-guide ↔ color-system** — if style-guide tone registers changed, does color-system's palette still reflect the mood?
- **color-system ↔ ui-kit** — if color-system tokens were added/changed, does ui-kit reference them correctly?
- **interaction-model ↔ ui-kit** — if interaction-model actions changed, does ui-kit have matching affordances?
- **interaction-model ↔ feedback-system** — if interaction-model actions changed, does feedback-system have matching event entries?
- **feedback-system ↔ audio-direction** — if feedback-system events changed, does audio-direction have matching sound categories?
- **feedback-system ↔ color-system** — if feedback-system priorities changed, do color token assignments still reflect the visual hierarchy?
- **All Step 5 docs ↔ design doc** — if design doc Core Fantasy, Failure Philosophy, or Player Control Model changed, do Step 5 docs still align?

Apply **deterministic alignment updates** only — these are safe to auto-apply:
- Renamed token/entity/state/signal/resource reference → update the reference to the new name
- New cross-reference where the mapping already exists upstream (e.g., color-system added a token, ui-kit table already references that token category) → add the reference
- Syncing table references after an approved additive change from Step 3

**Escalate or log as advisory** — these involve semantic choices:
- Assigning which token a new component should use
- Assigning which sound category matches a new feedback row
- Assigning priority level to a new entry
- Assigning presentation weight or visual hierarchy position
- Deciding interaction affordance shape or pattern for a new action

Do not lump semantic choices into "reasonable defaults." If no closely analogous existing pattern exists in the same doc, escalate rather than guess.

Flag cross-layer updates (system docs, Step 3 docs, engine docs) for human action.

**Do not auto-heal around unresolved escalations.** If a cross-doc inconsistency depends on an unresolved escalation from Step 4, do not auto-align yet.

**Reference integrity after update:** After all consistency edits, verify that updated Step 5 docs still have valid:
- `Conforms to` links (targets still exist)
- Color token references in ui-kit (tokens exist in color-system)
- Audio category references in feedback-system (categories exist in audio-direction)
- State/entity/resource references (upstream entries still exist)

This is a lightweight post-edit validation, not a full `/scaffold-validate --scope style` run. It catches breakage introduced by the revision itself.

## Step 6 — Update Revision History

**Log location:** `scaffold/decisions/revision-logs/REVISION-style-YYYY-MM-DD.md`

```markdown
# Style Revision: YYYY-MM-DD

**Revision Timestamp:** YYYY-MM-DDTHH:MM:SSZ
**Source:** [P#-### completed / SLICE-### completed / foundation-recheck / broad scan]
**Feedback items processed:** N
**Auto-updated:** N
**Escalated:** N issues
**Deferred:** N issues
**Docs affected:** [list]
**Per-doc baselines used:**
- style-guide.md: last revised YYYY-MM-DD (REVISION-style-YYYY-MM-DD)
- color-system.md: last revised YYYY-MM-DD (REVISION-style-YYYY-MM-DD)
- [etc. — only list docs that were checked in this run]

## Updates Applied
| # | Doc | Section/Entry | Change | Trigger | Classification |
|---|-----|--------------|--------|---------|----------------|
| 1 | color-system | State Tokens | Added colonist_fleeing token | state-transitions.md new state | Missing token |
| 2 | feedback-system | Event-Response Table | Added zone_alert row | signal-registry.md new signal | Feedback table entry |
| 3 | ui-kit | Resource Display | Updated ore icon reference | resource-definitions.md rename | Stale reference |

## Escalations
| # | Priority | Type | Doc(s) | Resolution |
|---|----------|------|--------|------------|
| 1 | HIGH | Aesthetic direction | style-guide | User chose option (a) |
| 2 | CRITICAL | Accessibility | color-system, feedback-system | User chose option (a) |
| 3 | MEDIUM | Component removal | ui-kit | User chose option (c) — deferred |

## Deferred Issues
| # | Doc | Issue | Reason |
|---|-----|-------|--------|
| 1 | ui-kit | Orphan tooltip component | Needs design decision — may be used in Phase 2 |

## Advisory Drift Deferred
| # | Upstream Doc | Affected Style Doc | Reason Suppressed |
|---|-------------|--------------------|--------------------|
| 1 | design-doc.md | style-guide | Design doc section is Draft — advisory only until Approved |
```

## Step 7 — Report

```
## Style Docs Revised

### Summary
| Field | Value |
|-------|-------|
| Source | [P#-### / SLICE-### / foundation-recheck / broad scan] |
| Feedback items | N processed |
| Auto-updated | N |
| Escalated | N issues (N resolved, N deferred) |
| Docs affected | N |

### Visual/UX Layer Confidence
**Stable / Decreased / Improved** — [Based on: number and severity of drift signals, whether aesthetic direction held, whether cross-doc consistency is intact, whether token system stayed clean, how many playtest patterns were addressed.]

### Next Steps
- Run `/scaffold-fix-style [--target X]` to clean up mechanical issues from updates
- Run `/scaffold-iterate-style [--target X --topics "affected"]` to review changed areas
- Run `/scaffold-validate --scope style` to confirm structural readiness
```

If no drift detected:
```
## Style Docs Revised

**Status: No drift detected** — style docs are consistent with implementation feedback and upstream docs. No changes made.
```

## Rules

- **Only edit Step 5 docs.** Never edit design doc, system designs, Step 3 docs, engine docs, specs, tasks, or planning docs.
- **Step 5 docs follow upstream authority — but only for specific reasons.** Step 5 docs (Rank 2) follow the design doc (Rank 1) for **creative intent**: Core Fantasy, aesthetic direction, tone, player experience goals. Step 5 docs follow systems (Rank 5) and Step 3 docs (Rank 3-6) only for **factual referential truth**: state names, entity names, signal names, resource names, and player-visible actions already approved upstream. Lower-ranked docs do not drive Step 5 aesthetic or UX decisions wholesale — they supply the vocabulary and data that Step 5 docs present. If a Step 5 doc seems right and the design doc seems wrong, flag for revise-design — do not edit the design doc.
- **Respect the Step 5 authority flow.** style-guide → color-system → ui-kit. feedback-system → audio-direction. interaction-model and feedback-system are peers. Update in flow direction — never propagate changes backward.
- **When `--target` is set, only edit the targeted doc.** Cross-doc implications are flagged for fix-style.
- **Aesthetic direction is sacred until the user changes it.** Never auto-change tone registers, aesthetic pillars, visual identity principles, or mood descriptors. These are subjective creative decisions.
- **Priority hierarchies are sacred until the user changes it.** Never auto-change the ordering of feedback priorities or audio hierarchy. Adding entries at reasonable priorities is safe. Restructuring the hierarchy is not.
- **Token naming follows existing patterns.** Auto-added tokens must follow the established prefix/grouping convention. If the convention is unclear, escalate.
- **New feedback entries require an analogous pattern.** Only auto-add when a closely analogous row exists in the table. **"Closely analogous" means:** same event family (e.g., both are resource events, both are alert events), same trigger class (e.g., both triggered by state transitions, both triggered by player actions), and same player-facing urgency band (e.g., both are informational, both are warnings). All three must match. Copy structure from the analogous row with constrained defaults (non-critical, low/medium, single channel). Never auto-add Critical events. If no analogous row exists, escalate.
- **Only accepted or corroborated signals count as drift.** Accepted decisions (ADR, triage, user approval) count directly. Playtest patterns (3+ reports) count for additive changes. Observed implementation reality counts only when corroborated.
- **Design-led changes catch up. Implementation-led divergence escalates.** If upstream authority changed (design-led), Step 5 docs follow. If code diverged from Step 5 docs without authority (implementation-led), escalate to decide which is right. Playtest-led changes allow auto-update for additive entries but escalate for modifications.
- **No duplicate tokens or entries.** Check for semantic equivalence before adding.
- **Deletion is riskier than addition.** Never delete tokens, components, feedback entries, or sound categories without ADR or upstream authority change backing the removal. Prefer marking as deprecated over deleting.
- **Evidence precedence resolves conflicts.** When sources disagree: accepted ADR > user decision > higher-authority doc > playtest pattern > completed spec > code review > known issue.
- **Cross-doc updates follow authority flow.** style-guide is the aesthetic source. color-system is the token source. feedback-system is the event source. Downstream docs conform to their upstream, not the reverse.
- **Revision suppression when upstream is unstable.** If the design doc has unresolved escalations (from revise-design), suppress auto-updates to Step 5 docs that depend on those decisions. Same for Step 3 docs with unresolved escalations from revise-references. **Partial instability:** if an upstream doc changed but is not stabilized (Status is Draft or Review, not Approved), treat drift signals from that doc as **advisory only** — log them but do not auto-update Step 5 docs. **Exception — referential breakage is always repairable:** if an unstable upstream doc renamed a state, signal, entity, or resource and the old name no longer resolves anywhere in the project, the stale reference in the Step 5 doc can be fixed as hygiene even though the upstream is Draft. The test: does the old reference still exist anywhere? If not, the project has effectively adopted the new name and preserving the broken reference helps no one. Semantic drift (new interpretation, changed meaning) from unstable upstream remains advisory only.
- **Accessibility changes always escalate.** Even when backed by ADR, accessibility changes have compliance implications that require explicit user confirmation.
- **Accessibility findings are never suppressed by instability.** The upstream instability suppression rule (Draft/Review → advisory only) does not apply to accessibility risks. If a code review or implementation reveals an accessibility barrier (color-only state, hover-only cue, single-channel critical event), surface it as an advisory finding even when the upstream doc is Draft. Design alignment drift from unstable upstream should be suppressed; accessibility risk to players should always be visible.
- **Always write a revision log.** Every run produces a dated record.
- **Confidence heuristic is advisory only.** Improved: mostly auto-updates, aesthetic direction held, playtest patterns addressed. Stable: mix of auto-updates and escalations, token system intact. Decreased: aesthetic shifts, priority restructure, accessibility changes, or multiple docs affected by the same upstream drift. **This heuristic is for human reporting only.** No downstream skill (fix-style, iterate-style, validate, approve) should use the confidence level as gating input. It is a subjective summary, not a machine-readable signal.

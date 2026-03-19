---
name: scaffold-validate
description: Run cross-reference and planning-pipeline validation across all scaffold documents. Reports broken references, missing registrations, glossary violations, synchronization drift across spec and task pipelines (slice tables, indexes, status fields, triage logs), engine doc structural integrity (Step 3 alignment, cross-engine consistency, layer boundary compliance), and cross-cutting integrity (decision closure, workflow compliance, upstream change staleness).
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
argument-hint: [--scope all|design|systems|foundation|roadmap|phases|slices|tasks|specs|refs|engine] [--range SYS-###-SYS-###]
---

# Validate Cross-References

Run cross-reference and planning-pipeline validation, then report issues.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--scope` | No | `all` | Which checks to run: `all` (everything), `design` (design doc structure, governance, and cross-references), `systems` (system design structural checks), `foundation` (foundation architecture completeness), `roadmap` (roadmap structure and coverage), `phases` (phase pipeline checks only), `slices` (slice pipeline checks only), `tasks` (task/slice/triage pipeline checks only), `specs` (spec/slice pipeline checks only), `refs` (reference-layer validation — scripted ID/glossary checks plus expanded Step 3 doc structure, value validity, and cross-doc consistency checks), `engine` (engine doc structure, content health, Step 3 alignment, cross-engine consistency, and layer boundary compliance), `style` (Step 5 visual/UX doc structure, content health, cross-doc consistency, authority flow, boundary compliance, and accessibility coherence) |
| `--range` | No | all | For `--scope systems`: `SYS-###` or `SYS-###-SYS-###` to validate a specific system or range. If omitted, validates all systems. |

## Steps

### 0. Determine Scope

Parse the `--scope` argument from `$ARGUMENTS`:
- `--scope design` → run only Step 2h (design doc checks). Skip all other steps.
- `--scope systems` → run only Step 2i (system design checks). Skip all other steps. If `--range` is provided, validate only those systems.
- `--scope foundation` → run only Step 2g (foundation checks). Skip all other steps.
- `--scope roadmap` → run only Step 2f (roadmap checks). Skip all other steps.
- `--scope phases` → run only Step 2e (phase-pipeline checks). Skip all other steps.
- `--scope slices` → run only Step 2d (slice-pipeline checks). Skip all other steps.
- `--scope tasks` → run only Step 2b (task-pipeline checks). Skip all other steps.
- `--scope specs` → run only Step 2c (spec-pipeline checks). Skip all other steps.
- `--scope refs` → run Step 1 (Python script) AND Step 2j (expanded reference checks). Skip all other steps.
- `--scope engine` → run only Step 2k (engine-pipeline checks). Skip all other steps.
- `--scope style` → run only Step 2m (style-pipeline checks). Skip all other steps.
- `--scope all` or no argument → run all steps.

### 1. Run the Validator (scope: `all` or `refs`)

1. **Run** `python scaffold/tools/validate-refs.py --format json` from the project root.
2. **Parse the JSON output** into a list of issues.

### 2. Categorize Results

> **Step lettering note:** Subsection labels (2b, 2c, 2d, ..., 2k, 2l) preserve historical insertion order. They are stable identifiers, not display order — do not renumber when adding new sections.

Group issues by check type:

| Check | What It Validates |
|-------|------------------|
| `system-ids` | Every SYS-### reference points to a registered system |
| `authority-entities` | Entity authorities match authority.md owners |
| `signals-systems` | Signal emitters/consumers are registered systems |
| `interfaces-systems` | Interface sources/targets are registered systems |
| `states-systems` | State machine authorities are registered systems |
| `glossary-not-terms` | No non-theory doc uses a term from the glossary NOT column |
| `bidirectional-registration` | systems/_index.md and design-doc.md System Design Index match |
| `spec-slice` | Every spec appears in at least one slice |
| `task-spec` | Every task references a valid spec |

### 2b. Planning-Pipeline Checks (scope: `all` or `tasks`)

Run these additional checks directly (not via the Python script). These validate the synchronization state that matters for the triage → reorder → approve → implement pipeline.

| Check | What It Validates |
|-------|------------------|
| `slice-task-membership` | Every task in a slice's Tasks table implements a spec in that slice. Every task file implementing a slice's spec appears in the slice's Tasks table. Catches stale/missing rows from triage churn. |
| `task-index-files` | Every row in `scaffold/tasks/_index.md` points to an existing file. Every task file in `scaffold/tasks/` is registered in the index. Catches index drift from merges, splits, and renames. |
| `task-status-filename-sync` | Task files with `_draft` suffix have `Status: Draft` inside. `_approved` → Approved. `_complete` → Complete. Catches lifecycle drift from partial updates. |
| `spec-status-filename-sync` | Spec files with `_draft` suffix have `Status: Draft` inside. `_approved` → Approved. `_complete` → Complete. |
| `slice-status-filename-sync` | Slice files with `_draft` suffix have `Status: Draft` inside. `_approved` → Approved. `_complete` → Complete. |
| `phase-status-filename-sync` | Phase files with `_draft` suffix have `Status: Draft` inside. `_approved` → Approved. `_complete` → Complete. |
| `adr-status-filename-sync` | ADR files with `_accepted` suffix have `Status: Accepted` inside. |
| `slice-table-status-sync` | The Status column in each slice's Tasks table matches the actual `> **Status:**` line in each task file. Catches slice tables that weren't updated after approve or complete. |
| `triage-upstream-targets` | Every upstream action in `scaffold/decisions/triage-logs/TRIAGE-SLICE-*.md` references a real target document. Referenced SYS-###, SPEC-###, and ADR-### IDs resolve to existing files. Catches stale triage logs pointing at renamed or removed docs. |
| `reference-file-resolution` | Every `Implements: SPEC-###` in a task file resolves to an existing spec file (not just a valid-looking ID). Every spec referenced in a slice's Specs table resolves to an existing spec file. Every `SYS-###` reference in specs resolves to an existing system file. Every `Phase: P#-###` in a slice header resolves to an existing phase file. Every `SLICE-###` reference in a phase resolves to an existing slice file. Catches stale references where the ID looks valid but the target was deleted or renamed. |
| `slice-order-integrity` | Order values in each slice's Tasks table are unique (no duplicates). Pre-blocker ordering (`0a`, `0b`, `0b.01`, etc.) is structurally valid and appears before all main-sequence tasks. Main-sequence ordering uses integers, does not repeat, and does not move backward in the rendered table. No malformed order tokens exist. Catches broken reorder output or bad manual edits. |

**How to run these checks:**
1. For `slice-task-membership`: Read each slice's Specs table and Tasks table. Grep task files for `Implements: SPEC-###` matching slice specs. Compare the two sets.
2. For `task-index-files`: Read `scaffold/tasks/_index.md`. Glob `scaffold/tasks/TASK-*.md`. Compare registered vs. actual.
3. For `*-status-filename-sync` (5 checks, shared implementation): Glob planning-layer files by type (`TASK-*`, `SPEC-*`, `SLICE-*`, `P#-*`, `ADR-*`). For each, check that the filename suffix matches the internal Status field (`_draft`/Draft, `_approved`/Approved, `_complete`/Complete, `_accepted`/Accepted for ADRs). Skip singleton docs (e.g., `design-doc.md`, `style-guide.md`) — they don't use status suffixes per project convention. Report issues grouped by doc type for cleaner output.
4. For `slice-table-status-sync`: For each slice, read its Tasks table. For each task row, read the task file's Status line. Compare.
5. For `triage-upstream-targets`: Glob `scaffold/decisions/triage-logs/TRIAGE-SLICE-*.md`. Parse the Upstream Actions table. For each target document reference, verify the file exists.
6. For `reference-file-resolution`: For each task, glob `scaffold/specs/SPEC-###-*.md` to confirm the `Implements:` target exists as a file. For each spec in a slice table, glob to confirm. For each `SYS-###` reference in specs, glob `scaffold/design/systems/SYS-###-*.md`. For each `Phase: P#-###` in a slice, glob `scaffold/phases/P#-###-*.md`. For each `SLICE-###` in a phase, glob `scaffold/slices/SLICE-###-*.md`. Fail if the ID is syntactically valid but no file matches.
7. For `slice-order-integrity`: For each slice's Tasks table, extract the Order column. Check uniqueness, check format (pre-blocker `0*` vs main-sequence integers), verify all pre-blocker entries appear before main-sequence entries, verify main-sequence integers don't repeat or decrease. Flag duplicates, malformed tokens, or ordering violations.

### 2c. Spec-Pipeline Checks (scope: `all` or `specs`)

Run these checks to validate the spec stabilization pipeline. These catch drift specific to the spec layer that Step 2b's task-focused checks don't cover.

| Check | What It Validates |
|-------|------------------|
| `spec-index-files` | Every row in `scaffold/specs/_index.md` points to an existing file. Every spec file in `scaffold/specs/` is registered in the index. Catches index drift from merges, splits, and renames during spec triage. |
| `spec-slice-membership` | Every spec in a slice's Specs table resolves to an existing spec file. Every spec file that explicitly belongs to a slice (per `scaffold/specs/_index.md` slice reference or spec metadata) appears in that slice's Specs table. Does NOT infer membership from system coverage — a slice may cover a system without including every spec for that system. Catches stale/missing rows from spec triage churn. |
| `spec-system-resolution` | Every spec's System reference resolves to an existing system file in `scaffold/design/systems/`. Catches broken system references after system renames or merges. |
| `spec-status-sync` | The Status column in each slice's Specs table matches the actual `> **Status:**` line in each spec file. Catches slice tables not updated after approve-specs or complete. |
| `spec-triage-upstream-targets` | Every upstream action in `scaffold/decisions/triage-logs/TRIAGE-SPECS-SLICE-*.md` references a real target document. Catches stale spec triage logs. |

**How to run these checks:**
1. For `spec-index-files`: Read `scaffold/specs/_index.md`. Glob `scaffold/specs/SPEC-*.md`. Compare registered vs. actual.
2. For `spec-slice-membership`: For each slice, read its Specs table. For each spec row, glob to confirm the file exists. For each spec file, determine its declared slice from `scaffold/specs/_index.md` (slice reference column) or spec metadata. Check that it appears in that declared slice's Specs table. Do not infer membership from system coverage — a system may have specs across many slices.
3. For `spec-system-resolution`: For each spec file, extract the System reference. Glob `scaffold/design/systems/SYS-###-*.md` to confirm it exists.
4. For `spec-status-sync`: For each slice, read its Specs table. For each spec row, read the spec file's Status line. Compare.
5. For `spec-triage-upstream-targets`: Glob `scaffold/decisions/triage-logs/TRIAGE-SPECS-SLICE-*.md`. Parse the Upstream Actions table. For each target document reference, verify the file exists.

**Maturity-aware activation:**
- If any task files exist → `task-index-files`, `status-filename-sync`, and `reference-file-resolution` are required.
- If any spec files exist → `spec-index-files`, `spec-system-resolution`, and `status-filename-sync` (for specs) are required.
- If any slices contain Tasks tables → `slice-task-membership`, `slice-table-status-sync`, and `slice-order-integrity` are required.
- If any slices contain Specs tables → `spec-slice-membership` and `spec-status-sync` are required.
- If any task triage logs exist → `triage-upstream-targets` is required.
- If any spec triage logs exist → `spec-triage-upstream-targets` is required.
- If any slice files exist → `slice-index-files`, `slice-phase-resolution`, `slice-status-sync`, `slice-dependency-resolution`, `slice-dependency-order`, and `single-active-slice` are required. `slice-review-freshness` is required for Approved slices (FAIL) and advisory for Draft slices (WARN).

### 2d. Slice-Pipeline Checks (scope: `all` or `slices`)

Run these checks to validate the slice planning pipeline.

| Check | What It Validates |
|-------|------------------|
| `slice-index-files` | Every row in `scaffold/slices/_index.md` points to an existing file. Every slice file in `scaffold/slices/` is registered in the index. Catches index drift from renames or deletions. |
| `slice-phase-resolution` | Every slice's Phase reference resolves to an existing phase file. Catches broken phase references after phase renames or restructuring. |
| `slice-status-sync` | Slice files with `_draft` suffix have `Status: Draft` inside. Files with `_approved` suffix have `Status: Approved`. Files with `_complete` suffix have `Status: Complete`. Catches lifecycle drift. |
| `slice-interface-resolution` | Every interface referenced in a slice's Integration Points section exists in `scaffold/design/interfaces.md`. Catches references to removed or renamed interfaces. |
| `slice-dependency-resolution` | Every SLICE-### ID in a slice's `> **Depends on:**` field resolves to an existing slice file in the same phase. Slice dependencies must be intra-phase only — cross-phase prerequisites belong in phase entry criteria, not slice `Depends on`. No circular dependencies exist (A depends on B, B depends on A). No self-references. Catches broken dependency references and dependency cycles. |
| `slice-dependency-order` | For every slice, all declared dependencies appear earlier in `scaffold/slices/_index.md` implementation order. Catches the scenario where a split or new dependency creates an impossible sequential implementation order (e.g., SLICE-004 depends on SLICE-010 but SLICE-010 is listed after SLICE-004). |
| `single-active-slice` | For each phase, at most one slice may have Status: Approved while not Complete. Catches accidental multi-slice activation that breaks the one-at-a-time feedback loop. |
| `slice-review-freshness` | If a slice is Approved, verify both REVIEW and ITERATE logs exist in `scaffold/decisions/review/` and that the latest log post-dates the slice file's last modification. Missing or stale logs for Approved slices are **FAIL**. Missing logs for Draft slices are **WARN**. |

**How to run these checks:**
1. For `slice-index-files`: Read `scaffold/slices/_index.md`. Glob `scaffold/slices/SLICE-*.md`. Compare registered vs. actual.
2. For `slice-phase-resolution`: For each slice file, extract the Phase reference. Glob `scaffold/phases/P#-###-*.md` to confirm it exists.
3. For `slice-status-sync`: Glob `scaffold/slices/SLICE-*.md`. For each, check that the filename suffix matches the internal Status field.
4. For `slice-interface-resolution`: For each slice, read the Integration Points section. Validate only explicitly formatted interface references (interface names in tables, bullet lists, or structured references) — not arbitrary prose mentions. Unstructured prose mentions are ignored by this validator. For each extracted interface name, verify it appears in `scaffold/design/interfaces.md`.
5. For `slice-dependency-resolution`: For each slice, extract the `> **Depends on:**` field. If it contains SLICE-### IDs (not "—" or absent): (a) Glob each referenced ID to confirm the file exists. (b) Verify the referenced slice belongs to the same phase. (c) Build a dependency graph across all slices in the phase and check for cycles (depth-first traversal). (d) Flag self-references (a slice depending on itself).
6. For `slice-dependency-order`: Read `scaffold/slices/_index.md` to get the implementation order (row position). For each slice with dependencies, verify every dependency appears at an earlier position in the index. If SLICE-004 depends on SLICE-010 but SLICE-010 is at position 10 and SLICE-004 is at position 4, that's a FAIL — the user will reach SLICE-004 before its dependency is complete.
7. For `single-active-slice`: Group all slices by phase. For each phase, count slices with Status: Approved (not Complete). If more than one, FAIL.
8. For `slice-review-freshness`: For each slice, check its Status. If Approved, glob `scaffold/decisions/review/REVIEW-slice-SLICE-###-*.md` and `scaffold/decisions/review/ITERATE-slice-SLICE-###-*.md`. Both must exist and the latest log must post-date the slice file's modification time. Missing or stale logs for Approved slices are FAIL. If Draft, missing logs are WARN (advisory — review hasn't happened yet, which is expected for early Drafts).

**Severity model:**
- Preconditions not met (e.g., no task files exist yet) → **SKIP** — not an error, just not applicable.
- Optional structures that should exist by convention but are missing unexpectedly (e.g., no triage log for a slice that has been through triage) → **WARN**.
- Required structures for current maturity are missing or broken (e.g., task files exist but `tasks/_index.md` is missing) → **FAIL**.

### 2e. Phase-Pipeline Checks (scope: `all` or `phases`)

Run these checks to validate the phase planning pipeline.

| Check | What It Validates |
|-------|------------------|
| `phase-index-files` | Every row in `scaffold/phases/_index.md` points to an existing file. Every phase file in `scaffold/phases/` (excluding `roadmap.md`) is registered in the index. |
| `phase-roadmap-sync` | Every phase in `_index.md` appears in `scaffold/phases/roadmap.md` Phase Overview, and vice versa. Status matches across both. The phase file's internal Status field is canonical — `_index.md` and `roadmap.md` must mirror it. On mismatch, suggest fixing the index/roadmap to match the phase file. |
| `phase-status-sync` | Phase files with `_draft` suffix have `Status: Draft` inside. Files with `_approved` suffix have `Status: Approved`. Files with `_complete` suffix have `Status: Complete`. |
| `phase-structure` | Every phase file contains required structural sections: Goal, Capability Unlocked, Entry Criteria, In Scope, Out of Scope, Deliverables, Exit Criteria, Dependencies. Missing sections are FAIL — a malformed phase should not pass validation even if all references resolve. |
| `phase-order-integrity` | Phase order in `scaffold/phases/_index.md` matches the Phase Overview order in `scaffold/phases/roadmap.md`. All IDs may exist and sync, but if sequencing differs between the two files, tools and humans get conflicting ordering signals. |
| `phase-entry-chain` | For each phase, entry criteria that reference other phase IDs resolve to existing phase files. Referenced phases have status Complete (for "P#-### Complete" conditions) or at least exist. This check validates existence and status only, not semantic sufficiency of prior phase exits — semantic chain validation belongs in `/scaffold-iterate-phase` Topic 2. |
| `single-active-phase` | At most one phase may have Status: Approved while not Complete. Catches accidental multi-phase activation. |
| `phase-system-resolution` | Every SYS-### ID referenced in a phase's In Scope resolves to an existing system file. |
| `phase-slice-resolution` | Every SLICE-### ID referenced in structured sections of a phase file (Slice Strategy, Deliverables, Dependencies, Done Criteria tables) resolves to an existing slice file. Ignores prose mentions in Goal, Notes, or changelog sections to avoid false positives. Keeps `--scope phases` self-contained without depending on slice-pipeline checks. |
| `phase-review-freshness` | If a phase is Approved, verify an iterate log exists (`scaffold/decisions/review/ITERATE-phase-P#-###-*.md`) and post-dates the phase file's last modification. Missing or stale logs for Approved phases are FAIL. Missing logs for Draft phases are WARN. |

**How to run these checks:**
1. For `phase-index-files`: Read `scaffold/phases/_index.md`. Glob `scaffold/phases/P*-*.md`. Compare registered vs. actual.
2. For `phase-roadmap-sync`: Read `scaffold/phases/roadmap.md` Phase Overview. Compare phase IDs and statuses with `_index.md`.
3. For `phase-order-integrity`: Extract the ordered list of phase IDs from `_index.md` and from the roadmap Phase Overview. Compare sequences — same IDs in different order is FAIL.
4. For `phase-status-sync`: Glob `scaffold/phases/P*-*.md`. For each, check that the filename suffix matches the internal Status field.
5. For `phase-structure`: For each phase file, check for required section headings: `## Goal`, `## Capability Unlocked`, `## Entry Criteria`, `## In Scope`, `## Out of Scope`, `## Deliverables`, `## Exit Criteria`, `## Dependencies`. Missing heading = FAIL.
6. For `phase-entry-chain`: For each phase, extract entry criteria. For any criterion referencing a P#-### ID, glob to confirm the phase exists and check its status.
7. For `single-active-phase`: Count phases with Status: Approved (not Complete). If more than one, FAIL.
8. For `phase-system-resolution`: For each phase, extract SYS-### IDs from In Scope. Glob `scaffold/design/systems/SYS-###-*.md` to confirm each exists.
9. For `phase-slice-resolution`: For each phase file, extract SLICE-### IDs. Glob `scaffold/slices/SLICE-###-*.md` to confirm each exists.
10. For `phase-review-freshness`: For each phase, check status. If Approved: iterate log must exist and post-date last file modification — missing or stale is FAIL. If Draft: missing iterate log is WARN (review expected before approval). If Complete: SKIP (already past the gate).

**Maturity-aware activation:**
- If any phase files exist → `phase-index-files`, `phase-roadmap-sync`, `phase-order-integrity`, `phase-status-sync`, `phase-structure`, `phase-entry-chain`, `single-active-phase`, `phase-system-resolution`, and `phase-slice-resolution` are required. `phase-review-freshness` is required for Approved phases (FAIL) and advisory for Draft phases (WARN).

### 2f. Roadmap Checks (scope: `all` or `roadmap`)

Run these checks to validate the roadmap document.

| Check | What It Validates |
|-------|------------------|
| `roadmap-exists` | `scaffold/phases/roadmap.md` exists and is not at template defaults. Treat as template-default if required sections are present but core content fields (Vision Checkpoint, Phase Overview, Capability Ladder) remain blank, TODO, or default placeholder text — don't just inspect the first N lines. |
| `roadmap-structure` | Roadmap contains required sections: Vision Checkpoint, Design Pillars, Ship Definition, Capability Ladder, Phase Overview, Phase Boundaries, System Coverage Map, Current Phase, Upcoming Phases, ADR Feedback Log, Completed Phases, Revision History, Phase Transition Protocol (13 sections). Missing sections are FAIL — iterate-roadmap, fix-roadmap, and revise-roadmap expect this structure. |
| `roadmap-vision-sync` | Vision Checkpoint text matches `scaffold/design/design-doc.md` Core Fantasy. Drift is FAIL. |
| `roadmap-design-pillars-presence` | Design Pillars section exists and contains at least 3 entries that are not template defaults. |
| `roadmap-ship-definition-sync` | Ship Definition section exists and is not blank or template default content. |
| `roadmap-capability-ladder-sync` | Every phase in Phase Overview appears in the Capability Ladder. Ladder order matches Phase Overview order. Each phase has non-blank capability text. No duplicate or blank ladder entries. |
| `roadmap-phase-sync` | Every phase in the Phase Overview appears in `scaffold/phases/_index.md`, and vice versa. IDs and statuses match. The roadmap mirrors phase file statuses (phase file is canonical). |
| `roadmap-order-integrity` | Phase Overview order matches Capability Ladder order. Current Phase is the earliest Approved-not-Complete phase (if one exists). Upcoming Phases appear after Current Phase in roadmap order. Completed Phases are not listed as Upcoming. |
| `roadmap-phase-boundaries` | Each phase listed in Phase Overview has a corresponding entry in the Phase Boundaries section containing what it proves, what it defers, and what "good enough" looks like. Missing entries are FAIL. |
| `roadmap-system-coverage` | Every gameplay-facing system in `scaffold/design/systems/_index.md` appears in the roadmap's System Coverage Map or is explicitly listed as deferred. A gameplay-facing system is any system whose behavior materially affects player-visible simulation, player decisions, or user-facing experience. Pure tooling, editor, debug, or internal support systems may be excluded if explicitly marked as non-roadmap in the systems index. Validates against the roadmap document, not phase files. Uncovered systems are WARN. |
| `roadmap-adr-currency` | Every accepted ADR from completed phases has an entry in the ADR Feedback Log. Missing entries are FAIL. |
| `roadmap-completed-phases` | Every phase marked Complete in the Phase Overview has an entry in the Completed Phases section with: phase ID, completion date, and at least one summary/delivery note. Missing entries are FAIL. |
| `roadmap-current-phase` | If an Approved phase exists, Current Phase must point to it — FAIL if it doesn't. If no Approved phase exists and Current Phase is blank/TBD — WARN. If Current Phase points to a Draft or Complete phase while an Approved one exists — FAIL. |

**How to run these checks:**
1. For `roadmap-exists`: Check file exists. Check core content fields (Vision Checkpoint, Phase Overview, Capability Ladder) — if all remain blank/TODO/default placeholder text, FAIL as template defaults.
2. For `roadmap-structure`: Check for all 13 required section headings in the roadmap.
3. For `roadmap-vision-sync`: Read design doc Core Fantasy. Compare against Vision Checkpoint text.
4. For `roadmap-design-pillars-presence`: Check section exists, count entries, verify not template defaults.
5. For `roadmap-ship-definition-sync`: Check section exists and contains non-default content.
6. For `roadmap-capability-ladder-sync`: Parse Capability Ladder and Phase Overview. Compare phase lists, order, and presence of capability text.
7. For `roadmap-phase-sync`: Compare Phase Overview table against `_index.md`. When status mismatches exist, use phase files as the canonical source for lifecycle status — the roadmap and index must mirror the phase file.
8. For `roadmap-order-integrity`: Extract ordered phase lists from Phase Overview, Capability Ladder, Upcoming Phases, and Completed Phases. Verify consistency.
9. For `roadmap-phase-boundaries`: For each phase in Phase Overview, check Phase Boundaries section has a matching entry with proves/defers/good-enough content.
10. For `roadmap-system-coverage`: Read systems index. For each gameplay-facing system, check the roadmap's System Coverage Map (not phase files). Uncovered and not deferred = WARN.
11. For `roadmap-adr-currency`: Glob ADRs. Filter to those from completed phases. Check each has an ADR Feedback Log entry.
12. For `roadmap-completed-phases`: Compare Complete phases in Phase Overview against Completed Phases section entries. Verify phase ID and at least one note present.
13. For `roadmap-current-phase`: Read Current Phase section. If an Approved phase exists, Current Phase must reference it. If no Approved phase, blank/TBD is acceptable (WARN).

**Maturity-aware activation:**
- If `scaffold/phases/roadmap.md` exists and is not template defaults → all roadmap checks are required. `roadmap-system-coverage` is WARN (advisory) not FAIL. `roadmap-adr-currency`, `roadmap-completed-phases`, and `roadmap-current-phase` (Approved-phase check) only apply if any phases exist beyond Draft. `roadmap-phase-boundaries` requires the Phase Boundaries section to exist (checked by `roadmap-structure`).

### 2h. Design Doc Checks (scope: `all` or `design`)

Run these checks to validate the design document's structure, governance mechanisms, and cross-references.

| Check | What It Validates |
|-------|------------------|
| `design-exists` | `design/design-doc.md` exists and is not at template defaults. Treat as template-default if all 9 section groups (Identity, Shape, Control, World, Presentation, Content, System Domains, Philosophy, Scope) remain at HTML comment prompts or TODO placeholders. |
| `design-structure` | Design doc contains all required section groups and sections from the init-design template. For each of the 9 groups, verify the group heading exists. Missing group headings are FAIL. Within each group, section headings are split into **core-required** and **adaptive**. Core-required sections missing are FAIL. Adaptive sections missing are WARN. **Core-required sections:** Core Fantasy, Design Invariants, Core Loop, Player Control Model, Player Mental Model, Player Information Model, Failure Philosophy, Decision Anchors, Design Pressure Tests, Scope Reality Check. All other sections from the template are adaptive. |
| `design-section-health` | For each section, classify as Complete (substantive content), Partial (some content but placeholder markers remain), or Empty (only HTML comments or TODO). Report a weighted health percentage: Complete = 1.0, Partial = 0.5, Empty = 0. Formula: (sum of weights) / total sections. Below 50% is FAIL — the design doc is too incomplete for downstream work. Below 75% is WARN. |
| `design-invariant-format` | Each Design Invariant follows the required format: `Invariant: <ShortName>`, `Rule:`, `Reason:`, `Implication:`. Missing fields are FAIL. Invariants without a ShortName are FAIL (downstream docs can't cite them). Count must be 3-7; outside range is WARN. |
| `design-anchor-format` | Decision Anchors section contains 3-5 entries. Each must be a single concise line expressing a tradeoff in "X over Y" format — not paragraph prose. Outside count range (< 3 or > 5) is WARN. Entries that don't contain a clear " over " tradeoff are FAIL. Multi-line or paragraph-form anchors are FAIL (anchors must be scannable tie-breakers, not essays). |
| `design-pressure-test-format` | Each Design Pressure Test follows the required format: `Pressure Test: <name>`, `Scenario:`, `Expectation:`, `Failure Signal:`. Missing fields are FAIL. Count must be 3-6; outside range is WARN. |
| `design-gravity-count` | Design Gravity section contains 3-4 directional statements. Outside range is WARN. Empty is FAIL. |
| `design-boundary-presence` | Design Boundaries section exists and contains at least one specific boundary. Empty is FAIL — boundaries are a key governance brake that prevents scope drift during implementation. |
| `design-system-index-sync` | The System Design Index table in the design doc matches `design/systems/_index.md`. Every system in one table exists in the other. IDs and names match. Status values match. Mismatches are FAIL. |
| `design-glossary-compliance` | The design doc does not use terms from the `design/glossary.md` NOT column. Violations are FAIL. |
| `design-adr-consistency` | No design doc content directly contradicts an accepted ADR that explicitly supersedes a design decision. Only checks ADRs that explicitly reference design doc sections. Contradictions are FAIL. |
| `design-provisional-markers` | Count `<!-- PROVISIONAL -->` markers remaining in the design doc. Each is WARN — provisional content should be confirmed or removed before proceeding to Step 2+. |
| `design-review-freshness` | Check for review logs across both fix-design (`scaffold/decisions/review/FIX-design-*.md`) and iterate-design (`scaffold/decisions/review/ITERATE-design-*.md`). If any logs exist from either type, use the latest log date across both. If the design doc was modified after the latest log, WARN (review may be stale). If no logs of either type exist, SKIP (review hasn't happened yet). |

**How to run these checks:**
1. For `design-exists`: Check file exists. Scan the 9 group headings (Identity, Shape, Control, World, Presentation, Content, System Domains, Philosophy, Scope). If all sections within all groups remain at template defaults (only HTML comments or TODOs), FAIL.
2. For `design-structure`: Check for group headings (`## Identity`, `## Shape`, `## Control`, `## World`, `## Presentation`, `## Content`, `## System Domains`, `## Philosophy`, `## Scope`). Within each group, check for section headings. Core-required sections (Core Fantasy, Design Invariants, Core Loop, Player Control Model, Player Mental Model, Player Information Model, Failure Philosophy, Decision Anchors, Design Pressure Tests, Scope Reality Check) missing = FAIL. Other sections from the init-design template missing = WARN.
3. For `design-section-health`: For each section (heading to next heading), check content between heading and next heading. If only HTML comments, classify Empty (weight 0). If contains `TODO`, `<!-- PROVISIONAL -->`, or placeholder text mixed with real content, classify Partial (weight 0.5). Otherwise Complete (weight 1.0). Calculate weighted health: sum(weights) / total sections. Report as percentage.
4. For `design-invariant-format`: Find the Design Invariants section. Parse each invariant block. Check for `Invariant:`, `Rule:`, `Reason:`, `Implication:` fields. Verify ShortName is present after `Invariant:`. Count invariants.
5. For `design-anchor-format`: Find the Decision Anchors section. Count entries. Each anchor must be a single concise line containing " over " expressing a clear tradeoff. Multi-line or paragraph-form entries are FAIL. Entries without " over " are FAIL.
6. For `design-pressure-test-format`: Find the Design Pressure Tests section. Parse each test block. Check for `Pressure Test:`, `Scenario:`, `Expectation:`, `Failure Signal:` fields. Count tests.
7. For `design-gravity-count`: Find the Design Gravity section. Count directional statements (non-empty lines that aren't headings or comments).
8. For `design-boundary-presence`: Find the Design Boundaries section. Check for at least one substantive entry.
9. For `design-system-index-sync`: Read design doc's System Design Index table. Read `design/systems/_index.md`. Compare ID sets, name matches, and status values bidirectionally.
10. For `design-glossary-compliance`: Read `design/glossary.md` NOT column entries. Grep the design doc for each NOT term (case-insensitive, word-boundary). Exclude terms appearing only in the glossary reference section itself.
11. For `design-adr-consistency`: Glob accepted ADRs. For each, check if it explicitly references a design doc section. If so, verify the design doc section doesn't contradict the ADR's decision.
12. For `design-provisional-markers`: Grep for `<!-- PROVISIONAL` in the design doc. Count occurrences.
13. For `design-review-freshness`: Glob `scaffold/decisions/review/ITERATE-design-*.md` and `scaffold/decisions/review/FIX-design-*.md` (if fix-design produces logs). Use the latest log across both types. Compare latest log date against design doc modification time. Stale = WARN.

**Maturity-aware activation:**
- If `design/design-doc.md` exists and is not template defaults → all design checks are required. `design-glossary-compliance` requires `design/glossary.md` to exist (SKIP otherwise). `design-system-index-sync` requires `design/systems/_index.md` to exist (SKIP otherwise). `design-adr-consistency` only applies if accepted ADRs exist. `design-review-freshness` only applies if any review logs exist (FIX-design or ITERATE-design); SKIP if no logs of either type exist.

### 2i. System Design Checks (scope: `all` or `systems`)

Run these checks to validate system design structural readiness. If `--range` is provided, validate only those systems; otherwise validate all.

| Check | What It Validates |
|-------|------------------|
| `systems-index-files` | Every row in `design/systems/_index.md` points to an existing file. Every system file in `design/systems/` is registered in the index. Catches index drift from renames or deletions. |
| `systems-design-doc-sync` | Every system in `design/systems/_index.md` appears in the design doc's System Design Index, and vice versa. IDs, names, and statuses match. The system file's internal Status and name are canonical — both `_index.md` and the design doc's table must mirror the file. On mismatch, report which source is wrong relative to the file. |
| `systems-status-sync` | System files with `_draft` suffix have `Status: Draft` inside. Files with `_approved` suffix have `Status: Approved`. Files with `_complete` suffix have `Status: Complete`. |
| `systems-structure` | Every system file contains all required sections from the canonical system template. **Core-required sections** (FAIL if missing): Purpose, Simulation Responsibility, Player Intent, Design Constraints, Player Actions, Owned State, Upstream Dependencies, Downstream Consequences, Non-Responsibilities. **Adaptive sections** (WARN if missing): Visibility to Player, System Resolution, State Lifecycle, Failure / Friction States, Edge Cases & Ambiguity Killers, Feel & Feedback, Open Questions. |
| `systems-core-section-defaults` | Core-required sections that are present but still at template defaults are FAIL. Template default = only HTML comments, `<!-- SEEDED -->` with no authored prose, copied template instruction text, TODO/TBD placeholders, bracketed fill-in prompts (`[fill in]`), or unchanged example sentences from the template. This is stricter than section-health — it specifically gates core sections. |
| `systems-section-health` | For each system, classify sections as Complete (substantive content), Partial (some content but seeded/placeholder markers remain), or Empty (only HTML comments or TODO). Report weighted health per system: Complete=1.0, Partial=0.5, Empty=0. Below 50% is FAIL — system is too incomplete for downstream work. Below 70% is WARN. |
| `systems-owned-state-format` | Owned State section exists and uses the required table format with State, Description, and Persistence columns. Empty table with no entries is WARN. Missing table entirely is FAIL. |
| `systems-glossary-compliance` | System docs do not use NOT-column terms from `design/glossary.md` as authoritative design terminology. Violations are FAIL. Requires glossary to exist (SKIP otherwise). |
| `systems-dependency-symmetry` | If System A lists System B in Upstream Dependencies, System B should list System A in Downstream Consequences (and vice versa). Asymmetric references are WARN. |
| `systems-owned-state-overlap` | Exact duplicate state names appearing in the Owned State tables of multiple systems are FAIL (authority conflict). Only checks identical names — semantic similarity analysis is out of scope for validation and belongs in iterate-systems. |
| `systems-dependency-cycles` | Build a directed graph from Upstream Dependencies tables only (canonical graph source). Detect cycles via depth-first traversal. Cycles are WARN (may be legitimate feedback loops — iterate-systems interprets whether they are intentional or confused). |
| `systems-orphan-detection` | Systems with zero entries in both Upstream Dependencies and Downstream Consequences tables are WARN by default. Suppress WARN only when Purpose section explicitly contains the words "informational", "observational", "oversight", or "alerting." |
| `systems-dependency-table-format` | Upstream Dependencies and Downstream Consequences sections use the expected table format with the correct column headers (Source System / What It Provides for upstream; Target System / What It Receives for downstream). Missing or malformed tables in non-empty sections are WARN. |
| `systems-template-drift` | System doc contains section headings not present in the canonical system template. WARN on unexpected extra sections — may indicate old template version, manual drift, or renamed sections that break tooling. |
| `systems-seeded-markers` | Count remaining `<!-- SEEDED -->` markers across system docs. Each is WARN — seeded content should be verified and markers removed after authoring. |
| `systems-review-freshness` | For each system in scope, find the latest matching FIX-systems or ITERATE-systems log that includes that system's range. Compare that log date to the system file's modification time. Stale = WARN. SKIP if no logs exist. |

**How to run these checks:**
1. For `systems-index-files`: Read `design/systems/_index.md`. Glob `design/systems/SYS-*.md`. Compare registered vs actual.
2. For `systems-design-doc-sync`: Read design doc System Design Index table. Compare against `_index.md`. System file status is canonical.
3. For `systems-status-sync`: Glob `design/systems/SYS-*.md`. Check filename suffix matches internal Status field (`_draft`/Draft, `_approved`/Approved, `_complete`/Complete).
4. For `systems-structure`: Read the canonical system template at `scaffold/templates/system-template.md` to get the expected section list. For each system, check for core-required section headings (FAIL if missing) and adaptive section headings (WARN if missing).
5. For `systems-core-section-defaults`: For each core-required section, check if content is only HTML comments, `<!-- SEEDED -->` markers, or placeholder text. If so, FAIL.
6. For `systems-section-health`: For each section (heading to next heading), classify as Complete/Partial/Empty using the same weighted formula as design-section-health. Calculate per-system.
7. For `systems-owned-state-format`: Check Owned State section has a markdown table with State, Description, Persistence columns.
8. For `systems-glossary-compliance`: Read glossary NOT column. Grep each system doc for NOT terms (case-insensitive, word-boundary). Exclude terms in examples/quotes.
9. For `systems-dependency-symmetry`: For each system, read Upstream Dependencies and Downstream Consequences tables. For each referenced system, check the reciprocal entry exists.
10. For `systems-owned-state-overlap`: Collect all Owned State table entries (State column) across all systems. Check for exact duplicate names. Report which systems conflict.
11. For `systems-dependency-cycles`: Build directed graph from Upstream Dependencies tables only. Run depth-first cycle detection. Report any cycles found with the full path.
12. For `systems-orphan-detection`: Identify systems with empty dependency and consequence tables. WARN by default. Suppress only when Purpose contains "informational", "observational", "oversight", or "alerting".
13. For `systems-dependency-table-format`: Check Upstream Dependencies section has a table with "Source System" and "What It Provides" headers. Check Downstream Consequences section has a table with "Target System" and "What It Receives" headers. WARN if headers don't match or table is malformed.
14. For `systems-template-drift`: Read canonical template section headings. For each system, identify section headings not in the template. WARN on extras.
15. For `systems-seeded-markers`: Grep all system docs for `<!-- SEEDED`. Count occurrences per system.
16. For `systems-review-freshness`: For each system, find the latest review log whose filename range includes that system's ID (single-system log for that SYS, or range log whose numeric bounds include that SYS). Compare log date to system file modification time.

**Range semantics:** When `--range` is provided, per-system checks (structure, health, core-section-defaults, owned-state-format, glossary, seeded-markers, template-drift, review-freshness) validate only systems in the range. Cross-system checks (dependency-symmetry, owned-state-overlap, dependency-cycles, orphan-detection) still read all systems for graph completeness but only report issues involving at least one system in the range. Index/sync checks (index-files, design-doc-sync, status-sync) validate only rows relevant to systems in the range.

**Maturity-aware activation:**
- If any system files exist → `systems-index-files`, `systems-status-sync`, `systems-structure`, `systems-core-section-defaults`, `systems-section-health`, `systems-owned-state-format`, `systems-dependency-table-format`, `systems-seeded-markers`, and `systems-template-drift` are required. `systems-glossary-compliance` requires glossary to exist (SKIP otherwise). `systems-design-doc-sync` requires design doc System Design Index to exist (SKIP otherwise). `systems-dependency-symmetry`, `systems-owned-state-overlap`, `systems-dependency-cycles`, and `systems-orphan-detection` require at least 2 systems to be meaningful. `systems-review-freshness` only applies if review logs exist.

### 2g. Foundation Checks (scope: `all` or `foundation`)

Run these checks to validate foundation architecture completeness and cross-doc consistency.

| Check | What It Validates |
|-------|------------------|
| `foundation-docs-exist` | `design/architecture.md`, `design/authority.md`, and `design/interfaces.md` exist and are not at template defaults. |
| `foundation-area-coverage` | Each of the 6 foundation areas (identity, content-definition, storage, save/load, spatial, API boundaries) has a non-placeholder section in `architecture.md`. Areas at template defaults are FAIL. |
| `foundation-area-status` | Each foundation area is explicitly Locked, Partial, or Deferred. Undefined areas (no explicit status) are FAIL. Partial areas without a `known-issues.md` entry are FAIL. |
| `foundation-authority-consistency` | Ownership rules in `authority.md` match `architecture.md` API boundary rules. Systems claiming ownership in their design files match `authority.md` entries. Mismatches are FAIL. |
| `foundation-interface-completeness` | Systems that interact (per architecture.md or system designs) have contracts in `interfaces.md`. Missing contracts for documented interactions are WARN. |
| `foundation-signal-consistency` | Signals referenced in architecture.md or interface contracts exist in `reference/signal-registry.md`. Missing signals are WARN. |
| `foundation-entity-consistency` | Entity handle/identity rules in `architecture.md` match handle columns in `reference/entity-components.md`. Mismatches are FAIL. |
| `foundation-iterate-freshness` | If foundation has been iterated, verify an iterate log exists (`scaffold/decisions/review/ITERATE-foundation-*.md`). If architecture docs were modified after the latest iterate log, WARN (review may be stale). |

**How to run these checks:**
1. For `foundation-docs-exist`: Check files exist. Read opening sections — if all template defaults, FAIL.
2. For `foundation-area-coverage`: For each of the 6 areas, check `architecture.md` has a corresponding section with non-placeholder content.
3. For `foundation-area-status`: For each area, check for explicit Locked/Partial/Deferred marking. For Partial areas, verify `known-issues.md` has a tracking entry.
4. For `foundation-authority-consistency`: Compare authority.md ownership against architecture.md boundary rules and system design ownership claims. Three-way consistency check.
5. For `foundation-interface-completeness`: Identify interacting system pairs from architecture.md. Check each pair has an interfaces.md contract.
6. For `foundation-signal-consistency`: Extract signal references from architecture.md and interfaces.md. Verify each exists in signal-registry.md.
7. For `foundation-entity-consistency`: Compare architecture.md identity/handle rules against entity-components.md handle column entries.
8. For `foundation-iterate-freshness`: Glob iterate logs. Compare dates against architecture doc modification times.

**Maturity-aware activation:**
- If `design/architecture.md` exists and is not template defaults → all foundation checks are required. `foundation-interface-completeness` and `foundation-signal-consistency` are WARN (advisory) not FAIL. `foundation-iterate-freshness` only applies if iterate logs exist.

### 2j. Expanded Reference Checks (scope: `all` or `refs`)

Run these checks to validate all 9 Step 3 docs beyond what the Python script covers. These are deterministic structural checks — not design judgments.

**Existence & Structure:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `refs-docs-exist` | All 9 Step 3 docs exist: architecture.md, authority.md, interfaces.md, state-transitions.md, entity-components.md, resource-definitions.md, signal-registry.md, balance-params.md, enums-and-statuses.md. | FAIL if missing, SKIP if Step 3 hasn't run yet |
| `refs-architecture-sections` | architecture.md has all required sections: Scene Tree Layout (with System Representation), Dependency Graph, Tick Processing Order (with Simulation Update Semantics), Signal Wiring Map, Data Flow Rules (with Forbidden Patterns), Initialization & Boot Order, Entity Identity & References, Failure & Recovery Patterns, Code Patterns, Rules. | FAIL if core section missing, WARN if subsection missing |
| `refs-authority-sections` | authority.md has: Purpose, domain grouping sections, Conflict/TBD section, Rules. | FAIL if missing |
| `refs-interfaces-sections` | interfaces.md has: Purpose, domain grouping sections, Missing/TBD Contracts section, Rules. | FAIL if missing |
| `refs-state-transitions-sections` | state-transitions.md has: Purpose, numbered state machine sections each with Authority, Entity, transition table (with Timing column), Invariants. | FAIL if missing |
| `refs-entity-components-sections` | entity-components.md has: Purpose, Entity Reference Convention, Content Identity Convention, Reference Type Conventions, Singleton Conventions, Derived/Cache Field Policy, entity sections, Rules. | FAIL if convention section missing |
| `refs-signal-registry-sections` | signal-registry.md has: Purpose, Signal vs Intent Conventions, Signals table, Intent Objects table, Dispatch Timing Conventions, Payload Schema Conventions, Rules. | FAIL if missing |

**Column Completeness:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `refs-authority-columns` | Every authority.md row has: Variable/Property, Owning System, Write Mode, Authority Type, Persistence Owner, Readers, Update Cadence. | WARN if columns missing |
| `refs-interfaces-columns` | Every interfaces.md row has: Source System, Target System, Data Exchanged, Direction, Realization Path, Timing, Failure Guarantee. | WARN if columns missing |
| `refs-state-timing` | Every state-transitions.md transition row has a Timing value (immediate / queued / end-of-tick / TBD). | WARN if missing |
| `refs-entity-persistence` | Every entity-components.md row has a Persistence value (Saved / Derived / Transient). | WARN if missing |
| `refs-signal-columns` | Every signal-registry.md signal row has: Level, Delivery Expectation, Gameplay/Logging. | WARN if missing |
| `refs-balance-type` | Every balance-params.md row has a Type value (threshold / rate / duration / capacity / multiplier / TBD). | WARN if missing |
| `refs-enums-authority` | Every enums-and-statuses.md row has: Owning Authority/System, Source of Truth. | WARN if missing |

**Enumerated Value Validity:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `refs-direction-values` | interfaces.md Direction values are Push / Pull / Request / TBD only. | FAIL if invalid |
| `refs-realization-values` | interfaces.md Realization Path values are signal / intent / query API / direct sanctioned interface call / TBD only. | FAIL if invalid |
| `refs-timing-values` | interfaces.md Timing values are immediate / deferred / next tick / TBD only. State-transitions Timing values are immediate / queued / end-of-tick / TBD only. | FAIL if invalid |
| `refs-level-values` | signal-registry.md Level values are Entity / Room / System / Colony / Global only. | FAIL if invalid |
| `refs-delivery-values` | signal-registry.md Delivery Expectation values are fire-and-forget / reliable / deduped / queued / TBD only. | FAIL if invalid |
| `refs-gameplay-logging-values` | signal-registry.md Gameplay/Logging values are Gameplay / Logging / Both only. | FAIL if invalid |
| `refs-balance-type-values` | balance-params.md Type values are threshold / rate / duration / capacity / multiplier / TBD only. | FAIL if invalid |
| `refs-source-of-truth-values` | enums-and-statuses.md Source of Truth values are state-transition / authority / interface / UI only. | FAIL if invalid |
| `refs-fungibility-values` | resource-definitions.md Fungibility values are fungible / unique / TBD only. | FAIL if invalid |
| `refs-persistence-values` | entity-components.md Persistence values are Saved / Derived / Transient only. | FAIL if invalid |

**Cross-Doc Consistency:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `refs-authority-entity-alignment` | Every entity-components.md Authority column entry matches authority.md ownership. authority.md wins on conflict. | FAIL if mismatch |
| `refs-interface-signal-alignment` | Every interfaces.md contract with Realization Path: signal has a corresponding signal in signal-registry.md. Every signal with Gameplay classification appears in interfaces.md. | WARN if orphan signal, FAIL if missing signal for interface |
| `refs-state-enum-alignment` | Cross-system state names in state-transitions.md match exactly in enums-and-statuses.md. | FAIL if mismatch |
| `refs-state-entity-alignment` | Every state machine's entity type exists in entity-components.md with a corresponding enum field. | WARN if missing |
| `refs-architecture-scene-tree` | Every system in systems/_index.md appears in architecture.md scene tree. | WARN if missing |
| `refs-architecture-tick-order` | Every ticked system in the scene tree has a tick position in the Tick Processing Order table. | WARN if missing |
| `refs-enums-used-by-count` | Every enum in enums-and-statuses.md has 2+ systems in Used By. Single-system enums don't belong here. | WARN if single-system |
| `refs-no-duplicate-entries` | No duplicate entries by equivalence key: same Variable/Property (authority), same Source+Target+Data (interfaces), same Signal Name (signals), same Resource name (resources), same State value (enums), same Parameter+System (balance). | FAIL if duplicate |
| `refs-resource-chain-completeness` | Every Tier 2+ resource in resource-definitions.md has a production chain entry, unless Source is marked imported / scavenged / event-only / expedition-only. | WARN if missing chain |
| `refs-architecture-signal-resolution` | Every signal named in architecture.md Signal Wiring Map exists in signal-registry.md. | WARN if missing, FAIL if architecture explicitly claims a canonical gameplay signal path and the signal is absent |
| `refs-authority-interface-ownership` | For Push-direction interfaces where Data Exchanged exactly matches or names a Variable/Property from authority.md, the Source System must be the owning system in authority.md. This is a heuristic match on exact variable/property names only — not semantic interpretation. | WARN if mismatch (heuristic) |
| `refs-balance-system-resolution` | Every System value in balance-params.md resolves to an existing system in systems/_index.md. | FAIL if missing |
| `refs-enums-used-by-resolution` | Every system listed in enums-and-statuses.md Used By and Owning Authority resolves to an existing system file. | FAIL if missing |
| `refs-interface-intent-alignment` | Every interfaces.md contract with Realization Path: intent has a corresponding intent object in signal-registry.md Intent Objects table. | FAIL if missing |
| `refs-no-duplicate-intents` | No duplicate Intent Object names in signal-registry.md. | FAIL if duplicate |
| `refs-intent-system-resolution` | Every Requester and Handler in signal-registry.md Intent Objects table resolves to an existing system in systems/_index.md or is valid UI shorthand. | FAIL if missing |
| `refs-architecture-interface-coverage` | System pairs explicitly connected in architecture.md Signal Wiring Map or sanctioned communication paths appear in interfaces.md. | WARN if missing |
| `refs-resource-station-resolution` | Every station named in production chains or Production Stations table resolves to a canonical station entry in resource-definitions.md. | WARN if missing |

**Maturity-aware activation:**
- `refs-docs-exist`: Always run. Missing docs are FAIL only if Step 3 has been started (at least architecture.md or authority.md exists). If neither exists, all expanded refs checks SKIP.
- Column completeness checks: WARN, not FAIL — docs may be partially populated during seeding.
- Enumerated value checks: FAIL — invalid values are always bugs regardless of maturity.
- Cross-doc consistency checks: Run only when both sides of the check exist. SKIP if one doc is missing.

**How to run these checks:**
1. Read each Step 3 doc.
2. For section checks: verify headings exist using pattern matching.
3. For column checks: parse table headers and verify expected columns are present.
4. For value checks: extract column values and validate against allowed sets.
5. For cross-doc checks: extract entries from both docs and compare by key.
6. For duplicate checks: group entries by equivalence key and flag groups with count > 1.

### 2k. Engine-Pipeline Checks (scope: `all` or `engine`)

Run these checks to validate engine doc (Step 4) structural integrity, content health, Step 3 alignment, cross-engine consistency, and layer boundary compliance. Checks are split into **document-level** (per engine doc) and **ecosystem-level** (across all engine docs) for cleaner reporting.

**Status-Severity Matrix:**

All status-aware checks use this matrix. Status is read from the doc's blockquote header.

| Check Category | Draft | Review | Approved | Complete | Deprecated |
|---------------|-------|--------|----------|----------|------------|
| Missing required sections | FAIL | FAIL | FAIL | FAIL | WARN |
| Empty Purpose | FAIL | FAIL | FAIL | FAIL | WARN |
| Remaining TODOs | INFO | WARN | FAIL | FAIL | SKIP |
| Rules not populated | WARN | WARN | FAIL | FAIL | SKIP |
| Section health below threshold | WARN/FAIL | WARN/FAIL | WARN/FAIL | WARN/FAIL | SKIP |
| Review freshness (stale/missing) | WARN | WARN | FAIL | SKIP | SKIP |
| Seeded markers remaining | WARN | WARN | FAIL | FAIL | SKIP |
| Stale template comments | WARN | WARN | WARN | WARN | SKIP |

**Deprecated doc handling:** Deprecated engine docs must keep valid header metadata and index registration (FAIL if broken). Content-health, review-freshness, TODO, and template checks downgrade to WARN or SKIP. Layer-boundary FAILs still apply if the doc remains referenced by other engine docs.

**Heading match semantics:** Section heading checks use **case-insensitive normalized matching** — `## Project Overrides` matches `## Project overrides`. Heading text is trimmed and compared after lowering case. This prevents false failures from trivial casing drift.

---

#### Document-Level Checks

These run independently per engine doc.

**Index & Registration:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-index-files` | Every row in `scaffold/engine/_index.md` Documents table points to an existing file. Every `.md` file in `scaffold/engine/` (excluding `_index.md`) is registered in the index. Catches index drift from additions, renames, or deletions. | FAIL |
| `engine-index-topic-present` | Every row in the Documents table has a non-empty Topic column. Empty topics make the index useless as a lookup tool. | WARN |

**Header & Metadata:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-header-fields` | Every engine doc has the blockquote header with required fields: `Layer`, `Authority`, `Conforms to`, `Status`. | FAIL if missing |
| `engine-layer-value` | Every engine doc's Layer field is exactly `Implementation`. | FAIL if wrong |
| `engine-authority-rank` | Every engine doc's Authority field is `Rank 9` per the CLAUDE.md authority chain. | FAIL if not Rank 9 |
| `engine-status-value` | Every engine doc's Status field is one of: Draft, Review, Approved, Complete, Deprecated. | FAIL if invalid |
| `engine-conforms-to-resolution` | Every document referenced in the `Conforms to` field resolves to an existing file. Parse markdown link(s) and verify target exists. Must have at least one `Conforms to` link. | FAIL if target missing or no links |

**Structure:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-common-sections` | Every engine doc contains the three universal sections present in every engine template: `## Purpose`, `## Project Overrides`, `## Rules`. Uses case-insensitive heading match. | FAIL if missing (see status matrix for Deprecated) |
| `engine-template-sections` | For engine docs with a matching template, all template-defined `##` section headings are present. Template matching is **index-driven**: read the `_index.md` Templates table first; only fall back to filename inference (`engine-<topic>-template.md` from doc topic) if no explicit mapping exists. If inferred mapping differs from explicit mapping, WARN. | WARN if template section missing |
| `engine-project-overrides-format` | The Project Overrides section contains a markdown table with columns: Convention, Default, Override, Rationale. | WARN if malformed or missing table |
| `engine-rules-populated` | The Rules section contains at least one authored rule (not just TODO placeholders). | See status matrix |

**Content Health:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-section-health` | For each engine doc, classify every top-level `##` section as Complete (substantive content), Partial (some content but TODO/placeholder markers remain), or Empty (only HTML comments, TODO, or template instruction text). Report weighted health per doc: Complete=1.0, Partial=0.5, Empty=0. **Denominator:** only top-level `##` sections count — ignore `###` subsections. Only count sections that exist in the doc. Missing required sections are caught by `engine-common-sections` and `engine-template-sections`, not double-penalized here. | FAIL below 40%, WARN below 65% (SKIP for Deprecated) |
| `engine-purpose-populated` | **Gate check.** The Purpose section has substantive authored content, not just the template HTML comment or TODO. This is checked separately from section-health because an empty Purpose is always a hard failure regardless of overall health score. | FAIL if empty/template-default (WARN for Deprecated) |
| `engine-todo-count` | Count remaining `*TODO:` markers in each engine doc. | See status matrix |
| `engine-seeded-markers` | Count remaining `<!-- SEEDED -->` or `<!-- SEEDED:` markers. Seeded content should be verified and markers removed after authoring. | See status matrix |
| `engine-template-comments` | Remaining HTML template instruction comments (`<!-- ... -->`) in sections classified as Complete or Partial. Template comments in Empty sections are expected and not flagged. | See status matrix |

**Step 3 Alignment (deterministic):**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-constrained-todo-freshness` | For each TODO that references a blocking document or decision ("after architecture.md", "pending ADR-###", "when SPEC-### is approved"), check whether the referenced item has been resolved (status changed to Approved/Complete/Accepted). Stale constrained TODOs mean the blocking decision was made but the engine doc wasn't updated. | WARN if blocking decision appears resolved |
| `engine-no-system-design-sections` | Engine docs do not contain section headings from the system design template. `## Purpose` is shared and exempt; but `## Simulation Responsibility`, `## Player Intent`, `## Design Constraints`, `## Owned State`, `## Non-Responsibilities` are system-design-only sections. Their presence in an engine doc indicates misplaced design content. | FAIL if found |

**Step 3 Alignment (heuristic advisory):**

These checks use heuristic pattern matching and may produce false positives. Results are labeled `[ADVISORY]` in the report to distinguish them from deterministic checks. Treat as investigation prompts, not definitive failures.

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-architecture-references` | **Scoped by doc type.** Only runs on engine docs whose topic directly implements architecture.md concepts. scene-architecture → scene tree, boot order. simulation-runtime → tick order, signal dispatch. save-load → boot-from-save, identity. coding-best-practices → data flow, forbidden patterns. Other engine docs (UI, input, localization, post-processing, testing, asset-import, implementation-patterns, debugging) → SKIP this check. Verifies system names and structures referenced in the scoped engine doc exist in architecture.md. | WARN [ADVISORY] if mismatch |
| `engine-authority-compliance` | Engine docs do not claim data ownership that conflicts with `scaffold/design/authority.md`. Scans for ownership-claiming phrases ("owns", "single writer", "authority over", "writes to") near system or variable names. Cross-references against authority.md. | WARN [ADVISORY] if apparent conflict |
| `engine-signal-registry-compliance` | Signal names mentioned in engine docs (near "signal", "emit", "connect") exist in `scaffold/reference/signal-registry.md`. **Exempt:** underscore-prefixed signals (`_internal_signal`), signals inside code block comments, signals in example/placeholder code blocks explicitly marked as illustrative, and UI-only local scene signals (prefixed with `ui_` or in UI-specific engine docs where the signal is clearly scene-local). | WARN [ADVISORY] if orphan signal |
| `engine-no-design-content` | Engine docs do not contain design-layer content. Scans for design-layer phrases ("the player can", "when the player", "the system decides", "this system is responsible for") without surrounding implementation context. **Exempt:** phrases inside code blocks, inside `>` blockquotes citing design docs, or within ±3 lines of implementation keywords ("implement", "achieved through", "code pattern", "in Godot"). | WARN [ADVISORY] if apparent design content |

**Template & Review:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-template-drift` | Engine doc contains `##` section headings not present in its matching template. May indicate manual additions, renamed sections, or old template version. | WARN on unexpected sections |
| `engine-template-mapping-complete` | The `_index.md` Templates table lists a mapping for every engine doc that has a matching template file in `scaffold/templates/`. **Index-driven:** the Templates table is the canonical mapping source. Glob `scaffold/templates/engine-*-template.md` to find available templates. Flag docs with available templates not listed in the Templates table. | WARN if unmapped |
| `engine-review-freshness` | For each engine doc, check for matching review logs in `scaffold/decisions/review/`. **Matching:** review log body or filename must contain the engine doc's filename stem (e.g., `coding-best-practices`). Prefer explicit filename reference in log body; fall back to filename pattern matching (`ITERATE-engine-*`, `FIX-engine-*`). | See status matrix |

---

#### Ecosystem-Level Checks

These compare engine docs against each other. Require at least 2 engine docs to be meaningful. Require the coding-best-practices engine doc to exist (it defines canonical conventions). SKIP otherwise.

**Cross-Engine Consistency (heuristic advisory):**

These checks are labeled `[ADVISORY]` in the report. They compare code examples and convention statements across engine docs using pattern matching. False positives are possible.

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-naming-convention-consistency` | Naming conventions stated in the coding-best-practices engine doc (snake_case for functions, PascalCase for classes, etc.) are not contradicted by code examples in other engine docs. Scans code blocks only — prose mentions of names are exempt. | WARN [ADVISORY] |
| `engine-language-boundary-consistency` | The C++/GDScript language boundary defined in the coding-best-practices doc is respected across all engine docs. Flags explicit language/layer assignments that contradict the boundary (e.g., "implement this in GDScript" for simulation logic when the boundary says C++). | WARN [ADVISORY] |
| `engine-signal-pattern-consistency` | Signal naming conventions and connection patterns (past-tense verbs, connect in `_ready()`, typed signals) stated in the coding doc are followed by signal examples in other engine docs. | WARN [ADVISORY] |

**Cross-Engine Consistency (deterministic):**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `engine-topic-overlap` | No two engine docs have Purpose sections with substantially overlapping scope. Lightweight check: extract the first sentence of each Purpose section and flag pairs that reference the same primary concern (e.g., two docs both claiming to govern "signal wiring conventions"). Does not attempt semantic similarity — only flags exact or near-exact overlap in Purpose lead sentences. | WARN if overlap detected |

---

**How to run these checks:**

1. For `engine-index-files`: Read `scaffold/engine/_index.md`. Parse the Documents table. Glob `scaffold/engine/*.md` excluding `_index.md`. Compare registered vs actual bidirectionally.
2. For `engine-index-topic-present`: Check each Documents table row has a non-empty Topic column.
3. For `engine-header-fields`: For each engine doc, read the first 10 lines. Extract blockquote lines starting with `> **`. Check presence of Layer, Authority, Conforms to, Status.
4. For `engine-layer-value`: Parse Layer field. Must be exactly `Implementation`.
5. For `engine-authority-rank`: Parse Authority field. Must be `Rank 9`.
6. For `engine-status-value`: Parse Status field. Must be one of Draft, Review, Approved, Complete, Deprecated.
7. For `engine-conforms-to-resolution`: Parse `Conforms to` markdown links. Must have at least one link. Resolve paths relative to `scaffold/`. Verify each target file exists.
8. For `engine-common-sections`: Extract all `##` headings from each engine doc. Normalize to lowercase for comparison. Check for Purpose, Project Overrides, Rules.
9. For `engine-template-sections`: Read the `_index.md` Templates table for explicit doc-to-template mapping. For docs without explicit mapping, infer: strip engine prefix (e.g., `godot4-`) and match to `engine-<topic>-template.md`. If both exist and differ, WARN. Read the matched template, extract `##` headings. Check each heading (except Purpose, Project Overrides, Rules — already covered) exists in the engine doc. SKIP if no template match.
10. For `engine-project-overrides-format`: Read the Project Overrides section. Check for a markdown table with columns containing Convention, Default, Override, Rationale (case-insensitive header match).
11. For `engine-rules-populated`: Read the Rules section. Check for at least one line matching `^\d+\.\s` or `^- ` that is not `*TODO:` or placeholder text. Apply status matrix.
12. For `engine-section-health`: For each top-level `##` section (heading to next `##` heading — ignore `###`): if only `<!-- ... -->` and/or `*TODO:` → Empty (0). If mix of authored prose and markers → Partial (0.5). If no markers → Complete (1.0). Denominator = count of `##` sections that exist in the doc. Calculate health = sum(weights) / denominator.
13. For `engine-purpose-populated`: Check Purpose section is not Empty. Gate check — always FAIL regardless of overall health score (WARN for Deprecated).
14. For `engine-todo-count`: Grep each engine doc for `*TODO:`. Count per doc. Apply status matrix.
15. For `engine-seeded-markers`: Grep all engine docs for `<!-- SEEDED`. Count per doc. Apply status matrix.
16. For `engine-template-comments`: For each `##` section classified as Complete or Partial, check for remaining `<!-- ... -->` HTML comments. Flag as stale. Apply status matrix.
17. For `engine-constrained-todo-freshness`: For each `*TODO:` that references a document path or ID, check the referenced document's current status. If resolved (Approved/Complete/Accepted), WARN as stale.
18. For `engine-no-system-design-sections`: Check engine doc headings against system-design-only sections: `## Simulation Responsibility`, `## Player Intent`, `## Design Constraints`, `## Owned State`, `## Non-Responsibilities`. `## Purpose` is shared and exempt. Case-insensitive match.
19. For `engine-architecture-references`: Check doc topic against the scoped list (scene-architecture, simulation-runtime, save-load, coding-best-practices). SKIP for other docs. Read `scaffold/design/architecture.md`. Extract system names from Scene Tree Layout and Tick Processing Order. Extract system/node names from the engine doc. Compare sets. Report engine-doc references not found in architecture.md.
20. For `engine-authority-compliance`: Grep each engine doc for ownership-claiming phrases (`owns`, `single writer`, `authority over`, `writes to`). Extract nearby system and variable names. Cross-reference authority.md ownership table. Report mismatches. Label `[ADVISORY]`.
21. For `engine-signal-registry-compliance`: Grep engine docs for signal name patterns (snake_case near "signal", "emit", "connect"). Cross-reference `scaffold/reference/signal-registry.md`. Exclude: underscore-prefixed signals, signals in code block comments, signals in explicitly illustrative examples, `ui_`-prefixed signals in UI engine docs. Report orphans. Label `[ADVISORY]`.
22. For `engine-no-design-content`: Grep each engine doc for design-layer phrases. Check surrounding context (±3 lines). Exempt: inside code blocks, inside `>` blockquotes, or near implementation keywords. Standalone behavioral descriptions are WARN `[ADVISORY]`.
23. For `engine-naming-convention-consistency`: Read the coding-best-practices engine doc. Extract naming rules. Scan code blocks (not prose) in all other engine docs for identifiers. Flag violations. Label `[ADVISORY]`.
24. For `engine-language-boundary-consistency`: Read the coding-best-practices doc's language boundary section. For each other engine doc, check for explicit language/layer assignments in prose that contradict the boundary. Label `[ADVISORY]`.
25. For `engine-signal-pattern-consistency`: Read the coding doc's signal policy. Scan signal examples in code blocks of other engine docs. Flag examples that use wrong naming, wrong connection location, or untyped signals. Label `[ADVISORY]`.
26. For `engine-topic-overlap`: Extract the first sentence of each engine doc's Purpose section. Compare all pairs. Flag pairs where both first sentences reference the same primary implementation concern using exact or near-exact keyword overlap. This is a lightweight string check, not semantic analysis.
27. For `engine-template-drift`: For each engine doc with a matched template (index-driven, then filename fallback), compare headings. Headings in doc but not in template are drifted.
28. For `engine-template-mapping-complete`: Read `_index.md` Templates table. Glob `scaffold/templates/engine-*-template.md`. For each available template, check if a mapping exists in the Templates table. Flag available templates with no mapping.
29. For `engine-review-freshness`: For each engine doc, check for review logs. Matching: search log body for the engine doc filename stem first; fall back to filename pattern matching. Apply status matrix.

**Maturity-aware activation:**
- If `scaffold/engine/_index.md` does not exist → SKIP all engine checks.
- If no engine doc files exist (only `_index.md`) → `engine-index-files` runs (to catch empty index), all other checks SKIP.
- Document-level checks → required for all engine docs that exist. Deprecated docs use relaxed severity per status matrix.
- Step 3 alignment (deterministic) checks → required for all engine docs. `engine-no-system-design-sections` always runs. `engine-constrained-todo-freshness` requires at least one TODO with a document reference.
- Step 3 alignment (heuristic advisory) checks → run only when the referenced Step 3 doc exists (architecture.md, authority.md, signal-registry.md). SKIP if upstream doc missing. `engine-architecture-references` only runs on scoped doc types.
- Ecosystem-level checks → require at least 2 engine docs and require the coding-best-practices doc to exist. SKIP otherwise. `engine-topic-overlap` only requires 2+ docs (no coding doc dependency).
- Template-based checks → SKIP for engine docs with no matching template (explicit or inferred).
- Review freshness → see status matrix. SKIP for Deprecated and Complete docs.

### 2m. Style-Pipeline Checks (scope: `all` or `style`)

Run these checks to validate Step 5 visual/UX doc structural integrity, content health, cross-doc consistency, authority flow, boundary compliance, and accessibility coherence.

**Target docs:**

| Doc | Path | Template |
|-----|------|----------|
| style-guide.md | `design/style-guide.md` | `templates/style-guide-template.md` |
| color-system.md | `design/color-system.md` | `templates/color-system-template.md` |
| ui-kit.md | `design/ui-kit.md` | `templates/ui-kit-template.md` |
| interaction-model.md | `design/interaction-model.md` | `templates/interaction-model-template.md` |
| feedback-system.md | `design/feedback-system.md` | `templates/feedback-system-template.md` |
| audio-direction.md | `design/audio-direction.md` | `templates/audio-direction-template.md` |

**Status-Severity Matrix:**

| Check Category | Draft | Review | Approved | Complete | Deprecated |
|---------------|-------|--------|----------|----------|------------|
| Missing required sections | FAIL | FAIL | FAIL | FAIL | WARN |
| Empty Purpose/intro | FAIL | FAIL | FAIL | FAIL | WARN |
| Remaining TODOs | INFO | WARN | FAIL | FAIL | SKIP |
| Rules not populated | WARN | WARN | FAIL | FAIL | SKIP |
| Section health below threshold | WARN/FAIL | WARN/FAIL | WARN/FAIL | WARN/FAIL | SKIP |
| Review freshness (stale/missing) | WARN | WARN | FAIL | SKIP | SKIP |
| Template comments remaining | WARN | WARN | WARN | WARN | SKIP |

---

#### Document-Level Checks

These run independently per Step 5 doc.

**Header & Metadata:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-header-fields` | Every Step 5 doc has the blockquote header with required fields: `Authority`, `Layer`, `Conforms to`, `Created`, `Last Updated`, `Status`. | FAIL if missing |
| `style-authority-rank` | Every Step 5 doc's Authority field is `Rank 2`. | FAIL if not Rank 2 |
| `style-layer-value` | Every Step 5 doc's Layer field is `Canon`. | FAIL if wrong |
| `style-status-value` | Every Step 5 doc's Status field is one of: Draft, Review, Approved, Complete, Deprecated. | FAIL if invalid |
| `style-conforms-to-resolution` | Every document referenced in `Conforms to` resolves to an existing file. Must have at least one link (design-doc.md at minimum). | FAIL if target missing |

**Structure:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-template-sections` | Each Step 5 doc contains all `##` section headings from its corresponding template. Uses case-insensitive heading match. | WARN if template section missing |
| `style-rules-populated` | The Rules section contains at least one authored rule. | See status matrix |

**Content Health:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-section-health` | For each Step 5 doc, classify every top-level `##` section as Complete (1.0), Partial (0.5), or Empty (0). Report weighted health per doc. | FAIL below 40%, WARN below 65% (SKIP for Deprecated) |
| `style-todo-count` | Count remaining `*TODO:` markers in each Step 5 doc. | See status matrix |
| `style-template-comments` | Remaining HTML template instruction comments in sections classified as Complete or Partial. | See status matrix |

**Per-Doc Structural Checks:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-guide-pillars` | style-guide has at least 3 concrete aesthetic pillars (not template text). | WARN if fewer |
| `style-guide-tone-registers` | style-guide defines at least 2 named tone registers with visual descriptions. | WARN if missing |
| `color-system-tokens` | color-system has State Tokens and UI Tokens tables with at least 5 entries each. | WARN if fewer |
| `color-system-hex-valid` | All hex values in color-system are well-formed (#RRGGBB or #RRGGBBAA). | FAIL if malformed |
| `color-system-no-duplicate-tokens` | No duplicate token names in color-system tables. | FAIL if duplicates |
| `ui-kit-component-states` | ui-kit has a Component States table with at least 5 states (default, hover, pressed, disabled, error). | WARN if fewer |
| `ui-kit-scope-guard` | ui-kit does not contain screen maps, scene hierarchies, modal graphs, or HUD layout keywords ("screen region", "scene tree", "node hierarchy", "HUD layout", "screen map"). | FAIL if found |
| `interaction-model-selection` | interaction-model defines at least one selectable entity type and selection mechanics. | WARN if missing |
| `interaction-model-commands` | interaction-model defines at least 3 concrete player commands. | WARN if fewer |
| `feedback-system-priority` | feedback-system defines an explicit priority hierarchy. | WARN if missing |
| `feedback-system-event-table` | feedback-system has an Event-Response Table with at least 10 entries. | WARN if fewer |
| `feedback-system-event-columns` | Event-Response Table rows have: Event, Visual, Audio, UI, Timing, Priority columns. | WARN if columns missing |
| `audio-direction-categories` | audio-direction defines at least 4 sound categories. | WARN if fewer |
| `audio-direction-hierarchy` | audio-direction defines a feedback priority/hierarchy ordering. | WARN if missing |

---

#### Cross-Doc Consistency Checks

These compare Step 5 docs against each other. Require at least 3 Step 5 docs to be meaningful.

**Authority Flow:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-authority-flow` | Authority flows downstream: style-guide → color-system → ui-kit. Interaction-model and feedback-system are peers. Audio-direction derives priority from feedback-system. Check that `Conforms to` links reflect this hierarchy (color-system conforms to style-guide, ui-kit conforms to style-guide + color-system, etc.). | WARN if hierarchy violated |

**Token & Reference Consistency:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-token-resolution` | Color tokens referenced in ui-kit Component States table exist in color-system. | FAIL if token missing |
| `style-no-raw-hex` | ui-kit, interaction-model, feedback-system, and audio-direction do not contain raw hex color values (#RRGGBB) outside of color-system. | WARN if found |
| `style-state-transitions-coverage` | Entity states from `design/state-transitions.md` have corresponding color tokens in color-system. | WARN per unmapped state |
| `style-entity-icon-coverage` | Entity types from `reference/entity-components.md` have corresponding icon or visual descriptions across style-guide and ui-kit. | WARN per uncovered entity |
| `style-resource-coverage` | Resources from `reference/resource-definitions.md` have corresponding UI representation in ui-kit. | WARN per uncovered resource |

**Boundary Compliance:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-interaction-no-responses` | interaction-model does not contain event-response coordination content (keywords: "the system responds", "feedback fires", "alert triggers", "audio plays in response"). | WARN [ADVISORY] if found |
| `style-feedback-no-inputs` | feedback-system does not contain input mapping content (keywords: "the player clicks", "on hover the player", "drag to select", "right-click to"). | WARN [ADVISORY] if found |
| `style-audio-no-timing` | audio-direction does not contain coordination timing content (keywords: "fires when", "triggers after", "plays at the same time as", "delays until"). | WARN [ADVISORY] if found |
| `style-ui-kit-no-engine` | ui-kit does not contain engine-specific content (keywords: "scene tree", "Control node", "CanvasLayer", "node hierarchy", "_ready()", "autoload"). | FAIL if found |

**Feedback System Coherence:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-interaction-feedback-coverage` | Every player action type defined in interaction-model has a corresponding feedback type in feedback-system. Extract action types from interaction-model (selection, command, cancel, drag, etc.) and check for matching feedback entries. | WARN per uncovered action |
| `style-feedback-audio-coverage` | Every feedback type in feedback-system that specifies an audio response references a sound category defined in audio-direction. | WARN per unresolved category |
| `style-priority-hierarchy-alignment` | feedback-system priority hierarchy and audio-direction feedback hierarchy use the same ordering. Extract priority lists from both docs and compare. | WARN if ordering conflicts |

**Accessibility Coherence:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-accessibility-contrast` | color-system defines concrete WCAG contrast ratio targets (not just "good contrast" or "accessible"). Check for numeric ratios (e.g., "4.5:1", "3:1"). | WARN if no concrete ratios |
| `style-accessibility-redundancy` | feedback-system defines at least two channels for every Critical-severity event. Check Event-Response Table: Critical events must have non-empty Visual AND (Audio OR UI) columns. | FAIL per single-channel critical event |
| `style-accessibility-no-color-only` | No gameplay state is communicated through color alone. Check color-system state tokens and ui-kit component states for cases where color is the only differentiator (no icon, no text, no shape change). | WARN [ADVISORY] if found |
| `style-accessibility-no-hover-only` | interaction-model does not define interaction cues available only through hover (inaccessible to keyboard/gamepad). Check for hover-dependent information without keyboard alternative. | WARN [ADVISORY] if found |

**Review Freshness:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `style-review-freshness` | For each Step 5 doc, check for matching review logs in `scaffold/decisions/review/`. Match by filename pattern (`ITERATE-style-*`, `FIX-style-*`) or log body containing the doc name. | See status matrix |

---

**How to run these checks:**

1. For `style-header-fields`: For each Step 5 doc, read blockquote header. Check presence of Authority, Layer, Conforms to, Created, Last Updated, Status.
2. For `style-authority-rank`: Parse Authority field. Must be `Rank 2`.
3. For `style-layer-value`: Parse Layer field. Must be `Canon`.
4. For `style-status-value`: Parse Status field. Must be Draft/Review/Approved/Complete/Deprecated.
5. For `style-conforms-to-resolution`: Parse `Conforms to` markdown links. Resolve paths relative to `scaffold/`. Verify targets exist.
6. For `style-template-sections`: Read the doc's corresponding template. Extract `##` headings. Check each exists in the doc (case-insensitive).
7. For `style-rules-populated`: Check Rules section has at least one authored rule line.
8. For `style-section-health`: For each `##` section: Empty if only comments/TODO, Partial if mix, Complete if no markers. Health = sum(weights) / section count.
9. For `style-todo-count`: Grep for `*TODO:`. Count per doc. Apply status matrix.
10. For `style-template-comments`: For Complete/Partial sections, check for remaining `<!-- ... -->` HTML comments.
11. For per-doc structural checks: Read each doc and verify the specific content described (pillar count, token count, table structure, etc.).
12. For `style-authority-flow`: Read `Conforms to` links in each doc. Verify color-system references style-guide, ui-kit references style-guide + color-system, audio-direction references feedback-system, etc.
13. For `style-token-resolution`: Extract token names from ui-kit Component States table. Check each exists in color-system token tables.
14. For `style-no-raw-hex`: Grep ui-kit, interaction-model, feedback-system, audio-direction for `#[0-9a-fA-F]{6}` patterns outside of color-system.
15. For `style-state-transitions-coverage`: Read state-transitions.md state names. Check color-system has a token for each.
16. For `style-entity-icon-coverage`: Read entity-components.md entity types. Check style-guide and ui-kit for visual descriptions or icon definitions.
17. For `style-resource-coverage`: Read resource-definitions.md resources. Check ui-kit for display components.
18. For boundary checks: Grep target docs for specified keywords. Exempt phrases inside code blocks or blockquotes.
19. For `style-interaction-feedback-coverage`: Extract action types from interaction-model section headings and content. Check feedback-system for matching entries.
20. For `style-feedback-audio-coverage`: Extract audio column values from Event-Response Table. Check audio-direction sound categories.
21. For `style-priority-hierarchy-alignment`: Extract ordered priority lists from both feedback-system and audio-direction. Compare ordering.
22. For accessibility checks: Run specific pattern checks as described per check.
23. For `style-review-freshness`: Glob `scaffold/decisions/review/ITERATE-style-*` and `FIX-style-*`. Match to docs. Apply status matrix.

**Maturity-aware activation:**
- If no Step 5 docs exist → SKIP all style checks.
- If fewer than 3 Step 5 docs exist → document-level checks run, cross-doc checks SKIP.
- Boundary compliance checks → SKIP for docs that don't exist.
- Token resolution → SKIP if color-system doesn't exist.
- State-transitions coverage → SKIP if state-transitions.md doesn't exist.
- Entity/resource coverage → SKIP if entity-components.md or resource-definitions.md doesn't exist.
- Feedback coherence → SKIP if either interaction-model or feedback-system doesn't exist.
- Priority alignment → SKIP if either feedback-system or audio-direction doesn't exist.

---

### 2l. Cross-Cutting Integrity Checks (scope: `all`)

These checks span all document types. They enforce decision closure, workflow compliance, and evolution integrity. Run on `--scope all` only — individual scopes skip these.

**Findings persistence:** Cross-cutting findings are written to `scaffold/decisions/cross-cutting-findings.md` as rows in the Active Findings table. Each new finding gets the next `XC-###` ID. On each run:
1. Read existing findings. For any with Status: **Resolved**, re-check if the issue still exists. If clean, remove the row. If still present, reopen as **Open**.
2. For any with Status: **Acknowledged**, downgrade to INFO in output (do not re-report as FAIL).
3. For any with Status: **Deferred**, verify the tracking reference (KI-### or ADR-###) still exists. If missing, reopen as **Open**.
4. New findings not already in the table get appended with Status: **Open**.
5. Use `/scaffold-fix-cross-cutting` to resolve findings interactively.

**Decision Closure:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `decision-closure-tasks` | Approved/Complete task files have no unresolved `*TODO:`, `TBD`, `<!-- TODO`, or `Open Questions` entries unless explicitly marked `[DEFERRED: tracked in KI-### / ADR-###]`. | Draft: INFO, Review: WARN, Approved/Complete: FAIL |
| `decision-closure-specs` | Approved/Complete spec files have no unresolved `*TODO:`, `TBD`, `<!-- TODO`, or `Open Questions` entries unless explicitly deferred and tracked. | Draft: INFO, Review: WARN, Approved/Complete: FAIL |
| `decision-closure-slices` | Approved/Complete slice files have no unresolved markers unless explicitly deferred and tracked. | Draft: INFO, Review: WARN, Approved/Complete: FAIL |
| `decision-closure-phases` | Approved/Complete phase files have no unresolved markers unless explicitly deferred and tracked. | Draft: INFO, Review: WARN, Approved/Complete: FAIL |
| `decision-closure-engine` | Approved/Complete engine docs have no unresolved markers unless explicitly deferred and tracked. Constrained TODOs (blocked on Step 3 decisions) are exempt — they are tracked by `engine-constrained-todo-freshness` in scope `engine`. | Draft: INFO, Review: WARN, Approved/Complete: FAIL |

**Workflow Integrity:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `workflow-slice-review-before-approve` | Approved slices have both a FIX/REVIEW log and an ITERATE log in `scaffold/decisions/review/`. A slice cannot be Approved without having passed adversarial review. | FAIL if Approved without logs |
| `workflow-phase-review-before-approve` | Approved phases have an ITERATE log in `scaffold/decisions/review/`. | FAIL if Approved without log |
| `workflow-tasks-reordered-before-approve` | Approved tasks belong to a slice whose Tasks table has valid ordering (no duplicates, no gaps, pre-blockers before main-sequence). Catches tasks approved before `/scaffold-reorder-tasks` ran. Validates indirectly: if the slice Tasks table has ordering issues, tasks in that slice should not be Approved. | FAIL if slice ordering is broken but tasks are Approved |
| `workflow-phase-sequence` | No phase was approved before its predecessor phase was Complete. For each Approved phase, all phases referenced in its Entry Criteria with "P#-### Complete" conditions must actually be Complete. | FAIL if predecessor not Complete |
| `workflow-completed-phase-revision` | When a phase is Complete, the roadmap's Completed Phases section must contain an entry for it. Catches phases marked Complete without triggering the roadmap revision cycle. | FAIL if Complete phase missing from Completed Phases |
| `workflow-validate-after-edit` | For Approved docs (phases, slices, specs, tasks), the most recent validate log date (if recorded in review logs) should post-date the doc's last material edit. This is a WARN — validate doesn't always leave a log, so absence is not proof of skipping. | WARN if validate appears stale |

**Upstream Change Staleness:**

| Check | What It Validates | Severity |
|-------|------------------|----------|
| `staleness-spec-system` | For each Approved/Complete spec, the referenced system file's last modification date is compared against the spec's last stabilization pass (latest ITERATE log or approval date). If the system was modified after the spec was stabilized, the spec may be stale. | WARN |
| `staleness-task-spec` | For each Approved/Complete task, the referenced spec file's last modification date is compared against the task's approval date (from review logs or filename rename timestamp). If the spec changed after the task was approved, the task may be stale. | WARN |
| `staleness-engine-architecture` | For each Approved engine doc that references architecture.md, authority.md, or interfaces.md, compare the Step 3 doc's modification date against the engine doc's last review log date. If Step 3 changed after the engine doc's last review, the engine doc may be stale. | WARN |
| `staleness-roadmap-phases` | For each phase listed in the roadmap's Phase Overview, compare the phase file's modification date against the roadmap's last modification date. If a phase file changed after the roadmap was last updated, the roadmap may be stale. | WARN |
| `staleness-slice-phase` | For each Approved slice, compare the parent phase file's modification date against the slice's last review date. If the phase was rescoped after the slice was stabilized, the slice may be stale. | WARN |

**How to run these checks:**

1. For `decision-closure-*`: Glob files by type. For each, read Status. If Approved or Complete, grep for unresolved markers: `*TODO:`, `TBD` (word-boundary, case-insensitive), `<!-- TODO`, and `## Open Questions` sections with non-empty content. For each match, check if it's followed by `[DEFERRED:` with a tracking reference. Untracked markers at Approved/Complete status = FAIL. For engine docs, additionally exempt lines containing `Constrained TODO` (those are tracked separately).
2. For `workflow-slice-review-before-approve`: For each Approved slice, glob `scaffold/decisions/review/*slice*SLICE-###*`. Must find at least one ITERATE log.
3. For `workflow-phase-review-before-approve`: For each Approved phase, glob `scaffold/decisions/review/*phase*P#-###*`. Must find at least one ITERATE log.
4. For `workflow-tasks-reordered-before-approve`: For each slice containing Approved tasks, run the `slice-order-integrity` logic on the slice's Tasks table. If ordering is broken (duplicates, gaps, missing pre-blockers), any Approved tasks in that slice = FAIL.
5. For `workflow-phase-sequence`: For each Approved phase, extract Entry Criteria. Find "P#-### Complete" conditions. Verify each referenced phase has Status: Complete.
6. For `workflow-completed-phase-revision`: For each Complete phase in `scaffold/phases/`, check `scaffold/phases/roadmap.md` Completed Phases section for a matching entry.
7. For `workflow-validate-after-edit`: For each Approved doc, find the latest validate-related log (if any). Compare against doc modification time. WARN if doc is newer. SKIP if no validate logs exist (cannot determine if validate ran).
8. For `staleness-spec-system`: For each Approved/Complete spec, extract `System: SYS-###`. Get the system file's modification time. Get the spec's latest ITERATE log date or approval rename date. If system is newer → WARN.
9. For `staleness-task-spec`: For each Approved/Complete task, extract `Implements: SPEC-###`. Get the spec file's modification time. Get the task's approval rename timestamp. If spec is newer → WARN.
10. For `staleness-engine-architecture`: For each Approved engine doc, identify referenced Step 3 docs from `Conforms to` links and content references. Get Step 3 doc modification times. Get the engine doc's latest review log date. If any Step 3 doc is newer → WARN.
11. For `staleness-roadmap-phases`: Get roadmap modification time. For each phase in Phase Overview, get phase file modification time. If any phase is newer → WARN.
12. For `staleness-slice-phase`: For each Approved slice, extract Phase reference. Get phase file modification time. Get slice's latest review log date. If phase is newer → WARN.

**Maturity-aware activation:**
- Decision closure: runs on all numbered docs that exist. Severity scales with status per the table above. Deprecated docs → SKIP.
- Workflow integrity: runs only when the relevant lifecycle artifacts exist (review logs directory, roadmap, etc.). SKIP if preconditions not met.
- Upstream change staleness: runs only when both the downstream doc and its upstream reference exist and the downstream doc is Approved or Complete. Draft/Review docs → SKIP (not yet stabilized, staleness is expected).

**Suggested fixes:**
- Decision closure FAIL → "Resolve the TODO/TBD in [file] at [line], or mark it `[DEFERRED: tracked in KI-### / ADR-###]` if intentionally deferred"
- Workflow review missing → "Run `/scaffold-iterate-[type]` on [doc] before keeping Approved status"
- Workflow tasks not reordered → "Run `/scaffold-reorder-tasks SLICE-###` to fix ordering, then re-approve"
- Workflow phase sequence → "Complete P#-### before approving P#-### — entry criteria require it"
- Workflow phase revision missing → "Run `/scaffold-revise-roadmap` to record the completed phase"
- Upstream staleness → "[upstream doc] was modified after [downstream doc] was stabilized. Review whether [downstream doc] needs updating. Run the appropriate fix/iterate skill to restabilize"

### 3. Report

Present results as a summary table with four status levels:

| Status | Meaning |
|--------|---------|
| **PASS** | Check ran and found no issues |
| **FAIL** | Check ran and found issues that must be fixed |
| **WARN** | Check ran and found issues that should be reviewed but may be acceptable |
| **SKIP** | Check preconditions not met (maturity-aware activation) — not an error |

```
| Check | Status | Issues |
|-------|--------|--------|
| System IDs | PASS | 0 |
| Task index files | FAIL | 2 |
| Triage upstream targets | SKIP | 0 |
| Status filename sync | WARN | 1 |
| ... | ... | ... |
```

Then list each FAIL and WARN issue with file, line, and message. SKIP checks get a one-line note explaining why they were skipped.

If all checks pass, report: **All cross-references validated. No issues found.**

### 4. Suggest Fixes

For each failing check, suggest the specific edit needed:
- Missing system registration → "Register SYS-### in systems/_index.md"
- Authority mismatch → "Update entity-components.md Authority column or authority.md Owning System"
- Glossary violation → "Replace [NOT term] with [canonical term] in [file]"
- Missing spec-slice link → "Add SPEC-### to a slice's Specs Included table"
- Missing task-spec link → "Verify TASK-### references a valid SPEC-### in its Implements field"
- Slice-task membership mismatch (stale/missing rows) → "Run `/scaffold-reorder-tasks SLICE-###` to resync the slice Tasks table"
- Slice-task membership mismatch (wrong `Implements:` or cross-slice misassignment) → "Fix task metadata first or run `/scaffold-triage-tasks` to reassign, then reorder"
- Task index drift → "Add missing task to `scaffold/tasks/_index.md`" or "Remove stale row for deleted task"
- Status-filename mismatch → "Rename file with `git mv` to match status, or update internal Status field"
- Slice table status drift → "Run `/scaffold-approve-tasks` or `/scaffold-complete` to resync, or manually update the slice table"
- Triage upstream target missing → "Update triage log to reference current document ID, or mark upstream action as Resolved if the target was intentionally removed"
- Reference file not found → "TASK-### references SPEC-### but no matching file exists — update the Implements field or recreate the spec"
- Slice order duplicate/malformed → "Run `/scaffold-reorder-tasks SLICE-###` to regenerate the Tasks table with valid ordering"
- Spec index drift → "Add missing spec to `scaffold/specs/_index.md`" or "Remove stale row for deleted spec"
- Spec-slice membership mismatch → "Run `/scaffold-triage-specs SLICE-###` to resync, or manually update the slice Specs table"
- Spec system reference broken → "Update the spec's System reference to a valid SYS-### ID, or check if the system was renamed"
- Spec status drift in slice table → "Run `/scaffold-approve-specs` or `/scaffold-complete` to resync, or manually update the slice Specs table"
- Spec triage upstream target missing → "Update spec triage log to reference current document ID, or mark upstream action as Resolved"
- Slice index drift → "Add missing slice to `scaffold/slices/_index.md`" or "Remove stale row for deleted slice"
- Slice phase reference broken → "Update the slice's Phase reference to a valid P#-### ID"
- Slice status-filename mismatch → "Rename file with `git mv` to match status, or update internal Status field"
- Slice interface reference broken → "Update the slice's Integration Points to reference valid interfaces, or add the interface to interfaces.md"
- Slice dependency reference broken → "Update the slice's `Depends on` field to reference a valid SLICE-### ID, or remove the dependency if it's no longer needed"
- Slice dependency cycle → "Break the circular dependency between SLICE-### and SLICE-### by removing one direction of the dependency"
- Slice dependency cross-phase → "Move the dependency SLICE-### to the same phase, or remove the cross-phase dependency and document the prerequisite in the phase's entry criteria instead"
- Slice dependency order violation → "Manually reorder `scaffold/slices/_index.md` so SLICE-### appears before SLICE-### (its dependent). If the bad order reflects a deeper planning change, run `/scaffold-revise-slices` to reconcile the full dependency graph."
- Single active slice violation → "Phase P#-### has multiple Approved slices: SLICE-### and SLICE-###. Complete one before the other can be active. Run `/scaffold-complete` on the finished slice."
- Slice review freshness (stale) → "SLICE-### was modified after its last review/iterate log. Rerun `/scaffold-review-slice` and `/scaffold-iterate-slice`."
- Slice review freshness (missing) → "SLICE-### has no review or iterate log. Run `/scaffold-review-slice` and `/scaffold-iterate-slice` before approving."
- Phase index drift → "Add missing phase to `scaffold/phases/_index.md`" or "Remove stale row for deleted phase"
- Phase roadmap sync → "Update `scaffold/phases/roadmap.md` Phase Overview to match `_index.md`, or vice versa"
- Phase status-filename mismatch → "Rename file with `git mv` to match status, or update internal Status field"
- Phase entry chain broken → "Entry criteria reference P#-### but that phase doesn't exist or isn't Complete — update entry criteria or complete the prerequisite"
- Single active phase violation → "Phase P#-### is already Approved and not Complete. Complete it before approving another."
- Phase system reference broken → "In Scope references SYS-### but no matching system file exists — update the In Scope list or create the system"
- Phase review freshness (stale) → "P#-### was modified after its last iterate log. Rerun `/scaffold-fix-phase` and `/scaffold-iterate-phase`."
- Phase review freshness (missing) → "P#-### has no iterate log. Run `/scaffold-iterate-phase` before approving."
- Design doc at template defaults → "Run `/scaffold-init-design` to populate the design document."
- Design doc missing section group → "Design doc is missing the [Group] section group. Run `/scaffold-init-design --mode fill-gaps --sections [Group]`."
- Design doc below 50% health → "Design doc is too incomplete for downstream work. Run `/scaffold-init-design --mode fill-gaps` to fill remaining sections."
- Invariant missing fields → "Invariant '[ShortName]' is missing [field]. Run `/scaffold-fix-design` to auto-fix format issues."
- Invariant missing ShortName → "Invariant has no ShortName — downstream docs cannot cite it. Add `Invariant: <ShortName>` or run `/scaffold-fix-design`."
- Invariant count outside range → "Design has [N] invariants (target: 3-7). Run `/scaffold-init-design --mode refresh --sections Identity` to adjust."
- Anchor format wrong → "Decision Anchor '[text]' is not in 'X over Y' format. Run `/scaffold-fix-design` to flag for correction."
- Anchor count outside range → "Design has [N] anchors (target: 3-5). Run `/scaffold-init-design --mode refresh --sections Philosophy` to adjust."
- Pressure test missing fields → "Pressure Test '[name]' is missing [field]. Run `/scaffold-fix-design` to auto-fix format issues."
- Pressure test count outside range → "Design has [N] pressure tests (target: 3-6). Run `/scaffold-init-design --mode refresh --sections Philosophy` to adjust."
- Design gravity empty → "Design Gravity section is empty. Run `/scaffold-init-design --mode fill-gaps --sections Philosophy`."
- Design gravity count outside range → "Design has [N] gravity directions (target: 3-4). Consider adjusting."
- System index mismatch → "Design doc System Design Index doesn't match `design/systems/_index.md`. Run `/scaffold-fix-design` to sync."
- Design glossary violation → "Design doc uses NOT-column term '[term]' — replace with canonical term '[canonical]' from glossary."
- Design-ADR contradiction → "Design doc section [section] contradicts accepted ADR-###. Run `/scaffold-init-design --mode reconcile` to resolve."
- Provisional markers remaining → "[N] PROVISIONAL markers remain in the design doc. Confirm or remove each before proceeding to Step 2+."
- Design review freshness (stale) → "Design doc was modified after its last iterate log. Rerun `/scaffold-fix-design` and `/scaffold-iterate-design`."
- Engine doc not in index → "Add `<filename>` to `scaffold/engine/_index.md` Documents table"
- Engine file in index but missing → "Create the engine doc or remove the stale row from `scaffold/engine/_index.md`"
- Engine missing header field → "Add `> **<Field>:** <value>` to the engine doc's blockquote header"
- Engine wrong Authority Rank → "Change to `Rank 9` in the engine doc header to match the authority chain in CLAUDE.md"
- Engine Conforms-to target missing → "Update the `Conforms to` link to reference an existing document, or create the missing document"
- Engine missing common section → "Add `## <Section>` to the engine doc — all engine docs require Purpose, Project Overrides, and Rules"
- Engine template section missing → "Add `## <Section>` from the matching template `scaffold/templates/<template>.md`, or document why it was intentionally omitted"
- Engine section health below threshold → "Fill remaining TODO sections. Run `/scaffold-fix-engine <topic>` to auto-fix structural issues"
- Engine Purpose empty → "Fill the Purpose section explaining what this doc governs and why it exists"
- Engine TODOs in Approved doc → "Resolve all remaining `*TODO:` markers before keeping Approved status, or revert to Draft"
- Engine stale constrained TODO → "The blocking document has been resolved. Update or remove the constrained TODO"
- Engine architecture mismatch → "Update the engine doc to match `scaffold/design/architecture.md`, or file an ADR if the architecture needs to change"
- Engine authority conflict → "Remove ownership claim from the engine doc — ownership is defined in `scaffold/design/authority.md` only"
- Engine orphan signal → "Register the signal in `scaffold/reference/signal-registry.md`, or remove the reference if it's engine-internal (prefix with `_`)"
- Engine design content detected → "Move behavioral descriptions to the appropriate system design doc. Engine docs describe HOW to implement, not WHAT the behavior is"
- Engine system design sections found → "Remove `## <Section>` — this section belongs in a system design doc (SYS-###), not an engine doc"
- Engine naming inconsistency → "Update code examples to follow the naming conventions in the coding-best-practices engine doc"
- Engine language boundary violation → "Move logic to the correct language layer per the coding-best-practices language boundary rules"
- Engine template drift → "Section `## <Section>` is not in the canonical template. Verify it's intentional or rename to match"
- Engine template mapping missing → "Add the template mapping to the `_index.md` Templates table"
- Engine seeded marker remaining → "Review the seeded content and remove the `<!-- SEEDED -->` marker"
- Engine stale template comment → "Remove the template instruction comment — the section has authored content"
- Engine review freshness (stale) → "Engine doc was modified after its last review log. Rerun `/scaffold-fix-engine` and `/scaffold-iterate-engine`"
- Engine review freshness (missing, Approved) → "No review log exists for this Approved engine doc. Run `/scaffold-iterate-engine` before keeping Approved status"
- Engine topic overlap → "Two engine docs have overlapping Purpose scope. Clarify boundaries or merge into one doc. Check `_index.md` Topic column for uniqueness"
- Engine Conforms-to missing links → "Add at least one `Conforms to` link to a Step 3 or design doc that this engine doc implements"
- Engine template mapping mismatch → "The `_index.md` Templates table maps this doc to a different template than filename inference suggests. Update the Templates table to match the correct template"
- Style doc missing header field → "Add `> **<Field>:** <value>` to the Step 5 doc's blockquote header"
- Style doc wrong Authority Rank → "Change to `Rank 2` in the doc header to match the authority chain"
- Style doc Conforms-to missing → "Add `Conforms to` link to at least design-doc.md"
- Style doc missing template section → "Add `## <Section>` from `scaffold/templates/<template>.md`"
- Style doc health below threshold → "Fill remaining TODO sections. Run `/scaffold-fix-style --target <doc>` to auto-fix structural issues"
- Style token missing in color-system → "Add the token to `scaffold/design/color-system.md` or update the ui-kit reference"
- Style raw hex found → "Replace raw hex value with the corresponding color-system token"
- Style unmapped state → "Add a color token for the entity state in `scaffold/design/color-system.md`"
- Style uncovered entity → "Add visual description in style-guide or icon definition in ui-kit for the entity type"
- Style uncovered resource → "Add UI representation in ui-kit for the resource type"
- Style boundary violation (interaction) → "Move event-response content from interaction-model to feedback-system"
- Style boundary violation (feedback) → "Move input mapping content from feedback-system to interaction-model"
- Style boundary violation (audio) → "Move timing coordination content from audio-direction to feedback-system"
- Style boundary violation (ui-kit engine) → "Move engine-specific content from ui-kit to the engine UI doc"
- Style action without feedback → "Add feedback entry in feedback-system for the uncovered player action"
- Style feedback without audio category → "Add the sound category to audio-direction or update the feedback-system audio column"
- Style priority hierarchy mismatch → "Align priority ordering between feedback-system and audio-direction"
- Style no contrast ratios → "Add concrete WCAG contrast ratio targets (e.g., '4.5:1') to color-system accessibility section"
- Style single-channel critical → "Add a second feedback channel (audio or UI) for the critical event in the feedback-system Event-Response Table"
- Style color-only state → "Add a non-color differentiator (icon, shape, text) for the gameplay state"
- Style hover-only cue → "Add keyboard/gamepad alternative for the hover-dependent interaction in interaction-model"
- Style review freshness (stale) → "Step 5 doc was modified after its last review log. Run `/scaffold-fix-style` and `/scaffold-iterate-style`"
- Style review freshness (missing, Approved) → "No review log exists for this Approved Step 5 doc. Run `/scaffold-iterate-style` before keeping Approved status"
- Style ui-kit scope guard → "Remove screen map / scene hierarchy / HUD layout content from ui-kit — belongs in engine UI doc"
- Style duplicate tokens → "Merge duplicate token entries in color-system, keeping the more complete version"
- Style malformed hex → "Fix hex value to #RRGGBB or #RRGGBBAA format"

## Rules

- **Read-only analysis.** This skill reports issues but does not fix them. Use `/scaffold-update-doc` to apply fixes.
- **Run from project root.** The script expects `scaffold/` to be in the current directory.
- **If the script fails**, check that Python 3 is available and `scaffold/tools/validate-refs.py` exists.
- **Maturity-aware severity.** See the Severity Model in Step 2b for SKIP vs WARN vs FAIL rules. The severity depends on whether preconditions are met and whether the structure is required at the current project maturity.

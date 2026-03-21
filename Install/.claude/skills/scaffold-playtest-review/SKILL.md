---
name: scaffold-playtest-review
description: Review playtest feedback patterns. Read-only analysis with severity x frequency grid, cross-reference checks, and delight inventory.
allowed-tools: Read, Grep, Glob
---

# Review Playtest Feedback

Analyze playtest feedback patterns and generate a prioritized report.

## Steps

### 1. Read Context

1. **Read playtest feedback** at `scaffold/decisions/playtest-feedback.md`.
2. **Read known issues** at `scaffold/decisions/known-issues.md`.
3. **Read design debt** at `scaffold/decisions/design-debt.md`.
4. **Read all ADRs** — Glob `scaffold/decisions/ADR-*.md` and read each one.
5. **Read the systems index** at `scaffold/design/systems/_index.md`.
6. **Read the roadmap** at `scaffold/phases/roadmap.md` for current phase context.
7. **Read theory** at `scaffold/theory/playtesting-guidelines.md` for methodology context.

### 2. Pattern Report by System

Group all feedback entries (Open + Pattern) by System/Spec. For each system:

- Count total observations.
- Count by type (Confusion, Frustration, Delight, Suggestion, Bug).
- List any entries at Pattern status.
- Flag systems with 3+ Confusion or Frustration entries as "hot spots."

Present the results as a table:

| System | Total | Confusion | Frustration | Delight | Suggestion | Bug | Hot Spot |
|--------|-------|-----------|-------------|---------|------------|-----|----------|

### 3. Severity x Frequency Grid

Classify all Open and Pattern entries into the priority grid:

| | High Frequency (≥3/N) | Medium Frequency (2/N) | Low Frequency (1/N) |
|---|---|---|---|
| **High Severity** | ACT NOW | ACT NOW | WATCH CLOSELY |
| **Medium Severity** | WATCH CLOSELY | MONITOR | NOTE & MOVE ON |
| **Low Severity** | MONITOR | NOTE & MOVE ON | NOTE & MOVE ON |

List specific PF-### IDs in each cell. Flag any "ACT NOW" entries that don't yet have a Pattern entry or action plan.

### 4. Action Recommendations

For each ACT NOW and WATCH CLOSELY entry, recommend one of:

- **Create a spec** — the issue needs a behavior change. Suggest a spec name.
- **File a known issue** — the issue needs investigation. File via `/scaffold-file-decision --type ki`.
- **File design debt** — the issue is understood but deferred. File via `/scaffold-file-decision --type dd`.
- **Update an existing spec** — the issue affects an already-defined behavior. Identify which spec.
- **Add to phase scope** — the issue should be addressed in the next phase. Identify which phase.
- **Protect** — (for Delight entries) ensure upcoming changes don't break what players love.

### 5. Cross-Reference Check

Check for overlaps between playtest feedback and existing tracking docs:

- **KI overlap:** Does any Open Feedback entry describe the same issue as an existing KI-### entry? If so, link them and note the overlap.
- **DD overlap:** Does any entry describe behavior that's already logged as design debt? Link and note.
- **ADR overlap:** Did any ADR already address an issue that's still in Open Feedback? Flag it as potentially resolved.

Present overlaps as a table:

| PF-### | Overlaps With | Notes |
|--------|---------------|-------|

### 6. Stale Entry Check

Flag entries that may need attention:

- **Old sessions:** Sessions more than 2 phases old — are their open entries still relevant?
- **Orphan entries:** Entries whose System/Spec no longer exists (system was removed or renamed).
- **Stale patterns:** Patterns with no Action Taken after 1+ phases.

### 7. Report

Present the full analysis:

1. **Summary** — Total entries, total sessions, entries by status (Open / Pattern / Resolved).
2. **System Heat Map** — The table from Step 2.
3. **Priority Grid** — The severity x frequency grid from Step 3 with specific PF-### IDs.
4. **Recommended Actions** — The action recommendations from Step 4.
5. **Cross-Reference Overlaps** — The overlap table from Step 5.
6. **Stale Entries** — Any flags from Step 6.
7. **Delight Inventory** — List all Delight entries. These are features to protect and amplify.
8. **Next Steps** — Suggest concrete next actions (e.g., "Run `/scaffold-playtest-log` after the next session", "Create SPEC-### for PF-001 pattern").

## Rules

- **Read-only.** This skill does not modify any files. It analyzes and reports.
- **Data-driven.** Recommendations are based on the severity x frequency grid, not opinion. Present the data first, recommendations second.
- **Delight is data.** Always include the delight inventory. Positive feedback is actionable.
- **Cross-reference everything.** Playtest feedback doesn't exist in isolation — it connects to KI, DD, ADR, and spec trackers.
- **No entry left behind.** Every Open and Pattern entry should appear somewhere in the report (grid, recommendations, or stale check).

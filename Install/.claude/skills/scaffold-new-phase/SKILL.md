---
name: scaffold-new-phase
description: Create a new phase scope gate. Reads ADRs from prior phases to inform scope. Use after the roadmap is defined.
argument-hint: [phase-name]
allowed-tools: Read, Edit, Write, Grep, Glob
---

# New Phase Scope Gate

Create a new phase document for: **$ARGUMENTS**

## Steps

### 1. Read Context

1. **Read the roadmap** at `scaffold/phases/roadmap.md` — find this phase in the Phase Overview table.
2. **Read the phase template** at `scaffold/templates/phase-template.md`.
3. **Read the phases index** at `scaffold/phases/_index.md` to find the next available PHASE-### ID.
4. **Read the design doc** at `scaffold/design/design-doc.md` for overall scope.
5. **Read the systems index** at `scaffold/design/systems/_index.md` to see available systems.
6. **Read all ADRs** — Glob `scaffold/decisions/ADR-*.md` and read each one. These are critical input for phase planning.
7. **Read known issues** at `scaffold/decisions/known-issues.md`.
8. **Read design debt** at `scaffold/decisions/design-debt.md`.
9. **Read playtest feedback** at `scaffold/decisions/playtest-feedback.md` — check for Pattern-status entries that may affect this phase's scope.

### 2. ADR Impact Analysis

Before defining scope, analyze all ADRs for their impact on this phase:

- **Which ADRs affect this phase's scope?** — Identify any ADR whose decision changes what this phase must deliver.
- **Did any ADR from a previous phase defer work into this phase?** — Look for ADRs that explicitly push work forward.
- **Did any ADR change a system design that affects what this phase needs to build?** — Look for design changes that ripple into this phase's systems or features.

Present the ADR impact summary to the user before proceeding. If no ADRs exist, say so explicitly and move on.

### 2b. Playtest Feedback Analysis

Check `scaffold/decisions/playtest-feedback.md` for Pattern-status entries that affect this phase:

- **Which patterns relate to systems in this phase's scope?** — Identify feedback patterns whose System/Spec overlaps with what this phase will build.
- **Are there ACT NOW patterns that should be addressed in this phase?** — High-severity, high-frequency patterns demand action.
- **Are there Delight entries to protect?** — If this phase touches systems that players love, flag them so scope decisions don't break what works.

Present the playtest feedback summary to the user alongside the ADR summary. If no playtest feedback exists, say so explicitly and move on.

### 3. Define the Phase

Walk the user through each section of the phase template, asking one question at a time. Write answers into the phase document immediately after each response.

1. **Goal** — Ask: *"In one sentence, what does this phase deliver?"*
1b. **Capability Unlocked** — Ask: *"When this phase ends, what can you now do that you couldn't before? Not a system — a capability. If QA ran a scenario, what new behavior would they see?"*
2. **Entry Criteria** — Ask: *"What must be true before this phase can start? Previous phases complete? Specific systems designed?"* Entry criteria should reference specific phase IDs (e.g., P1-001) or system IDs (e.g., SYS-003), not vague conditions.
3. **In Scope** — Ask: *"What systems, features, or slices are included in this phase?"* Reference ADR impacts from Step 2 to help the user think through scope.
4. **Out of Scope** — Ask: *"What is explicitly deferred to later phases?"*
5. **Deliverables** — Ask: *"What concrete outputs does this phase produce? What can you show or play?"*
6. **Exit Criteria** — Ask: *"What must be true for this phase to be complete?"*
7. **Non-Goals** — Ask: *"What is intentionally NOT solved in this phase? What scope creep should this prevent?"*
8. **Slice Strategy** — Ask: *"How should slices look in this phase? What verticality, size, and proof style are expected?"*
9. **Risk Focus** — Ask: *"What are the major risks or unknowns this phase should reduce?"*
10. **Phase Demo** — Ask: *"How would you demonstrate this phase is complete in a dev demo or playtest? Walk me through the steps."*
11. **System Readiness** — Ask: *"For each system in scope, what maturity level is expected by the end of this phase?"*
12. **Architectural Constraints** — Ask: *"Are there architecture rules slices must respect during this phase? Foundation decisions that constrain implementation?"*
13. **Dependencies** — Ask: *"What does this phase depend on — other phases, systems, decisions?"*

### 4. Create the Phase File

Create `scaffold/phases/PHASE-###-<name>_draft.md` where:

- `P#` is the phase number from the roadmap.
- `###` is the next sequential ID from `scaffold/phases/_index.md`.
- `<name>` is a lowercase-kebab-case version of the phase name.
- `_draft` is the status suffix (all new documents start as Draft).

Use the phase template with the user's answers filled in.

### 5. Register

1. **Add a row** to `scaffold/phases/_index.md` (Status: Draft).
2. **Update the Phase Overview** in `scaffold/phases/roadmap.md` if needed to reflect the new phase entry.

### 6. Report

Show the user:

- The file path and assigned ID.
- ADRs that influenced the scope (or note that no ADRs existed).
- Suggest running `/scaffold-new-slice` to define vertical slices for this phase.

## Rules

- **Ask one section at a time.** Do not batch questions — walk through each section sequentially.
- **Write answers into the phase doc immediately.** Do not wait until the end to create the file.
- **ADR analysis is mandatory — never skip it.** If no ADRs exist, say so explicitly before proceeding.
- **If no argument is provided**, ask the user for a phase name before proceeding.
- **IDs are sequential and permanent** — never skip or reuse.
- **Entry criteria must reference specific IDs** — use phase IDs (P1-001) or system IDs (SYS-003), not vague conditions like "when the design is ready."
- **Never overwrite an existing phase file.**
- **Created documents start with Status: Draft.**

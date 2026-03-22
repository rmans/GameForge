---
name: scaffold-bulk-seed-phases
description: Read the roadmap, design doc, systems, and ADRs to bulk-create phase scope gate stubs. Roadmap goals drive phase selection. Use after the roadmap is defined.
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Seed Phases from Roadmap

Read the roadmap, design doc, system designs, and decision history to bulk-create phase scope gate stubs. The roadmap is the primary driver — it defines what each phase must deliver.

## Prerequisites

1. **Read `scaffold/phases/roadmap.md`** — the source of truth for phase goals and ordering.
2. **Read `scaffold/phases/_index.md`** to find the next available ID and check existing phases.
3. **Read `scaffold/design/design-doc.md`** for overall vision and scope.
4. **Read the systems index** at `scaffold/design/systems/_index.md`.
5. **Read relevant system designs** from `scaffold/design/systems/`.
6. **Read `scaffold/design/architecture.md`** for foundation decisions that constrain phase ordering.
7. **Read all ADRs** — Glob `scaffold/decisions/ADR-*.md` — ADRs may have changed scope.
8. **Read known issues** at `scaffold/decisions/known-issues.md`.
9. **Read playtest feedback** at `scaffold/decisions/playtest-feedback.md` — Pattern-status entries may affect phase scope.
10. **Read the phase template** at `scaffold/templates/phase-template.md`.
11. **If the roadmap is not defined**, stop and tell the user to run `/scaffold-new-roadmap` first.
12. **Verify the roadmap contains a Phase Overview table.** The roadmap must have a structured table with at minimum: phase number/name, goal, and key deliverables. If the roadmap is unstructured prose with no table, stop and instruct the user to add a Phase Overview table to `roadmap.md` before seeding.

## Step 0 — Validate Index and Assess Existing State

### 0a. Validate phase index consistency

Before assigning any IDs, verify `scaffold/phases/_index.md` is in sync with the filesystem:
- Glob `scaffold/phases/P*-*.md` (excluding `roadmap.md`).
- Compare against `scaffold/phases/_index.md` entries.
- If mismatched (files exist without index rows, or index rows point to missing files), **stop** and instruct the user to run `/scaffold-validate --scope phases` first.

Bulk creation tools must never guess IDs from a stale index.

### 0b. Assess existing state

Check what phases already exist:
- If no phases exist, this is a fresh seeding pass — generate all candidates from the roadmap.
- If phases already exist, operate in additive mode — propose candidates only for roadmap entries that do not have a confirmed corresponding phase file. Do not re-generate existing phases.

**Correspondence rule:** A roadmap entry is automatically treated as implemented only if the phase name similarity is strong AND the existing phase goal clearly matches the roadmap description (semantic goal comparison, not just keyword overlap). All other cases — including partial name matches, similar but not identical goals, or same systems but different scope — are classified as "Possible match — user must confirm or treat as new." Default to ambiguous rather than assuming a match.

### 0c. Extract roadmap structure

Before generating candidates, parse the roadmap Phase Overview table into structured data:

| Roadmap Phase | Name | Goal | Named Systems | Deliverables | Notes |
|---------------|------|------|---------------|--------------|-------|

For each row, extract:
- Phase number and name
- Goal sentence
- Explicitly named systems (if any)
- Key deliverables
- Dependencies implied by ordering

This structured extraction is used by all subsequent steps. It prevents the AI from interpreting prose sections inconsistently across candidates.

For each existing phase, classify:
- **Draft** — eligible for user-directed replacement or merge decisions. This skill does not revise or replace Draft phases automatically.
- **Approved** — fixed point; candidates must work around it
- **Complete** — fixed point; candidates must not re-scope what it delivered

**Never modify existing phase files automatically.** If a roadmap change conflicts with an existing Draft phase, present the conflict and request user decision.

## Phase 1 — Derive Phase Candidates from Roadmap

### 1a. Identify what the roadmap defines

Read the roadmap's Phase Overview table and each phase description. For each roadmap entry without a confirmed corresponding phase file:
- Extract the phase goal and key deliverables
- Identify which systems are in scope. If the roadmap text does not explicitly name systems, derive them cautiously from design-doc scope statements and mark as "inferred" in the candidate. **Limit inferred systems to a maximum of 3.** If more seem relevant, present the full list as a user decision rather than auto-attaching.
- Identify entry/exit criteria implied by the roadmap ordering
- **Identify architecture gate dependencies** — scan `architecture.md` and accepted ADRs for foundation decisions (identity model, save/load philosophy, content registry, spatial model, etc.) that this phase's scope depends on. Mark phases requiring unlocked decisions.

### 1b. Draft each candidate

For each candidate phase:
- **Goal** — one sentence describing what this phase delivers (from roadmap)
- **Entry Criteria** — prefer prior phase IDs for sequencing (e.g., "P1-001 Complete"). Use system IDs only when no prior phase exists yet or when the dependency is architectural rather than roadmap-order based. Phase-ID gating is more stable than system-ID gating.
- **In Scope** — systems, features, and capabilities this phase must deliver. **Phases should normally include 1–4 systems.** If more than 5 systems appear in scope, flag as potential over-scope and present to user for confirmation or splitting.
- **Out of Scope** — what is explicitly deferred to later phases
- **Deliverables** — concrete outputs that can be demonstrated
- **Exit Criteria** — verifiable conditions for phase completion. Exit criteria must be observable in a playtest, dev demo, UI display, or test scenario — not just "system implemented" or "feature functional."
- **Dependencies** — phases, systems, or foundation decisions this depends on

### 1c. ADR and feedback impact check

For each candidate:
- Check whether accepted ADRs defer work into this phase or change systems in scope
- Check whether known issues constrain or block this phase's scope
- Check playtest feedback using these interpretation rules:
  - **ACT NOW** — may move work into the earliest feasible phase. Flag if this candidate covers the affected system.
  - **Pattern** — may alter scope of phases affecting the system. Annotate the candidate.
  - **Observation** — note only, do not affect scope automatically.
- Annotate candidates with references and impacts

### 1d. Check ordering and entry/exit chains

Verify that the candidate set forms a valid chain using these explicit rules:

1. **Entry criteria may only reference:** earlier roadmap phases, foundation architecture gate decisions, or system availability (existing system designs).
2. **Exit criteria must produce artifacts** that satisfy the entry criteria of the next phase in roadmap order. If phase B's entry says "P1-001 Complete", phase A's exit criteria must be achievable.
3. **No phase may depend on a later phase.** Forward references in entry criteria are a chain break.
4. **Architecture gate dependencies must appear before the first phase requiring them.** If a phase's scope depends on a foundation decision (e.g., identity model, save/load philosophy), verify that decision is locked or that the Foundation Architecture Gate precedes this phase.
5. **Exit criteria must be demonstrable** in a playtest or dev demo — not just "phase complete" or "systems implemented."

### 1e. Verify roadmap coverage

After deriving candidates, verify that every roadmap entry is accounted for:
- **Confirmed existing match** — roadmap entry has a corresponding phase file
- **Candidate** — roadmap entry will become a new phase
- **Possible match (ambiguous)** — user must confirm
- **Explicitly deferred** — user chose to skip this roadmap entry

If any roadmap entry has none of these dispositions, surface it as: "⚠ Roadmap entry [name] has no candidate and no existing match — this work will be silently dropped unless addressed." Roadmap entries must not quietly disappear.

## Phase 2 — Present for Confirmation

Use temporary candidate labels (Candidate A, B, C) — do not assign P#-### IDs until confirmation.

```
### Phase Candidates from Roadmap

**Existing phases:** [list with status, or "None"]

Candidate A (Roadmap Phase N): [name]
- Goal: [one sentence]
- Entry criteria: [what must be true before starting]
- In scope: [systems and features]
- Out of scope: [explicit deferrals]
- Exit criteria: [verifiable conditions]
- ADR impacts: [if any]
- KI impacts: [if any]
- Playtest pattern impacts: [if any]

Candidate B: [name]
...

#### Chain Validation
✓ Entry/exit criteria chain is valid
⚠ [Any ordering issues or gaps]
⚠ Foundation dependency unresolved: [decision or gate not yet locked, if any]

#### Roadmap Coverage
✓ All roadmap entries accounted for: [N candidates, M existing matches, K possible matches]
⚠ Roadmap entry [name] is currently unaccounted for — phase creation will stop until addressed
```

Present decisions using the Human Decision Presentation pattern (see WORKFLOW.md). Each candidate gets a confirm/modify/remove choice. Possible matches get explicit confirm-as-existing/treat-as-new options. Wait for the user's decisions on each issue before proceeding.

## Phase 3 — Create Phase Files

**Only after user confirms the final candidate set.**

For each confirmed candidate:

1. **Assign the next sequential P#-### ID** from `scaffold/phases/_index.md`.
2. **Convert temporary dependency labels** to assigned P#-### IDs.
3. **Create** `scaffold/phases/P#-###-<name>_draft.md` using the phase template. Write substantive content for ALL sections — remove template HTML comments and replace with authored prose. No section should be left at template defaults.

   | Section | What to write | Minimum content |
   |---------|--------------|-----------------|
   | **Goal** | One sentence describing what this phase delivers, derived from roadmap entry | Complete sentence, not a fragment or TODO |
   | **Capability Unlocked** | What can be done after this phase that couldn't before — a testable capability, not a system name | 1-2 sentences describing the observable difference |
   | **Entry Criteria** | What must be true before this phase starts — prefer phase IDs for sequencing | At least 1 criterion; use P#-### references where applicable |
   | **In Scope** | Bulleted list of systems and features included, derived from roadmap system coverage | At least 2 bullet points with SYS-### references |
   | **Out of Scope** | Explicitly deferred work — what is NOT in this phase | At least 2 bullet points naming specific deferrals |
   | **Non-Goals** | Things intentionally not solved — prevents scope creep into future phases | At least 1 non-goal |
   | **Deliverables** | Concrete outputs (systems, features, slices) — demonstrable, not abstract | At least 2 deliverables |
   | **Exit Criteria** | What must be true for phase completion — must be demonstrable in playtest or dev demo, not just "implemented" | At least 2 verifiable criteria |
   | **Slice Strategy** | How slices should look in this phase — verticality expectations, typical size, systems touched, proof style | At least 3 bullet points covering size, integration expectations, and proof style |
   | **Risk Focus** | Major risks or unknowns this phase is expected to reduce | At least 1 risk with explanation of how the phase addresses it |
   | **Phase Demo** | How the phase should be demonstrated — becomes the anchor for slice demo scripts | 2-3 sentences describing the demo scenario |
   | **System Readiness** | Expected maturity level for each in-scope system | Table with at least 1 row per in-scope system, maturity column filled |
   | **Architectural Constraints** | Architecture rules slices must respect — foundation decisions that constrain implementation | At least 1 constraint, or explicit "No architectural constraints beyond standard project conventions" |
   | **Dependencies** | Phases, systems, or decisions this depends on | At least 1 entry, or explicit "No dependencies — this is the first phase" |
4. **Register** in `scaffold/phases/_index.md`.
5. **Update** `scaffold/phases/roadmap.md` Phase Overview with the new phase ID. Only update the row corresponding to the confirmed roadmap entry. Never rewrite other roadmap rows. If no matching row is unambiguous, stop and ask the user which row to update.

## Phase 4 — Report

```
## Phases Seeded

| Phase | Goal | Systems in Scope | ADR/KI Impacts |
|-------|------|-------------------|----------------|
| P#-### — Name | [goal] | SYS-###, SYS-### | [impacts or "none"] |
| ... | ... | ... | ... |

**Total:** N phases created
**Entry/exit chain:** valid / issues noted

### Next Steps
- Run `/scaffold-fix-phase P#-###-P#-###` to auto-fix mechanical issues
- Run `/scaffold-iterate phase P#-###-P#-###` for adversarial review
- Run `/scaffold-validate --scope phases` to check structural integrity
- Run `/scaffold-approve-phases P#-###` to approve the first phase for slice seeding
```

## Rules

- **Seeded files must contain substantive content, not template placeholders.** Every section that the skill populates must have real authored prose derived from roadmap and design doc analysis. Do not leave pre-filled sections as TODO, HTML comment prompts, or single generic sentences. Remove template HTML comments from sections that receive authored content — replace them, don't leave them alongside the real content. A phase file where Goal is "TBD" or Entry Criteria is the template's HTML comment has failed the seed.
- **Roadmap drives phase selection.** Derive candidates from the roadmap, not from exhaustive system enumeration.
- **Never write without confirmation.** Present all proposed phases before creating files.
- **No IDs until confirmation.** Use temporary candidate labels during the confirmation phase.
- **Additive mode for existing phases.** If phases already exist, only propose candidates for missing roadmap entries.
- **ADR and feedback analysis is mandatory.** Never skip it.
- **Entry/exit chains must be valid.** Each phase's entry criteria must be satisfiable by prior phases.
- **Validate index before assigning IDs.** If `_index.md` is out of sync with the filesystem, stop. Never guess IDs from a stale index.
- **Never modify existing phase files.** If a roadmap change conflicts with an existing Draft phase, present the conflict — don't silently overwrite.
- **System inference must be cautious.** If the roadmap doesn't explicitly name systems, derive them from design-doc scope statements, mark as "inferred," and limit to 3 systems maximum. More than 3 requires user confirmation.
- **Phase size guardrail.** Phases should normally include 1–4 systems. If more than 5 appear in scope, flag as potential over-scope.
- **Respect authority layer boundaries.** If the project's architecture defines distinct authority layers (e.g., colony/region/world), avoid mixing systems from different layers in the same phase unless the phase explicitly requires cross-layer integration. Mixing layers silently makes debugging painful.
- **IDs are sequential and permanent** — never skip or reuse.
- **Created documents start with Status: Draft.**

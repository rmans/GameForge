---
name: scaffold-new-system
description: Create a single system design document with overlap and authority auditing. Reads design doc, existing systems, and ADRs. Use when a new system is needed after initial bulk seeding — triggered by revise-systems escalation, validate gap detection, or direct user request.
argument-hint: [system-name] [--split-from SYS-###] [--trigger ADR-###|KI:keyword]
allowed-tools: Read, Edit, Write, Grep, Glob
---

# New System Design

Create a new system design for: **$ARGUMENTS**

This skill creates a single system design document — unlike `/scaffold-bulk-seed-systems` which proposes and creates an entire simulation layer at once. Use this when:

- `/scaffold-revise-systems` escalates an emergent subsystem, ownership shift, or identity drift that requires a new system
- `/scaffold-validate` detects a design-to-systems coverage gap
- You need to add a system after the initial bulk seed

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `system-name` | No | — | Name for the system. If omitted, asks interactively. |
| `--split-from` | No | — | SYS-### ID of an existing system being split. Pre-fills context from the parent system's scope and identifies the responsibility boundary. |
| `--trigger` | No | — | The drift signal or gap that motivated this system. Accepted formats: `ADR-###`, `KI:keyword`. Reads the referenced document for context. |

## Step 1 — Read Context

1. **Read the system template** at `scaffold/templates/system-template.md`.
2. **Read the systems index** at `scaffold/design/systems/_index.md` to find the next available SYS-### ID.
3. **Read the design doc** at `scaffold/design/design-doc.md` — specifically Design Invariants, Simulation Depth Target, Major System Domains, Player Control Model, Design Boundaries.
4. **Read all existing system files** — Glob `scaffold/design/systems/SYS-###-*.md`. Read at least Purpose, Simulation Responsibility, and Owned State from each. Needed for the overlap/authority audit.
5. **Read the authority table** at `scaffold/design/authority.md` — for single-writer rule checks.
6. **Read the interfaces doc** at `scaffold/design/interfaces.md` — for dependency context.
7. **Read all ADRs** — Glob `scaffold/decisions/ADR-*.md`.
8. **Read known issues** at `scaffold/decisions/known-issues.md` (if exists).
9. **Read the glossary** at `scaffold/design/glossary.md` — for terminology compliance.
10. **If `--split-from SYS-###`** — read the parent system document in full. This is the primary context source.
11. **If `--trigger ADR-###`** — read the referenced ADR. If `--trigger KI:keyword` — search `scaffold/decisions/known-issues.md` for the matching entry.

Only read docs that exist — skip missing sources silently.

## Step 2 — ADR Impact Check

Check if any ADRs affect this system's domain:

- Did an ADR change ownership boundaries that create room for this system?
- Did an ADR add constraints that shape what this system should or shouldn't do?
- If `--trigger ADR-###` is provided, that ADR is the primary motivation — summarize it.
- If `--split-from` is provided, check for ADRs affecting the parent system.

Present relevant ADRs before defining the system.

## Step 3 — Overlap and Authority Audit

Before defining the system, verify it has a valid reason to exist. This is a subset of the audit from `/scaffold-bulk-seed-systems`, adapted for a single system.

### 3a. Overlap detection

Compare the proposed system's purpose/responsibility (from the name, argument context, or `--split-from` scope gap) against every existing system's Purpose and Simulation Responsibility. Flag if any existing system already appears to own the same concern.

### 3b. Single-writer check

If the user has described owned state (or it can be inferred from `--split-from`), verify no existing system in `authority.md` or in system docs already claims that state.

### 3c. Invariant check

Verify the proposed system doesn't imply mechanics that violate Design Invariants or Design Boundaries from the design doc.

### 3d. Simulation Depth check

Verify the proposed system is consistent with the Simulation Depth Target. Don't create a deeply granular system when the design says "moderate simulation."

### 3e. Layer boundary check

Verify this is a gameplay simulation system, not a presentation concern (UI rendering, HUD layout), input concern (key bindings, controller mapping), or engine concern (scene management, performance). Those belong to Steps 4–6, not Step 2.

### 3f. Split validation (when --split-from is provided)

Verify the split makes sense:
- Does the parent system show scope pressure (accumulated edge cases, identity drift, or emergent subsystem signals)?
- Is the proposed separation clean — does each system have a distinct simulation responsibility after the split?
- Present the parent system's current scope alongside the proposed new system's scope so the user can see the boundary.

### 3g. Authority flow validation

If the project uses a layered simulation model (e.g., Colony → Region → World), verify this system's proposed interactions follow the allowed flow direction:

- Does this system introduce any cross-layer interactions?
- Do they follow the allowed direction defined in the design doc's architecture or authority model?
- Any direct layer skips (e.g., Colony → World bypassing Region) are invalid unless explicitly allowed by an ADR or Design Invariant.

If no layered model is defined in the design doc, skip this check.

### 3h. Necessity check

This is the most important gate. Answer three questions:

1. **What gameplay problem does this system solve that cannot be solved by extending an existing system?** If an existing system could absorb this responsibility with minor scope expansion, that's the better path.
2. **What breaks if this system does NOT exist?** If nothing breaks — if gameplay still works, just less cleanly organized — the system is premature.
3. **Is this needed NOW (current phase), or is it future scope?** If the current phase doesn't exercise this system's behavior, defer it.

**Result:**
- **Required** — clear gameplay gap, cannot be absorbed by existing systems, needed this phase. Proceed.
- **Premature** — valid concept but not needed yet. Stop: "This system addresses a real concern but isn't needed until [phase/slice]. Log it in `scaffold/decisions/known-issues.md` as a future system candidate and revisit when its phase begins."
- **Redundant** — an existing system can absorb this. Stop: "SYS-### [Name] already covers this responsibility. Consider expanding it via `/scaffold-update-doc SYS-###` instead."

Present the necessity assessment to the user. If the result is Required, proceed. If Premature or Redundant, present the recommendation but let the user override with justification.

### 3i. Present audit results

```
## Audit Results

| Check | Result |
|-------|--------|
| Overlap with existing systems | [None / Flagged: SYS-### — describe overlap] |
| Single-writer conflicts | [None / Flagged: state X claimed by SYS-###] |
| Invariant compliance | [Compliant / Flagged: violates Invariant X] |
| Simulation depth | [Consistent / Flagged: exceeds stated depth] |
| Layer boundary | [Simulation layer / Flagged: belongs to Step N] |
| Authority flow | [Valid / Flagged: layer skip X → Z / N/A — no layered model] |
| Split clarity (if applicable) | [Clean separation / Flagged: ambiguous boundary] |
| Necessity | [Required / Premature / Redundant] |

**Options:** Proceed / Adjust boundaries / Merge with SYS-### / Defer / Cancel
```

Wait for user confirmation before proceeding. If overlap, authority conflicts, or necessity issues are found, present options and let the user decide.

## Step 4 — Classify

1. If `--split-from` is provided, infer the gameplay domain from the parent system.
2. Otherwise, infer from the argument and the design doc's Major System Domains.
3. Classify against the system categories from `/scaffold-bulk-seed-systems`:
   - Actors, World State, Resources & Economy, Tasks & Coordination, Construction & Transformation, Conflict & Consequences, Progression & Meta, Events & Pressure, Player Oversight
4. Present inferred classification for user confirmation.

## Step 5 — Define the System

Walk through the system template sections one at a time. Pre-fill from context where possible — especially when `--split-from` or `--trigger` provides strong signal. Write answers into the system doc immediately after each section is confirmed.

1. **Purpose** — Ask: *"In one sentence, what player-visible behavior does this system own?"* If `--split-from`, pre-fill from the parent system's scope gap.
2. **Simulation Responsibility** — Ask: *"What state does this system uniquely own and update?"* If `--split-from`, pre-fill from the responsibility being extracted from the parent.
3. **Player Intent** — Ask: *"What is the player trying to accomplish when they engage with this system?"*
4. **Design Constraints** — Pre-fill from Design Invariants and Boundaries that apply to this domain. Ask for confirmation.
5. **Visibility to Player** — Ask: *"What parts of this system are visible, partially visible, or hidden?"*
6. **Player Actions** — Ask: *"Step by step, what does the player actually do?"*
7. **System Resolution** — Ask: *"What happens after the player acts? How does the game world respond?"*
8. **State Lifecycle** — Ask: *"What are the major states from the player's perspective? Are there any temporal discontinuities — moments where behavior changes non-obviously over time (e.g., gradual decay, threshold triggers, delayed effects)?"*
9. **Failure / Friction States** — Ask: *"What can go wrong? What does the player see?"*
10. **Owned State** — Ask: *"What gameplay state does this system exclusively own?"* Cross-reference with audit results from Step 3. Flag any state that authority.md doesn't yet cover — this feeds the authority registration gate in Step 6b.
11. **Upstream Dependencies** — Pre-fill from known system interactions and interfaces. For each dependency, ask: *"Does this system pull data from the source, or does the source push to it?"* Clarify direction.
12. **Downstream Consequences** — Pre-fill from known system interactions and interfaces. For each consequence, ask: *"Does this system push state out, or do consumers pull from it?"* Clarify direction.
13. **Non-Responsibilities** — Ask: *"What does this system explicitly NOT own?"* If `--split-from`, pre-fill with the parent system's retained responsibilities that this system does NOT take over.
14. **Edge Cases & Ambiguity Killers** — Ask: *"What questions would a player or implementer naturally ask? How might a player misuse or exploit this system — what unintended strategies could emerge?"*
15. **Feel & Feedback** — Ask: *"How should this system feel to use?"*
16. **Open Questions** — Ask: *"Any unresolved design questions?"*
17. **Observability & Debug Surface** — Ask: *"What values must be inspectable at runtime? What events should be logged? What debug overlays or UI indicators would help diagnose problems with this system?"* Frame as design-level visibility requirements, not implementation details.
18. **Performance Characteristics** — Ask: *"How often does this system update — every tick, periodically, or event-driven? What is its scope — per entity, per region, or global? Are there obvious scaling risks (e.g., O(n^2) comparisons, large aggregations)?"* Frame as high-level constraints that inform implementation, not implementation prescriptions.

Pre-filled content is a starting point. Always present pre-filled content for user confirmation — never treat it as final.

## Step 5b — Identity Check

After all sections are defined, validate that the system has a clear identity boundary. This prevents "soft systems" that bleed responsibilities over time.

1. **One-sentence test** — Can this system's Purpose be described in one sentence without "and" or "also"? If it needs a conjunction, it may be two systems.
2. **Absorption test** — If this system were removed, could another single existing system absorb all its responsibilities cleanly? If yes, this system may be redundant.
3. **Core concept test** — Does this system own ONE core concept, or has the definition drifted into multiple concerns during the walkthrough?

**Result:**
- **Strong identity** — passes all three tests. Proceed to file creation.
- **Weak identity** — fails one or more tests. Present the failure to the user:
  - If one-sentence test fails: suggest splitting into two systems or narrowing scope.
  - If absorption test fails: suggest merging with the absorbing system via `/scaffold-update-doc`.
  - If core concept test fails: identify which sections belong to a different concern and suggest refactoring.

The user may override a Weak identity result with justification, but the concern is logged in the system's Open Questions section.

**Marker conventions:**
- If `--split-from`: mark pre-filled sections with `<!-- SPLIT: derived from SYS-### [Parent Name]. Verify and expand. -->`
- If `--trigger`: mark pre-filled sections with `<!-- SEEDED: derived from [trigger reference]. Verify and expand. -->`
- Otherwise: mark pre-filled sections with `<!-- SEEDED: derived from design doc. Verify and expand. -->`

## Step 6 — Create the System File

Create `scaffold/design/systems/SYS-###-<name>_draft.md` where:
- `SYS-###` is the next sequential ID from the index
- `<name>` is lowercase-kebab-case
- Populate all sections from the user's confirmed answers
- Set header fields: Authority Rank 5, Layer Canon, Status Draft
- Set `Created` and `Last Updated` to today's date
- Add Changelog entry:
  - Default: `- YYYY-MM-DD: Created.`
  - If `--split-from`: `- YYYY-MM-DD: Created (split from SYS-### [Parent Name]).`
  - If `--trigger`: `- YYYY-MM-DD: Created (triggered by [trigger reference]).`

## Step 6b — Authority Registration Gate

If the system defines any Owned State entries, `design/authority.md` MUST be updated before proceeding. Unregistered owned state silently breaks the single-writer rule — other skills and systems won't know this state is claimed.

1. **Check** — does the new system's Owned State table have entries?
2. **If yes** — update `design/authority.md` to register each owned state entry under this system's SYS-### ID using the Edit tool. Add rows to the authority table with the system as the single writer.
3. **If authority.md doesn't exist yet** — skip this gate (it will be created by `/scaffold-bulk-seed-references`).
4. **If the owned state conflicts with an existing authority entry** — this should have been caught in Step 3b. If it wasn't, STOP and escalate to the user before writing the file.

This is not a suggestion — it is a gate. Do not proceed to Step 7 with unregistered owned state when `authority.md` exists.

## Step 7 — Register

1. Add a row to `scaffold/design/systems/_index.md` with Status Draft.
2. Add a row to the System Design Index in `scaffold/design/design-doc.md`.

Both indexes must match — this is the dual-registration rule for systems.

## Step 8 — Update Parent System (if --split-from)

When `--split-from SYS-###` was provided, update the parent system:

1. **Non-Responsibilities** — add the extracted concern with ownership reference: "[Concern] (owned by SYS-### [New System Name])"
2. **Downstream Consequences** — add the new system if it receives state from the parent.
3. **Upstream Dependencies** — add the new system if the parent now depends on it.
4. **Last Updated** — set to today's date.
5. **Changelog** — append: `- YYYY-MM-DD: Split [concern] to SYS-### [New System Name].`

**Scope of parent edits is strictly bounded:**
- Never change the parent's Purpose or Simulation Responsibility — those define what the parent system is.
- Never remove Owned State from the parent — if state ownership transferred, that's an escalation for the user to resolve via `/scaffold-update-doc` or triage.
- Only add Non-Responsibilities entries and update dependency tables.

## Step 9 — Report

```
## System Created

### Summary
| Field | Value |
|-------|-------|
| ID | SYS-### |
| Name | [System Name] |
| File | `design/systems/SYS-###-<name>_draft.md` |
| Category | [classification from Step 4] |
| Split from | [SYS-### or —] |
| Trigger | [ADR-###, KI:keyword, or —] |

### Audit Summary
| Check | Result |
|-------|--------|
| Overlap | [None / Resolved] |
| Authority | [Clean / Resolved] |
| Invariants | [Compliant] |
| Simulation depth | [Consistent] |
| Layer boundary | [Simulation layer] |
| Authority flow | [Valid / N/A] |
| Necessity | [Required] |
| Identity | [Strong / Weak — overridden with justification] |
| Authority registration | [Updated / N/A — no owned state or no authority.md] |

### ADRs Considered
- [List ADRs that influenced the system, or "None"]

### Parent System Changes (if --split-from)
- [What was updated in the parent system]

### Next Steps
- Run `/scaffold-fix-systems SYS-###` to clean up mechanical issues
- Run `/scaffold-iterate systems SYS-###` to adversarially review the new system
- Run `/scaffold-validate --scope systems` to confirm structural readiness
- Update `design/interfaces.md` if the system interacts with others → `/scaffold-update-doc interfaces`
```

## Rules

- **Ask one section at a time.** Do not dump all questions at once.
- **Write answers into the system doc immediately** after each section is confirmed.
- **ADR check is mandatory** — never skip it, even if no ADRs exist yet (report that none were found).
- **Overlap and authority audit is mandatory** — never skip it. The audit prevents creating systems that conflict with existing ones.
- **Pre-fill from context where possible**, but always present pre-filled content for user confirmation.
- **Systems describe BEHAVIOR, not IMPLEMENTATION.** No code, no engine constructs, no class names, no signals, no methods, no nodes.
- **System names are nouns, not verbs.** "Construction" not "Building things."
- **IDs are sequential and permanent** — never skip or reuse.
- **Never overwrite an existing system file.**
- **Keep both indexes in sync** — `systems/_index.md` and the design doc System Design Index must both be updated.
- **Created documents start with Status: Draft.**
- **If no argument is provided**, ask the user for a system name before proceeding.
- **When invoked from `revise-systems`**, honor the provided context (`--split-from`, `--trigger`) but still walk through all sections — don't skip the interactive definition.
- **Respect the Simulation Depth Target.** Don't create deeply granular systems when the design says moderate.
- **Respect Design Invariants.** A system that implies mechanics violating an invariant is a contradiction.
- **Only create gameplay simulation systems.** Presentation, input, or engine concerns belong to Steps 4–6, not Step 2.
- **Parent system edits are bounded.** When `--split-from` is used, only add Non-Responsibilities entries and update dependency tables. Never change the parent's Purpose, Simulation Responsibility, or Owned State.
- **Owned State entries require explicit confirmation.** Because owned state defines authority boundaries, never auto-fill Owned State from inference alone — always present proposed entries for user confirmation.
- **Necessity check is mandatory.** Every new system must justify its existence: what problem it solves, what breaks without it, and whether it's needed now. Premature and redundant systems are stopped with a recommendation, not silently created.
- **Identity check is mandatory.** After definition, every system must pass the one-sentence, absorption, and core-concept tests. Weak identity is flagged and the user must acknowledge or refactor.
- **Authority registration is a gate, not a suggestion.** When `authority.md` exists and the system defines owned state, the authority table must be updated before registration. Unregistered owned state breaks the single-writer contract.
- **Authority flow must follow the project's simulation model.** If the design doc defines a layered authority flow (e.g., Colony → Region → World), new systems must not skip layers. Direct layer skips are invalid unless backed by an ADR.
- **Observability and performance sections use design-level language.** "What must be inspectable" not "add a debug panel." "Expected update frequency" not "use a coroutine." Keep these sections in the behavior layer.

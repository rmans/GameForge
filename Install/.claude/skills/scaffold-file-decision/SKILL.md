---
name: scaffold-file-decision
description: File an ADR (Architecture Decision Record), KI (Known Issue), or DD (Design Debt) entry. Assigns the next sequential ID, fills the template from provided context, registers in the appropriate index, and cross-references affected documents. Use when implementation friction, review findings, or design gaps need to be formally recorded.
argument-hint: --type adr|ki|dd "title or description"
allowed-tools: Read, Edit, Write, Grep, Glob
---

# File a Decision Document

Create an ADR, KI, or DD entry from the provided context: **$ARGUMENTS**

Decision documents are the project's feedback mechanism. They record why decisions were made (ADR), what's unresolved (KI), and what compromises exist (DD). Every decision doc must trace back to what triggered it and forward to what it affects.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--type` | Yes | — | `adr` (Architecture Decision Record), `ki` (Known Issue), or `dd` (Design Debt) |
| title/description | Yes | — | Brief title or description of the decision/issue/debt. Can be a quoted string or free-form text after the type flag. |
| `--triggered-by` | No | — | What prompted this filing (e.g., `TASK-015`, `iterate-systems SYS-005`, `code-review CR-003`). If not provided, ask the user. |
| `--blocking` | No | — | (KI only) What this blocks: `SLICE-###`, `P#-###`, system name, `future`, or `—`. |
| `--priority` | No | Medium | (DD only) `High`, `Medium`, or `Low`. |
| `--status` | No | Proposed (ADR) / Open (KI) / Active (DD) | Initial status. ADRs start as Proposed; use `--status accepted` to file as already decided. |

## Phase 1 — Gather Context

1. **Determine the type** from `--type`. If missing, ask the user: "What are you filing? (a) ADR — a decision that changes how something works, (b) KI — something unresolved, ambiguous, or broken, (c) DD — an intentional compromise you're living with for now."

2. **Read existing entries** to assign the next sequential ID:
   - ADR: Glob `decisions/architecture-decision-record/ADR-*.md` → next ADR-###
   - KI: Glob `decisions/known-issues/KI-*.md` → next KI-###
   - DD: Glob `decisions/design-debt/DD-*.md` → next DD-###

3. **Read the relevant template:**
   - ADR: `scaffold/templates/decision-template.md`
   - KI: `scaffold/templates/known-issue-entry-template.md`
   - DD: `scaffold/templates/design-debt-entry-template.md`

4. **Gather context from the user.** Based on the type, collect the information needed to fill the template. Use the title/description provided in the arguments as a starting point, then ask for missing pieces:

   **For ADR:**
   - What situation or conflict prompted this? (Context)
   - What was decided? (Decision — be concrete)
   - What alternatives were considered? (at least 1)
   - What documents need to change? (Updated Documents)
   - What are the positive and negative consequences?
   - Is there implementation scope? (Scope & Migration — or skip for design-only)

   **For KI:**
   - What's wrong, missing, or ambiguous? (Description)
   - What category? Gap / Conflict / TBD / Ambiguity
   - What documents are affected?
   - What are the fix options? (at least 2 if known)
   - Does this block anything?

   **For DD:**
   - What's the compromise? (Compromise)
   - Why is it acceptable for now? (Why Accepted)
   - What documents are affected?
   - What's the payoff plan — when and how will this be fixed?
   - What area does this affect? (System/domain)

   If the user provided enough context in the arguments or conversation to fill these fields, don't re-ask — just confirm: "I have enough context to file this. Here's what I'll write: [summary]. Proceed?"

## Phase 2 — Write the Entry

1. **Create the file** from the template with all fields filled:
   - Replace `###` with the assigned ID
   - Replace `[Decision/Issue/Debt Title]` with the title
   - Set dates to today
   - Fill ALL template sections with substantive content — no HTML comments or TODOs left in sections that have content. Remove template instruction comments and replace with authored prose.
   - Set the `Triggered by` field from `--triggered-by` or the user's answer
   - For ADRs with `--status accepted`: set Status to `Accepted` and use `_accepted` filename suffix

2. **File location and naming:**
   - ADR: `decisions/architecture-decision-record/ADR-###-<slug>_proposed.md` (or `_accepted`)
   - KI: `decisions/known-issues/KI-###-<slug>.md`
   - DD: `decisions/design-debt/DD-###-<slug>.md`
   - Slug: lowercase, hyphens, no special characters, max 50 chars

3. **Register in the index:**
   - ADR: Add row to `decisions/architecture-decision-record/_index.md`
   - KI: Add row to `decisions/known-issues/_index.md`
   - DD: Add row to `decisions/design-debt/_index.md`

## Phase 3 — Cross-Reference

After filing, update affected documents:

**For ADR (Accepted):**
- If the ADR explicitly changes a design doc section → note it, but do NOT edit the design doc here. That's the job of `revise-design` or manual update. Log: "ADR-### accepted — run `/scaffold-revise-design` or manually update design-doc.md to reflect this decision."
- If the ADR affects system designs → same: note which systems, don't edit them. Log which systems need updating.
- Add to the roadmap's ADR Feedback Log if a roadmap exists.

**For KI:**
- If the KI blocks a specific slice or phase → add a note in that doc's Dependencies or Notes section referencing KI-###.
- If the KI was triggered by a validate finding → reference the finding ID.

**For DD:**
- If the DD has a payoff plan targeting a specific phase/slice → add a note in that phase/slice referencing DD-###.

## Phase 4 — Report

```
## Decision Filed

| Field | Value |
|-------|-------|
| Type | ADR / KI / DD |
| ID | ADR-### / KI-### / DD-### |
| Title | [title] |
| Status | Proposed / Open / Active |
| Triggered by | [source] |
| Blocking | [what it blocks, or "—"] |
| File | decisions/[subdir]/[filename].md |

### Affected Documents
| Document | Impact |
|----------|--------|
| [path] | [what needs to change or is affected] |

### Next Steps
- [context-specific next steps]
```

## Rules

- **Never file without user confirmation.** Present the summary before writing.
- **IDs are sequential and permanent.** Never skip or reuse. Check existing files to find the next available ID.
- **Every entry must have a trigger.** If `--triggered-by` wasn't provided and the user can't name one, use "manual filing" — but this is rare. Most decision docs come from somewhere.
- **ADRs don't edit upstream docs directly.** An ADR records the decision and lists what needs to change. The actual changes to design docs, system docs, etc. happen through revise skills or manual edits. This prevents decision filing from becoming a backdoor for unreviewed design changes.
- **KIs should have fix options when possible.** An issue with no options is still valid (category: TBD), but issues with concrete options are more actionable.
- **DD entries must have a payoff plan.** "Fix it later" is not a plan. Name a trigger condition, phase, or slice. If the payoff is genuinely unknown, say so explicitly: "Payoff trigger: unknown — revisit during Phase N planning."
- **Don't duplicate.** Before filing, check if a similar ADR/KI/DD already exists. If one does, suggest updating it instead of creating a duplicate.
- **Slug must be descriptive.** `ADR-015-flat-scene-tree` is good. `ADR-015-decision` is not.
- **Cross-references use the ID, not the filename.** Other docs reference `ADR-###`, `KI-###`, `DD-###` — not file paths.
- **Filing a KI does not block progress by default.** Only KIs with an explicit `Blocking` field stop downstream work. A KI with Blocking: `—` is tracked but non-blocking.
- **Update VERSION.md** with a patch bump and changelog entry noting the filing.

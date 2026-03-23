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
| `--context` | No | — | (ADR) What situation prompted this. (KI) What's wrong. (DD) What's compromised. Calling skills pass this to skip the interview. |
| `--decision` | No | — | (ADR only) What was decided. |
| `--alternatives` | No | — | (ADR only) Alternatives considered, comma-separated or multi-line. |
| `--consequences` | No | — | (ADR only) Positive and negative consequences. |
| `--affected` | No | — | Comma-separated list of affected document paths. |
| `--fix-options` | No | — | (KI only) Fix options, comma-separated. |
| `--blocking` | No | — | (KI only) What this blocks: `SLICE-###`, `P#-###`, system name, `future`, or `—`. |
| `--compromise` | No | — | (DD only) What's wrong and what you're living with. |
| `--why-accepted` | No | — | (DD only) Why acceptable for now. |
| `--payoff-when` | No | — | (DD only) When this gets fixed (phase, slice, trigger). |
| `--payoff-how` | No | — | (DD only) How the fix looks. |
| `--priority` | No | Medium | (DD only) `High`, `Medium`, or `Low`. |
| `--status` | No | Proposed (ADR) / Open (KI) / Active (DD) | Initial status. ADRs start as Proposed; use `--status accepted` to file as already decided. |
| `--skip-review` | No | false | Skip the automatic review after filing. Use when the calling skill will handle review separately. |

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

4. **Gather context.** Check which arguments were provided. If all required fields for the type have values (from arguments or the calling skill's context), skip the interview and go to confirmation.

   **Required fields per type:**

   | Type | Required | Optional |
   |------|----------|----------|
   | ADR | `--context`, `--decision` | `--alternatives`, `--consequences`, `--affected` |
   | KI | `--context` | `--fix-options`, `--blocking`, `--affected` |
   | DD | `--context` (or `--compromise`), `--payoff-when` | `--why-accepted`, `--payoff-how`, `--affected` |

   **If all required fields are provided** (common when called by another skill):
   - Skip the interview
   - Confirm: "Filing [type] from [triggered-by]. Here's what I'll write: [summary]. Proceed?"
   - This enables seamless chaining — triage-specs can file a KI without stopping for an interview

   **If required fields are missing** (common when called by the user directly):
   - Ask only for the missing pieces. Don't re-ask for fields already provided.

   **Full interview questions (when needed):**

   **For ADR:**
   - What situation or conflict prompted this? (`--context`)
   - What was decided? (`--decision` — be concrete)
   - What alternatives were considered? (`--alternatives` — at least 1)
   - What documents need to change? (`--affected`)
   - What are the positive and negative consequences? (`--consequences`)
   - Is there implementation scope? (Scope & Migration — or skip for design-only)

   **For KI:**
   - What's wrong, missing, or ambiguous? (`--context`)
   - What category? Gap / Conflict / TBD / Ambiguity
   - What documents are affected? (`--affected`)
   - What are the fix options? (`--fix-options` — at least 2 if known)
   - Does this block anything? (`--blocking`)

   **For DD:**
   - What's the compromise? (`--compromise` or `--context`)
   - Why is it acceptable for now? (`--why-accepted`)
   - What documents are affected? (`--affected`)
   - What's the payoff plan — when and how? (`--payoff-when`, `--payoff-how`)
   - What area? (System/domain)

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

## Phase 4 — Review

Unless `--skip-review` is set, automatically run the review pipeline on the new decision doc:

```
/scaffold-review <type> <ID>
```

Where `<type>` is `adr`, `ki`, or `dd` and `<ID>` is the newly created entry (e.g., `ADR-015`, `KI-007`, `DD-003`).

This chains fix → iterate → validate on the decision doc:
- **Fix:** Cleans up template text, glossary compliance, missing sections
- **Iterate:** External LLM reviews: is the decision sound? are alternatives honest? are consequences complete?
- **Validate:** Structural checks pass

If the user filed with `--status accepted` (ADR), the review is especially important — an accepted ADR that's vague will cause downstream confusion.

If `--skip-review` is set, skip this phase. Use when the calling skill handles review separately or when filing a batch of related decisions that will be reviewed together.

## Phase 5 — Report

```
## Decision Filed and Reviewed

| Field | Value |
|-------|-------|
| Type | ADR / KI / DD |
| ID | ADR-### / KI-### / DD-### |
| Title | [title] |
| Status | Proposed / Open / Active |
| Triggered by | [source] |
| Blocking | [what it blocks, or "—"] |
| File | decisions/[subdir]/[filename].md |
| Review | PASS / WARN / FAIL |

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

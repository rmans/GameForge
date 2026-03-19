---
name: scaffold-update-doc
description: Add, remove, or modify entries in any scaffold document. Updates cross-references and indexes automatically.
argument-hint: [doc-name or path]
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Update Scaffold Document

Make targeted edits to a scaffold document: **$ARGUMENTS**

## Supported Documents

| Argument | File | Entry Format |
|----------|------|-------------|
| `design-doc` | `scaffold/design/design-doc.md` | Sections with content |
| `style-guide` | `scaffold/design/style-guide.md` | Sections with content |
| `color-system` | `scaffold/design/color-system.md` | Sections with content |
| `ui-kit` | `scaffold/design/ui-kit.md` | Sections with content |
| `glossary` | `scaffold/design/glossary.md` | Table rows (Term, Definition, NOT, Authority, Criticality). Also: Deprecated Terms table, Term Hierarchy table. |
| `interfaces` | `scaffold/design/interfaces.md` | Interface contracts |
| `authority` | `scaffold/design/authority.md` | Table rows (Variable, Owning System, Readers, Cadence) |
| `state-transitions` | `scaffold/design/state-transitions.md` | State machine blocks |
| `entities` | `scaffold/reference/entity-components.md` | Entity component tables |
| `resources` | `scaffold/reference/resource-definitions.md` | Resource table rows |
| `signals` | `scaffold/reference/signal-registry.md` | Signal/intent table rows |
| `balance` | `scaffold/reference/balance-params.md` | Parameter table rows |
| `known-issues` | `scaffold/decisions/known-issues.md` | Issue entries |
| `design-debt` | `scaffold/decisions/design-debt.md` | Debt entries |
| `playtest-feedback` | `scaffold/decisions/playtest-feedback.md` | Feedback entries |
| `architecture` | `scaffold/design/architecture.md` | Sections with content |
| `action-map` | `scaffold/inputs/action-map.md` | Action entries |
| Any `SYS-###` ID | `scaffold/design/systems/SYS-###-*.md` | System design sections |
| Any file path | Direct path within `scaffold/` | Depends on doc type |

## Steps

### 1. Identify Target

1. Match the argument to a supported document above.
2. If the argument is a SYS-### ID, find the matching system file.
3. If the argument is a file path, use it directly.
4. If no argument or unrecognized, list the options and ask the user which doc to update.

### 2. Read the Target Doc

1. Read the target doc in full.
2. Identify its format — table-based, section-based, or mixed.
3. Summarize the current state to the user: how many entries, which sections, etc.

### 3. Ask What to Do

Ask the user: *"What would you like to do?"*

- **Add** — add a new entry, row, section, or block
- **Remove** — remove an existing entry, row, section, or block
- **Modify** — change an existing entry's content

If the user's initial message already specifies the action, skip this question and proceed.

### 4. Execute the Edit

Depending on the doc type and action:

**Table-based docs** (glossary, authority, entities, resources, signals, balance, action-map):
- **Add:** Ask for the required fields. Validate format matches the table schema. Insert in the correct position (alphabetical for glossary, grouped by system for balance params, etc.).
- **Remove:** Show matching entries and confirm which one to remove. Warn if the entry is referenced by other docs.
- **Modify:** Show the current entry, ask what to change, write the update.

**Section-based docs** (design-doc, style-guide, color-system, ui-kit, system designs):
- **Add:** Ask which section to add content to, or if adding a new section entirely. Write content into the section, replacing TODO markers if present.
- **Remove:** Confirm which section or content to remove. Replace with a TODO marker rather than deleting the section header.
- **Modify:** Show the current section content, ask what to change, write the update.

**State machines** (state-transitions):
- **Add:** Ask for the entity name, states, transitions, and triggers. Create a new state machine block.
- **Remove:** Show existing state machines, confirm which to remove.
- **Modify:** Show the current state machine, ask what to change (add/remove states, transitions, triggers).

**Issue/debt tracking** (known-issues, design-debt):
- **Add:** Ask for the issue description, severity, and related system/doc.
- **Remove:** Show existing entries, confirm which to remove or mark as resolved.
- **Modify:** Show the current entry, ask what to change.

### 5. ADR Changelog Entry

If the user mentions an ADR as the reason for the edit, add a changelog entry to the modified document's blockquote header:

```
> **Changelog:** ADR-### (YYYY-MM-DD): Brief description of what changed
```

If the document already has a `> **Changelog:**` line, append the new entry after the existing ones (comma-separated or on a new `>` line).

### 6. Update Cross-References

After making the edit, check and update related docs:

**Glossary changes:**
- If a term is renamed, grep all scaffold docs for the old term and flag occurrences.
- If a term is removed, warn if it's still used in other docs.

**Authority changes:**
- If a variable is added/removed, check `scaffold/reference/entity-components.md` for matching Authority column entries.

**System changes (add/remove/rename):**
- Update `scaffold/design/systems/_index.md`.
- Update the System Design Index in `scaffold/design/design-doc.md`.
- If removing a system, warn about references in other systems' Inputs/Outputs tables, authority.md, signal-registry.md, and balance-params.md.

**Signal changes:**
- If a signal is added/removed, check system Outputs tables for alignment.
- Check `scaffold/design/interfaces.md` for matching contracts.

**Entity changes:**
- If an entity is added/removed, check `scaffold/design/state-transitions.md` for matching state machines.
- Check `scaffold/design/authority.md` for matching authority entries.

**Resource changes:**
- If a resource is added/removed, check system designs for references.
- Check `scaffold/reference/balance-params.md` for related parameters.

**Balance param changes:**
- If a parameter is added/removed, check the owning system for references.

**Architecture changes:**
- If the scene tree, dependency graph, tick order, signal wiring, or code patterns change, check that `scaffold/engine/scene-architecture.md` and `scaffold/engine/coding-best-practices.md` don't contradict.
- If a new system is added/removed from the dependency graph or tick order, check that the system is registered in `scaffold/design/systems/_index.md` and `scaffold/reference/signal-registry.md`.

**State machine changes:**
- If a state machine is added/removed, check `scaffold/reference/entity-components.md` for matching state/status fields.

### 7. Report

Show the user:
- What was changed and where
- Any cross-references that were updated
- Any cross-references that need manual attention (warn but don't auto-fix if uncertain)

## Rules

- **Always confirm before writing.** Show the proposed edit and ask for confirmation.
- **Never silently break cross-references.** If removing an entry that's referenced elsewhere, warn the user and list every reference before proceeding.
- **Preserve formatting.** Match the existing table alignment, heading style, and whitespace conventions in the target doc.
- **Respect authority.** This skill can edit any doc, but remind the user if they're modifying a higher-authority doc that lower docs depend on.
- **One edit at a time.** If the user wants multiple changes, complete one full cycle (edit → cross-reference → report) before starting the next.
- **Don't auto-fix uncertain cross-references.** If a cross-reference update requires judgment (e.g., renaming a term in a system design where context matters), flag it for the user instead of silently changing it.
- **Alphabetical order for glossary.** Always maintain alphabetical ordering when adding glossary entries.
- **Grouped by system for balance params.** Maintain system grouping when adding balance parameters.

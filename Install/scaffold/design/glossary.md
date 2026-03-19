# Glossary

> **Authority:** Rank 2
> **Layer:** Canon
> **Conforms to:** [design-doc.md](design-doc.md)
> **Status:** Draft

---

## Purpose

Canonical terminology for this project. When a term is defined here, all documents, code, and conversations must use it consistently. The "NOT" column is just as important as the definition — it prevents drift toward ambiguous synonyms.

Every canonical term has an **Authority** (the doc that owns its definition) and a **Criticality** level that determines how tightly the term is controlled.

## Terms

<!-- Add terms as they emerge. Alphabetical order. -->

| Term | Definition | NOT (do not use) | Authority | Criticality |
|------|-----------|------------------|-----------|-------------|
| *None yet* | — | — | — | — |

<!-- Column guide:
- Term: The canonical name. Use this exact string everywhere.
- Definition: One sentence. What it means in this project. Disambiguating, not circular.
- NOT: Synonyms that must not be used. Both discouraged wording AND recognized aliases go here.
- Authority: The doc that owns this term's definition (e.g., SYS-003, entity-components, design-doc). Exactly one authority per term.
- Criticality: Core (cross-system, tightly controlled) | Shared (multi-doc, moderate control) | Local (single-system, safe to evolve)
-->

<!-- Example entries:
| Colonist | A player-controlled settler living in the colony | Pawn, NPC, character, unit, villager | design-doc | Core |
| Blueprint | A placed but unbuilt object awaiting construction | Ghost, plan, placeholder, template | SYS-004 | Core |
| Stockpile | A designated zone for storing resources | Warehouse, storage, chest, container | SYS-007 | Shared |
| Mood break | An uncontrolled behavior triggered by critically low mood | Mental break, tantrum, meltdown, snap | SYS-003 | Core |
| Downed | A colonist at 0 HP, incapacitated but not dead | Dead, knocked out, unconscious, KO'd | SYS-010 | Shared |
| Tick | One simulation step (not a rendered frame) | Frame, update, cycle, step | architecture | Core |
-->

## Deprecated Terms

<!-- Terms that were once canonical but have been retired or replaced. Do not delete them — move them here so the history is visible and old references can be traced.

| Term | Replaced By | Deprecated Date | ADR |
|------|-----------|-----------------|-----|
-->

*None yet.*

## Term Hierarchy

<!-- Optional parent-child relationships between terms. Use when a general concept has specific subtypes that also need glossary entries. Not every term needs a parent — only add hierarchy when the relationship is important for disambiguation.

| Term | Parent | Relationship |
|------|--------|-------------|
| Raw Resource | Resource | subtype |
| Processed Resource | Resource | subtype |
-->

*None yet.*

## Rules

1. **If it's in this glossary, use the exact term.** No synonyms in docs or code. Variable names, signal names, UI labels — all match the glossary.
2. **The NOT column is enforced.** If you see a "NOT" term in a document or codebase, replace it with the canonical term.
3. **New terms should be added early.** If you find yourself explaining what a word means, it belongs in the glossary.
4. **Terms can be renamed via ADR.** If a better term emerges, file an ADR, update the glossary, and update all references. The old term moves to Deprecated Terms with a "Replaced By" entry.
5. **Every term has exactly one Authority.** The authority doc owns the definition. If the term's meaning needs to change, the authority doc is where the change starts. Other docs conform to the glossary.
6. **Criticality drives review effort.** Core terms require ADR-level governance to change. Shared terms should be reviewed across affected docs. Local terms can evolve within their owning system.
7. **Deprecated terms are never deleted.** They move to the Deprecated Terms section with a replacement reference. This preserves traceability for old docs and changelogs.

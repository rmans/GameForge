---
name: scaffold-sync-glossary
description: Scan scaffold docs for domain terms missing from the glossary and propose additions with worthiness gating, ambiguity detection, and confidence tiers. Supports canonical, alias, NOT-entry, and reject decisions per term. Also detects stale glossary terms no longer in use. Use after any bulk-seed step, when validate flags glossary gaps, or standalone anytime.
argument-hint: [--scope all|design|systems|references|style|input] [--dry-run]
allowed-tools: Read, Edit, Grep, Glob
---

# Sync Glossary

Scan scaffold docs for domain terms that should be in the glossary but aren't: **$ARGUMENTS**

The glossary gets its initial population in Step 2 (`bulk-seed-systems`), but every subsequent step introduces new domain terms — entity names, resource types, state labels, signal names, interaction patterns. Without periodic syncing, the glossary falls behind the project's actual vocabulary, and terminology drift goes undetected.

This skill extracts candidate terms, filters for glossary-worthiness, checks for ambiguity with existing terms, and presents a batch with per-term decision options (canonical, alias, NOT-entry, or reject). It also detects stale glossary terms that may no longer be in use. It never auto-writes — every change is user-confirmed.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--scope` | No | `all` | Which doc layers to scan. `all` scans everything. Scoped options: `design` (design doc), `systems` (system designs), `references` (Step 3 docs), `style` (Step 5 docs), `input` (Step 6 docs). Multiple scopes can be comma-separated: `--scope references,style`. |
| `--dry-run` | No | — | Report candidates and glossary health without proposing or writing anything. |

## Step 1 — Read Current Glossary

1. **Read** `scaffold/design/glossary.md`.
2. **Build the known-terms set** — all terms in the Terms table (canonical terms AND NOT-column entries). Both are "known" — canonical terms are registered, NOT-column terms are explicitly rejected. Neither should be proposed again.
3. If the glossary doesn't exist, stop: "No glossary found. Run `/scaffold-bulk-seed-systems` first to create and populate the glossary."

## Step 2 — Extract Candidates by Source

Scan docs within the requested scope. For each source type, extract terms from **structured fields** (tables, headers, defined labels) — not from prose. Prose extraction is unreliable; structured fields are authoritative.

Each extracted term carries metadata:
- **Term** — the extracted string
- **Source doc** — which file it came from
- **Source field** — which table/section/header
- **Source weight** — Strong or Advisory (see 2g)
- **First source** — the doc where it was first encountered
- **Source count** — how many docs reference it
- **Layer count** — how many doc layers (design, systems, references, style, input) it spans
- **Authority candidate** — the highest-authority doc that defines this term (based on doc-authority.md rank). This becomes the proposed Authority column value.
- **Contextual definition** — if the source doc provides a definition or description for the term, capture it per source. Multiple sources may define the same term differently — this feeds conflict detection.
- **Dependent docs** — all docs that use this term (not just the source of extraction). Grep all scaffold docs for the term to build the full dependency list.
- **Dependent systems** — SYS-### IDs of systems whose docs reference this term

### 2a. System designs (scope: systems)

Glob `scaffold/design/systems/SYS-###-*.md`. Extract:
- System names (from the `# SYS-### — [Name]` header)
- Owned State names (from the Owned State table's State column)
- State Lifecycle phase names (from State Lifecycle section)
- Non-Responsibility boundary terms (the concern being disclaimed)

### 2b. Reference docs (scope: references)

Extract from structured tables and definition fields:

| Doc | Fields to extract from |
|-----|----------------------|
| `reference/entity-components.md` | Entity type names (row headers), component names |
| `reference/resource-definitions.md` | Resource names, resource category names |
| `reference/signal-registry.md` | Signal names (without technical prefixes), event category names |
| `reference/balance-params.md` | Parameter group names |
| `reference/enums-and-statuses.md` | Enum names, status value names |
| `design/state-transitions.md` | State names, transition trigger names |
| `design/authority.md` | Data domain names (if not already captured from systems) |
| `design/interfaces.md` | Contract names, interaction pattern names |
| `design/architecture.md` | Foundation area names, architectural concept names |

### 2c. Style docs (scope: style)

| Doc | Fields to extract from |
|-----|----------------------|
| `design/style-guide.md` | Tone register names, visual style terms used as labels |
| `design/color-system.md` | Color token names (semantic names like "danger-red", not hex values) |
| `design/ui-kit.md` | UI component names (as game-facing labels, not implementation classes) |
| `design/interaction-model.md` | Interaction pattern names, gesture/action names |
| `design/feedback-system.md` | Feedback event names, priority tier names |
| `design/audio-direction.md` | Audio category names, mood/tone labels |

### 2d. Input docs (scope: input)

| Doc | Fields to extract from |
|-----|----------------------|
| `inputs/action-map.md` | Action names (player-facing labels, not raw IDs like `player_build`) |
| `inputs/input-philosophy.md` | Named principles (if they define terms) |
| `inputs/ui-navigation.md` | Navigation mode names, focus zone names |

### 2e. Design doc (scope: design)

Extract from structured sections only:
- Major System Domain names
- Design Invariant ShortNames (these should already be in the glossary from Step 2 — flag if missing)
- Content Structure category names
- Decision Type names
- Named mechanics from Core Loop and Secondary Loops

### 2f. Repeated unregistered terms (all scopes)

After structured extraction, do a frequency scan across all in-scope docs:
- Find capitalized multi-word terms (e.g., "Colony Mood", "Work Queue") that appear 3+ times across 2+ documents
- Filter out common English words, section headers, and document references
- Filter out terms already captured by structured extraction

### 2g. Source weighting

Not all structured fields produce equally strong glossary candidates. Apply source weighting to control noise:

**Strong candidates** (default propose):
- System names, owned state names, entity names, resource names
- Signal/event names, state names, named mechanics
- Interaction pattern names, Design Invariant ShortNames

**Advisory candidates** (default present but flagged as advisory):
- Color token names, raw enum values, balance parameter group names
- Local UI component names, priority tier names, tone register names
- Audio category names, mood/tone labels
- Navigation mode names, focus zone names

Advisory candidates are promoted to Strong if they appear across 2+ doc layers (indicating cross-layer vocabulary) or if they name a player-facing concept referenced in specs or tasks.

Only read docs that exist — skip missing sources silently.

## Step 3 — Normalize and Deduplicate

### 3a. Naming normalization

Before filtering, normalize candidate variants to prevent near-duplicates from appearing separately:

- **Case normalization** — compare case-insensitively. "Power Grid", "power grid", "PowerGrid" are the same candidate. Keep the most common casing as the proposed form.
- **Punctuation normalization** — "danger-red", "Danger Red", "danger_red" are the same candidate. Keep the form used in the highest-authority source doc.
- **Singular/plural** — "Colonist" and "Colonists" are the same candidate. Keep the singular form.
- **Cluster variants** — group all normalized matches and present the canonical form with variants noted.

### 3b. Deduplication

If the same concept appears from multiple sources:
- Merge into one candidate
- Track all source docs and layers (this feeds breadth tracking)
- Keep the first-encountered source as the primary

## Step 4 — Filter Candidates

Remove from the candidate list:

1. **Already in glossary** — term matches a canonical term or NOT-column entry (case-insensitive).
2. **Pure implementation terms** — class names, node names, signal method names, file paths. The glossary is design-layer vocabulary.
3. **Generic English words** — "system", "state", "action", "type", "level" on their own (but keep compound terms like "Mood Level" or "Action Map").
4. **Draft-only provisional terms** — terms that appear only in Draft-status docs with no Approved or Complete references. These are unstable and may change. Flag as blocked candidates (see Step 4c).

### 4a. Glossary worthiness gate

This is the most important filter. A candidate term is only eligible if **at least one** is true:

- It appears across **2+ document layers** (shared cross-layer vocabulary)
- It names a **player-facing concept** (something the player sees, does, or decides about)
- It names a **simulation concept with cross-doc authority significance** (owned state, entity type, resource type)
- It is **required to disambiguate** similar concepts (two terms that could be confused need glossary entries to distinguish them)
- It is **referenced by validation, review, or revision workflows** as shared vocabulary

**Reject or downgrade to advisory** if:
- It is **local to one doc only** and not a player-facing or authority-significant concept
- It is **purely presentational or cosmetic** (a visual label with no behavioral meaning)
- It is an **implementation convenience label** (a grouping header, a table column name)
- It is a **narrow table-local value** with no broader vocabulary role (e.g., an enum value only used in one system's state machine)

Terms that fail the worthiness gate are excluded from the proposal. They are listed in the report under "Filtered (not glossary-worthy)" so the user can see what was considered and why it was excluded.

### 4b. Pressure test

For each candidate that passes the worthiness gate, apply an active challenge:

1. **Does this term reduce ambiguity or increase it?** If adding this term would create confusion with existing terms or concepts, it may do more harm than good.
2. **Would removing this term simplify the project vocabulary?** If the concept is clear without a dedicated term, it doesn't need one.
3. **Is this concept better expressed as:**
   - An **attribute** of an existing term? (e.g., "Colony Mood Level" might be an attribute of "Colony" or "Mood", not a standalone term)
   - A **parameter** in balance-params? (e.g., "Base Construction Speed" is a tunable, not a glossary concept)
   - A **state** in state-transitions? (e.g., "Dazed" might be a state value, not a term)

If any of these apply, downgrade the candidate to advisory or suggest the alternative representation. The user can still override to Canonical.

### 4c. Ambiguity and collision check

For each surviving candidate, check for collision or confusion with existing glossary terms:

- **Near-equivalent** — does a glossary term with similar meaning already exist? (e.g., candidate "Alert" when "Warning" is already canonical)
- **Prefix/suffix variant** — does the candidate differ from an existing term only by prefix, suffix, or pluralization? (e.g., candidate "Task Queue" when "Task" is canonical)
- **Cross-layer confusion** — could this term be confused with a term used differently in another layer? (e.g., "Priority" meaning severity in feedback-system but ordering in task-system)

For each collision detected:
- Flag the candidate as an **ambiguity risk**
- Suggest a resolution: merge with existing term, add as alias, add to NOT column, or differentiate with a disambiguating definition

### 4d. Definition conflict detection

If a candidate term appears with **different contextual definitions** across source docs, flag it as a definition conflict:

```
### Definition Conflict: [Term]

| Source | Definition / Usage |
|--------|-------------------|
| SYS-003 | Numeric happiness value for a colonist |
| balance-params | Composite state including stress + satisfaction |
| feedback-system | Visual indicator of colonist emotional state |

**Resolution required before Canonical:**
a) Align all sources to one definition (the Authority source wins)
b) Split into multiple terms with disambiguating prefixes
c) Choose one definition and file ADRs to correct the others
```

A term with unresolved definition conflicts **cannot** be added as Canonical. The user must resolve the conflict first or defer the term.

### 4e. Cross-layer semantic drift detection

When a term appears across multiple doc layers, compare how it's used in each layer:

- **Same meaning, different emphasis** — acceptable. (e.g., "Blueprint" means the same thing in systems vs specs, just described at different levels of detail)
- **Different meaning per layer** — flag as **semantic drift risk**. (e.g., "Priority" meaning execution order in task-system but visual emphasis in UI)

For semantic drift:
- Present the per-layer meanings side by side
- Suggest: split into layer-qualified terms (e.g., "Task Priority" vs "Alert Priority"), add one to NOT column, or confirm the overloaded usage is intentional

### 4f. Assign authority and criticality

For each candidate:

**Authority** — identify the single doc that should own this term's definition:
- The highest-ranked doc (per `doc-authority.md`) that defines or describes this term is the authority candidate
- If multiple same-rank docs define it, flag for user decision
- Rule: every canonical term must have exactly one authority source

**Criticality:**
- **Core** — cross-system term used by 3+ systems or referenced by Design Invariants/authority.md. Changes require ADR-level governance.
- **Shared** — multi-doc term spanning 2+ layers or 2+ systems. Changes should be reviewed across affected docs.
- **Local** — single-system or single-layer term. Safe to evolve within its owning context.

**Hierarchy (optional):**
- If the term is a subtype of an existing glossary term (e.g., "Raw Resource" → parent "Resource"), note the parent relationship. Present for user confirmation — don't auto-assign hierarchy.

### 4g. Blocked candidates

Terms extracted from Draft-only docs that have no Approved/Complete references are blocked:
- Do not propose them
- List them in the report as "Blocked — awaiting upstream stabilization"
- Note which doc(s) need to stabilize before the term is eligible

### 4h. Assign confidence tier

| Tier | Criteria | Presentation |
|------|----------|-------------|
| **High** | Extracted from canonical structured fields (system names, owned state, entity/resource/signal names) with Strong source weight | Propose directly |
| **Medium** | Extracted from labeled but narrower fields (style registers, component names, interaction labels) with Advisory source weight, OR Strong-weighted terms from only 1 doc | Propose with advisory flag |
| **Low** | Frequency-based repeated unregistered terms, not from structured fields | Present separately, require user-provided definition |

## Step 5 — Present Candidates

Present candidates grouped by confidence tier, with source breadth and ambiguity flags visible:

```
## Glossary Sync — Proposed Terms

### High Confidence
| # | Term | Definition | NOT | Authority | Criticality | Sources | Layers | Deps | Flags | Decision |
|---|------|-----------|-----|-----------|-------------|---------|--------|------|-------|----------|
| 1 | Stockpile | A designated zone for storing hauled resources | Storage, warehouse | SYS-007 | Shared | 5 docs | 3 | SYS-007, SYS-002, SPEC-012 | — | Canonical / Alias / NOT / Reject |
| 2 | Mood Level | A colonist's current emotional state as a numeric value | Happiness, morale | SYS-003 | Core | 8 docs | 3 | SYS-003, SYS-006, balance-params | Ambiguity: "Mood" | Canonical / Alias / NOT / Reject |

### Medium Confidence (advisory)
| # | Term | Definition | NOT | Authority | Criticality | Sources | Layers | Flags | Decision |
|---|------|-----------|-----|-----------|-------------|---------|--------|-------|----------|
| 3 | danger-red | The semantic color token for critical warnings | — | color-system | Local | 1 doc | 1 | — | Canonical / Alias / NOT / Reject |

### Low Confidence (frequency-based)
| # | Term | Sources | Count | Layers | Flags | Decision |
|---|------|---------|-------|--------|-------|----------|
| 4 | Work Queue | systems, specs, tasks | 7 | 3 | Ambiguity: "Task Queue" | Canonical / Alias / NOT / Reject |

### Definition Conflicts
| Term | Source | Definition / Usage |
|------|--------|-------------------|
| Morale | SYS-003 | Numeric happiness value |
| Morale | balance-params | Composite state including stress + satisfaction |
| Morale | feedback-system | Visual indicator of emotional state |
→ **Must resolve before adding as Canonical.** Options: (a) align to authority source, (b) split into distinct terms, (c) defer

### Semantic Drift Risks
| Term | Layer | Meaning |
|------|-------|---------|
| Priority | task-system | Execution order |
| Priority | feedback-system | Alert severity |
| Priority | ui-kit | Visual emphasis |
→ **Overloaded term.** Options: (a) split into "Task Priority" / "Alert Priority" / "Visual Priority", (b) confirm intentional overloading

### Ambiguity Alerts
| # | Candidate | Collides With | Risk | Suggested Resolution |
|---|-----------|--------------|------|---------------------|
| 2 | Mood Level | Mood (existing) | Prefix variant | Alias of "Mood" or differentiate |
| 4 | Work Queue | Task Queue (candidate #5) | Synonym | Merge, or add one to NOT column |

### Term Hierarchy (optional)
| # | Term | Proposed Parent | Relationship |
|---|------|----------------|-------------|
| — | Raw Resource | Resource | subtype |
→ Confirm or skip. Hierarchy is optional.
```

**Decision per candidate:**
- **Canonical** — add as a new canonical glossary term with Definition, NOT, Authority, and Criticality columns filled
- **Alias** — do not add a new row; instead, add this term to an existing canonical term's NOT column as a recognized redirect
- **NOT** — add this term to an existing canonical term's NOT column as a discouraged synonym
- **Reject** — do not add to the glossary at all
- **Defer (conflict)** — term has an unresolved definition conflict or semantic drift. Do not add until resolved.

If `--dry-run` is specified, show the tables but do not offer decisions. Report the counts and stop.

Wait for user decisions before writing anything.

## Step 6 — Deprecated Term Advisory

After candidate processing, scan for stale glossary terms:

1. **Read all canonical terms** from the glossary.
2. **Grep all scaffold docs** (excluding changelogs, revision logs, and the glossary itself) for each canonical term.
3. **Flag terms that:**
   - Appear in **zero current scaffold docs** — possibly stale
   - Appear **only in historical docs** (changelogs, revision logs, deprecated docs) — possibly retired
   - Have a **near-match** that appears more frequently (possible rename that wasn't propagated)

Present as an advisory — do not auto-remove:

```
### Possibly Stale Glossary Terms
| Term | Last seen in | Current doc references | Status |
|------|-------------|----------------------|--------|
| Expedition | — | 0 | Possibly stale — no current references |
| Caravan | changelog only | 0 active | Possibly retired |
| Homestead | — | 0 (but "Settlement" has 12 refs) | Possibly renamed |

**These are advisory only.** Review and remove via `/scaffold-update-doc glossary` if confirmed stale.
```

## Step 7 — Write Confirmed Decisions

For each user decision:

1. **Canonical** — add a new row to `scaffold/design/glossary.md` Terms table in alphabetical position with all five columns: Term, Definition, NOT, Authority, Criticality. If a parent relationship was confirmed, add a row to the Term Hierarchy table.
2. **Alias** — add the term to the specified existing canonical term's NOT column. Do NOT mark it as discouraged — it's a recognized redirect. (The NOT column serves double duty: discouraged synonyms and recognized aliases both go there to prevent ambiguous usage.)
3. **NOT** — add the term to the specified existing canonical term's NOT column as a discouraged synonym.
4. **Reject** — no write. Logged in the report only.
5. **Defer** — no write. Term has an unresolved definition conflict or semantic drift. Logged in the report with the conflict details so it can be revisited.

After all writes:
- Update `Last Updated` to today's date.
- Add Changelog entry: `- YYYY-MM-DD: Synced N terms from [scope] — N canonical, N aliases, N NOT entries (scaffold-sync-glossary).`

## Step 8 — Report

```
## Glossary Synced

### Summary
| Metric | Value |
|--------|-------|
| Scope | [all / specific scopes] |
| Docs scanned | N |
| Candidates extracted | N |
| Already in glossary | N |
| Filtered (implementation/generic) | N |
| Filtered (not glossary-worthy) | N |
| Blocked (Draft-only) | N |
| Ambiguity alerts | N |
| Proposed to user | N |

### Decisions
| Decision | Count |
|----------|-------|
| Canonical (new terms) | N |
| Alias (redirected to existing) | N |
| NOT (discouraged synonym) | N |
| Deferred (conflict/drift) | N |
| Rejected | N |
| Glossary total terms | N (was M) |

### Source Breadth
| Layer | Terms extracted | Already known | Worthy | Proposed |
|-------|---------------|--------------|--------|----------|
| Design | N | N | N | N |
| Systems | N | N | N | N |
| References | N | N | N | N |
| Style | N | N | N | N |
| Input | N | N | N | N |

### Glossary Health
| Metric | Value |
|--------|-------|
| Total canonical terms | N |
| Terms missing Authority | N (should be 0) |
| Terms with no cross-doc usage | N |
| Terms heavily used but undefined | N |
| Competing synonym clusters | N |
| NOT terms still actively used in docs | N |
| Possibly stale terms | N |
| Definition conflicts detected | N |
| Semantic drift risks | N |
| Terms with unclear criticality | N |

### Dependency Impact (top 10 most-connected terms)
| Term | Dependent Systems | Dependent Docs | Criticality |
|------|------------------|---------------|-------------|
| [term] | SYS-###, SYS-###, ... | N docs | Core |
→ Renaming or redefining these terms has the highest blast radius.

### Blocked Candidates (awaiting stabilization)
| Term | Source | Blocked by |
|------|--------|-----------|
| [term] | [Draft-only doc] | [doc] needs Approved status |
```

## Rules

- **Never auto-write terms.** Every term must be user-confirmed via the decision model (Canonical / Alias / NOT / Reject).
- **Worthiness gate is mandatory.** Not every extracted term belongs in the glossary. The glossary is shared project vocabulary, not a mirror of every table label. Apply the worthiness criteria strictly.
- **Structured fields over prose.** Extract from tables, headers, and defined labels — not from free-text paragraphs. Prose extraction produces false positives.
- **Design-layer vocabulary only.** The glossary defines player-facing and design-facing terms. Implementation class names, engine node names, and code identifiers don't belong unless they're also the canonical design term.
- **Preserve alphabetical order.** All new entries go in alphabetical position in the glossary table.
- **NOT column is important.** When proposing terms, suggest NOT-column entries where obvious synonyms exist. If no clear synonyms, leave NOT empty — don't invent them.
- **Don't re-propose rejected terms.** If a term is already in the NOT column (meaning it was explicitly rejected as a synonym), don't propose it as a new canonical term.
- **Ambiguity must be surfaced.** Never propose a term that collides with or closely resembles an existing term without flagging the collision and suggesting a resolution.
- **Confidence tier determines presentation, not eligibility.** High, Medium, and Low candidates all go through the same worthiness gate. Confidence affects how they're presented and what defaults are suggested, not whether they're shown.
- **Source breadth is tracked explicitly.** Every candidate shows how many docs and layers reference it. Single-doc advisory candidates should be scrutinized more than cross-layer terms.
- **Draft-only terms are blocked, not rejected.** They may become eligible when their source doc stabilizes. Don't discard them — track them.
- **Deprecated term detection is advisory only.** Never auto-remove glossary terms. Present stale terms for human review.
- **Definition quality matters.** Proposed definitions must be short (one sentence preferred), disambiguating (explain what it IS and how it differs from similar concepts), non-circular (don't define a term using the term itself), system-agnostic where possible (define the concept, not which system owns it), and free of implementation details.
- **Every canonical term must have exactly one Authority.** The authority doc owns the definition. If multiple docs define a term differently, the conflict must be resolved before the term can be added as Canonical.
- **Definition conflicts block Canonical status.** A term with contradictory definitions across sources cannot be added until the user resolves the conflict (align, split, or defer).
- **Semantic drift must be surfaced.** When the same term means different things in different layers, flag it explicitly. Overloaded terms are a major source of long-term drift.
- **Criticality determines governance.** Core terms require ADR-level changes. Shared terms need cross-doc review. Local terms can evolve within their owning system.
- **Track dependencies for impact awareness.** Every canonical term should have a known set of dependent systems and docs. This enables safe renaming and refactoring.
- **Hierarchy is optional but encouraged.** Parent-child relationships between terms help prevent glossary bloat by making subtypes explicit rather than creating disconnected entries.
- **Pressure test before proposing.** Every candidate must survive the active challenge: does it reduce ambiguity, is it needed as a standalone term, or is it better expressed as an attribute/parameter/state of something else?
- **Idempotent.** Running sync-glossary twice with the same scope and no doc changes should produce zero new candidates.
- **Normalize before comparing.** Always normalize case, punctuation, hyphens/spaces, and singular/plural before checking against the known-terms set or comparing candidates to each other.

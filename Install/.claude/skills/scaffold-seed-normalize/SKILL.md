---
name: scaffold-seed-normalize
description: "Normalize the full candidate set after proposal. Merges duplicates, enforces boundaries, rebalances domains, classifies core vs support, validates scale. Writes result.json with the cleaned list."
argument-hint: (called by /scaffold-seed dispatcher — not user-invocable)
allowed-tools: Read, Write, Grep, Glob
---

# Normalize System Set

This skill is called by the `/scaffold-seed` dispatcher after all proposals are collected and before user confirmation. It takes the full candidate list and enforces global coherence — something per-requirement proposals cannot guarantee.

## Why This Exists

Each `/scaffold-seed-propose` call is locally optimal — it produces correct candidates for one upstream requirement. But the accumulated set can have:

- **Synonym duplicates** — "Task System" and "Job System" proposed from different sections
- **Overlapping responsibilities** — two systems that both claim the same state domain
- **Uneven domains** — one domain with 8 systems, another with 1
- **Missing core/support classification** — no way to prioritize during planning
- **Scale violations** — too many micro-systems or too few mega-systems

This skill fixes all of that in one global pass.

## Input

Read `.reviews/seed/action.json`:

```json
{
  "action": "normalize",
  "layer": "systems",
  "candidates": [...all proposed candidates...],
  "propose_rules": {
    "derivation_order": [...],
    "boundary_rules": [...],
    "kill_rules": [...],
    "ownership_rules": [...],
    "domain_definition": "...",
    "scale_target": "Expect 12-25 systems...",
    "grouping_hint": "...",
    "weight_heuristic": "...",
    "tier_consequences": {...}
  },
  "session_id": "..."
}
```

Note: inventory is deliberately excluded — normalization operates only on the candidate set and propose_rules.

## Process

Execute these passes in order. Each pass takes the output of the previous one.

### Pass 1 — Merge Duplicates

Scan all candidates for:
- **Synonym overlap** — different names, same player-facing purpose. Examples: "Work System" / "Task System" / "Job System" should be one system.
- **Responsibility overlap** — two systems whose `content_outline` describes the same state domain or player action.
- **Subsumption** — one system is a strict subset of another (e.g., "Priority System" is part of "Task System").

For each merge:
- Keep the candidate with the more descriptive name and broader scope
- Combine `source` fields (track which upstream sections produced each)
- Union `depends_on` lists
- Record the merge in `normalization_log`

### Pass 2 — Enforce Boundaries and Kill Weak Systems

For each surviving candidate, apply ALL of these tests. Fail any one → reject:

1. **Player-engagement test:** "The player engages with this system when ___, and if ignored ___ happens." If both blanks cannot be filled with concrete answers → reject.
2. **Technical concern test:** Reject candidates that describe engine implementation (pathfinding, rendering, save/load, networking) unless the design doc explicitly defines them as gameplay systems.
3. **WHAT not HOW test:** Systems describe game-world behavior, not engine architecture.
4. **Persistent state test:** Does this system have persistent state that changes over time? If not → reject. A system without state is not a system.
5. **Consequence test:** Can this system produce or react to gameplay consequences? If it neither causes nor responds to state changes → reject. It is inert.
6. **UI convenience test:** Does this system exist only to display information? If yes → reject. UI displays systems, it is not a system itself.

Record rejections in `normalization_log` with reasons.

### Pass 3 — Validate Ownership

Check the `owns`, `consumes`, and `produces` fields on all surviving candidates:
- **No overlapping ownership** — if two systems both claim to own the same state, they must be merged or the contested state assigned to exactly one owner. Record the resolution.
- **Consumes must have a source** — if a system consumes state, another system must own that state. Flag unresolved dependencies.
- **Produces must have consumers** — orphaned outputs are a smell (the system may be too isolated). Flag but don't reject.

### Pass 4 — Rebalance Domains

A domain is a persistent simulation state space with its own rules and player interaction surface. Review the `domain` field on all surviving candidates:
- **Consolidate fragmented domains** — if a domain has only 1 system, merge it into a related domain. A single-system domain is not a real domain.
- **Split overloaded domains** — if a domain has 6+ systems, split into sub-domains.
- **Ensure consistent granularity** — domains should have 2-5 systems each.
- **Every system must belong to exactly one domain** — no orphans, no dual membership.

Update `domain` fields as needed.

### Pass 5 — Enforce Scale

Check the total candidate count against `propose_rules.scale_target`:
- **Over 25** — Force additional merges. Identify the weakest candidates (least player engagement, most overlap with neighbors) and merge or reject.
- **Under 12** — Flag missing domains. Check coverage rules against the design doc sections to identify gaps. Add these as `suggested_additions` in the output.

### Pass 6 — Classify Core vs Support

Assign a `tier` field to each candidate:
- **core** — Player-loop-critical. The core loop cannot function without this system. Derived primarily from Priority 1 (Core Loop) systems.
- **support** — Enables or enriches core systems but isn't in the critical path. Derived from Secondary Loops, State Domains, and Player Verbs that supplement the core loop.

Classification criteria:
- If removing this system would break the core loop → `core`
- If removing this system would reduce depth but the game still functions → `support`

**Tier has consequences** (from `propose_rules.tier_consequences`):
- **core** systems must appear in the first vertical slice, must have at least 2 specs, cannot be deferred past Phase 1.
- **support** systems can be deferred to later phases, can depend on core systems, may start with 1 spec if the domain is narrow.

Include these consequences in the `tier_note` field so the user sees the implications during confirmation.

### Pass 7 — Contract Compliance

If `propose_rules.contract_rules` exist in action.json and the design doc defines Failure and/or Risk contracts:

- **Failure Contract** — For each candidate that can produce failure states, verify it has a `failure_contract` field. Flag systems that produce failures but don't declare which contract rules apply.
- **Risk Contract** — Verify every candidate has a `risk_class` field (risk_generating, risk_neutral, or risk_immune). Flag any system with no classification. Check that classifications align with the contract's MUST/MUST NEVER lists — a system classified as risk_neutral must not overlap with activities on the MUST list.

Record contract violations in `normalization_log`.

### Pass 8 — Weight Validation

Check each candidate against the weight heuristic:

> "A system should represent a cohesive player-facing domain that would reasonably have 2-6 specs."

- **Micro-system** (would have 0-1 specs) — likely should be merged into a parent system. Flag it.
- **God-system** (would have 7+ specs) — likely should be split. Flag it.

These are flags, not automatic actions — the user decides during confirmation.

## Output

Write `.reviews/seed/result.json`:

```json
{
  "normalized_candidates": [
    {
      "proposed_id": "sys-task",
      "name": "Task System",
      "type": "system",
      "domain": "Colonist Domain",
      "tier": "core",
      "tier_note": "Must appear in first vertical slice. Must have at least 2 specs.",
      "source": "Core Loop step 3 (Adjust), Player Verb (Prioritize, Assign)",
      "depends_on": ["sys-colonist-state"],
      "owns": "colonist work assignments, task queue, task priorities",
      "consumes": "colonist skills (from Colonist System), room availability (from Room System)",
      "produces": "task_completed, task_failed, colonist_idle",
      "content_outline": "...",
      "needs": {},
      "risk_class": "risk_neutral",
      "failure_contract": ["upstream player decision required", "mid-stage warning required"],
      "weight_flag": null
    }
  ],
  "normalization_log": [
    {
      "action": "merged",
      "candidates": ["sys-task", "sys-work", "sys-job-assignment"],
      "result": "sys-task",
      "reason": "All three describe the same player-facing domain: assigning colonists to work"
    },
    {
      "action": "rejected",
      "candidate": "sys-pathfinding",
      "reason": "Technical concern — not a player-facing behavior domain"
    },
    {
      "action": "domain_rebalanced",
      "candidate": "sys-exposure",
      "old_domain": "Colonist Domain",
      "new_domain": "Risk Domain",
      "reason": "Better fit — exposure is a risk mechanic, not a colonist state"
    },
    {
      "action": "ownership_resolved",
      "state": "colonist_stress",
      "claimants": ["sys-colonist", "sys-needs"],
      "owner": "sys-needs",
      "reason": "Stress is a need metric — Needs System owns it, Colonist System consumes it"
    },
    {
      "action": "killed",
      "candidate": "sys-notification",
      "reason": "No persistent state — exists only to display alerts from other systems (UI convenience)"
    }
  ],
  "suggested_additions": [],
  "scale_check": {
    "count": 16,
    "in_range": true,
    "target": "12-25"
  },
  "domain_summary": {
    "Simulation Core": {"count": 3, "systems": ["sys-time", "sys-event", "sys-instability"]},
    "Colonist Domain": {"count": 3, "systems": ["sys-colonist", "sys-needs", "sys-task"]}
  }
}
```

## Principles

- **Be aggressive with merges.** Two systems that share player-facing purpose are one system. When in doubt, merge.
- **Preserve traceability.** Every merge, rejection, and reclassification goes in the log. The user sees exactly what changed and why.
- **Don't invent systems.** Normalization removes and reorganizes — it does not add. New systems only appear as `suggested_additions` for the user to approve.
- **Respect the design doc.** All decisions trace back to what the design doc says, not what "seems right" abstractly.

## What NOT to Do

- **Don't create files.** This is a normalization pass, not a creation step.
- **Don't read files beyond action.json.** The candidates and propose_rules are your complete context.
- **Don't override the user's intent.** If a candidate clearly maps to a design doc section, keep it even if it seems small. Flag it with `weight_flag` instead of removing it.
